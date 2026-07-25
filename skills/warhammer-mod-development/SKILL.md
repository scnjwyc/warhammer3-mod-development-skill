---
name: warhammer-mod-development
description: "提供全面战争：战锤3 MOD开发指导，包括TSV表格格式、Lua脚本模式、项目结构、法术DB、角色技能树与领主/英雄动作、美术资源(见 warhammer-mod-art)。触发词：战锤、MOD、WH3、Lua脚本、数据库表、MOD开发、法术、spell、vortex、projectile、动作、动画、日志、log、有问题、问题依然存在。涉及法术/技能树/动作时须查阅仓库根目录三份专题文档（见附加资源）。注意：翻译、本地化、译名、术语、汉化相关任务请使用 warhammer-mod-translation 技能；技能图标、角色兵牌、立绘、porthole 等美术资源绘制请使用 warhammer-mod-art 技能；新建传奇领主/英雄角色的完整流程请使用 warhammer-mod-character-creation 技能。"
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

1. **增量/追加模式**：使用MOD专属前缀（如 `!wyccc_`），用于新增条目或覆盖部分行
2. **使用 `!` 前缀**表示覆盖原版数据（增量模式）
3. **全量替换模式**：当需要替换整张表的所有行时，文件必须命名为 `data__.tsv`（与原版DB文件名一致）

### 正确示例

```
# 增量模式（新增/覆盖部分行）
!wyccc_cathay_internal_alliance.tsv    # 正确
!wyccc_effect_bundles.tsv              # 正确

# 全量替换模式（替换整张表）
data__.tsv                              # 正确：全量替换时必须用此名称
```

### 错误示例

```
wyccc_cathay_internal_alliance.tsv      # 错误：缺少 ! 前缀
!wyccc_xxx.tsv                          # 错误：全量替换时不能用前缀名，必须用 data__.tsv
data__.tsv                              # 错误：增量追加时不应使用 data__
```

### 如何选择模式

| 场景 | 文件名 | 说明 |
|------|--------|------|
| 新增几条记录 | `!wyccc_xxx.tsv` | 增量追加，不影响原版其他行 |
| 覆盖某几行的值 | `!wyccc_xxx.tsv` | 按主键覆盖，其他行保持不变 |
| 修改整张表的大部分行 | `data__.tsv` | 全量替换，必须包含完整表数据 |

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
- [ ] **数值型主键在 schema 字段类型范围内**（见下方"数值主键范围校验"章节，特别是 `I32` 字段）
- [ ] 脚本函数存在于原版文档且参数正确
- [ ] 生成的中/英文本地化文件使用原版条目
- [ ] 新效果作用域配置正确
- [ ] 本地化键名遵循命名规范（参见"本地化文本约定"章节)
- [ ] 新人物技能、战斗 ability 与装备的描述字段仅写背景文本，不含任何机械效果摘要

### 数值主键范围校验（必读）

**RPFM 的 TSV 导入对每张表的字段类型严格校验。数值型主键（或数值列）若超出 schema 定义的范围，会导致整行被判定无效——RPFM 不一定报错，而是表现为"该行数据未生效/表内容为空/格式显示异常"。这是比字节格式更深一层的错误。**

#### 字段类型与范围

RPFM schema（`schema_wh3.ron`）中数值字段类型：

| 类型 | 范围 | 说明 |
|------|------|------|
| `I32` | -2,147,483,648 ~ 2,147,483,647（约 ±21.4 亿） | **最常见的整数主键类型，最易溢出** |
| `I64` | ±9.2 × 10¹⁸ | 大整数，几乎不会溢出 |
| `F32` | ±3.4 × 10³⁸（7 位有效数字） | 单精度浮点 |
| `StringU8` / `OptionalStringU8` | 任意字符串 | 字符串主键，无范围限制 |

#### 必查：所有 I32 类型主键不能超过 2,147,483,647

**绝对禁止使用 `9900000001`、`9999990001` 这类 90 亿+ 的数值作为主键**——它超过 `I32` 上限（21.4 亿）4 倍以上，RPFM 解析时整行作废，但 TSV 字节格式看起来完全正常，极具迷惑性。

