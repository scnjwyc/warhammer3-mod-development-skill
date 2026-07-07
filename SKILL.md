---
name: warhammer-mod-development
description: "提供全面战争：战锤3 MOD开发指导，包括TSV表格格式、Lua脚本模式、本地化约定、项目结构、技能图标。触发词：战锤、MOD、WH3、Lua脚本、数据库表、本地化、翻译、MOD开发、技能图标、主动技能图标、ability_icons、日志、log、有问题、问题依然存在"
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

### 翻译规则（写入本地化文本时必须遵守）

#### 1. 换行符严格使用 `\n`

**换行符必须严格使用字面的 `\n`（反斜杠 + n 两个字符），而不是真正的换行控制字符。**

- 本地化 `.tsv`/`.loc` 文件中，多行文本的换行用字面字符串 `\n` 表示，不要让文本在文件里实际断行。
- ❌ 错误：把文本写成物理换行（文件里真的换了一行）
- ✅ 正确：文本写成一整行，内部用 `\n` 这两个字符表示换行

例如描述中需要分段时：

```tsv
-- ✅ 正确：用字面 \n
effect_bundles_localised_description_xxx	第一段内容。\n第二段内容。\n第三段内容。

-- ❌ 错误：物理换行
effect_bundles_localised_description_xxx	第一段内容。
第二段内容。
```

#### 2. 术语必须查原版翻译库，禁止机翻

**所有人名、地名、物品、单位名称、法术等专有术语，均需查询原版翻译库获取标准译名，不得机翻。** 宁可不翻译（保留原文），也不要机翻。

##### 步骤 0：先查术语库（必须，最优先）

路径：`C:\Users\Administrator\Desktop\战锤MOD相关\多语言\术语库.md`

**翻译前必须先用 Grep / Read 在术语库中搜索每一个待译术语。** 术语库收录了此前翻译中**已按原版库验证过**的标准译名，命中则直接复用，禁止自行另译。

- 术语库的目的：避免重复查证、避免同一术语在不同条目中译名漂移。
- **查到新术语后必须回填术语库**：每按下方「查询流程」从原版库确证一个术语库尚未收录的新术语，**立即追加到术语库对应分类下**（英文 / 中文 / 出处 key 三列）。术语库需随翻译工作持续增长，这是翻译流程的强制环节，不是可选项。
- 术语库中已有的译名不得擅自替换为"更顺口"的写法；若发现译名与原版本地化库不一致，以原版本地化库为准并修正术语库。

##### 查询流程（术语库未收录时）

**步骤 1：用英文名词在英文库搜索**

路径：`C:\Users\Administrator\Desktop\战锤MOD相关\多语言\EN`

- 用 Grep 在 `EN` 目录下搜索该术语的英文原文（如 `Grimgor`、`Celestial Dragon Guard`、`Comet of Casandora`）。
- 搜索结果大概率命中一整段英文文本（词条是完整的句子或段落），而不是孤立的单词。
- 从这段英文文本中确认该术语确实存在，并定位其所在的行/条目。
- **每个术语独立搜索，不要把多个术语拼在一个正则里批量搜**——批量搜会漏命中，且无法对应到具体 key（详见下方反面案例）。

**步骤 2：用 key 去中文库查翻译**

路径：`C:\Users\Administrator\Desktop\战锤MOD相关\多语言\localisation__.loc_CN.tsv`

- 英文库每条记录都有一个 `key`（通常是第一列），用这个 `key` 在中文库中查找对应行。
- 从中文翻译文本中提取该术语在官方中文版里的标准译名（如 `Grimgor` → `格里姆格`）。
- 该译名即为写入本地化文件时应使用的标准译名。

##### 流程示意

```
英文术语 "Celestial Dragon Guard"
    │
    ▼ 步骤 0：先查 多语言/术语库.md
    ├─ 命中？→ 直接复用术语库译名（结束）
    └─ 未命中？↓
    │
    ▼ 步骤 1：Grep 搜索 多语言/EN（单独搜，不要批量）
命中 key = "wh3_main_unit_description_cth_celestial_dragon_guard"
对应的英文段落："...The Celestial Dragon Guard are..."
    │
    ▼ 步骤 2：用该 key 查 多语言/localisation__.loc_CN.tsv
命中中文段落："...龙卫军是..."
    │
    ▼ 提取译名
标准译名 = "龙卫军"
    │
    ▼ 步骤 3（强制）：把 {英文, 中文, 出处 key} 回填进 多语言/术语库.md
```

