"""Synthetic PE/CFG invariants and an isolated, owned Python-process capture."""
import contextlib
import ctypes
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import wh3_dump as dump
import capture_module as capture

BASE = 0x180120000  # Deliberately differs from PE preferred base.


def call(site, target):
    return b"\xe8" + struct.pack("<i", target - site - 5)


def rip(prefix, site, target):
    return prefix + struct.pack("<i", target - site - len(prefix) - 4)


def fixture():
    data = bytearray(0x5000)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3C, 0x80)
    data[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", data, 0x84, 0x8664, 3, 1234, 0, 0, 240, 0x22)
    opt = 0x98
    struct.pack_into("<H", data, opt, 0x20B)
    struct.pack_into("<Q", data, opt + 24, 0x140000000)
    struct.pack_into("<I", data, opt + 56, len(data))
    struct.pack_into("<I", data, opt + 108, 16)
    functions = [(0x1000, 0x1010), (0x1100, 0x1120), (0x1200, 0x1220),
                 (0x1300, 0x1340), (0x1400, 0x1430), (0x1500, 0x1510), (0x1600, 0x1610)]
    struct.pack_into("<II", data, opt + 112 + 3 * 8, 0x4000, len(functions) * 12)
    for i, (name, rva, size, raw_offset, flags) in enumerate([
        (b".text", 0x1000, 0x1000, 0x400, 0x60000020),
        (b".rdata", 0x3000, 0x400, 0x600, 0x40000040),
        (b".pdata", 0x4000, 0x1000, 0xA00, 0x40000040),
    ]):
        struct.pack_into("<8sIIIIIIHHI", data, opt + 240 + i * 40,
                         name, size, rva, 0x200, raw_offset, 0, 0, 0, 0, flags)
    for i, (start, end) in enumerate(functions):
        struct.pack_into("<III", data, 0x4000 + i * 12, start, end, 0x3100)
    code = {
        0x1000: call(0x1000, 0x1100) + b"\xc3",
        0x1100: call(0x1100, 0x1200) + b"\xc3",
        0x1200: rip(b"\x48\x8d\x05", 0x1200, 0x3020)
                + rip(b"\x8b\x0d", 0x1207, 0x3020) + b"\xff\xd0\xc3",
        0x1300: b"\x48\x69\xc0\xc8\x01\x00\x00"  # imul rax,rax,0x1c8
                b"\x89\x48\x09"                     # write [rax+9]
                b"\x8b\x48\x09"                     # read [rax+9]
                b"\x01\x48\x09"                     # read-modify-write [rax+9]
                b"\xf3\x0f\x11\x80\xb0\x00\x00\x00"  # movss write +b0
                b"\x48\x8d\x50\x09"                 # address-only, not field read
                b"\x89\x4c\x24\x09\xc3",            # stack write excluded
        0x1400: b"\x85\xc0\x74\x03\xc3\x90\x90" + call(0x1407, 0x1200) + b"\xc3",
        0x1500: b"\x48\xb8" + call(0x1502, 0x1200) + b"\x00\x00\x00\xc3",
        0x1600: call(0x1600, 0x6000) + b"\xc3",
    }
    for rva, block in code.items():
        data[rva:rva + len(block)] = block
    data[0x1FFD:0x2000] = b"\xe8\x00\x00"  # Truncated instruction at readable boundary.
    data[0x2000:0x2004] = b"HOLE"  # Bytes in an unavailable region must not be evidence.
    data[0x3020:0x302E] = b"taking_damage\0"
    data[0x3040:0x304A] = "汉字锚点".encode("utf-16le") + b"\0\0"
    struct.pack_into("<Q", data, 0x30A0, BASE + 0x1200)
    struct.pack_into("<Q", data, 0x30B1, BASE + 0x1200)
    regions = [
        {"rva": 0, "size": 0x1000, "state": 0x1000, "protect": 2},
        {"rva": 0x1000, "size": 0x1000, "state": 0x1000, "protect": 0x20},
        {"rva": 0x2000, "size": 0x1000, "state": 0x10000, "protect": 1},
        {"rva": 0x3000, "size": 0x2000, "state": 0x1000, "protect": 2},
    ]
    layout = {"schema": dump.SCHEMA, "format": "mapped-pe", "image_base": BASE,
              "image_size": len(data), "dump_sha256": hashlib.sha256(data).hexdigest(),
              "valid_ranges": [{"rva": 0, "size": 0x2000}, {"rva": 0x3000, "size": 0x2000}],
              "regions": regions}
    return data, layout


class OfflineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="wh3-offline-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin, self.layout = self.root / "sample.bin", self.root / "sample.layout.json"
        self.data, self.meta = fixture()
        self.write()
        self.image = dump.Image(self.bin, self.layout)

    def write(self):
        self.bin.write_bytes(self.data)
        self.meta["dump_sha256"] = hashlib.sha256(self.data).hexdigest()
        self.layout.write_text(json.dumps(self.meta), encoding="utf-8")

    def cli(self, *args):
        output, error = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            code = dump.main(["--dump", str(self.bin), "--layout", str(self.layout), *args])
        return code, output.getvalue(), error.getvalue()

    def test_dynamic_base_and_rva_not_disk_offset(self):
        self.assertEqual(self.image.base, BASE)
        self.assertNotEqual(self.image.base, self.image.preferred_base)
        hit = dump.find_pattern(self.image, b"taking_damage", 20)["hits"][0]
        self.assertEqual(hit["rva"], 0x3020)
        self.assertEqual(hit["va"], BASE + 0x3020)
        self.assertEqual(self.image.functions[0], dump.Function(0x1000, 0x1010))

    def test_dump_hash_size_and_legacy_metadata_rejected(self):
        for patch in ({"dump_sha256": "0" * 64}, {"image_size": 1}, {"schema": "legacy"}):
            with self.subTest(patch=patch):
                self.layout.write_text(json.dumps({**self.meta, **patch}))
                with self.assertRaises(ValueError):
                    dump.Image(self.bin, self.layout)

    def test_raw_disk_pe_cannot_masquerade_as_mapped_image(self):
        self.data = self.data[:0x1000]
        self.meta["image_size"] = len(self.data)
        self.meta["valid_ranges"] = [{"rva": 0, "size": len(self.data)}]
        self.meta.pop("regions")
        self.write()
        with self.assertRaisesRegex(ValueError, "SizeOfImage"):
            dump.Image(self.bin, self.layout)

    def test_holes_never_match_and_utf16_locations_retained(self):
        self.assertEqual(dump.find_pattern(self.image, b"HOLE", 20)["total"], 0)
        with self.assertRaises(ValueError):
            self.image.read(0x1FFF, 2)
        result = dump.find_pattern(self.image, "汉字锚点".encode("utf-16le"), 20)
        self.assertEqual(result["hits"][0]["rva"], 0x3040)
        self.assertEqual(self.image.holes(), [{"rva": 0x2000, "size": 0x1000}])

    def test_guard_metadata_is_not_valid_coverage(self):
        self.meta["regions"][1]["protect"] |= 0x100
        self.write()
        with self.assertRaisesRegex(ValueError, "guard"):
            dump.Image(self.bin, self.layout)

    def test_literal_matches_report_true_total_and_truncation(self):
        result = dump.find_pattern(dump.Image(self.bin, raw=True), b"\0", 3)
        self.assertGreater(result["total"], 3)
        self.assertEqual(result["returned"], 3)
        self.assertTrue(result["truncated"])

    def test_multilevel_callers_use_function_ranges(self):
        graph = dump.graph_data(self.image, self.image.functions, 1000)
        edges = dump.reverse_callers(graph, 0x1200, 3)["edges"]
        self.assertTrue(any(e["caller"] == 0x1100 and e["depth"] == 1 for e in edges))
        self.assertTrue(any(e["caller"] == 0x1000 and e["depth"] == 2 for e in edges))
        self.assertFalse(any(e["caller"] == 0x1500 for e in edges))

    def test_embedded_e8_is_candidate_but_not_decoded_call(self):
        code, output, error = self.cli("candidates", "--target", "0x1200")
        self.assertEqual(code, 0, error)
        sites = {h["site"] for h in json.loads(output)["result"]["hits"]}
        self.assertIn(0x1502, sites)
        graph = dump.graph_data(self.image, self.image.functions, 1000)
        self.assertNotIn(0x1502, [e["site"] for e in graph["edges"]])

    def test_conditional_path_after_first_return_is_preserved(self):
        graph = dump.graph_data(self.image, self.image.functions, 1000)
        self.assertTrue(any(e["site"] == 0x1407 and e["callee"] == 0x1200 for e in graph["edges"]))

    def test_external_and_indirect_calls_remain_visible(self):
        graph = dump.graph_data(self.image, self.image.functions, 1000)
        external = next(e for e in graph["edges"] if e["site"] == 0x1600)
        self.assertEqual(external["target_va"], BASE + 0x6000)
        self.assertIsNone(external["target_rva"])
        self.assertTrue(any(not e["direct"] and e["kind"] == "call" for e in graph["edges"]))

    def test_rip_lea_and_mov_are_distinguished(self):
        code, output, error = self.cli("xref", "--target", "0x3020")
        self.assertEqual(code, 0, error)
        refs = json.loads(output)["result"]["refs"]
        self.assertEqual(len(refs), 2)
        self.assertTrue(refs[0]["address_only"])
        self.assertFalse(refs[0]["read"])
        self.assertTrue(refs[1]["read"])

    def test_segment_relative_load_is_not_a_plain_rip_reference(self):
        block = rip(b"\x65\x8b\x0d", 0x1200, 0x3020) + b"\xc3"
        self.data[0x1200:0x1200 + len(block)] = block
        self.write()
        code, output, error = self.cli("xref", "--target", "0x3020")
        self.assertEqual(code, 0, error)
        self.assertEqual(json.loads(output)["result"]["total"], 0)

    def test_out_of_module_rva_is_rejected(self):
        self.assertEqual(self.cli("pointers", "--target", "0x9000")[0], 2)
        self.assertEqual(self.cli("disasm", "--rva", "-1")[0], 2)

    def test_field_reads_writes_rmw_simd_and_small_decimal_offset(self):
        fields = dump.field_data(self.image, self.image.functions, 1000, [], 0x1C8, 200)
        self.assertEqual(fields["stride_total"], 1)
        self.assertEqual(fields["field_total"], 4)
        small = [f for f in fields["fields"] if f["disp"] == 9]
        self.assertEqual([(f["read"], f["write"]) for f in small],
                         [(False, True), (True, False), (True, True)])
        simd = next(f for f in fields["fields"] if f["disp"] == 0xB0)
        self.assertEqual(simd["width"], 4)
        self.assertTrue(simd["write"])
        self.assertTrue(all(f["base"] == "rax" for f in fields["fields"]))

    def test_pointer_alignment_and_all_hits_option(self):
        pattern = struct.pack("<Q", BASE + 0x1200)
        self.assertEqual(dump.find_pattern(self.image, pattern, 20, alignment=8)["total"], 1)
        self.assertEqual(dump.find_pattern(self.image, pattern, 20, alignment=1)["total"], 2)

    def test_cache_identity_layout_and_ranges_are_checked(self):
        graph = dump.graph_data(self.image, self.image.functions, 1000)
        dump.validate_graph(graph, self.image, self.image.functions)
        self.layout.write_text(json.dumps(self.meta, indent=2))
        other = dump.Image(self.bin, self.layout)
        with self.assertRaisesRegex(ValueError, "cache"):
            dump.validate_graph(graph, other, other.functions)
        with self.assertRaisesRegex(ValueError, "ranges"):
            dump.validate_graph(graph, self.image, [dump.Function(0x1000, 0x1010, "manual-vetted-entry")])

    def test_decode_budget_and_unavailable_code_are_reported(self):
        graph = dump.graph_data(self.image, self.image.functions, 1)
        self.assertTrue(graph["coverage"]["budget_exhausted"])
        engine, cs, x86 = dump.capstone_engine()
        ins, issues = dump.decode_function(self.image, dump.Function(0x1FFD, 0x2005), 100, engine, cs, x86)
        self.assertFalse(ins)
        self.assertTrue(any(i["reason"] == "decode stopped" for i in issues))

    def test_anchors_exit_code_and_output_never_overwritten(self):
        self.assertEqual(self.cli("anchors", "--anchor", "0=4d 5a")[0], 0)
        self.assertEqual(self.cli("anchors", "--anchor", "0=00 00")[0], 2)
        self.assertEqual(self.cli("anchors", "--anchor", "0x2000=48 4f 4c 45")[0], 2)
        artifact = self.root / "graph.json"
        self.assertEqual(self.cli("graph", "--out", str(artifact))[0], 0)
        self.assertEqual(self.cli("graph", "--out", str(artifact))[0], 2)
        code, output, error = self.cli("callers", "--target", "0x1200", "--graph", str(artifact))
        self.assertEqual(code, 0, error)
        self.assertTrue(any(e["depth"] == 2 for e in json.loads(output)["result"]["edges"]))


class CaptureTests(unittest.TestCase):
    def test_partial_reads_preserved_and_guard_not_read(self):
        class FakeReader:
            def __init__(self):
                self.calls = []
            def read(self, address, size):
                self.calls.append((address, size))
                if address == 0:
                    return b"A" * 8, 299
                if address == 8:
                    return b"B" * 4, 299
                return b"C" * size, 0
        reader, stream = FakeReader(), io.BytesIO(b"\0" * 48)
        regions = [{"rva": 0, "size": 32, "state": 0x1000, "protect": 4},
                   {"rva": 32, "size": 16, "state": 0x1000, "protect": 0x104}]
        result = capture.capture_span(reader, 0, 48, regions, stream, 32, 16)
        self.assertEqual(result["valid_ranges"], [{"rva": 0, "size": 12}, {"rva": 16, "size": 16}])
        self.assertEqual(stream.getvalue()[12:16], b"\0" * 4)
        self.assertEqual(stream.getvalue()[32:], b"\0" * 16)
        self.assertFalse(any(address >= 32 for address, _ in reader.calls))

    def test_failed_large_read_recovers_readable_pages(self):
        class FakeReader:
            def read(self, address, size):
                return (b"x" * size, 0) if address == 16 else (b"", 299)
        stream = io.BytesIO(b"\0" * 32)
        result = capture.capture_span(FakeReader(), 0, 32,
                                     [{"rva": 0, "size": 32, "state": 0x1000, "protect": 2}],
                                     stream, 32, 16)
        self.assertEqual(result["valid_ranges"], [{"rva": 16, "size": 16}])

    def test_region_coverage_and_module_ambiguity(self):
        with self.assertRaisesRegex(ValueError, "cover"):
            capture.capture_span(None, 0, 32,
                                 [{"rva": 1, "size": 32, "state": 0x1000, "protect": 2}], io.BytesIO())
        modules = [{"name": "x.dll", "path": "C:/a/x.dll"}, {"name": "x.dll", "path": "C:/b/x.dll"}]
        with self.assertRaisesRegex(ValueError, "match"):
            capture.select_module(modules, "x.dll")
        self.assertEqual(capture.select_module(modules, "C:/b/x.dll"), modules[1])

    @unittest.skipUnless(os.name == "nt" and ctypes.sizeof(ctypes.c_void_p) == 8, "Windows x64 API contract")
    def test_windows_x64_abi_layout(self):
        self.assertEqual(ctypes.sizeof(capture.MBI), 48)
        self.assertEqual(capture.MBI.RegionSize.offset, 24)
        self.assertEqual(capture.MBI.Protect.offset, 36)
        self.assertEqual(ctypes.sizeof(capture.ModuleEntry), 1080)
        self.assertEqual(capture.ModuleEntry.modBaseAddr.offset, 24)

    @unittest.skipUnless(os.name == "nt" and ctypes.sizeof(ctypes.c_void_p) == 8, "Windows x64 controlled capture")
    def test_capture_own_python_helper_end_to_end(self):
        # Windows venv launchers can report sys.executable outside the loaded image.
        # Ask the controlled child for its real main module, without guessing a path.
        child = (
            "import ctypes,json,os,sys; "
            "api=ctypes.WinDLL('kernel32',use_last_error=True).GetModuleFileNameW; "
            "api.argtypes=[ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_uint]; "
            "api.restype=ctypes.c_uint; path=ctypes.create_unicode_buffer(32768); "
            "assert api(None,path,len(path)); "
            "print(json.dumps({'pid':os.getpid(),'module':path.value}),flush=True); sys.stdin.read()"
        )
        process = subprocess.Popen(
            [sys.executable, "-B", "-c", child],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(lambda: process.poll() is None and process.kill())
        try:
            sample = json.loads(process.stdout.readline())
            pid = sample["pid"]
            with tempfile.TemporaryDirectory(prefix="wh3-owned-process-test-") as folder:
                output, error = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
                    code = capture.main(["--pid", str(pid), "--module", sample["module"],
                                         "--out-dir", folder])
                self.assertEqual(code, 0, error.getvalue())
                layouts = list(Path(folder).glob("*.layout.json"))
                self.assertEqual(len(layouts), 1)
                layout = json.loads(layouts[0].read_text())
                binary = layouts[0].with_name(layouts[0].name.replace(".layout.json", ".bin"))
                image = dump.Image(binary, layouts[0])
                self.assertEqual(image.read(0, 2), b"MZ")
                self.assertEqual(layout["pid"], pid)
                self.assertGreater(layout["image_base"], 2**32)
                self.assertTrue(image.functions)
        finally:
            process.communicate("", timeout=10)
            self.assertEqual(process.returncode, 0)


if __name__ == "__main__":
    unittest.main()