**安全做法：**
- 新建数值主键前，**先查 schema 确认字段类型**（方法见下）
- 若是 `I32`，key 取值建议在 **2,000,000,000 ~ 2,100,000,000** 区间（源表数据多在 20 亿内，此区间既不与源表冲突又留足余量）
- 若是 `I64`，可放心使用大数值

#### 查询 schema 字段类型的方法

RPFM schema 路径（Windows）：
```
%APPDATA%\FrodoWazEre\rpfm\config\schemas\schema_wh3.ron
```
即 `C:\Users\Administrator\AppData\Roaming\FrodoWazEre\rpfm\config\schemas\schema_wh3.ron`

**一键查询某张表所有字段的类型与是否主键**（Python 脚本，替换 `TABLE_NAME`）：

```python
import re
p = r'C:\Users\Administrator\AppData\Roaming\FrodoWazEre\rpfm\config\schemas\schema_wh3.ron'
with open(p, 'r', encoding='utf-8') as f:
    txt = f.read()
TABLE_NAME = 'building_units_allowed_tables'  # ← 改成目标表名
idx = txt.find(f'"{TABLE_NAME}": [')
end = txt.find('",\n        "', idx + 50)
chunk = txt[idx:end]
fields = re.findall(r'name:\s*"([^"]+)"[^}]*?field_type:\s*([A-Za-z0-9_]+)[^}]*?is_key:\s*(true|false)', chunk[:3000])
for name, ftype, iskey in fields:
    if iskey == 'true':
        print(f'  {name!r:30} type={ftype:20} is_key=KEY  <<<<')
    else:
        print(f'  {name!r:30} type={ftype}')
```

#### 已知使用 I32 数值主键的常见表（非全量，务必逐表查 schema）

| 表名 | I32 主键字段 |
|------|-------------|
| `building_units_allowed_tables` | `key` |
| `building_effects_junction_tables` | （主键为字符串 `building`+`effect`，非 I32） |
| `cdir_events_incident_payloads_tables` | `id`（`I32`） |

> 上述清单不完整。**每次给一张新表写数值主键前，都先用上面的脚本查一次 schema**，不要凭记忆。

#### 诊断特征（遇到这些现象先怀疑主键溢出）

- TSV 字节格式完全正确（无 BOM、列数对、tab 正确、引用 key 都存在）
- RPFM 导入"看起来没报错"或"格式显示异常"
- 导入后表内容为空、整行消失、或对应行未在游戏内生效
- 主键数值 ≥ 2,147,483,648

满足以上全部 → 几乎可以确定是 I32 溢出，立即查 schema 并改用 ≤ 2,147,483,647 的 key。

### `unit_attributes_tables` 仅允许使用原版属性

