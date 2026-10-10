"""Validate the portable bundle using only Python's standard library.

Run from any directory. --relocate copies the entire skills collection to an
isolated temporary directory and exercises UI, DB, MCP and raw-image helpers.
Game binaries, live Packs and original author paths are never used.
"""
from __future__ import annotations

import argparse
import ast
from contextlib import closing
from datetime import date
from html.parser import HTMLParser
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from urllib.parse import unquote
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_SKILLS = {
    'warhammer-mod-development', 'warhammer-mod-character-creation',
    'warhammer-mod-translation', 'warhammer-mod-art', 'warhammer-ui',
}
sys.dont_write_bytecode = True


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def bundle_files(root):
    return sorted(p for p in root.rglob('*')
                  if p.is_file() and '.git' not in p.relative_to(root).parts
                  and '__pycache__' not in p.relative_to(root).parts
                  and p.suffix not in ('.pyc', '.pyo') and p.name != 'manifest.json')


def write_manifest(root):
    files = {p.relative_to(root).as_posix(): digest(p) for p in bundle_files(root)}
    manifest = {'format': 1, 'date': date.today().isoformat(), 'files': files}
    (root / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n',
                                       encoding='utf-8', newline='\n')
    return len(files)


def check_bundle(root, verify_manifest=True):
    errors = []
    resolved_root = root.resolve()
    resolved_targets = {}

    def resolve_target(path):
        key = os.path.abspath(path)
        if key not in resolved_targets:
            resolved_targets[key] = Path(key).resolve()
        return resolved_targets[key]

    skills = sorted((root / 'skills').glob('warhammer-*'))
    counts = {'skills': len(skills), 'markdown_links': 0, 'html_links': 0, 'python_files': 0, 'catalog_sources': 0}
    if {skill.name for skill in skills} != PUBLIC_SKILLS:
        errors.append(f'Expected exactly the 5 public skills, found {[skill.name for skill in skills]}')
    for path in bundle_files(root):
        if not resolve_target(path).is_relative_to(resolved_root):
            errors.append(f'External file dependency: {path.relative_to(root)}')
    for skill in skills:
        entry = skill / 'SKILL.md'
        if not entry.is_file():
            errors.append(f'Missing entry: {entry}')
            continue
        text = entry.read_text(encoding='utf-8-sig')
        front = re.match(r'^---\n(.*?)\n---\n', text, re.S)
        if not front or not re.search(r'^name: ' + re.escape(skill.name) + r'$', front[1], re.M):
            errors.append(f'Invalid name/frontmatter: {entry}')
        if not front or not re.search(r'^description: .+', front[1], re.M):
            errors.append(f'Missing description: {entry}')
    for path in root.rglob('*.md'):
        rel = path.relative_to(root)
        if any(x in rel.parts for x in ('.git', 'vendor', 'sources')):
            continue
        text = path.read_text(encoding='utf-8-sig')
        if re.search(r'[A-Za-z]:[/\\](?:Users|git|SteamLibrary)', text):
            errors.append(f'Author-specific absolute path: {rel}')
        for link in re.findall(r'\[[^\]\n]*\]\(([^)\n]+)\)', text):
            link = link.strip('<>').split('#', 1)[0]
            if not link or re.match(r'^[a-z]+:', link, re.I):
                continue
            target = resolve_target(path.parent / unquote(link))
            counts['markdown_links'] += 1
            if not target.is_relative_to(resolved_root) or not target.exists():
                errors.append(f'Broken or escaping link: {rel} -> {link}')
    for path in root.rglob('*.py'):
        if '.git' in path.parts:
            continue
        try:
            ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
            counts['python_files'] += 1
        except (SyntaxError, UnicodeError) as exc:
            errors.append(f'Python syntax: {path}: {exc}')
    ui = root / 'skills/warhammer-ui'
    class Links(HTMLParser):
        def handle_starttag(self, tag, attrs):
            self.links.extend(v for k, v in attrs if k in ('href', 'src') and v)

    for path in (ui / 'references/sources/documentation').rglob('*.html'):
        parser = Links()
        parser.links = []
        parser.feed(path.read_text(encoding='utf-8-sig'))
        for link in parser.links:
            url = urlsplit(link)
            if url.scheme or url.netloc or not url.path:
                continue
            counts['html_links'] += 1
            target = resolve_target(path.parent / unquote(url.path))
            if not target.is_relative_to(resolved_root) or not target.exists():
                errors.append(f'Broken HTML dependency: {path.relative_to(root)} -> {link}')
    db = ui / 'references/ui-catalog.sqlite'
    with closing(sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True)) as con:
        if con.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            errors.append('SQLite integrity check failed')
        for relative, sha in con.execute('SELECT path, sha256 FROM files'):
            source = ui / 'references/sources' / relative
            if not source.is_file() or digest(source) != sha:
                errors.append(f'Catalog source missing/mismatch: {relative}')
            counts['catalog_sources'] += 1
    if verify_manifest:
        manifest_path = root / 'manifest.json'
        if not manifest_path.exists():
            errors.append('manifest.json missing')
        else:
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            for relative, sha in manifest['files'].items():
                path = root / relative
                if not resolve_target(path).is_relative_to(resolved_root) or not path.is_file() or digest(path) != sha:
                    errors.append(f'Manifest mismatch: {relative}')
            actual = {p.relative_to(root).as_posix() for p in bundle_files(root)}
            if actual != set(manifest['files']):
                errors.append('Manifest file set mismatch')
            counts['manifest_files'] = len(manifest['files'])
    return counts, errors


