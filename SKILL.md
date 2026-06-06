---
name: warhammer-mod-development
description: 提供全面战争：战锤3 MOD开发指导，包括TSV表格格式、Lua脚本模式、本地化约定和项目结构。当用户提及战锤、MOD、WH3、Lua脚本、数据库表、本地化、翻译或MOD开发时使用。
---

# 战锤3 MOD 开发指南

## 工作区结构

```
战锤MOD相关/
├── 源码/          # 游戏原版脚本、UI、DB文件（供参考）
├── 多语言/        # 原版本地化文件（/CN 中文、/EN 英文）
└── mod/           # 所有MOD文件夹
    └── [MOD名]/
        ├── script/campaign/mod/    # Lua脚本
        ├── db/                     # 数据库表（TSV）
        └── text/db/                # 文本本地化
```

## TSV 文件命名规范

### 需遵循的规则

1. **前缀命名**：使用MOD专属前缀（如 `!wyccc_`），绝不使用 `data__`
2. **文件前缀必须与表前缀匹配**
3. **使用 `!` 前缀**表示覆盖原版数据

### 正确示例

```
!wyccc_cathay_internal_alliance.tsv    # 正确
!wyccc_effect_bundles.tsv              # 正确
data__.tsv                              # 错误！
```

### 错误示例

```
wyccc_cathay_internal_alliance.tsv      # 缺少 !
data__.tsv                              # 错误：使用了 data__
```

## TSV 文件格式要求

### 标准头部格式

```tsv
header
#表名;版本;表路径
key	列1	列2	列3
```

### 示例：effects_tables

```tsv
id	incident_key	payload_key	value	target_key
#cdir_events_incident_payloads_tables;2;db/cdir_events_incident_payloads_tables/!!wyccc_difficulty_ogre_unification
9999990001	wh3_dlc26_wyccc_incident_ogre_unification	TEXT_DISPLAY	LOOKUP[dummy_wyccc_ogre_unification]	default
```

### 检查清单

- [ ] 文件扩展名为 `.tsv`
- [ ] 列数与头部匹配
- [ ] 使用制表符分隔（非空格）
- [ ] 无多余空行或空列
- [ ] 路径前缀与文件名前缀匹配
- [ ] 版本号与原版表匹配
- [ ] 脚本函数存在于原版文档且参数正确
- [ ] 生成的中/英文本地化文件使用原版条目
- [ ] 新效果作用域配置正确
- [ ] 本地化键名遵循命名规范（参见"本地化文本约定"章节）

### 表版本参考

| 表名 | 原版版本 |
|------|---------|
| effects_tables | 0 |
| effect_bundles_tables | 4 |
| effect_bundles_to_effects_junctions_tables | 3 |
| incidents_tables | 7 |
| cdir_events_incident_payloads_tables | 2 |
| effect_bonus_value_faction_junctions_tables | 0 |

### 示例：effects_tables

```tsv
effect	icon	priority	icon_negative	category	is_positive_value_good
#effects_tables;0;db/effects_tables/!!wyccc_cathay_internal_alliance
wyccc_cathay_diplomatic_relations_rebel_lords_of_nan_yang	diplomacy.png	100	diplomacy.png	campaign	true
```

### 示例：cdir_events_incident_payloads_tables

```tsv
id	incident_key	payload_key	value	target_key
#cdir_events_incident_payloads_tables;2;db/cdir_events_incident_payloads_tables/!!wyccc_difficulty_ogre_unification
9999990001	wh3_dlc26_wyccc_incident_ogre_unification	TEXT_DISPLAY	LOOKUP[dummy_wyccc_ogre_unification]	default
```

### 示例：effect_bundles_tables

```tsv
key	localised_description	localised_title	bundle_target	priority	ui_icon	is_global_effect	show_in_3d_space	owner_only
#effect_bundles_tables;4;db/effect_bundles_tables/!!wyccc_cathay_nonorder_buffs
wyccc_nonorder_buff_lv1	[hidden]	[hidden]	faction	1		false	false	true
```

### 效果作用域检查清单
例如，wh_main_effect_economy_gdp_mod_all 在原版配置中使用 province_to_region_own_factionwide 或 faction_to_region_own_unseen 作用域。对于全局加成，使用 faction_to_region_own_unseen（派系 -> 区域）。对于建筑效果，使用 province_to_region_own_factionwide，以此类推。