- 禁止新增、覆盖或自定义 `db/unit_attributes_tables` 记录；该表的属性键属于游戏引擎固定枚举，加入自定义属性可能在数据库/Pack 加载阶段导致游戏无法启动。
- 所有技能、效果和 Lua 脚本只能引用原版 `unit_attributes_tables/data__.tsv` 已存在的属性键；需要脚本标记时，组合两个或多个原版合法属性并在脚本中同时验证，不得创建 `!wyccc_*.tsv` 属性表。

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
2100000001	wh3_dlc26_wyccc_incident_ogre_unification	TEXT_DISPLAY	LOOKUP[dummy_wyccc_ogre_unification]	default
```

> ⚠️ 注意 `id` 字段：`cdir_events_incident_payloads_tables` 的主键 `id` 在 schema 中是 **`I32`**，上限 `2,147,483,647`。**不要用 `9999990001` 这类 90 亿+ 数值**——会溢出导致整行无效。详见上方"数值主键范围校验"章节。

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

### 3.1 五行罗盘冷却注意事项

- `wh3_main_effect_campaign_compass_coodown_mod` 只影响罗盘选择冷却修正值，不能用来立即清除当前 `WOM_COMPASS_SCRIPT_INTERFACE:get_compass_cooldown()` 或 UI `CompassCooldown`。
- 不要把这个 effect 或临时自定义 effect bundle 当作“立即重置五行罗盘冷却”的修复方案。
- `cm:set_next_winds_of_magic_compass_selection_cooldown(faction, 0)` 可以设置派系下一次罗盘选择冷却，但未证明能清掉当前 `CompassCooldown`；必须用 `cm:model():world():winds_of_magic_compass():get_faction_cooldown(faction_key)`、`get_compass_cooldown()` 和最新 `script_log_*.txt` 验证。
- 如果需求是立即切换罗盘方向，应优先检查 UI/CCO 流程，例如 `CanChangeDirection`、`ChooseCompassDirection`、`skip_cooldown_confirmation_holder`，不要先猜 DB/effect workaround。
- 截至本地源码验证，没有 Lua setter 能直接把当前全局 `CompassCooldown` 写成 0；可实现的是走原版“跳过当前冷却”机制。
- 原版 `skip_cooldown_confirmation_holder` 的 `button_tick` 只播放动画/关闭确认框，不会执行 `ChooseCompassDirection`；实测只在 `button_tick` 中调用 `ChooseCompassDirection(StoredContext("CcoCampaignWomCompassDirection"))` 仍可能无效，因为弹窗确认时存储的方向上下文不可靠。
- 若要验证 UI 绕过路径，优先改方向按钮自身的 `ContextCommandLeftClick`。该回调已有 `CcoCampaignFactionWomCompass fac, CcoCampaignWomCompassDirection dir`，可直接测试 `fac.ChooseCompassDirection(dir)`，并用 `WoMCompassUserDirectionSelectedEvent` 日志确认是否进入模型层。
- 如果希望跳过当前冷却不消耗方向能量，将 `campaign_variables_tables` 的 `winds_of_magic_compass_selection_cost_per_turn_on_cd` 覆盖为 `0.0000`；再配合 `cm:set_next_winds_of_magic_compass_selection_cooldown(faction, 0)` 清掉派系层 `FactionCooldown`。

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

### 5. Lua 5.1 语法限制

**战锤3引擎使用 Lua 5.1，以下 Lua 5.2+ 特性不可使用：**

- ❌ `goto` 语句和 `::label::` 标签（Lua 5.2+）
- ❌ `//` 整除运算符（Lua 5.3+）
- ❌ `~` 位运算符（Lua 5.3+）
- ❌ `continue` 关键字（Lua 无此语法，其他语言习惯）

**`goto` 是最容易踩的坑，AI 生成代码时经常使用：**

```lua
-- ❌ 错误：goto 语法在 Lua 5.1 下会导致脚本加载失败
for _, item in ipairs(list) do
    if not item then goto continue end
    -- 处理逻辑
    ::continue::
end

-- ✅ 正确：用 if/else 嵌套替代 goto
for _, item in ipairs(list) do
    if item then
        -- 处理逻辑
    end
end
```

**报错特征：** `'=' expected near 'continue'`（引擎将 `::continue::` 解析为语法错误，导致整个脚本加载失败）

### 6. culture 与 subculture 的区别

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

> **完整 DB 文档**：本表仅列最常用的几张。全部 MOD 相关表（约 190 张）的用途、主键、关联关系详见 [references/db_index.md](references/db_index.md) 总索引及各域详情文档（见文末「附加资源」）。

| 表名 | 用途 | 详情文档 |
|------|------|---------|
| effects_tables | 定义效果类型 | [effects_and_bundles.md](references/effects_and_bundles.md) |
| effect_bundles_tables | 定义效果捆绑 | [effects_and_bundles.md](references/effects_and_bundles.md) |
| effect_bundles_to_effects_junctions_tables | 将效果捆绑绑定到效果 | [effects_and_bundles.md](references/effects_and_bundles.md) |
| effect_bonus_value_faction_junctions_tables | 将效果绑定到派系 | [effects_and_bundles.md](references/effects_and_bundles.md) |
| diplomatic_relationship_effects_tables | 外交关系效果 | （见 db_index 查询） |
| incidents_tables | 事件配置 | [missions_incidents_dilemmas.md](references/missions_incidents_dilemmas.md) |

## Campaign Group Member 一对一约束

`campaign_group_member_criteria_factions_tables` 中，每个 `member` 只能绑定**一个** `faction`。
若同一 `member` 对应多个 `faction`，引擎只对第一个生效，其余派系被忽略。

**正确做法**：为每个派系创建独立的 member key，再在 `campaign_group_members_tables` 中分别注册。

