"""Validate the portable bundle using only Python's standard library.

Run from any directory. --relocate copies the entire skills collection to an
isolated temporary directory and exercises the UI CLI without a Studio setting.
Game binaries, live Packs and original author paths are never used.
"""
from __future__ import annotations

import argparse
import ast
from contextlib import closing
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
sys.dont_write_bytecode = True


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def check_bundle(root, verify_manifest=True):
    errors = []
    skills = sorted((root / 'skills').glob('warhammer-*'))
    counts = {'skills': len(skills), 'markdown_links': 0, 'html_links': 0, 'python_files': 0, 'catalog_sources': 0}
    if len(skills) != 8:
        errors.append(f'Expected 8 skills, found {len(skills)}')
    for skill in skills:
        entry = skill / 'SKILL.md'
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
            target = (path.parent / unquote(link)).resolve()
            counts['markdown_links'] += 1
            if not target.is_relative_to(root.resolve()) or not target.exists():
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
            target = (path.parent / unquote(url.path)).resolve()
            if not target.is_relative_to(root.resolve()) or not target.exists():
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
                if not path.is_file() or digest(path) != sha:
                    errors.append(f'Manifest mismatch: {relative}')
            actual = {p.relative_to(root).as_posix() for p in root.rglob('*')
                      if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts
                      and p.name != 'manifest.json'}
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
            ['query', '--database', str(db), '--kind', 'component', 'spell_parent', '--limit', '3'],
            ['inspect', str(xml), '--id', 'spell_parent'],
            ['check', str(xml), '--baseline', str(xml)],
        ]
        for command in commands:
            result = subprocess.run([sys.executable, '-X', 'utf8', str(script), *command],
                                    cwd=root, env=env, capture_output=True, text=True, encoding='utf-8')
            if result.returncode:
                errors.append(f'Relocation {command[0]} failed: {result.stderr or result.stdout}')
            else:
                data = json.loads(result.stdout)
                if command[0] == 'query' and data.get('returned', 0) < 1:
                    errors.append('Relocated query returned no spell_parent')
                if command[0] == 'inspect' and data.get('matches', 0) < 1:
                    errors.append('Relocated inspect found no spell_parent')
                if command[0] != 'query' and data.get('studio_commit') != '7e3e1be568fac3f5e9362d0494665fc549dc22eb':
                    errors.append('Relocated parser has incorrect upstream provenance')
        return {'commands': len(commands), **counts}, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--relocate', action='store_true')
    args = parser.parse_args()
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
