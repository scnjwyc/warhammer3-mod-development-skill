"""Focused offline regression tests for the delivered LOC helper."""
import importlib.util
from pathlib import Path
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


LOC = load('portable_loc', ROOT / 'skills/warhammer-mod-translation/scripts/fix_loc_newlines.py')


class Helpers(unittest.TestCase):
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