```tsv
-- campaign_group_members_tables
id	group	priority
my_member_yuan_bo	my_group	0.0000
my_member_miao_ying	my_group	0.0000
my_member_zhao_ming	my_group	0.0000

-- campaign_group_member_criteria_factions_tables（每个 member 只对应一个 faction）
member	context	faction
my_member_yuan_bo	ACTOR	wh3_dlc24_cth_the_celestial_court
my_member_miao_ying	ACTOR	wh3_main_cth_the_northern_provinces
my_member_zhao_ming	ACTOR	wh3_main_cth_the_western_provinces
```

```tsv
-- 错误！同一 member 绑定多个 faction，只有第一个生效
member	context	faction
my_member	ACTOR	wh3_dlc24_cth_the_celestial_court
my_member	ACTOR	wh3_main_cth_the_northern_provinces   -- 被忽略！
my_member	ACTOR	wh3_main_cth_the_western_provinces    -- 被忽略！
```

## 新建人物技能、战斗能力与装备描述规则

实现或修改人物专属内容时，下列“描述字段”必须只写角色背景、经历、性格、传说、招式意象、装备来历或世界观叙事：

- 人物技能：`character_skills_localised_description_*`
- 战斗 ability：`unit_abilities_tooltip_text_*`
- 装备：`ancillaries_colour_text_*`、`ancillaries_explanation_text_*`

这些字段禁止罗列或概括机械效果，包括数值、属性增减、解锁内容、技能类型、使用次数、持续时间、冷却时间、作用范围、目标、等级成长、作用域、获取方式和角色限制。

- 机械信息由 DB 效果链、`effects_description_*`、附加效果行及游戏自动生成的效果面板承载；不得为了“说明清楚”再复制进上述描述字段。
- `effects_description_*` 属于机械效果显示行，不属于背景描述字段；例如装备解锁节点可以用它显示“获得专属装备”，同时节点自身的 `character_skills_localised_description_*` 仍只写装备传说。
- 装备描述不写“解锁并获得”“仅限某角色装备”“达到某级”等获取机制。
- 完成新增人物技能、ability 或装备后，必须逐条审查上述对应字段，确认移除所有数值和机制信息后仍是完整、自然的背景文本。

## 本地化文本约定（翻译相关）

本地化文本的翻译写入、术语查证、校对等完整规范已拆分到独立技能 **`warhammer-mod-translation`** 中。

涉及以下任务时，应加载该技能（触发词：翻译、本地化、译名、术语、汉化、loc、校对译文）：
- 编写或修改本地化文本（`.tsv`/`.loc`）
- 查证专有名词的标准中文译名
- 校对已有译文的术语准确性

**本地化键名命名规范要点**（开发时常需对照）：键名由「表前缀 + 完整键名」组成，例如 effect_bundles 的键为 `effect_bundles_localised_title_{key}` / `effect_bundles_localised_description_{key}`。详见 `warhammer-mod-translation` 技能。

## 美术资源绘制

技能图标、角色兵牌、立绘、porthole 等美术资源的绘制规范（含 38×38 被动图标、59×59 主动图标、60×130 兵牌、300×164 porthole 的构图、抠图、裁切验收），见 `warhammer-mod-art` 技能。

## 新建角色

新建传奇领主/英雄的完整流程（设计稿确认、DB 表全量清单、命名与 ID 调查方法、战役动作链、美术与本地化清单、验收清单），见 `warhammer-mod-character-creation` 技能。


## 开发工作流

### 重要：查看游戏日志

**每次测试后或者排查脚本问题前必须查看最新的游戏脚本日志！** 日志是调试的唯一可靠证据。

- 日志位置：`X:\SteamLibrary\steamapps\common\Total War WARHAMMER III/script_log_*.txt`
- 文件名含时间戳，务必查看最新的那个
- 用 `out()` 函数输出调试信息，然后在日志中搜索 `[out]` 标签
- **不要假设代码生效了**——必须在日志中找到你的 `out()` 输出才能确认
- 如果日志中没有你的输出，说明脚本未加载或回调未触发

**日志文件读取陷阱（必读）：**