##### 备选：联网查询

**如果原版翻译库中查不到该术语**（例如是新加入的内容、或是非官方术语），再联网查询标准译名：
- 优先查战锤官方维基、战锤中文社区等权威来源
- 仍查不到时，**保留英文原文，不要机翻**——宁可整段留英文，也不要给出低质量机翻

##### 禁止事项

- ❌ 直接用翻译工具（机翻）翻译专有名词
- ❌ 想当然地自行音译或意译术语
- ❌ 混用不同译名（同一术语在不同条目中译法不一致）
- ❌ 翻译前不查术语库就直接动手
- ❌ 查证了新术语却不回填术语库（让下一次翻译重复踩坑）
- ❌ 把多个术语拼在一个正则里批量搜（会漏命中且丢失 key 对应关系）
- ❌ 译文中夹带未经查证的英文单词（如把 `gibbering`、`razor`、`hamstring`、`crews`、`celest` 这类普通英文词原样留在中文译文里）

##### 反面案例（真实踩坑记录，务必引以为戒）

以下是一次 legend lore 汉化中真实犯下的错误，已被用户指出并修正。每条都对应上方某条禁止事项，**不要再犯同样的错**。

**案例 1：批量正则搜索导致漏查术语**

把多个术语拼在同一个 Grep 正则里搜：
```
Grep pattern: "Iron Dragon|Jade Dragon|Heavenly Bow|Tiger Court|..."
```
结果只命中了一两个（如 `Heaven's Gate`），就草草判定"已查证"。
- **实际后果**：`Iron Dragon`、`Dawi-Zharr`、`Tiger Court`、`House of Secrets` 等关键术语全部漏查。
- **正确做法**：每个术语单独搜索，逐个走完"EN 库搜英文 → 取 key → 中文库查译名"的完整流程。

**案例 2：跳过"步骤 2"凭印象改译**

`Iron Dragon` 在 Grep 结果中没有直接命中带上下文的段落，于是**跳过了"用 key 查中文库"这一步**，凭印象译成"铸铁龙"。
- **实际后果**：原版标准译名是**镔龙**（出处 `ancillaries_colour_text_wh3_cp1_anc_weapon_blades_of_shang_yang`："这套华丽的拳刃乃是奉镔龙本人之命…"）。"铸铁龙"是完全错误的译名。
- **正确做法**：EN 库搜到 `Iron Dragon` 后，取该条 key，到 `localisation__.loc_CN.tsv` 查同 key，从中文段落中提取标准译名。

**案例 3：术语直接保留英文不翻译**

`Dawi-Zharr` 在译文中原样保留英文，没有查证。
- **实际后果**：原版标准译名是**扎尔矮人**（出处 `ancillaries_colour_text_wh3_dlc23_anc_armour_blackshard_armour`）。保留英文属于漏翻。
- **正确做法**：所有英文专有名词都要查证，查不到才保留原文并标注"待查"。

**案例 4：把概念词当作"诗化标题"擅自改名**

`Heavenly Bowman` 是祟唐在原版库中的固定别称（标准译名**天穹射手**），却自作主张译成"苍天弓神"当作章节标题。
- **实际后果**：与游戏内术语脱节，玩家无法对应。
- **正确做法**：原版已有的固定别称/称号，必须采用原版译名，不得为了"听起来更诗意"而改写。即便用作章节标题也应统一。

**案例 5：译文夹带未查证的英文普通词**

译文中出现了 `gibbering 的恶魔`、`razor 锋利的爪刃`、`hamstring 了一头`、`炮兵 crews`、`在 celest 的鏖战中` 等中英混杂写法。
- **实际后果**：这些是普通英文词（非专有名词），本应译成中文，却因为翻译时图省事直接保留。
- **正确做法**：译文中除原版保留的专有英文（如 `Waaagh!`、武器原名 `Gitsnik`）外，不允许出现未翻译的英文单词。翻译完成后必须做一次全文扫描（可用脚本检测 text 列中长度 ≥ 4 的英文单词）。

