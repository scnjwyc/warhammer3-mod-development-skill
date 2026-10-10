-- Test-only ASCII subset of CA's string.find contract, not UTF-8 emulation.
-- Keep the original Lua patterns/fourth plain flag on string.find_lua.
-- Record violations independently so pcall cannot hide a contract failure.
local original = string.find_lua or string.find
local violations = {}
string.find_lua = original
string.find = function(subject, needle, ...)
    if select('#', ...) > 1 then
        violations[#violations + 1] = debug.traceback('invalid fourth argument to CA string.find', 2)
        error('CA string.find accepts 2-3 arguments; use string.find_lua', 2)
    end
    local start = ...
    return original(subject, needle, start or 1, true)
end
return {
    reset = function() violations = {} end,
    assert_clean = function() assert(#violations == 0, violations[1]) end,
}