1. **附件截断**：日志文件通常非常大（数千到数万行），作为附件传入时只显示开头的游戏初始化日志，MOD 的运行时输出在末尾会被截断
2. **Grep 搜索失败**：游戏日志可能是 UTF-16 LE 编码而非 UTF-8，导致 ripgrep/Grep 搜索返回 0 结果。中文路径也可能导致搜索失败
3. **PowerShell 编码问题**：工作区路径含中文时，`Get-Content` 可能因路径编码报错
4. **工具搜索不到 ≠ 内容不存在**：当用户说日志中有输出但工具搜不到时，应让用户直接粘贴相关日志片段，而非假设内容不存在

**正确的日志读取策略（按优先级）：**

1. 让用户直接粘贴 MOD 相关的日志片段（最可靠）
2. 用 `read_file` 的 `start_line`/`end_line` 读取日志末尾部分
3. 用 Grep 搜索时尝试加 `--encoding utf-16le` 参数
4. 如果以上都失败，让用户确认文件编码（用 `file` 命令或编辑器查看）

### 战斗能力目标链与涡流数值排查

先按日志边界定位故障层，再修改数据：`能力指令收到` → `手动目标捕获` → `瞬移/施法命令发出` → `命中或爆炸效果`。缺少哪一条，就只排查该边界；不要在目标尚未捕获时修改伤害或生命 API。

- 多段爆炸、连锁技能的隐藏 `unit_special_abilities` 可能没有独立伤害/半径；先沿其 `vortex` 字段回溯到同一条 `battle_vortexs` 记录。五个隐藏技能共享同一 `vortex_key` 时，只需修改共享行，并用 TSV 查询确认没有漏引用。
- `battle_vortexs.damage` 是普通伤害，`damage_ap` 是破甲伤害，`start_radius`/`goal_radius` 是涡流作用半径，`expansion_speed` 决定在 `duration` 内能否达到目标半径。扩大 `goal_radius` 时，若持续时间不变，按 `goal_radius / duration` 同步检查扩张速度。
- `unit_special_abilities.effect_range`、`target_intercept_range` 与涡流半径不是同一字段：前者可为自体中心的 `0`，后者控制手动目标可选的施法距离；不要因隐藏爆炸行的 `effect_range=0` 就判定爆炸没有范围。
- `composite_scene` 只决定视觉特效资源；画面大小不变不能证明命中半径不变。分别验证 DB 数值和游戏内命中结果，必要时再单独处理 VFX。
- 手动目标标记必须使用原版 `unit_attributes_tables` 中已存在、可叠加的属性；`special_ability_phase_attribute_effects.attribute_type=positive` 才是施加属性，`negative` 用于移除属性。脚本 `has_attribute` 找不到标记时，先查主技能的 `target_enemies`/`only_affect_target`/`target_intercept_range`，再沿 `special_ability_to_special_ability_phase_junctions` → `special_ability_phases` → `special_ability_phase_attribute_effects` 核对目标相位的 `affects_enemies`、原版标记属性和正负类型，并核对脚本的存活、敌我、标记分数与距离边界；此阶段不要改伤害或 vortex。禁止新增自定义 unit attribute。
- 生命百分比交换必须先缓存双方 `unary_hitpoints()`，再写回：`heal_hitpoints_unary(desired_fraction, false)` 设为目标比例，`reduce_hitpoints_unary(current_fraction - desired_fraction)` 扣除差值。只有日志出现“目标已捕获”后，才诊断这两个 API。
- 静态回归至少断言：所有隐藏技能的 `vortex` 引用、涡流伤害/半径字段、目标 `target_intercept_range`、目标标记数量与 `positive` 类型；再检查 TSV 列数、运行 `luac -p`（有 Lua 改动时）和作用域化 `git diff --check`。

### 重要：UI 运行时结构与 XML 静态定义的差异

**XML 定义的组件层级 ≠ 游戏运行时的实际层级！**

- 游戏引擎在运行时会通过回调（如 `UnitRecruitmentInterface`）动态重组组件树
- XML 中的 `template_recuitment_entry` 在静态层级中看起来是 `list_box` 的直接子组件，但运行时可能被嵌套在招募池容器内部
- `find_uicomponent` 只搜索直接子组件，不会递归搜索——路径层级必须与运行时实际层级完全匹配

**招募面板运行时层级（已验证）：**

```
root > units_panel > main_units_panel > recruitment_docker > recruitment_options
  ├── footer > filter_bar  （筛选按钮容器）
  └── recruitment_listbox > recruitment_pool_list
        ├── global_min  （全局招募池条目）
        └── local1      （本地招募池条目）
              └── 内部子组件包含 template_recuitment_entry 实例
```