**案例 6：武器名括注错误**

`Gitsnik`（格里姆格的战斧）首次出现时括注为"（碎颅者）"。
- **实际后果**：原版标准译名是**灭人斧**（出处 `ancillaries_onscreen_name_wh_main_anc_weapon_gitsnik`）。"碎颅者"是凭印象编的。
- **正确做法**：武器/物品名同样要走查证流程。

### 校对已翻译文本中的术语（第三方/旧翻译校正）

对**已有中文译文**的条目进行术语校对时，不能直接拿中文词去原版库搜——中文词
本身可能就是错的。必须采用"中文→英文→标准流程"的绕回查证法：

#### 校对流程

```
已有中文条目中的疑似译名（如"提尔赛斯"）
    │
    ▼ 步骤 A：找到该条目对应的英文原文
    ├─ 有英文源文件（mod/xxx/english/text/）→ 直接按 key 匹配
    ├─ 无英文源文件 → 从条目 key 名反推英文关键词
    │
    ▼ 步骤 B：从英文原文中提取该专有名词的准确英文拼写
    ├─ "提尔赛斯" → 对应 EN 文本中的 "Tirsyth"
    │
    ▼ 步骤 C：用该英文术语走标准翻译查询流程
    ├─ 步骤 0：查术语库 → 命中则直接复用
    ├─ 步骤 1：在 EN 目录下搜 "Tirsyth" → 找到 key
    ├─ 步骤 2：用 key 在 CN 库查官方译名 → "提西茨"
    │
    ▼ 步骤 D：对比官方译名与 mod 中文译文
    ├─ 一致 → 通过
    └─ 不一致 → 替换为官方译名（"提尔赛斯" → "提西茨"）
```

#### 反面案例

**`提尔赛斯——灰烬厅`**：
- 中文文本看起来通顺（一个音译地名 + 意译描述），不对比英文无法发现错误
- 英文原文为 `Tirsyth`（key: `wh_dlc05_wef_tree_tirsyth`）
- 官方 CN 译名为 **提西茨**
- `提尔赛斯` 是旧译者凭音感自创的译名，与原版不符

**教训**：**不能凭中文语感判断译文是否正确。** 必须找到英文原名，再走标准查证流程。

#### 批量校对策略

1. 从 mod 英文源文件中提取所有大写专有名词（地名/人名/物品名/单位名等）
2. 对每个英文专有名词，走标准流程查官方 CN 译名
3. 在 mod 的中文文件中搜索官方 CN 译名是否存在
4. 不存在 → 该条目用了错误译名 → 找出用了什么、替换为官方译名
5. 存在 → 候选通过（但仍需人工抽检，防止同词异译恰好撞上）


## 被动技能图标绘制规则

适用范围：`mod/[MOD名]/ui/battle ui/ability_icons/*.png` 中需要改成被动/常驻技能视觉风格的小图标。

### 目标风格

- 参考图优先使用：`源码/ui/battle ui/ability_icons/ballistic_plating.png`。
- 成品尺寸必须为 **38×38 PNG**，保留 alpha 透明通道，推荐保存为 `Format32bppArgb`、约 96 DPI。
- 图标角落必须透明；外侧阴影应使用参考图那种 **逐渐淡化的 alpha 边缘**，不要做成实心方底。
- 黑边只能是 **窄、柔和、渐隐** 的暗边；禁止做成明显粗黑环、硬切圆框、过宽黑框。
- 主体图案大小要接近参考图占位。旧 59×59 技能图标通常先把主体缩到约 **0.86** 的占位，再压制到 38×38；如果视觉上过小或过大，可微调，但必须先看放大预览。
- 保留原图的核心图案、方向、颜色身份和可识别特征；除非用户明确要求重绘，不要让 AI 生成替换掉原图案。

### 推荐制作流程

1. 修改前先读取目标 PNG 和参考 PNG，并检查目标文件当前状态；不要基于记忆编辑。
2. 可以用 `imagegen` 做风格参考或预览，但最终写回时优先以原始 PNG 为源做确定性像素处理，避免图案被 AI 改形。
3. 将源图居中缩放到目标占位，再缩到 38×38。
4. 最终 alpha 建议复用参考图 `ballistic_plating.png` 的透明度梯度，以获得相同的透明角、柔边和阴影过渡。
5. 外圈处理原则：
   - 源图透明或接近透明的边缘区域，输出为中性黑色并使用参考 alpha，形成柔和阴影；
   - 仅在最外侧 1–2 像素做轻微变暗；
   - 不要覆盖主体区域，不要生成宽黑框。
