"""Exercise the delivered CLI against isolated synthetic sources, never game files.

Run: python test_twui_kb.py --studio <TWUI_Studio checkout>
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

XML = '''<layout><hierarchy><root this="r"><button this="b"/></root></hierarchy>
<components><root id="root" this="r"/><button id="button" this="b" currentstate="s">
<states><active this="s" name="active" width="80" height="30"/></states>
<callbackwithcontextlist><callback_with_context callback_id="ContextVisibilitySetter" context_function_id="a < 2 && b"/></callbackwithcontextlist>
<componentimages><component_image this="i" imagepath="ui/skins/default/test.png"/></componentimages>
</button></components></layout>'''


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="twui-skill-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.ui = self.root / "source ui"
        self.ui.mkdir()
        self.xml = self.ui / "sample.twui.xml"
        self.xml.write_bytes(b"\xef\xbb\xbf" + XML.replace("\n", "\r\n").encode())
        self.original = self.xml.read_bytes()
        self.db = self.root / "catalog.sqlite"
        (self.ui / "metadata.json").write_text(json.dumps({"CcoTest": {"symbols": [
            {"name": "Value", "doc": "Prose is intentionally not duplicated", "return_type": {"type": "Number"}}]}}))

    def command(self, *args, code=0):
        p = subprocess.run([sys.executable, str(Path(__file__).with_name("twui_kb.py")),
                            "--studio", STUDIO, *map(str, args)], capture_output=True,
                           encoding="utf-8", env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        self.assertEqual(p.returncode, code, p.stderr + p.stdout)
        return json.loads(p.stdout) if p.stdout.strip() else p

    def build(self):
        return self.command("index", "--ui-root", self.ui, "--database", self.db)

    def test_index_query_and_provenance_without_source_mutation(self):
        info = self.build()
        self.assertEqual(info["parsed_files"], 1)
        self.assertEqual(info["entries"]["component"], 2)
        self.assertEqual(self.command("query", "--database", self.db, "--kind", "callback",
                                      "ContextVisibilitySetter")["returned"], 1)
        rows = self.command("query", "--database", self.db, "--kind", "cco", "CcoTest")["rows"]
        self.assertEqual(json.loads(rows[0]["signature"])["return_type"]["type"], "Number")
        self.assertNotIn("doc", json.loads(rows[0]["signature"]))
        self.assertEqual(self.xml.read_bytes(), self.original)
        self.assertEqual(self.command("query", "--database", self.db, "--kind", "meta")["studio_commit"], info["studio_commit"])

    def test_inspect_records_line_and_preserves_raw_expression(self):
        item = self.command("inspect", self.xml, "--id", "button")
        self.assertEqual(item["matches"], 1)
        component = item["components"][0]
        self.assertEqual(component["parent_guid"], "r")
        self.assertEqual(component["line"], 2)
        self.assertEqual(item["sha256"], hashlib.sha256(self.original).hexdigest())
        self.assertEqual(component["groups"]["callbackwithcontextlist"]["children"][0]["attrs"]["context_function_id"], "a < 2 && b")

    def test_check_detects_new_error_and_baseline_does_not_hide_change(self):
        self.command("check", self.xml)
        changed = self.root / "changed.twui.xml"
        changed.write_text(XML.replace('currentstate="s"', 'currentstate="missing"'), encoding="utf-8")
        result = self.command("check", changed, "--baseline", self.xml, code=1)
        self.assertTrue(any(r["code"] == "dangling_reference" for r in result["introduced"]))
        same = self.command("check", changed, "--baseline", changed)
        self.assertEqual(same["introduced"], [])
        self.assertEqual(same["counts"]["error"], 1)

    def test_parse_failure_is_recorded_without_losing_good_files(self):
        (self.ui / "bad.twui.xml").write_text("<layout><bad></layout>")
        result = self.command("index", "--ui-root", self.ui, "--database", self.db, code=1)
        self.assertEqual(result["files"], 2)
        self.assertEqual(result["parsed_files"], 1)
        self.assertEqual(len(result["parse_failures"]), 1)
        self.assertEqual(self.command("query", "--database", self.db, "--kind", "component", "button")["returned"], 1)

    def test_query_literal_underscores_and_read_only_database(self):
        self.build()
        before = self.db.read_bytes()
        self.assertEqual(self.command("query", "--database", self.db, "--kind", "component", "but_on")["returned"], 0)
        self.assertEqual(self.command("query", "--database", self.db, "--kind", "component", "button")["returned"], 1)
        self.assertEqual(self.db.read_bytes(), before)
        self.command("query", "--database", self.root / "missing.sqlite", code=2)
        self.assertFalse((self.root / "missing.sqlite").exists())

    def test_output_guard_and_malformed_check(self):
        self.command("index", "--ui-root", self.ui, "--database", self.xml, code=2)
        self.command("index", "--ui-root", self.ui, "--database", self.ui / "catalog.sqlite", code=2)
        self.command("index", "--ui-root", self.ui, "--database", self.db, "--report", self.xml, code=2)
        self.assertEqual(self.xml.read_bytes(), self.original)
        bad = self.root / "bad.xml"
        bad.write_text("<layout><broken></layout>")
        self.command("check", bad, code=2)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--studio", required=True)
    options, rest = p.parse_known_args()
    STUDIO = str(Path(options.studio).resolve())
    unittest.main(argv=[sys.argv[0], *rest])