**关键经验**：
- `recruitment_pool_list` 的 `list_box` 子组件包含的是**招募池级别**的条目（如 `global_min`, `local1`），不是兵种分类
- 兵种分类条目（`template_recuitment_entry`）嵌套在池条目的内部，需要递归搜索
- 当组件层级不确定时，写一个递归 `dump_tree` 函数转储完整组件树到日志，帮助确认实际结构

### 标准步骤
0. **查看日志**：如果是排查脚本问题，且脚本中有大量的OUT输出，那么可以直接查看最新的`script_log_*.txt` 确认 `out()` 输出
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

### 大地图与战斗骑手骨骼、动作匹配

- 大地图角色的 `campaign_character_arts_tables.land_animation`、`campaign_mount_animation_set_overrides_tables.character_animation_set` 与 `rider_animation_set` 必须和骑手模型的骨骼类型一致；不得因角色外观或性别而跨骨骼套用动作。
- 例如，穗香的骑手骨骼为 `hu1`，陆地及坐骑骑手动作只能使用 `cam_hu1_*`；不得使用 `cam_hu1e_*`。跨骨骼会造成十字摆姿或错误的默认外观。
- 排查大地图骑乘异常时，先沿上述三项动作键确认骨骼前缀一致，再检查 `agent_uniforms`、`variants` 和模型资源；战斗模型正常不代表大地图动作链有效。
- **战斗表是独立键域。** `battle_personalities_tables.man_animations_table` 与 `land_units_tables.man_animation` 都引用 `battle_animations_table.key`；即使 TSV 列数正确，键不存在也会被 RPFM 以 `Invalid reference` 拒绝导入。
- `cam_*` 仅属于大地图动作链，绝不能填入上述战斗字段，也不能靠删除 `cam_` 前缀推导战斗键。某个 `cam_hu1_empire_dr1_dragon_wb_sword_and_shield` 可以合法，但对应的 `hu1_empire_dr1_dragon_wb_sword_and_shield` 未必存在于战斗动画表。
- 修改坐骑战斗动作前，先在 `源码/db/battle_animations_table_tables/data__.tsv` 查找精确键，并核对本地 `schema_wh3.ron` 中字段的引用目标和可空性；再按骑手骨骼、武器和坐骑选用原版同类基准。相同骑手/坐骑的两张战斗表应使用同一或经原版证明兼容的键，战役覆盖表继续保留对应的 `cam_*` 键。
- 本例的女性持剑盾龙骑兵：`hu1_empire_dr1_dragon_wb_sword_and_shield` 为无效战斗键；可用且有原版女性龙骑兵先例的是 `hu1b_elf_dr1_dragon_wb_sword_and_shield`。这只是该骨骼/武器组合的基准，不能不经验证套用到其他角色。
- 导入前对所有改动的坐骑行验证：字段列数等于表头、每个战斗动画键存在于 `battle_animations_table.key`、无旧无效键残留，并运行 `git diff --check`；只改源 TSV，不打包 `.pack`。

### 骑手错位、挂点与飞行坐骑排查顺序

- 若骑手动作会播放、却没有正确坐在坐骑上，先查 `land_units_to_battle_personalities_junctions_tables.attach` 与 `riders_attachment_point`，不要继续盲换动作。必须以**相同 mount key 的原版单位**为基准；挂点名不可跨坐骑套用。例如高精耀星龙使用 `autonomous_rider` + `ap_riderpos_0`，`ap_riderposition_0` 是其他坐骑的不同挂点，拼写近似也会导致骑手错位。
- 挂点正确后，再同时核对 `land_units_tables.man_animation`、`battle_personalities_tables.man_animations_table` 与骑手 RMV2 骨骼；两张战斗表使用同一或原版证明兼容的动作键，且该键在 `battle_animations_table_tables` 中的骨骼必须匹配。不要由 `cam_*` 键名推导战斗键。
- 只有在活动 `.variantmeshdefinition` → `.wsmodel` → `.rigid_model_v2` 链明确显示根骨骼名称不一致时，才处理 `animroot`/`animRoot` 之类的大小写问题；先备份，确认替换为等长且仅改目标字节，并核对替换数量与文件长度。它不是挂点错误的替代诊断。
- 飞行坐骑不能只看 `mounts_tables`、`land_units` 的 `flying_*` AI 分组或 UI 的 `can_fly` 文案；必须沿 `land_units_tables.attribute_group` → `unit_attributes_to_groups_junctions_tables` 确认该单位实际获得原版 `flying` 属性。
- 若自定义坐骑复用了不含 `flying` 的原版属性组，不要给共享原版组补属性而影响其他单位；复制原组实际属性到 MOD 自有属性组，额外加入 `flying`，再仅让该自定义 `land_units` 指向新组。若仍无法飞行，再按同类原版单位核对 `unit_set_to_unit_junctions_tables` 的 `all_units_excluding_flying` 和是否应使用 `always_flying`。
- 最终验证除 TSV 列数与引用外，还要确认原版同类坐骑确实存在所选挂点、所有自定义属性键来自原版 `unit_attributes_tables`，并运行作用域化 `git diff --check`；不打包 `.pack`。

