"""Calibrate the bundled ASCII CA string double in isolated Lua 5.1 runtimes."""
from pathlib import Path
import unittest

from lupa import lua51

DOUBLE = Path(__file__).with_name("wh3_strings.lua")


class StringContractTests(unittest.TestCase):
    def setUp(self):
        self.lua = lua51.LuaRuntime(unpack_returned_tuples=True)
        self.contract = self.lua.execute(DOUBLE.read_text(encoding="utf-8"))

    def test_runtime_is_lua51(self):
        self.assertEqual(self.lua.eval("_VERSION"), "Lua 5.1")
        self.contract.assert_clean()

    def test_literal_search_does_not_use_patterns(self):
        self.assertEqual(self.lua.eval("string.find('a.b a.b', 'a.b', 2)"), (5, 7))
        self.assertIsNone(self.lua.eval("string.find('axb', 'a.b')"))
        self.assertIsNone(self.lua.eval("string.find('a' .. string.char(1), '%c')"))
        self.assertIsNone(self.lua.eval("string.find('unknown', '%S')"))
        self.contract.assert_clean()

    def test_original_lua_patterns_and_plain_flag_are_preserved(self):
        self.assertEqual(self.lua.eval("string.find_lua('axb', 'a.b')"), (1, 3))
        self.assertIsNone(self.lua.eval("string.find_lua('axb', 'a.b', 1, true)"))
        self.assertEqual(self.lua.eval("string.find_lua('a' .. string.char(1), '%c')"), (2, 2))
        self.assertEqual(self.lua.eval("string.find_lua(' x', '%S')"), (2, 2))
        self.contract.assert_clean()

    def test_fourth_argument_including_colon_and_nil_is_rejected(self):
        for expression in ("string.find('a', 'a', 1, true)",
                           "('a'):find('a', 1, true)",
                           "string.find('a', 'a', 1, nil)"):
            with self.subTest(expression=expression):
                self.contract.reset()
                with self.assertRaises(lua51.LuaError):
                    self.lua.execute(expression)
                with self.assertRaises(lua51.LuaError):
                    self.contract.assert_clean()

    def test_pcall_cannot_hide_violation_and_reset_is_explicit(self):
        self.lua.execute("local ok = pcall(function() string.find('a', 'a', 1, true) end); assert(not ok)")
        with self.assertRaises(lua51.LuaError):
            self.contract.assert_clean()
        self.contract.reset()
        self.contract.assert_clean()


if __name__ == "__main__":
    unittest.main()
