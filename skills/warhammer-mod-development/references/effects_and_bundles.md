# 效果系统 DB 表（Effect / Effect Bundle 域）

效果系统是 WH3 数据驱动加成的核心。几乎所有"修正""加成""debuff"都通过 effect → effect_bundle → 各类挂载点（建筑/科技/技能/装备/事件）的链路传递。

## 核心概念

```
effect            单个修正定义（如"收入+10%"）
    ↑
effect_bundle     一组 effect 的集合（玩家看到的"加成包"）
    ↑
挂载点             effect_bundle 通过 junction 表挂到：建筑/科技/技能/装备/事件载荷/仪式等
```

**两种使用方式：**
1. **DB 静态绑定**：通过 `effect_bundles_to_effects_junctions_tables` 把 bundle 绑到 effect，再把 bundle 挂到具体载体（建筑/科技等）。
2. **Lua 动态创建**：`cm:create_new_custom_effect_bundle(key)` + `bundle:add_effect(effect_key, scope, value)` + `cm:apply_effect_bundle(bundle_key, faction_key, turns)`。Lua 创建的 bundle 仍需在 `effect_bundles_tables` 中有 key 记录。

---

## 表清单与用途

### `effects_tables` — 效果类型定义（主表）
| 列 | 说明 |
|----|------|
| `effect` | effect 的 key（主键），如 `wh_main_effect_economy_gdp_mod_all` |
| `icon` / `icon_negative` | 正/负值时显示的图标路径 |
| `priority` | UI 排序优先级（数字越大越靠前） |
| `category` | 分类（如 `campaign`、`military_spending`），决定 UI 归组 |
| `is_positive_value_good` | **关键**：true=正值有益，false=负值有益（见 common_effect_keys.md） |

**关联**：被 `effect_bundles_to_effects_junctions_tables.effect_key`、`*_to_effects_junctions` 系列引用。

⚠️ 自定义 effect key 必须在此表注册，且该 key 在引擎内有对应游戏逻辑才能生效。无法确定是否有效时标 `[需验证]`。

---

### `effect_bundles_tables` — 效果捆绑定义（主表）
| 列 | 说明 |
|----|------|
| `key` | bundle 的 key（主键） |
| `localised_title` / `localised_description` | 标题/描述的本地化占位（实际文本走 loc，键名 `effect_bundles_localised_title_<key>` / `..._description_<key>`） |
| `bundle_target` | 默认挂载目标类型：`faction`/`region`/`force`/`character` 等 |
| `priority` | UI 显示优先级 |
| `ui_icon` | 图标路径 |
| `is_global_effect` | 是否全局效果（非地区局部） |
| `show_in_3d_space` | 是否在 3D 地图上显示 |
| `owner_only` | 是否只对拥有者显示 |

**关联**：被几乎所有"挂载 junction"表的 `effect_bundle` 列引用（建筑、科技、技能、装备、仪式载荷等）。

---

### `effect_bundles_to_effects_junctions_tables` — bundle ↔ effect 绑定（核心 junction）
| 列 | 说明 |
|----|------|
| `effect_bundle_key` | 指向 `effect_bundles_tables.key` |
| `effect_key` | 指向 `effects_tables.effect` |
| `effect_scope` | **作用域**：决定加成作用到哪个层级（见下表） |
| `value` | 加成数值 |
| `advancement_stage` | 科技推进阶段（多数为 0） |

**常用 effect_scope（作用域）速查：**

| scope | 含义 | 典型用途 |
|-------|------|---------|
| `faction_to_faction_own_unseen` | 派系全局 | 全局收入、科研、外交 |
| `faction_to_province_own_unseen` | 派系 → 自有行省 | 行省级修正 |
| `faction_to_region_own_unseen` | 派系 → 自有区域 | 区域级（全局招募容量常用） |
| `faction_to_force_own_unseen` | 派系 → 自有军队 | 军队维持费、补员 |
| `province_to_region_own_factionwide` | 行省 → 全派系区域 | 建筑效果 |
| `character_to_character_own_unseen` | 角色 → 自身 | 角色属性 |
| `agent_to_agent_own` | 事务官 → 自身 | 事务官属性 |

---

## Bonus Value Junction 系列（条件化加成）