### 仓库根目录专题整理（优先查阅）

涉及**法术/能力 DB、法术技能树、领主/英雄动作**时，必须先查阅仓库根目录下的专题文档，不要仅凭记忆：

| 文档 | 用途 |
|------|------|
| [战锤3法术相关DB字段说明.md](../../docs/战锤3法术相关DB字段说明.md) | 法术/能力相关 DB 表与每个字段含义（`unit_abilities`、`unit_special_abilities`、projectile / vortex / phase 等） |
| [战锤3原版法术类角色技能整理.md](../../docs/战锤3原版法术类角色技能整理.md) | 原版各学派法术类角色技能 key、中文名与等级效果 |
| [战锤3原版领主与英雄动作整理.md](../../docs/战锤3原版领主与英雄动作整理.md) | 原版领主与英雄动作 / 动画参考 |

相对路径：见本仓库 `docs/` 目录，由 development skill 通过 `../../docs/战锤3*.md` 引用（保持 `skills/` 与 `docs/` 的相对结构即可生效）

### 基础参考
- TSV格式详情，参见 [references/tsv_format.md](references/tsv_format.md)
- Lua API参考，参见 [references/lua_api.md](references/lua_api.md)
- 命名规范，参见 [references/naming_conventions.md](references/naming_conventions.md)
- 常用效果键，参见 [references/common_effect_keys.md](references/common_effect_keys.md)
- 项目结构，参见 [references/project_structure.md](references/project_structure.md)

### DB 表用途与关联关系（按业务域分文档）

**先看总索引**：[references/db_index.md](references/db_index.md) — 全部 MOD 相关表（约 190 张）的字母速查 + 域导航。知道表名查用途、知道想做某功能查该用哪些表，都从这里入口。

按域深入（每份文档含该域所有表的用途、主键列、被谁引用的关联关系、常见工作流）：

- 效果与效果捆绑：[references/effects_and_bundles.md](references/effects_and_bundles.md) — `effects_tables`、`effect_bundles_tables`、各种 bonus_value junction
- 装备与特性：[references/ancillaries_and_traits.md](references/ancillaries_and_traits.md) — `ancillaries_tables`、`character_traits_tables`
- 单位与战斗：[references/units_and_combat.md](references/units_and_combat.md) — `main_units_tables`、`land_units_tables`、武器/投射物/技能
- 建筑：[references/buildings.md](references/buildings.md) — `building_levels_tables`、`building_effects_junction_tables`
- 任务/事件/两难：[references/missions_incidents_dilemmas.md](references/missions_incidents_dilemmas.md) — `incidents_tables`、`missions_tables`、`cdir_events_*_payloads_tables`
- 仪式：[references/rituals.md](references/rituals.md) — `rituals_tables`、`ritual_payloads_tables`
- 池资源：[references/pooled_resources.md](references/pooled_resources.md) — `pooled_resources_tables`、因子系统
- 战役组/载荷/佣兵：[references/campaigns_payloads_mercenaries.md](references/campaigns_payloads_mercenaries.md) — `campaign_groups_tables`、`campaign_payload_ui_details_tables`、佣兵池
- 角色/技能/事务官：[references/characters_skills_agents.md](references/characters_skills_agents.md) — `character_skills_tables`、`agent_subtypes_tables`
