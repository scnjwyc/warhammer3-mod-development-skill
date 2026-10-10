#!/usr/bin/env node
'use strict';
// Adapted from the shared warhammer-mod audit workflow. No bundled author baseline.
// Reads exports/installed files; only --snapshot creates a new JSON file.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { TextDecoder } = require('util');
const opts = {};
const args = process.argv.slice(2);
function error(message) { throw new Error(message); }
function hashFile(file) {
  const hash = crypto.createHash('sha256');
  const fd = fs.openSync(file, 'r');
  const block = Buffer.allocUnsafe(1024 * 1024);
  try {
    let count;
    while ((count = fs.readSync(fd, block, 0, block.length, null)) > 0) hash.update(block.subarray(0, count));
  } finally { fs.closeSync(fd); }
  return hash.digest('hex');
}
function object(value) { return value && typeof value === 'object' && !Array.isArray(value); }
function validHash(value) { return typeof value === 'string' && /^[a-f0-9]{64}$/.test(value); }
function validateBaseline(base) {
  if (!object(base) || base.format !== 1 || !object(base.tables) || !Object.keys(base.tables).length ||
      !object(base.packs) || !object(base.scripts) ||
      (base.schema !== null && !validHash(base.schema)) || typeof base.gameVersion !== 'string' ||
      (base.buildId !== null && typeof base.buildId !== 'string')) error('Invalid baseline structure');
  for (const [name, row] of Object.entries(base.tables)) {
    if (!object(row) || !validHash(row.sha256) || !Number.isSafeInteger(row.version) || row.version < 0 ||
        !Number.isSafeInteger(row.rows) || row.rows < 0 || !Array.isArray(row.columns) || !row.columns.length ||
        row.columns.some(c => typeof c !== 'string' || !c) || new Set(row.columns).size !== row.columns.length)
      error('Invalid baseline table: ' + name);
  }
  for (const group of [base.packs, base.scripts]) {
    for (const [name, hash] of Object.entries(group)) if (!validHash(hash)) error('Invalid baseline hash: ' + name);
  }
}
try {
  for (let i = 0; i < args.length; i++) {
    const flag = args[i];
    if (['--json', '--help'].includes(flag)) { opts[flag.slice(2)] = true; continue; }
    if (!['--source', '--game', '--baseline', '--snapshot', '--game-version', '--schema'].includes(flag) ||
        !args[i + 1] || args[i + 1].startsWith('--')) error('Invalid argument: ' + flag);
    opts[flag.slice(2)] = args[++i];
  }
  if (opts.help) {
    console.log('node audit-version.js --source <export-root> (--baseline <json> | --snapshot <new-json>) [--schema <ron>] [--game <game-root>] [--game-version <verified-version>] [--json]\nCompare is read-only; snapshot never overwrites. Exit: 0 consistent, 1 drift/bad export, 2 arguments/environment/baseline.');
    process.exit(0);
  }
  if (!!opts.baseline === !!opts.snapshot) error('Provide exactly one of --baseline or --snapshot');
  if (!opts.source) error('Provide --source <export-root>');
  let baseline = null;
  if (opts.baseline) {
    baseline = JSON.parse(fs.readFileSync(opts.baseline, 'utf8'));
    validateBaseline(baseline);
  }
  const source = path.resolve(opts.source);
  const db = path.join(source, 'db');
  if (!fs.existsSync(db) || !fs.statSync(db).isDirectory()) error('DB export directory not found: ' + db);
  const facts = { format: 1, sourceRoot: source, gameVersion: opts['game-version'] || 'unknown',
    buildId: null, schema: null, packs: {}, scripts: {}, tables: {} };
  const issues = [], notes = [];
  for (const entry of fs.readdirSync(db, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    if (!entry.isDirectory() || !entry.name.endsWith('_tables')) continue;
    const file = path.join(db, entry.name, 'data__.tsv');
    if (!fs.existsSync(file)) { issues.push('Missing TSV export: ' + entry.name); continue; }
    try {
      const bytes = fs.readFileSync(file);
      if (bytes.subarray(0, 3).equals(Buffer.from([0xef, 0xbb, 0xbf]))) error('UTF-8 BOM');
      const text = new TextDecoder('utf-8', { fatal: true }).decode(bytes);
      const lines = text.split(/\r?\n/);
      if (lines.at(-1) === '') lines.pop();
      if (lines.length < 2) error('Missing header/metadata');
      const columns = lines[0].split('\t');
      if (columns.some(c => !c) || new Set(columns).size !== columns.length) error('Empty/duplicate column names');
      const meta = lines[1].match(/^#([^;\t]+);(\d+);db\/([^/\t]+)\/data__\t*$/);
      if (!meta || meta[1] !== entry.name || meta[3] !== entry.name || !Number.isSafeInteger(Number(meta[2]))) error('Invalid metadata');
      for (let i = 2; i < lines.length; i++) if (lines[i].split('\t').length !== columns.length) error('Column count at line ' + (i + 1));
      facts.tables[entry.name] = { sha256: crypto.createHash('sha256').update(bytes).digest('hex'),
        version: Number(meta[2]), columns, rows: lines.length - 2 };
    } catch (exc) { issues.push(entry.name + ': ' + exc.message); }
  }
  if (!Object.keys(facts.tables).length) issues.push('No valid TSV tables');
  if (opts.schema) facts.schema = hashFile(opts.schema);
  else notes.push('Schema check omitted; provide --schema');
  if (opts.game) {
    const game = path.resolve(opts.game);
    if (!fs.statSync(game).isDirectory()) error('Invalid game directory');
    facts.gameRoot = game;
    for (const name of ['db.pack', 'local_cn.pack', 'local_en.pack', 'data_script.pack']) {
      const file = path.join(game, 'data', name);
      if (fs.existsSync(file)) facts.packs[name] = hashFile(file);
      else if (name.startsWith('local_')) notes.push('Optional language Pack absent: ' + name);
      else issues.push('Missing selected game Pack: ' + name);
    }
    const manifest = path.resolve(game, '..', '..', 'appmanifest_1142710.acf');
    if (fs.existsSync(manifest)) {
      const match = fs.readFileSync(manifest, 'utf8').match(/"buildid"\s+"(\d+)"/i);
      if (match) facts.buildId = match[1];
      else notes.push('Steam build ID not found in manifest');
    } else notes.push('Steam manifest absent; build ID unknown');
  } else notes.push('Installed game checks omitted; provide --game');
  const lib = path.join(source, 'script', '_lib');
  if (fs.existsSync(lib)) {
    for (const entry of fs.readdirSync(lib, { withFileTypes: true })) {
      if (entry.isFile() && entry.name.endsWith('.lua')) facts.scripts[entry.name] = hashFile(path.join(lib, entry.name));
    }
  }
  if (!Object.keys(facts.scripts).length) notes.push('No exported script/_lib/*.lua; API-library checks omitted');
  if (!opts['game-version']) notes.push('Game version label unverified/unknown');
  const changes = [];
  function change(kind, name, before, after) { changes.push({ kind, name, before: before ?? null, after: after ?? null }); }
  if (baseline) {
    for (const name of new Set([...Object.keys(baseline.tables), ...Object.keys(facts.tables)])) {
      const old = baseline.tables[name], now = facts.tables[name];
      if (!old || !now) { change('table presence', name, !!old, !!now); continue; }
      for (const field of ['version', 'columns', 'rows', 'sha256']) {
        if (JSON.stringify(old[field]) !== JSON.stringify(now[field])) change('table ' + field, name, old[field], now[field]);
      }
    }
    for (const group of ['packs', 'scripts']) {
      for (const name of new Set([...Object.keys(baseline[group]), ...Object.keys(facts[group])])) {
        if (baseline[group][name] !== facts[group][name]) change(group + ' fingerprint', name, baseline[group][name], facts[group][name]);
      }
    }
    if (baseline.schema !== facts.schema) change('schema fingerprint', 'schema', baseline.schema, facts.schema);
    if (baseline.buildId !== facts.buildId) change('Steam build ID', 'buildId', baseline.buildId, facts.buildId);
    if (opts['game-version'] && baseline.gameVersion !== facts.gameVersion) change('version label', 'gameVersion', baseline.gameVersion, facts.gameVersion);
  }
  const passed = !issues.length && !changes.length;
  if (opts.snapshot && passed) {
    const dest = path.resolve(opts.snapshot);
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    fs.writeFileSync(dest, JSON.stringify({ ...facts, notes }, null, 2) + '\n', { flag: 'wx' });
  }
  const result = { passed, mode: opts.snapshot ? 'snapshot' : 'compare',
    tableCount: Object.keys(facts.tables).length, issues, changes, notes, facts };
  if (opts.json) console.log(JSON.stringify(result, null, 2));
  else {
    console.log(`${passed ? 'PASS' : 'REVIEW'}: ${result.tableCount} tables, ${issues.length} export/file issues, ${changes.length} changes`);
    for (const item of issues) console.log('ISSUE: ' + item);
    for (const item of changes) console.log('CHANGE: ' + item.kind + ' / ' + item.name);
    for (const item of notes) console.log('SCOPE: ' + item);
  }
  process.exitCode = passed ? 0 : 1;
} catch (exc) {
  if (opts.json) console.log(JSON.stringify({ passed: false, error: exc.message }));
  else console.error('ERROR: ' + exc.message);
  process.exitCode = 2;
}