当 effect 需要**针对特定目标**生效（如"对某派系外交+10""对某单位集伤害+5%"），需用 `effect_bonus_value_*_junctions` 系列把 effect 绑到目标实体。所有这类表都包含 `bonus_value_id` + `effect` + 目标列。

### `effect_bonus_value_faction_junctions_tables`
针对**特定派系**的加成（最常用，如外交修正）。
| 列 | 说明 |
|----|------|
| `bonus_value_id` | 唯一标识符（自定义字符串） |
| `effect` | 指向 `effects_tables.effect` |
| `faction` | 指向目标派系 key |

**典型链路**（外交修正）：
1. `effects_tables` 注册 effect
2. 此表用 `effect` + 目标 `faction` 绑定
3. bundle 通过 `effect_bundles_to_effects_junctions` 引用同一 effect，scope 用 `faction_to_faction_own_unseen`

### 其他 bonus_value junction 表（结构同上，目标列不同）

| 表名 | 目标列 | 用途 |
|------|--------|------|
| `effect_bonus_value_agent_subtype_junctions_tables` | `subtype` | 针对特定事务官子类型 |
| `effect_bonus_value_military_force_ability_junctions_tables` | `force_ability` | 针对军队能力 |
| `effect_bonus_value_missile_weapon_junctions_tables` | `missile_weapon_junction` | 针对特定远程武器 |
| `effect_bonus_value_pooled_resource_factor_junctions_tables` | `resource_factor` | 针对特定池资源因子 |
| `effect_bonus_value_ritual_junctions_tables` | `ritual` | 针对特定仪式 |
| `effect_bonus_value_unit_ability_junctions_tables` | `unit_ability` | 针对单位能力 |
| `effect_bonus_value_unit_list_junctions_tables` | `unit_list` | 针对单位列表 |
| `effect_bonus_value_unit_record_junctions_tables` | `unit_record_key` | 针对特定单位记录 |
| `effect_bonus_value_unit_set_special_ability_phase_junctions_tables` | `unit_set_special_ability_phase` | 针对单位集特殊技能阶段 |
| `effect_bonus_value_unit_set_unit_ability_junctions_tables` | `unit_set_ability` | 针对单位集能力 |
| `effect_bonus_value_unit_set_unit_attribute_junctions_tables` | `unit_set_attribute` | 针对单位集属性 |
| `effect_bonus_value_ids_unit_sets_tables` | `unit_set` | 针对单位集（含 `effect` 列） |
| `effect_bonus_value_basic_junctions_tables` | — | 基础通用 bonus value 绑定 |

> **共性**：`effect_bonus_value_basic_junction_tables`（注意单数）与 `_junctions`（复数）功能相近，新版引擎倾向用复数版。

---

## 常见工作流

### 流程 A：新建一个静态加成（如建筑提供收入）
1. 确认 effect key 已存在（`effects_tables` 查）或新增
2. 确认 bundle 已存在或新建（`effect_bundles_tables`）
3. `effect_bundles_to_effects_junctions_tables` 把 effect 绑入 bundle，设定 `effect_scope` 和 `value`
4. 在建筑/科技等载体的 junction 表把 bundle 挂上

### 流程 B：Lua 动态给派系加成
```lua
local bundle = cm:create_new_custom_effect_bundle("my_custom_bundle_key")  -- bundle key 必须在 effect_bundles_tables 中存在
bundle:add_effect("wh_main_effect_economy_gdp_mod_all", "faction_to_faction_own_unseen", 10)
cm:apply_effect_bundle(bundle, faction_key, 0)  -- 0 = 永久
```
即使 Lua 动态加 effect，`my_custom_bundle_key` 仍需在 `effect_bundles_tables` 预注册（`key` 列有记录即可，其余列可留占位）。

---

## 版本参考
| 表名 | 原版版本 |
|------|---------|
| `effects_tables` | 0 |
| `effect_bundles_tables` | 4 |
| `effect_bundles_to_effects_junctions_tables` | 3 |

## 相关参考
- 常用 effect key 与 scope 速查：[common_effect_keys.md](common_effect_keys.md)
- 本地化键名规范（`effect_bundles_localised_title_*`）：SKILL.md「本地化文本约定」章节