## Lua 编码规范

### 1. 基本格式检查

```lua
-- 文件头注释（推荐）
-- mod_name.lua
-- 描述: MOD功能说明

local MODULE_KEY = "mod_name"

-- 检查派系是否存活
local function is_faction_alive(faction_key)
    local faction = cm:get_faction(faction_key)
    return faction and not faction:is_dead() and not faction:is_null_interface()
end
```

### 2. 事件监听器注册

**重要：`core:add_listener` 必须在 `cm:add_first_tick_callback` 内调用才能生效！**

在脚本顶层注册的监听器不会自动激活。

```lua
-- ============================================================
-- 正确模式：监听器在 add_first_tick_callback 内注册
-- ============================================================

-- 模块初始化函数
local function initialize_module()
    -- 在此注册所有监听器
    core:add_listener(
        "my_module_turn_listener",
        "FactionTurnStart",
        function(context)
            out("回合: " .. cm:turn_number())
            return true
        end,
        true  -- 保持监听器激活
    )

    out("MyModule: 监听器已注册")
end

-- 在游戏首次tick时初始化（触发监听器注册）
cm:add_first_tick_callback(function()
    initialize_module()
    out("MyModule: 模块已初始化")
end)
```

```lua
-- ============================================================
-- 错误模式：监听器在顶层注册（不会生效）
-- ============================================================

-- 错误！顶层注册不会生效
core:add_listener(
    "my_module_turn_listener",
    "FactionTurnStart",
    function(context)
        out("回合: " .. cm:turn_number())
        return true
    end,
    true
)

cm:add_first_tick_callback(function()
    out("这不会让上面的监听器生效")
end)
```

**`core:add_listener` 参数说明：**

| 参数 | 说明 |
|------|------|
| 第1个 | 唯一监听器名称（字符串） |
| 第2个 | 事件类型（如 "FactionTurnStart"、"BattleCompleted"） |
| 第3个 | 条件函数（返回 true 时执行回调） |
| 第4个 | 回调函数 |
| 第5个 | 持久化（true = 持续监听，false = 触发后移除） |

**常用事件类型：**

| 事件 | 触发时机 |
|------|---------|
| `FactionTurnStart` | 每个派系回合开始 |
| `WorldStartRound` | 每轮开始 |
| `BattleCompleted` | 战斗结束 |
| `CharacterTurnStart` | 角色回合开始 |
| `IncidentRequest` | 事件请求 |

### 3. API 函数验证

**始终验证函数存在于原版脚本文档中且参数与定义匹配**

常用源码路径：
```
源码/script/campaign/           # 战役脚本
源码/script/battle/             # 战斗脚本
源码/db/                        # 数据库表
源码/documentation/script       # 脚本文档
```

**常用 API 示例：**

| 功能 | 正确函数 |
|------|---------|
| 强制结盟 | `cm:force_alliance(faction_a, faction_b, true)` |
| 应用效果捆绑 | `cm:apply_effect_bundle(bundle_key, faction_key, duration)` |
| 创建自定义效果捆绑 | `cm:create_new_custom_effect_bundle(key)` |
| 添加效果 | `bundle:add_effect(effect_key, scope, value)` |
| 获取派系 | `cm:get_faction(faction_key)` |
| 首次tick回调 | `cm:add_first_tick_callback(function(context) end)` |
| 注册监听器 | `core:add_listener(name, event, condition_fn, callback_fn, persistent)` |

### 4. 常见错误

```lua
-- 错误1：使用不存在的函数
cm:force_diplomatic_alliance(a, b)  -- 不存在！

-- 正确：使用已验证的函数
cm:force_alliance(a, b, true)

-- 错误2：监听器在顶层注册（不会生效）
core:add_listener(...)  -- 不会生效！

-- 正确：必须在 add_first_tick_callback 内
cm:add_first_tick_callback(function()
    core:add_listener(...)  -- 正确位置
end)

-- 错误3：在 add_first_tick_callback_new 中注册监听器（可能失败）
cm:add_first_tick_callback_new(function(context)
    core:add_listener(...)  -- 时机可能太晚
end)

-- 推荐：使用 cm:add_first_tick_callback
cm:add_first_tick_callback(function()
    core:add_listener(...)
end)
```

