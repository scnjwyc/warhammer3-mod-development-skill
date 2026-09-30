"""Smoke test the real withdrawn Tk editor, sample edit, undo and export.

Settings and outputs live in a temporary directory. This validates Studio, not
Warhammer. Run with --studio <trusted TWUI_Studio checkout>.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import zipfile

sys.dont_write_bytecode = True


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--studio", required=True)
    args = p.parse_args()
    studio = Path(args.studio).resolve()
    sys.path.insert(0, str(studio))
    with tempfile.TemporaryDirectory(prefix="twui-gui-smoke-") as temporary:
        old_appdata = os.environ.get("APPDATA")
        os.environ["APPDATA"] = temporary
        os.environ["TWUI_STUDIO_LANGUAGE"] = "en"
        import tkinter as tk
        original_init = tk.Tk.__init__

        def hidden_init(self, *a, **kw):
            original_init(self, *a, **kw)
            self.withdraw()

        tk.Tk.__init__ = hidden_init
        editor = None
        try:
            from app import Studio
            from project import save_project, load_project, export_zip
            editor = Studio()
            tk_errors = []
            editor.report_callback_exception = lambda *error: tk_errors.append(str(error))
            sample = studio / "examples" / "frame_slaves_expense.twui.xml"
            raw = sample.read_bytes()
            editor.import_xml(sample)
            editor.update()
            editor.draw()
            source = editor.doc.source
            assert len(editor.doc.components) == 6
            assert not editor.missing, editor.missing
            assert editor.boxes, "No preview geometry"
            target = next(c for c in editor.doc.components if c.get("id") == "slaves_icon")
            guid = target.get("this")
            editor.commit(editor.doc.patch([(target, {"dock_offset": "41.00,0.00"})]), "smoke edit")
            assert editor.doc.by_guid[guid].get("dock_offset") == "41.00,0.00"
            assert editor.original_doc.source == source
            editor.undo()
            assert editor.doc.source == source
            editor.redo()
            assert editor.doc.by_guid[guid].get("dock_offset") == "41.00,0.00"
            output = Path(temporary) / "sample.twuiproj"
            save_project(output, editor.snapshot())
            saved = load_project(output)
            assert saved["documents"][saved["active"]]["xml"] == editor.doc.source
            archive = Path(temporary) / "sample.zip"
            result = export_zip(archive, editor.doc, editor.resources,
                                "ui/campaign ui/mod/frame_slaves_expense.twui.xml", editor.bom)
            assert result["written"] and result["images"] == 3, result
            with zipfile.ZipFile(archive) as z:
                members = z.namelist()
                assert len(members) == 4
                assert z.read(members[0]).decode("utf-8-sig") == editor.doc.source
            editor.update()
            assert not tk_errors, tk_errors
            assert sample.read_bytes() == raw
            print(json.dumps({"result": "PASS", "components": len(editor.doc.components),
                              "preview_boxes": len(editor.boxes), "missing_images": len(editor.missing),
                              "checks": ["real_Tk_draw", "attribute_edit", "original_preserved", "undo", "redo",
                                         "project_reload", "zip_xml_and_3_images", "sample_unchanged", "no_Tk_callback_errors"],
                              "game_validation": False}, ensure_ascii=False, indent=2))
        finally:
            if editor is not None:
                editor.destroy()
            tk.Tk.__init__ = original_init
            if old_appdata is None:
                os.environ.pop("APPDATA", None)
            else:
                os.environ["APPDATA"] = old_appdata


if __name__ == "__main__":
    main()
