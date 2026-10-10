"""Offline fixtures for provenance, complete log scans, and output boundaries."""

import hashlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "wh3_mcp_evidence.py"
SPEC = importlib.util.spec_from_file_location("wh3_mcp_evidence", SCRIPT)
evidence = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evidence)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="wh3-mcp-evidence-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / "游戏目录"
        self.game.mkdir()
        self.output = self.root / "证据"
        (self.game / "wh3_mcp_script_errors.log").write_bytes(b"")
        (self.game / "script_log_1_1.txt").write_bytes(b"ordinary log\n")

    def collect(self, **kwargs):
        return evidence.collect(self.game, self.output, **kwargs)

    @staticmethod
    def record(manifest, name):
        return next(record for record in manifest["files"] if record["name"] == name)

    def test_unicode_raw_bytes_result_and_pack_identity_preserved(self):
        raw = '奖励：中文\nERROR: 测试错误\n'.encode("utf-8")
        (self.game / "总督.log").write_bytes(raw)
        result = {"status": "ok", "result": {"text": "中文", "path": r"X:\SteamLibrary"}}
        result_path = self.game / "wh3_mcp_result.json"
        result_raw = json.dumps(result, ensure_ascii=False).encode("utf-8")
        result_path.write_bytes(result_raw)
        pack = self.root / "test.pack"
        pack.write_bytes(b"fixture pack bytes")
        before = {path.name: path.read_bytes() for path in self.game.iterdir()}
        manifest = self.collect(label="触发后", extra_logs=["总督.log"], packs=[pack])
        record = self.record(manifest, "总督.log")
        self.assertEqual((self.output / record["artifact"]).read_bytes(), raw)
        self.assertEqual(record["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(self.record(manifest, "wh3_mcp_result.json")["parsed"], result)
        self.assertEqual(manifest["packs"][0]["sha256"], hashlib.sha256(pack.read_bytes()).hexdigest())
        self.assertEqual(manifest["label"], "触发后")
        self.assertEqual(before, {path.name: path.read_bytes() for path in self.game.iterdir()})

    def test_all_250_ca_errors_returned_without_truncation(self):
        lines = [f"script error: fixture {i}" for i in range(250)]
        (self.game / "script_log_1_1.txt").write_text("\n".join(lines), encoding="utf-8")
        manifest = self.collect()
        self.assertEqual(manifest["summary"]["matched_error_line_count"], 250)
        returned = self.record(manifest, "script_log_1_1.txt")["matched_error_lines"]
        self.assertEqual(returned[-1], {"line": 250, "text": lines[-1]})

    def test_extra_log_errors_counted_in_summary(self):
        (self.game / "custom.log").write_text("ERROR: failed\nstack traceback:\n", encoding="utf-8")
        manifest = self.collect(extra_logs=["custom.log"])
        self.assertEqual(manifest["summary"]["log_scan"], "matches_found")
        self.assertEqual(manifest["summary"]["matched_error_line_count"], 2)

    def test_capture_log_messages_count_even_without_error_keyword(self):
        (self.game / "wh3_mcp_script_errors.log").write_text("[1.0 turn=8] bad state\n", encoding="utf-8")
        self.assertEqual(self.collect()["summary"]["matched_error_line_count"], 1)

    def test_invalid_json_preserved_without_repair(self):
        raw = b'{"status":"ok","path":"X:\\SteamLibrary"}'
        (self.game / "wh3_mcp_result.json").write_bytes(raw)
        manifest = self.collect()
        record = self.record(manifest, "wh3_mcp_result.json")
        self.assertEqual(record["status"], "parse_error")
        self.assertNotIn("parsed", record)
        self.assertEqual((self.output / record["artifact"]).read_bytes(), raw)

    def test_missing_logs_mark_incomplete(self):
        (self.game / "wh3_mcp_script_errors.log").unlink()
        (self.game / "script_log_1_1.txt").unlink()
        manifest = self.collect(extra_logs=["missing.log"])
        self.assertEqual(manifest["summary"]["log_scan"], "incomplete")
        self.assertFalse(manifest["summary"]["log_evidence_complete"])
        self.assertEqual(self.record(manifest, "wh3_mcp_result.json")["status"], "missing")

    def test_no_matches_does_not_fabricate_a_pass_result(self):
        summary = self.collect()["summary"]
        self.assertEqual(summary["log_scan"], "no_matches")
        self.assertNotIn("pass", summary)

    def test_newest_valid_ca_log_chosen_and_near_names_excluded(self):
        old = self.game / "script_log_1_1.txt"
        newest = self.game / "script_log_2_3.txt"
        newest.write_bytes(b"ERROR: newest\n")
        os.utime(old, ns=(1_000_000_000, 1_000_000_000))
        os.utime(newest, ns=(2_000_000_000, 2_000_000_000))
        (self.game / "script_log_custom.txt").write_bytes(b"ERROR: unrelated\n")
        manifest = self.collect()
        ca = next(record for record in manifest["files"] if record["role"] == "ca_log")
        self.assertEqual(ca["name"], newest.name)
        self.assertEqual(manifest["summary"]["matched_error_line_count"], 1)

    def test_utf16_and_changed_reads_remain_incomplete(self):
        (self.game / "wide.log").write_bytes("ERROR: utf16".encode("utf-16"))
        manifest = self.collect(extra_logs=["wide.log"])
        self.assertEqual(self.record(manifest, "wide.log")["status"], "encoding_error")
        self.assertEqual(manifest["summary"]["log_scan"], "incomplete")
        self.output = self.root / "变化证据"
        real_read = evidence.read_snapshot

        def changed(path):
            raw, metadata = real_read(path)
            if path.name == "script_log_1_1.txt":
                metadata["changed_during_read"] = True
            return raw, metadata

        with mock.patch.object(evidence, "read_snapshot", side_effect=changed):
            self.assertEqual(self.collect()["summary"]["log_scan"], "incomplete")

    def test_game_descendant_output_and_existing_output_rejected(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            evidence.collect(self.game, self.game / "evidence")
        self.assertFalse((self.game / "evidence").exists())
        self.output.mkdir()
        owned = self.output / "keep.txt"
        owned.write_bytes(b"existing work")
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.collect()
        self.assertEqual(owned.read_bytes(), b"existing work")

    def test_extra_path_traversal_rejected_before_creating_output(self):
        for name in ("../other.log", r"..\other.log", r"C:\other.log", "script_log_*.txt"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "plain filename"):
                self.collect(extra_logs=[name])
            self.assertFalse(self.output.exists())

    def test_user_copied_result_and_duplicate_keys_or_nan_reported(self):
        response = self.root / "response.json"
        response.write_text('{"status":"ok","status":"error"}', encoding="utf-8")
        first = self.collect(result_path=response)
        result = self.record(first, "response.json")
        self.assertEqual(result["status"], "parse_error")
        self.assertIn("duplicate", result["error"])
        self.output = self.root / "nonfinite"
        response.write_text('{"value":NaN}', encoding="utf-8")
        second = self.collect(result_path=response)
        self.assertEqual(self.record(second, "response.json")["status"], "parse_error")

    def test_float_overflow_preserves_bundle_and_reports_parse_error(self):
        response = self.game / "wh3_mcp_result.json"
        response.write_bytes(b'{"value":1e999}')
        manifest = self.collect()
        self.assertEqual(self.record(manifest, response.name)["status"], "parse_error")
        self.assertTrue((self.output / "manifest.json").is_file())

    def test_pack_identity_hash_uses_chunks_without_retaining_pack_bytes(self):
        pack = self.root / "large.pack"
        raw = b"fixture data" * 200_000
        pack.write_bytes(raw)
        captured, metadata = evidence.read_snapshot(pack, identity_only=True)
        self.assertEqual(captured, b"")
        self.assertEqual(metadata["size"], len(raw))
        self.assertEqual(metadata["sha256"], hashlib.sha256(raw).hexdigest())


if __name__ == "__main__":
    unittest.main()