### 5. culture 与 subculture 的区别

**游戏有两层文化系统：**

- **`culture`**：通常代表种族类别（如 `wh3_main_combi_mod_human`）。游戏脚本中很少用于派系检查。
- **`subculture`**：代表具体文化/派系归属（如 `wh3_main_sc_cth_cathay`）。游戏脚本中大多数派系检查使用 `subculture()`。

**检查派系是否属于震旦（示例）：**

```lua
-- 错误：震旦使用 subculture；culture() 始终返回 false
local function is_cathay(faction_key)
    local faction = cm:get_faction(faction_key)
    return faction and faction:culture() == "wh3_main_sc_cth_cathay"
end

-- 正确：使用 subculture() 检查震旦派系
local CATHAY_SUBCULTURE = "wh3_main_sc_cth_cathay"

local function is_cathay(faction_key)
    local faction = cm:get_faction(faction_key)
    return faction and faction:subculture() == CATHAY_SUBCULTURE
end
```

**如何确认 KEY 类型：**
- 前往 `源码/db/cultures_tables/` 和 `源码/db/cultures_subcultures_tables/` 查看定义
- 带 `sc_` 前缀的键通常是 subculture（如 `wh3_main_sc_cth_cathay`）
- 不带 `sc_` 前缀的键通常是 culture

## 数据库表类型参考

| 表名 | 用途 |
|------|------|
| effects_tables | 定义效果类型 |
| effect_bundles_tables | 定义效果捆绑 |
| effect_bundles_to_effects_junctions_tables | 将效果捆绑绑定到效果 |
| effect_bonus_value_faction_junctions_tables | 将效果绑定到派系 |
| diplomatic_relationship_effects_tables | 外交关系效果 |
| incidents_tables | 事件配置 |

## 本地化文本约定

### 核心原则：本地化键名命名规范

游戏从本地化文件加载文本时，键名必须遵循固定命名规范，由**表前缀** + **完整键名**组成。

**格式**：`{表前缀}_{完整键名}`

一个键通常对应两个本地化键：标题和描述。查询原版本地化文件获取用法示例。
例如，effects_tables 的键使用前缀 `effects_description_`。

### 常见错误

**错误**：直接将完整键名用作本地化键。

```tsv
-- 错误！游戏查找的键不是这个
wyccc_ogre_feast_warning_debuff	饕餮预警	debuff.png
```

**正确**：使用表前缀 + `_localised_title_` / `_localised_description_` 前缀。

```tsv
-- 正确！游戏查找这两个键
effect_bundles_localised_title_wyccc_ogre_feast_warning_debuff	饕餮预警
effect_bundles_localised_description_wyccc_ogre_feast_warning_debuff	食人魔大军逼近，城镇秩序下降，防御力量被削弱。
```

## 开发工作流

1. **阅读源码**：在 `源码/script/campaign/` 中搜索类似实现
2. **检查DB表结构**：参考 `源码/db/` 中的表定义
3. **验证命名**：确认使用了正确的MOD前缀
4. **Lua语法检查**：确保没有基本语法错误
5. **API验证**：使用 Grep 在源码目录中搜索所用函数

## 快速参考

- 源码位置：`c:\Users\Administrator\Desktop\战锤MOD相关\源码`
- MOD位置：`c:\Users\Administrator\Desktop\战锤MOD相关\mod`
- 原版本地化文件：`c:\Users\Administrator\Desktop\战锤MOD相关\多语言`，`localisation__.loc_CN` 为中文翻译
- 原版脚本文档：`C:\Users\Administrator\Desktop\战锤MOD相关\源码\documentation\script`
- 搜索功能：`Grep` 工具，设置搜索路径为源码目录

## 附加资源

- TSV格式详情，参见 [references/tsv_format.md](references/tsv_format.md)
- Lua API参考，参见 [references/lua_api.md](references/lua_api.md)
- 命名规范，参见 [references/naming_conventions.md](references/naming_conventions.md)
- 常用效果键，参见 [references/common_effect_keys.md](references/common_effect_keys.md)
- 项目结构，参见 [references/project_structure.md](references/project_structure.md)
