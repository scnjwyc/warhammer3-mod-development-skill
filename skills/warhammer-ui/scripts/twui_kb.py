#!/usr/bin/env python3
"""Read-only TWUI inspection and a rebuildable SQLite knowledge index.

Uses the bundled, unmodified TWUI Studio parser by default; --studio can
select a different trusted checkout. Upstream notices are under vendor/. index writes only its explicitly named database/report. Other
commands open sources and databases read-only. No game or Pack mutation.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True


def emit(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def studio_path(value):
    candidates = [Path(value)] if value else []
    if os.environ.get("TWUI_STUDIO_ROOT"):
        candidates.append(Path(os.environ["TWUI_STUDIO_ROOT"]))
    candidates.append(Path(__file__).resolve().parents[1] / "vendor" / "TWUI_Studio")
    for parent in (Path.cwd(), *Path.cwd().parents):
        candidates.append(parent / "tools" / "TWUI_Studio")
    for path in candidates:
        if (path / "model.py").is_file() and (path / "diagnostics.py").is_file():
            return path.resolve()
    raise ValueError("Specify --studio <TWUI_Studio clone> or TWUI_STUDIO_ROOT")


def load_parser(value):
    root = studio_path(value)
    sys.path.insert(0, str(root))
    from model import Document
    revision_file = root / "UPSTREAM_COMMIT"
    if revision_file.is_file():
        return Document, root, revision_file.read_text(encoding="utf-8").strip()
    try:
        revision = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True,
            stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        revision = "unknown"
    return Document, root, revision


def read_document(path, parser):
    raw = Path(path).read_bytes()
    return parser(raw.decode("utf-8-sig")), hashlib.sha256(raw).hexdigest()


def line_locator(source):
    starts = [-1] + [i for i, c in enumerate(source) if c == "\n"]
    return lambda node: bisect_right(starts, node.start)


def issue_rows(doc):
    line = line_locator(doc.source)
    return [{"code": issue.code, "severity": issue.severity,
             "lines": [line(n) for n in issue.nodes],
             "nodes": [n.get("id", n.get("this", n.tag)) for n in issue.nodes]}
            for issue in doc.issues]


def issue_key(row):
    return (row["code"], row["severity"], tuple(row["nodes"]))


def check(args):
    parser, root, revision = load_parser(args.studio)
    doc, digest = read_document(args.xml, parser)
    rows = issue_rows(doc)
    blocking = [r for r in rows if r["severity"] == "error"]
    result = {"path": str(Path(args.xml).resolve()), "sha256": digest,
              "studio_commit": revision, "components": len(doc.components),
              "counts": dict(Counter(r["severity"] for r in rows)), "issues": rows}
    if args.baseline:
        before, baseline_digest = read_document(args.baseline, parser)
        remaining = Counter(issue_key(r) for r in issue_rows(before))
        introduced = []
        for row in rows:
            key = issue_key(row)
            if remaining[key]:
                remaining[key] -= 1
            else:
                introduced.append(row)
        result.update(baseline_sha256=baseline_digest, introduced= introduced)
        blocking = [r for r in introduced if r["severity"] == "error"]
    result["meaning"] = "TWUI Studio structural diagnostics only; not game validation"
    emit(result)
    return 1 if blocking else 0


def inspect(args):
    parser, root, revision = load_parser(args.studio)
    doc, digest = read_document(args.xml, parser)
    line = line_locator(doc.source)
    selected = [c for c in doc.components
                if (not args.id or c.get("id") == args.id)
                and (not args.guid or c.get("this") == args.guid)]
    items = []
    for c in selected[:args.limit]:
        state = doc.state(c)
        items.append({"line": line(c), "attrs": c.attrs,
                      "parent_guid": doc.parents.get(c.get("this")),
                      "child_guids": doc.children.get(c.get("this"), []),
                      "preview_state": state.attrs if state else None,
                      "groups": {n.tag: {"attrs": n.attrs,
                                 "children": [{"tag": x.tag, "attrs": x.attrs}
                                              for x in n.children]}
                                 for n in c.children}})
    emit({"path": str(Path(args.xml).resolve()), "sha256": digest,
          "studio_commit": revision, "matches": len(selected),
          "truncated": len(selected) > args.limit, "components": items})
    return 0 if selected else 1


def entries(doc):
    line = line_locator(doc.source)
    for c in doc.components:
        cid, guid = c.get("id", c.tag), c.get("this", "")
        yield line(c), "component", cid, guid, cid, json.dumps(c.attrs, ensure_ascii=False)
        for n in c.descendants():
            kind = None
            if n.parent is not None and n.parent.tag == "states":
                kind, name = "state", n.get("name", n.tag)
            elif n.tag == "LayoutEngine":
                kind, name = "layout", n.get("type", "")
            elif n.tag == "callback_with_context":
                kind, name = "callback", n.get("callback_id", "")
            elif n.get("imagepath"):
                kind, name = "image", n.get("imagepath")
            elif n.tag == "component_text":
                kind, name = "text", n.get("textlabel", "")
            elif n.tag == "property" and n.parent.tag == "userproperties":
                kind, name = "property", n.get("name", "")
            elif n.tag == "state_uniqueguid":
                kind, name = "template_state", n.get("name", n.get("uniqueguid", ""))
            if kind:
                yield line(n), kind, cid, guid, name, json.dumps(n.attrs, ensure_ascii=False)


def build_index(args):
    parser, studio, revision = load_parser(args.studio)
    source_root = Path(args.ui_root).resolve()
    if not source_root.is_dir():
        raise ValueError("--ui-root must be an extracted UI directory")
    target = Path(args.database).resolve()
    # The database is derived research data, never a game source file.
    if target.suffix.lower() not in (".sqlite", ".db"):
        raise ValueError("Database filename must end with .sqlite or .db")
    if target.is_relative_to(source_root):
        raise ValueError("Place the derived database outside the source UI folder")
    report = Path(args.report).resolve() if args.report else None
    if report and (report == target or report.is_relative_to(source_root)
                   or report.suffix.lower() != ".json"):
        raise ValueError("Report must be a separate .json outside the source UI folder")
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".twui-index-", suffix=".sqlite", dir=target.parent)
    os.close(fd)
    con = None
    try:
        con = sqlite3.connect(temporary)
        con.executescript("""
        CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE files(path TEXT PRIMARY KEY, sha256 TEXT, bytes INTEGER,
                           components INTEGER, errors INTEGER, warnings INTEGER, parse_error TEXT);
        CREATE TABLE entries(file TEXT, line INTEGER, kind TEXT, component TEXT,
                             guid TEXT, name TEXT, value TEXT);
        CREATE TABLE issues(file TEXT, code TEXT, severity TEXT, lines TEXT, nodes TEXT);
        CREATE TABLE cco(type TEXT, name TEXT, signature TEXT);
        """)
        file_paths = sorted(source_root.rglob("*.twui.xml"))
        manifest = hashlib.sha256()
        failures = []
        for i, path in enumerate(file_paths, 1):
            raw = path.read_bytes()
            digest = hashlib.sha256(raw).hexdigest()
            relative = "ui/" + path.relative_to(source_root).as_posix()
            manifest.update((relative + "\0" + digest + "\n").encode())
            try:
                doc = parser(raw.decode("utf-8-sig"))
            except (ValueError, UnicodeError, IndexError, RecursionError) as exc:
                failures.append({"file": relative, "error": str(exc)})
                con.execute("INSERT INTO files VALUES (?,?,?,?,?,?,?)",
                            (relative, digest, len(raw), 0, 0, 0, str(exc)))
                continue
            except Exception as exc:
                # XML ParseError is parser-specific; preserve it as evidence too.
                failures.append({"file": relative, "error": type(exc).__name__ + ": " + str(exc)})
                con.execute("INSERT INTO files VALUES (?,?,?,?,?,?,?)",
                            (relative, digest, len(raw), 0, 0, 0, failures[-1]["error"]))
                continue
            issues = issue_rows(doc)
            counts = Counter(r["severity"] for r in issues)
            con.execute("INSERT INTO files VALUES (?,?,?,?,?,?,NULL)",
                        (relative, digest, len(raw), len(doc.components), counts["error"], counts["warning"]))
            con.executemany("INSERT INTO entries VALUES (?,?,?,?,?,?,?)",
                            ((relative, *row) for row in entries(doc)))
            con.executemany("INSERT INTO issues VALUES (?,?,?,?,?)",
                            ((relative, r["code"], r["severity"], json.dumps(r["lines"]),
                              json.dumps(r["nodes"], ensure_ascii=False)) for r in issues))
            if i % 100 == 0:
                print(f"Indexed {i}/{len(file_paths)}", file=sys.stderr)
        metadata = source_root / "metadata.json"
        metadata_digest = None
        if metadata.is_file():
            metadata_raw = metadata.read_bytes()
            metadata_digest = hashlib.sha256(metadata_raw).hexdigest()
            for type_name, definition in json.loads(metadata_raw.decode("utf-8-sig")).items():
                for symbol in definition.get("symbols", []):
                    # Store signatures, not a duplicate of the documentation prose.
                    signature = {k: v for k, v in symbol.items() if k != "doc"}
                    con.execute("INSERT INTO cco VALUES (?,?,?)", (type_name, symbol.get("name", ""),
                                json.dumps(signature, ensure_ascii=False)))
        counts = dict(con.execute("SELECT kind, count(*) FROM entries GROUP BY kind"))
        issue_counts = {f"{level}:{code}": count for level, code, count in
                        con.execute("SELECT severity, code, count(*) FROM issues GROUP BY severity, code")}
        summary = {"schema_version": 1, "generated_utc": datetime.now(timezone.utc).isoformat(),
                   "ui_root": str(source_root), "studio_root": str(studio), "studio_commit": revision,
                   "source_manifest_sha256": manifest.hexdigest(), "metadata_sha256": metadata_digest,
                   "files": len(file_paths), "parsed_files": len(file_paths) - len(failures),
                   "parse_failures": failures, "entries": counts, "diagnostic_counts": issue_counts,
                   "cco_types": con.execute("SELECT count(DISTINCT type) FROM cco").fetchone()[0],
                   "cco_symbols": con.execute("SELECT count(*) FROM cco").fetchone()[0],
                   "boundary": "Local extraction snapshot; not proof of current game version or engine validity"}
        con.executemany("INSERT INTO meta VALUES (?,?)", ((k, json.dumps(v, ensure_ascii=False))
                        for k, v in summary.items()))
        con.executescript("CREATE INDEX entries_kind ON entries(kind);"
                          "CREATE INDEX entries_file ON entries(file);"
                          "CREATE INDEX cco_type ON cco(type);")
        con.commit()
        con.close()
        con = None
        os.replace(temporary, target)
        if report:
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        emit(summary)
        return 1 if failures else 0
    finally:
        if con is not None:
            con.close()
        if os.path.exists(temporary):
            os.unlink(temporary)


def query(args):
    database = Path(args.database).resolve()
    con = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        if args.kind == "meta":
            emit({r["key"]: json.loads(r["value"]) for r in con.execute("SELECT * FROM meta")})
            return 0
        pattern = "%" + args.term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        if args.kind == "cco":
            rows = con.execute("SELECT * FROM cco WHERE type LIKE ? ESCAPE '\\' OR name LIKE ? ESCAPE '\\' "
                               "ORDER BY type, name LIMIT ?", (pattern, pattern, args.limit)).fetchall()
        elif args.kind == "issues":
            rows = con.execute("SELECT * FROM issues WHERE file LIKE ? ESCAPE '\\' OR code LIKE ? ESCAPE '\\' "
                               "ORDER BY file, code LIMIT ?", (pattern, pattern, args.limit)).fetchall()
        else:
            kinds = "" if args.kind == "all" else "kind = ? AND "
            parameters = ([] if args.kind == "all" else [args.kind]) + [pattern] * 4 + [args.limit]
            rows = con.execute("SELECT * FROM entries WHERE " + kinds +
                               "(component LIKE ? ESCAPE '\\' OR name LIKE ? ESCAPE '\\' "
                               "OR value LIKE ? ESCAPE '\\' OR file LIKE ? ESCAPE '\\') "
                               "ORDER BY file, line LIMIT ?", parameters).fetchall()
        emit({"database": str(database), "limit": args.limit, "returned": len(rows),
              "note": "Read the source at file/line; check source SHA before editing",
              "rows": [dict(r) for r in rows]})
        return 0
    finally:
        con.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--studio", help="Optional trusted TWUI Studio checkout; defaults to bundled vendor")
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("index", help="Build a derived local knowledge database")
    s.add_argument("--ui-root", required=True)
    s.add_argument("--database", required=True)
    s.add_argument("--report")
    s.set_defaults(run=build_index)
    s = sub.add_parser("query", help="Search metadata, examples, fields or CCO signatures")
    s.add_argument("--database", required=True)
    s.add_argument("--kind", choices=["all", "meta", "cco", "issues", "component", "state", "layout",
                                      "callback", "image", "text", "property", "template_state"], default="all")
    s.add_argument("term", nargs="?", default="")
    s.add_argument("--limit", type=int, default=20)
    s.set_defaults(run=query)
    s = sub.add_parser("inspect", help="Inspect exact component ids or GUIDs")
    s.add_argument("xml")
    s.add_argument("--id")
    s.add_argument("--guid")
    s.add_argument("--limit", type=int, default=10)
    s.set_defaults(run=inspect)
    s = sub.add_parser("check", help="Report Studio diagnostics, optionally relative to baseline")
    s.add_argument("xml")
    s.add_argument("--baseline")
    s.set_defaults(run=check)
    args = p.parse_args()
    if hasattr(args, "limit") and args.limit <= 0:
        p.error("--limit must be positive")
    try:
        return args.run(args)
    except (OSError, ValueError, ET.ParseError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