6. 临时预览可放在 `tmp/` 下，写回源文件后应清理临时目录。
7. 只改工作区源 PNG；不要打包 `.pack`，不要检查或质疑用户的 pack 覆盖流程。

### 验证清单

- [ ] 最终 PNG 为 38×38。
- [ ] PNG 带 alpha，角落透明，边缘有渐隐阴影。
- [ ] 黑边不粗、不硬、不显眼。
- [ ] 主体图案大小与参考图接近，未贴边挤满。
- [ ] 原图案可识别性保留，没有被 AI 重绘成别的图案。
- [ ] 用原始大小和 8 倍黑底预览各看一次。
- [ ] 报告所有写回的源文件路径；不执行 pack 打包。


## 战斗主动技能图标绘制规则

当用户要求重绘、优化或统一战斗技能图标，尤其是主动技能图标时，按以下规则执行：

1. 始终先确认源文件。用本地化文本或技能 key 在 `mod/<MOD名>/text/db/` 与 `mod/<MOD名>/db/unit_abilities_tables/` 中定位技能，再确认 `icon_name` 对应的 PNG 路径，不要仅凭图案猜文件名。
2. 修改前先读取当前 PNG 的尺寸、像素格式、哈希，并目视查看当前图标。若用户给了参考图，也先读取参考图。
3. 图标统一输出为 `59x59` PNG，优先转为 `Format24bppRgb`，保存到 `ui/battle ui/ability_icons/<icon_name>.png`。
4. 主动技能图标应保持 Total War 技能图标风格：内部为圆形构图，外缘有暗角或金属/魔法边框，表面带轻微玻璃高光；主体图案要居中、简洁、高对比，在 `59x59` 缩略图下仍可辨认。
5. 主体内容按用户指定主题或参考图绘制。保留参考图的核心轮廓、颜色关系和识别点，但要重绘为本 MOD 已采用的圆形玻璃化画风；不要照搬矩形卡片、透明背景或不一致的外框。
6. 主动技能可比被动/特质图标更有“施放感”：允许加入旋涡、光环、护盾、火焰、风流、符文光、粒子和方向性动势，但不要让特效遮住主题主体。
7. 禁止在图标中加入文字、字母、水印、人物大脸、UI 说明文字或过多小物件。若主题是物品，应让物品轮廓占据中心；若主题是光环/庇佑，应让核心符号与环形保护感清楚。
8. 使用 `imagegen` skill 的内置 `image_gen` 流程。生成的资产先存到工具的生成目录，再复制/缩放进工作区最终路径；不要把项目引用资产只留在生成目录。
9. 覆盖源 PNG 后，必须验证：尺寸为 `59x59`、PNG 存在、`unit_abilities_tables` 的 `icon_name` 与文件名一致，并目视检查最终缩略图。
10. 只改源文件，不执行 pack 打包、导入或覆盖 pack。最终回复中说明保存路径、是否修改 DB、是否未打包，以及使用的图像生成方式和提示词概要。


## 开发工作流

### 硬性边界：不修改第三方 MOD 源码

排查任何问题时，第三方 MOD 源码只能读取、搜索、对照和引用，**不得编辑**。

- `mod/第三方MOD/` 下的文件默认全部视为只读。
- 用户明确称为第三方、参考、原始、对照或外部来源的 MOD 文件默认只读，即使不在 `mod/第三方MOD/` 下。
- 即使日志显示第三方脚本或 DB 报错，也不要直接修第三方 MOD；应在用户维护的目标 MOD、兼容补丁、DB 覆盖或自身脚本防护中解决。
- 若需要验证第三方行为，可以读取日志、源码和 DB 链路，但不能写回第三方文件，不能用格式化工具或批量命令改动第三方目录。
- 只有用户明确要求“修改这个第三方 MOD 源码”时，才允许编辑该第三方 MOD。
- 如果误改了第三方 MOD，必须立即只回滚自己造成的第三方文件改动，并向用户说明。

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
