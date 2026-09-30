"""Focused offline regression tests for the delivered DDS/LOC helpers."""
import importlib.util
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


DDS = load('portable_dds', ROOT / 'skills/warhammer-character-textures/scripts/dds_utils.py')
LOC = load('portable_loc', ROOT / 'skills/warhammer-mod-translation/scripts/fix_loc_newlines.py')


class Helpers(unittest.TestCase):
    def header(self, fmt=None):
        data = bytearray(148 if fmt is not None else 128)
        data[:4] = b'DDS '
        for offset, value in ((4, 124), (12, 64), (16, 128), (28, 8), (76, 32)):
            struct.pack_into('<I', data, offset, value)
        data[84:88] = b'DX10' if fmt is not None else b'DXT1'
        if fmt is not None:
            struct.pack_into('<I', data, 128, fmt)
        return data

    def inspect(self, data):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'sample.dds'
            path.write_bytes(data)
            result = DDS.read_dds_info(path)
            self.assertEqual(path.read_bytes(), data)
            return result

    def test_dds_all_bc6_variants_are_detected(self):
        for fmt, name in ((94, 'BC6H_TYPELESS'), (95, 'BC6H_UF16'), (96, 'BC6H_SF16')):
            info = self.inspect(self.header(fmt))
            self.assertTrue(info.is_bc6)
            self.assertEqual(info.format_name, name)

    def test_dds_ldr_and_legacy_headers(self):
        for fmt in (71, 72, 77, 78, 98, 99, None):
            info = self.inspect(self.header(fmt))
            self.assertFalse(info.is_bc6)
            self.assertEqual((info.width, info.height, info.mip_count), (128, 64, 8))

    def test_dds_truncated_or_invalid_header_rejected(self):
        for data in (b'bad', self.header(99)[:140], bytearray(128)):
            with self.assertRaises(ValueError):
                self.inspect(data)
        data = self.header()
        struct.pack_into('<I', data, 16, 0)
        with self.assertRaises(ValueError):
            self.inspect(data)

    def test_loc_newline_normalization_is_idempotent(self):
        original = 'key\ttext\ttooltip\n#Loc;1;text/db/test\nkey_a\tA' + chr(92) + 'nB\ttrue\n'
        fixed, joins, singles = LOC.normalize(original)
        self.assertEqual((joins, singles), (0, 1))
        self.assertIn('A' + chr(92) * 2 + 'nB', fixed)
        self.assertEqual(LOC.normalize(fixed), (fixed, 0, 0))

    def test_loc_check_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'sample.loc.tsv'
            path.write_text('key\ttext\ttooltip\nk\ta' + chr(92) + 'nb\ttrue\n', encoding='utf-8')
            before = path.read_bytes()
            changed, _ = LOC.process(path, write=False)
            self.assertTrue(changed)
            self.assertEqual(before, path.read_bytes())


if __name__ == '__main__':
    unittest.main()
