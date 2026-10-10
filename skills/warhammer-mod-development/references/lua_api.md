# Lua 生命周期与 API

按 Lua 5.1 兼容子集编写；不使用 `goto`、标签、`//`、位运算符或 `continue`。用对应版本的 `luac -p` 检查；高版本 luac 通过不能证明 5.1 兼容。

## 初始化与监听

`cm:add_first_tick_callback` 适合每次会话（新局和读档）都需恢复的战役监听与状态；`cm:add_first_tick_callback_new` 仅用于新局初始化，不能把需要读档后恢复的监听放在那里。监听是否生效取决于实际加载与注册时机，不以“顶层注册一定无效”作为引擎规则。

```lua
cm:add_first_tick_callback(function()
    core:remove_listener("my_mod_turn")
    core:add_listener("my_mod_turn", "FactionTurnStart",
        function(context)
            local faction = context:faction()
            return faction and not faction:is_null_interface() and faction:is_human()
        end,
        function(context)
            out("my_mod: turn=" .. tostring(cm:turn_number()))
        end,
        true)
end)
```

`core:add_listener(name, event, condition, callback, persistent)` 的第五参数决定触发后是否保留。监听名需唯一，重复初始化须幂等。延时回调要重新获取可能失效的角色/UI 接口。

## 按当前脚本和文档核对签名

| 需求 | 常见 API，使用前核对参数 |
|---|---|
| 获取派系 | `cm:get_faction(key)`；先判 nil / null，再调用其他方法 |
| DB 效果包 | `cm:apply_effect_bundle(key, faction_key, turns)`，0 常表示永久 |
| 动态效果包 | `cm:create_new_custom_effect_bundle(key)`、`bundle:add_effect(key, scope, value)`、`bundle:set_duration(turns)`、`cm:apply_custom_effect_bundle_to_faction(bundle, faction)` |
| 存档状态 | `cm:get_saved_value(key)`、`cm:set_saved_value(key, value)`，处理旧档 nil 与迁移 |
| 延迟调用 | `cm:callback(function() ... end, seconds)` |
| 外交 | `cm:force_alliance` / `cm:force_confederation`；核对当前签名和派系有效性 |

不要从名字猜 API。文档里的 `源码/` 是 [环境约定](project_structure.md)，缺原版 API 文档时不能宣称签名已确认。

文化与亚文化是不同键域，分别查 `cultures_tables` 和 `cultures_subcultures_tables`；震旦亚文化实例是 `wh3_main_sc_cth_cathay`，用 `subculture()` 比较，不能填入 `culture()` 判断。

效果必须同时核对 effect 的 bonus-value junction、scope、目标接口和持续时间。[效果链参考](effects_and_bundles.md)；具体失败优先读 [日志排查](debugging.md)。

字符串搜索先核对 [CA 字符串契约](ca-string-api.md)，不能把标准 Lua 的四参数或模式行为直接用于 CA 的 `string.find`。状态、事件、延迟、保存恢复和 UI/CCO 改动按 [离线回归](lua-offline-testing.md) 校验实际源码路径；真实场景资料按 [MCP 证据工作流](wh3-mcp-workflow.md) 分析。