def relocated_smoke():
    with tempfile.TemporaryDirectory(prefix='warhammer-skills-portable-') as temporary:
        root = Path(temporary)
        shutil.copytree(ROOT / 'skills', root / 'skills', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        counts, errors = check_bundle(root, verify_manifest=False)
        ui = root / 'skills/warhammer-ui'
        script = ui / 'scripts/twui_kb.py'
        xml = ui / 'references/sources/ui/battle ui/hud_battle.twui.xml'
        db = ui / 'references/ui-catalog.sqlite'
        env = {**os.environ, 'PYTHONUTF8': '1', 'PYTHONDONTWRITEBYTECODE': '1'}
        env.pop('TWUI_STUDIO_ROOT', None)
        commands = [
            ('ui-query', [sys.executable, str(script), 'query', '--database', str(db), '--kind', 'component', 'spell_parent', '--limit', '3']),
            ('ui-inspect', [sys.executable, str(script), 'inspect', str(xml), '--id', 'spell_parent']),
            ('ui-check', [sys.executable, str(script), 'check', str(xml), '--baseline', str(xml)]),
        ]

        development = root / 'skills/warhammer-mod-development/scripts'
        fixtures = root / 'fixtures'
        fixtures.mkdir()
        table = fixtures / 'data__.tsv'
        table.write_text('key\tvalue\n#sample_tables;1;db/sample_tables/data__\na\t1\n', encoding='utf-8')
        commands.append(('db-row', [sys.executable, str(development / 'diff_row.py'), '--template', str(table),
                         '--mod', str(table), '--key-columns', 'key', '--template-key', 'a', '--mod-key', 'a', '--json']))
        binary = fixtures / 'raw.bin'
        binary.write_bytes(b'prefix\x00portable_anchor\x00suffix')
        commands.append(('raw-image', [sys.executable, str(development / 'wh3_dump.py'), '--dump', str(binary),
                         '--format', 'raw', 'find', '--text', 'portable_anchor']))
        game = fixtures / 'game'
        game.mkdir()
        (game / 'wh3_mcp_result.json').write_text('{"status":"ok","result":{"turn":42}}', encoding='utf-8')
        (game / 'wh3_mcp_script_errors.log').write_text('ERROR: portable probe\n', encoding='utf-8')
        (game / 'script_log_1_1.txt').write_text('ERROR: synthetic fixture\n', encoding='utf-8')
        commands.append(('mcp-evidence', [sys.executable, str(development / 'wh3_mcp_evidence.py'),
                         '--game-dir', str(game), '--out', str(fixtures / 'evidence')]))
        export = fixtures / 'export/db/sample_tables'
        export.mkdir(parents=True)
        shutil.copyfile(table, export / 'data__.tsv')
        node = shutil.which('node')
        if node:
            baseline = fixtures / 'baseline.json'
            commands.extend([
                ('version-snapshot', [node, str(development / 'audit-version.js'), '--source', str(fixtures / 'export'), '--snapshot', str(baseline), '--json']),
                ('version-compare', [node, str(development / 'audit-version.js'), '--source', str(fixtures / 'export'), '--baseline', str(baseline), '--json']),
            ])

        for name, command in commands:
            result = subprocess.run(command,
                                    cwd=root, env=env, capture_output=True, text=True, encoding='utf-8')
            if result.returncode:
                errors.append(f'Relocation {name} failed: {result.stderr or result.stdout}')
            else:
                data = json.loads(result.stdout)
                if name == 'ui-query' and data.get('returned', 0) < 1:
                    errors.append('Relocated query returned no spell_parent')
                if name == 'ui-inspect' and data.get('matches', 0) < 1:
                    errors.append('Relocated inspect found no spell_parent')
                if name in ('ui-inspect', 'ui-check') and data.get('studio_commit') != '7e3e1be568fac3f5e9362d0494665fc549dc22eb':
                    errors.append('Relocated parser has incorrect upstream provenance')
                if name == 'db-row' and (not data.get('passed') or data.get('differences')):
                    errors.append('Relocated DB comparison did not preserve the fixture')
                if name == 'raw-image' and data.get('result', {}).get('total') != 1:
                    errors.append('Relocated raw-image search did not find its anchor')
                if name == 'mcp-evidence':
                    evidence = json.loads((fixtures / 'evidence/manifest.json').read_text(encoding='utf-8'))
                    if evidence.get('summary', {}).get('matched_error_line_count', 0) != 2:
                        errors.append('Relocated MCP evidence omitted synthetic error lines')
        return {'commands': len(commands), 'node_audit': 'checked' if node else 'not_checked: Node.js absent', **counts}, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--relocate', action='store_true')
    parser.add_argument('--write-manifest', action='store_true', help='explicitly refresh hashes; run validation afterwards')
    args = parser.parse_args()
    if args.write_manifest:
        print(json.dumps({'status': 'manifest_written', 'files': write_manifest(ROOT)}))
        return 0
    counts, errors = check_bundle(ROOT)
    if args.relocate:
        relocated, failures = relocated_smoke()
        counts['relocation'] = relocated
        errors.extend(failures)
    print(json.dumps({'status': 'PASS' if not errors else 'FAIL', 'checks': counts, 'errors': errors},
                     ensure_ascii=False, indent=2))
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
