"""Preserve existing WH3 MCP results and logs without contacting the game.

Standard-library only. Reads the observed file length once, keeps raw bytes,
reports changes during reads, and scans every UTF-8 log line without a cap.
Output must be a new directory outside the game directory. This tool never
writes command files, deletes results, starts processes, or registers MCP.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "wh3-mcp-evidence/v1"
SCRIPT_LOG = re.compile(r"script_log_\d+_\d+\.txt\Z", re.IGNORECASE)
ERROR_LINE = re.compile(
    r"script error|error(:| in )|traceback|assertion|attempt to|stack trace",
    re.IGNORECASE,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_signature(stat: os.stat_result) -> tuple[int, int, int, int]:
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns


def read_snapshot(path: Path, *, identity_only: bool = False) -> tuple[bytes, dict[str, Any]]:
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        remaining = before.st_size
        chunks = []
        digest = hashlib.sha256()
        while remaining:
            chunk = stream.read(min(remaining, 1024 * 1024))
            if not chunk:
                break
            digest.update(chunk)
            remaining -= len(chunk)
            if not identity_only:
                chunks.append(chunk)
        after = os.fstat(stream.fileno())
    raw = b"".join(chunks)
    try:
        current = path.stat()
        changed = file_signature(current) != file_signature(before)
    except OSError:
        changed = True
    return raw, {
        "size": before.st_size - remaining,
        "observed_size": before.st_size,
        "mtime_ns": before.st_mtime_ns,
        "sha256": digest.hexdigest(),
        "changed_during_read": changed
        or file_signature(before) != file_signature(after)
        or remaining != 0,
    }


def decode_utf8(raw: bytes) -> str:
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise ValueError("UTF-16 input is unsupported; raw bytes have been preserved")
    return raw.decode("utf-8-sig", errors="strict")


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number: {value}")


def finite_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"JSON number exceeds finite float range: {value}")
    return number


def capture_file(path: Path, role: str, output: Path, index: int) -> dict[str, Any]:
    record: dict[str, Any] = {
        "source_path": str(path.resolve()), "name": path.name, "role": role
    }
    try:
        raw, metadata = read_snapshot(path)
    except FileNotFoundError:
        return {**record, "status": "missing"}
    except OSError as error:
        return {**record, "status": "read_error", "error": str(error)}

    artifact = Path("files") / f"{index:02d}-{path.name}"
    (output / artifact).write_bytes(raw)
    record.update(metadata, status="ok", artifact=artifact.as_posix())
    try:
        text = decode_utf8(raw)
        record["encoding"] = "utf-8"
        if role == "result":
            record["parsed"] = json.loads(
                text, object_pairs_hook=unique_object, parse_constant=reject_constant,
                parse_float=finite_float,
            )
        else:
            record["matched_error_lines"] = [
                {"line": number, "text": line}
                for number, line in enumerate(text.splitlines(), 1)
                if (role == "script_error_capture" and line.strip())
                or ERROR_LINE.search(line)
            ]
    except (UnicodeError, ValueError) as error:
        record["status"] = "parse_error" if role == "result" else "encoding_error"
        record["error"] = str(error)
    return record


def collect(
    game_dir: Path,
    output: Path,
    *,
    label: str = "",
    extra_logs: list[str] | None = None,
    result_path: Path | None = None,
    packs: list[Path] | None = None,
) -> dict[str, Any]:
    started = utc_now()
    game_dir = game_dir.resolve()
    output = output.resolve()
    if not game_dir.is_dir():
        raise ValueError(f"game directory does not exist: {game_dir}")
    if output == game_dir or output.is_relative_to(game_dir):
        raise ValueError("output directory must be outside the game directory")
    if output.exists():
        raise ValueError(f"output directory already exists: {output}")
    extras = list(dict.fromkeys(extra_logs or []))
    for name in extras:
        if not name or name in (".", "..") or any(c in name for c in '/\\:*?"<>|'):
            raise ValueError(f"extra log must be a plain filename: {name}")

    candidates = [
        path for path in game_dir.iterdir()
        if SCRIPT_LOG.fullmatch(path.name) and path.is_file()
    ]
    latest = max(candidates, key=lambda path: path.stat().st_mtime_ns, default=None)
    sources = [(game_dir / "wh3_mcp_script_errors.log", "script_error_capture")]
    if latest is not None:
        sources.append((latest, "ca_log"))
    seen = {str(path.resolve()).casefold() for path, _ in sources}
    for name in extras:
        path = game_dir / name
        key = str(path.resolve()).casefold()
        if key not in seen:
            sources.append((path, "extra_log"))
            seen.add(key)
    result = (result_path or game_dir / "wh3_mcp_result.json").resolve()
    if str(result).casefold() in seen:
        raise ValueError("result file must be distinct from the selected log files")
    sources.append((result, "result"))

    output.mkdir(parents=True, exist_ok=False)
    (output / "files").mkdir()
    records = [
        capture_file(path, role, output, index)
        for index, (path, role) in enumerate(sources, 1)
    ]
    if latest is None:
        records.insert(1, {
            "source_path": str(game_dir), "name": "script_log_*.txt", "role": "ca_log",
            "status": "missing", "error": "no_matching_script_log",
        })
    identities = []
    for pack in packs or []:
        record = {"source_path": str(pack.resolve())}
        try:
            _, metadata = read_snapshot(pack, identity_only=True)
            record.update(metadata, status="ok")
        except OSError as error:
            record.update(status="read_error", error=str(error))
        identities.append(record)

    logs = [record for record in records if record["role"] != "result"]
    matches = sum(len(record.get("matched_error_lines", [])) for record in logs)
    incomplete = any(
        record["status"] != "ok" or record.get("changed_during_read") for record in logs
    )
    manifest = {
        "schema": SCHEMA,
        "capture_started_utc": started,
        "capture_finished_utc": utc_now(),
        "label": label,
        "game_dir": str(game_dir),
        "files": records,
        "packs": identities,
        "summary": {
            "log_scan": "incomplete" if incomplete else "matches_found" if matches else "no_matches",
            "matched_error_line_count": matches,
            "log_evidence_complete": not incomplete,
        },
        "note": "Offline file capture, not a game test. Labels do not establish response/request identity."
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--label", default="")
    parser.add_argument("--extra-log", action="append", default=[], metavar="FILENAME")
    parser.add_argument("--result", type=Path, help="An existing response copied by the user")
    parser.add_argument("--pack", action="append", type=Path, default=[])
    args = parser.parse_args()
    try:
        manifest = collect(
            args.game_dir, args.out, label=args.label, extra_logs=args.extra_log,
            result_path=args.result, packs=args.pack,
        )
    except (OSError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")
    print(json.dumps({"manifest": str(args.out.resolve() / "manifest.json"),
                      "summary": manifest["summary"]}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
