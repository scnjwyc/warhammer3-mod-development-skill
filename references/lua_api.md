# Lua 常用API参考

## campaign_manager (`cm:`) 核心API

### 派系操作

```lua
-- 获取派系对象
cm:get_faction(faction_key) → faction对象/nil

-- 强制结盟
cm:force_alliance(faction_a_key, faction_b_key, make_allies)  -- make_allies: true=军事同盟

-- 强制合邦
cm:force_confederation(faction_a_key, faction_b_key)
```

### Effect Bundle操作

```lua
-- 创建自定义effect bundle（动态）
cm:create_new_custom_effect_bundle(bundle_key) → effect_bundle对象

-- 应用DB中预定义的effect bundle到派系
cm:apply_effect_bundle(bundle_key, faction_key, turns)  -- turns=0 表示永久

-- 移除effect bundle
cm:remove_effect_bundle(bundle_key, faction_key)
```

### Effect Bundle对象方法

```lua
-- 向bundle添加效果
effect_bundle:add_effect(effect_key, scope, value)

-- 设置持续时间（0=永久）
effect_bundle:set_duration(turns)

-- 应用到派系
cm:apply_custom_effect_bundle_to_faction(effect_bundle, faction_object)
```

### 存档操作

```lua
-- 读取存档值
cm:get_saved_value(key) → value 或 nil

-- 写入存档值
cm:set_saved_value(key, value)
```

### 回调注册

```lua
-- 首帧回调（游戏开始）
cm:add_first_tick_callback_new(function(context)
    -- 初始化代码
end)

-- 每回合回调
cm:add_turn_callback(function(context)
    -- 每回合执行的代码
end)

-- 延迟回调（秒为单位）
cm:callback(function()
    -- 延迟执行的代码
end, delay_seconds)
```

### 回合/模型信息

```lua
-- 获取当前回合数
cm:model():turn_number() → number

-- 获取战役名称
cm:model():campaign_name_key() → string
```

### 输出日志

```lua
out(message)  -- 输出到游戏日志
script_error(message)  -- 输出错误并可能中止
```

## Faction对象方法

```lua
local faction = cm:get_faction(faction_key)

-- 存活性检查（必须先检查！）
faction:is_dead() → boolean
faction:is_null_interface() → boolean

-- Bundle检查
faction:has_effect_bundle(bundle_key) → boolean

-- 同盟检查
faction:allied_with(other_faction_object) → boolean
```

## Lua文件结构模板

```lua
-- wyccc_<功能名>.lua
-- MOD名称：<功能描述>

local MODULE_KEY = "wyccc_<功能名>"

-- 常量定义
local MAX_LEVEL = 5
local TURNS_PER_LEVEL = 20

-- 工具函数
local function is_faction_alive(faction_key)
    local faction = cm:get_faction(faction_key)
    return faction and not faction:is_dead() and not faction:is_null_interface()
end

-- 核心逻辑函数
local function do_something()
    -- ...
end

-- 初始化回调
cm:add_first_tick_callback_new(function(context)
    out(MODULE_KEY .. ": Module registered")
    cm:callback(function()
        -- 延迟初始化
    end, 0.2)
end)

-- 回合回调
cm:add_turn_callback(function(context)
    -- 每回合逻辑
end)
```

## 常见作用域 (scope)

| scope | 含义 |
|-------|------|
| `faction_to_faction_own_unseen` | 派系→自身（全局效果，不显示UI） |
| `faction_to_force_own_unseen` | 派系→所有部队 |
| `faction_to_province_own_unseen` | 派系→所有行省 |
| `faction_to_region_own_unseen` | 派系→所有地区 |
| `faction_to_character_own_unseen` | 派系→所有角色 |
| `force_to_force_own` | 部队→自身 |

## 基础错误检查清单

1. `cm:get_faction()` 返回值需检查 `nil`、`is_null_interface()`、`is_dead()`
2. `out()` 调用需确保参数可转为字符串（使用 `tostring()`）
3. 延迟回调用 `cm:callback(fn, seconds)` 而非直接调用
4. 存档读写需处理 `nil` 返回值：`cm:get_saved_value(key) or 0`
5. `add_effect()` 的 scope 参数必须是有效的作用域字符串
