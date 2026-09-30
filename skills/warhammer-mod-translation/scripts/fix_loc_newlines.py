#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Normalize loc TSV newlines to RPFM on-disk form: two backslashes + n.

RPFM import_tsv treats \\n in the TSV as the loc newline escape.
A single backslash+n, or a real LF/CR inside the text column, is wrong.

Usage:
  python fix_loc_newlines.py <file-or-dir> [<file-or-dir> ...]
  python fix_loc_newlines.py --check <path>
  python fix_loc_newlines.py --dry-run <path>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

BS = "\\"
TARGET = BS + BS + "n"  # on-disk \\n  (bytes 5C 5C 6E)
SINGLE = BS + "n"  # on-disk \n   (bytes 5C 6E)


def iter_targets(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for path in paths:
        if path.is_file():
            out.append(path)
            continue
        if path.is_dir():
            out.extend(sorted(path.rglob("*.tsv")))
            out.extend(sorted(path.rglob("*.loc")))
    # unique, keep order
    seen: set[Path] = set()
    uniq: list[Path] = []
    for p in out:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            uniq.append(p)
    return uniq


def stitch_physical_breaks(text: str) -> tuple[str, int]:
    """Join TSV records that were split by real newlines inside the text column."""
    lines = text.splitlines()
    if not lines:
        return text, 0
    out: list[str] = [lines[0]]
    joins = 0
    for line in lines[1:]:
        prev = out[-1]
        prev_tabs = prev.count("\t")
        # header / meta / complete 3-col row stay as-is
        if prev_tabs >= 2 or prev.startswith("key\t") or prev.startswith("#"):
            out.append(line)
            continue
        # continuation of a broken record
        out[-1] = prev + TARGET + line
        joins += 1
    joined = "\n".join(out)
    if text.endswith("\n"):
        joined += "\n"
    return joined, joins


def upgrade_single_backslash_n(text: str) -> tuple[str, int]:
    """Turn lone \\n (5C 6E) into \\\\n (5C 5C 6E). Leave already-doubled alone."""
    out: list[str] = []
    n = 0
    i = 0
    length = len(text)
    while i < length:
        if text[i] == BS and i + 1 < length and text[i + 1] == "n":
            if i > 0 and text[i - 1] == BS:
                out.append(SINGLE)
                i += 2
                continue
            out.append(TARGET)
            n += 1
            i += 2
            continue
        out.append(text[i])
        i += 1
    return "".join(out), n


def normalize(text: str) -> tuple[str, int, int]:
    stitched, joins = stitch_physical_breaks(text)
    upgraded, singles = upgrade_single_backslash_n(stitched)
    return upgraded, joins, singles


def process(path: Path, write: bool) -> tuple[bool, str]:
    original = path.read_text(encoding="utf-8")
    fixed, joins, singles = normalize(original)
    changed = fixed != original
    note = f"{path}  physical_joins={joins}  single_to_double={singles}"
    if changed and write:
        path.write_text(fixed, encoding="utf-8", newline="\n")
        note += "  wrote"
    elif changed:
        note += "  needs_fix"
    else:
        note += "  ok"
    return changed, note


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--check", action="store_true", help="exit 1 if any file needs fix")
    parser.add_argument("--dry-run", action="store_true", help="report only, do not write")
    args = parser.parse_args(argv)

    files = iter_targets(args.paths)
    if not files:
        print("no .tsv/.loc files found", file=sys.stderr)
        return 2

    write = not args.check and not args.dry_run
    dirty = 0
    for path in files:
        try:
            changed, note = process(path, write=write)
        except OSError as exc:
            print(f"{path}  error: {exc}", file=sys.stderr)
            return 2
        print(note)
        if changed:
            dirty += 1

    print(f"files={len(files)} needs_fix={dirty}")
    if args.check and dirty:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
