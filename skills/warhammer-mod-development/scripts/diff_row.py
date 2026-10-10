#!/usr/bin/env python3
"""Read-only, exact RPFM TSV row comparison, including composite keys."""
import argparse
import json
import re
import sys
from pathlib import Path


def read_table(path):
    raw = Path(path).read_bytes()
    if raw.startswith(b'\xef\xbb\xbf'):
        raise ValueError(f'{path}: UTF-8 BOM is not accepted')
    lines = raw.decode('utf-8').splitlines()
    if len(lines) < 2:
        raise ValueError(f'{path}: missing header or metadata')
    columns = lines[0].split('\t')
    if any(not c for c in columns) or len(set(columns)) != len(columns):
        raise ValueError(f'{path}: empty or duplicate column names')
    meta = re.fullmatch(r'#([^;\t]+);(\d+);db/([^/\t]+)/([^/\t]+)\t*', lines[1])
    if not meta or meta[1] != meta[3] or meta[4].endswith('.tsv'):
        raise ValueError(f'{path}: invalid DB metadata')
    rows = []
    for line_number, line in enumerate(lines[2:], 3):
        values = line.split('\t')
        if len(values) != len(columns):
            raise ValueError(f'{path}:{line_number}: expected {len(columns)} columns, got {len(values)}')
        rows.append((line_number, values))
    return meta[1], int(meta[2]), columns, rows


def select_row(table, key_columns, key_values, path):
    columns, rows = table[2:]
    if len(key_columns) != len(key_values) or len(set(key_columns)) != len(key_columns):
        raise ValueError('Each key needs exactly one value per distinct key column')
    missing = set(key_columns) - set(columns)
    if missing:
        raise ValueError(f'{path}: key columns not found: {sorted(missing)}')
    indexes = [columns.index(c) for c in key_columns]
    matches = [(number, row) for number, row in rows
               if tuple(row[i] for i in indexes) == tuple(key_values)]
    if len(matches) != 1:
        raise ValueError(f'{path}: expected exactly one key match, found {len(matches)}')
    return matches[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--template', required=True)
    parser.add_argument('--mod', required=True)
    parser.add_argument('--key-columns', nargs='+', required=True)
    parser.add_argument('--template-key', nargs='+', required=True)
    parser.add_argument('--mod-key', nargs='+', required=True)
    parser.add_argument('--allow', action='append', default=[])
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    try:
        template = read_table(args.template)
        mod = read_table(args.mod)
        if template[:3] != mod[:3]:
            raise ValueError('Table name, version, columns and column order must match')
        unknown = set(args.allow) - set(template[2])
        if unknown:
            raise ValueError(f'Unknown allowed fields: {sorted(unknown)}')
        old_line, old = select_row(template, args.key_columns, args.template_key, args.template)
        new_line, new = select_row(mod, args.key_columns, args.mod_key, args.mod)
        differences = [dict(field=c, template=a, mod=b, allowed=c in args.allow)
                       for c, a, b in zip(template[2], old, new) if a != b]
        result = dict(table=template[0], version=template[1],
                      template_line=old_line, mod_line=new_line, differences=differences,
                      passed=all(d['allowed'] for d in differences))
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            for d in differences:
                label = 'ALLOWED' if d['allowed'] else 'REVIEW'
                print(f"{label} {d['field']}: {d['template']!r} -> {d['mod']!r}")
            print(f"{'PASS' if result['passed'] else 'REVIEW'}: {len(differences)} changed fields")
        return 0 if result['passed'] else 1
    except (OSError, UnicodeError, ValueError) as exc:
        if args.json:
            print(json.dumps({'passed': False, 'error': str(exc)}, ensure_ascii=False))
        else:
            print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
