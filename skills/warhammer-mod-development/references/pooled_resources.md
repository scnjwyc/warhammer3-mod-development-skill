# 池资源与资源消耗 DB 表（Pooled Resource 域）

**Pooled Resource（池资源）**：派系级的可累积数值资源（如"龙帝恩宠""食物""影响力""军功徽记"）。资源有上下限、因子（factor，决定如何增减）、收入策略等。这是 WH3 自定义货币体系的基础。

## 核心数据流

```
pooled_resources          资源定义（如"军功徽记"）
    └─ pooled_resource_factors        因子（如"战斗获得""招募消耗"）
         └─ pooled_resource_factor_junctions   因子 ↔ 资源绑定
    └─ resource_costs                 资源消耗规则（金/食物等通用消耗）
         └─ resource_cost_pooled_resource_junctions  消耗 ↔ 因子绑定
```

---

## `pooled_resources_tables` — 资源主表
| 列 | 说明 |
|----|------|
| `key` | 资源 key（主键），如 `wh3_main_effect_resource_food`、`wwd_cth_upgrades_feats` |
| `maximum` / `minimum` | 上下限 |
| `default_factor` | 默认因子 |
| `ai_ignored` | AI 是否忽略此资源 |
| `optional_icon_path` | 图标路径 |
| `income_policy` | 收入策略 |
| `reset_before_income` | 收入前是否重置 |
| `scope` | 作用域（如 `faction`） |
| `has_persistent_factors` | 是否有持久因子 |
| `sort_order` | UI 排序 |
| `battle_conversion` | 战斗转换 |
| `appy_income_on_creation` | 创建时即应用收入 |
| `always_display_zero_factors` | 是否总显示零因子 |
| `can_scale_effect_thresholds_per_unit` | 效果阈值可否按单位缩放 |

**关联**：被 `pooled_resource_factor_junctions_tables.resource`、`campaign_group_pooled_resources_tables.resource`、`effect_bonus_value_pooled_resource_factor_junctions_tables.resource_factor`（间接）引用。

---

## 因子系统

### `pooled_resource_factors_tables` — 因子定义
| 列 | 说明 |
|----|------|
| `key` | 因子 key（主键），如 `battles`、`recruitment` |
| `is_hidden` | 是否隐藏（不在 UI 显示） |

**用途**：因子是资源"如何变化"的来源分类。例如军功资源下，因子 `battles` 表示"战斗获得"，因子 `recruitment` 表示"招募消耗"。每个因子独立累积/显示。

### `pooled_resource_factor_junctions_tables` — 因子 ↔ 资源绑定（核心 junction）
| 列 | 说明 |
|----|------|
| `unique_id` | 主键 |
| `factor` | → `pooled_resource_factors_tables.key` |
| `resource` | → `pooled_resources_tables.key` |
| `minimum` / `maximum` | 该因子的上下限 |
| `specific_faction_set` | 特定派系集限定 |

**用途**：把因子挂到资源下。一个资源可挂多个因子。**新增自定义资源时，必须通过此表把它与至少一个 factor 绑定，否则资源无法增减。**

---

## 资源消耗（resource costs）

### `resource_costs_tables` — 资源消耗定义
| 列 | 说明 |
|----|------|
| `id` | 主键 |
| `treasury_cost` | 国库消耗（金钱） |
| `expenditure_type` / `income_type` | 支出/收入类型 |
| `expenditure_type_when_regular` / `income_type_when_regular` | 常规时的支出/收入类型 |

**用途**：定义通用的资源消耗规则（金钱、食物等），供建筑/单位/仪式的 `resource_requirement`/`resource_cost` 引用。

### `resource_cost_pooled_resource_junctions_tables` — 资源消耗 ↔ 池资源因子
| 列 | 说明 |
|----|------|
| `pooled_resource_factor` | → `pooled_resource_factors_tables.key` |
| `resource_cost` | → `resource_costs_tables.id` |
| `amount` | 数量 |
| `context` | 上下文 |
| `ui_resource_transaction_pooled_resource` | UI 资源交易显示 |

**用途**：把池资源因子挂到资源消耗规则上（如"招募某单位消耗 5 军功徽记"）。

---

## Lua 操作池资源

```lua
-- 给派系增加池资源（最常用）
cm:faction_add_pooled_resource(faction_key, resource_key, factor_key, amount)
-- 例：cm:faction_add_pooled_resource(faction_key, "wwd_cth_upgrades_feats", "battles", 200)

-- 获取当前资源量
local faction = cm:get_faction(faction_key)
local value = faction:pooled_resource_manager():resource_value(resource_key)

-- 设置具体值
local prm = faction:pooled_resource_manager()
prm:set_resource_value(resource_key, value)
```

⚠️ `cm:faction_add_pooled_resource` 的 factor 必须已通过 `pooled_resource_factor_junctions_tables` 绑定到 resource，否则加值无效（或报错）。

---

## 典型链路示例（自定义军功资源）

以"与龙同行"MOD 的 `wwd_cth_upgrades_feats`（军功徽记）为例：

1. `pooled_resources_tables` 注册资源 `wwd_cth_upgrades_feats`（设 maximum、scope=faction）
2. `pooled_resource_factors_tables` 注册因子 `battles`（战斗获得）
3. `pooled_resource_factor_junctions_tables` 把 `battles` 因子绑定到 `wwd_cth_upgrades_feats` 资源
4. 任务/事件载荷用 `faction_pooled_resource_transaction{resource wwd_cth_upgrades_feats;factor battles;amount 200;context absolute;}` 发放
5. 或 Lua `cm:faction_add_pooled_resource(fk, "wwd_cth_upgrades_feats", "battles", 200)` 发放
6. 建筑的 `resource_requirement` 引用 `resource_costs_tables` 实现消耗

---

## 相关参考
- 效果（`faction_pooled_resource_transaction` 载荷）：[effects_and_bundles.md](effects_and_bundles.md)
- 建筑资源需求（`resource_requirement`）：[buildings.md](buildings.md)
- 任务/事件载荷（发放池资源）：[missions_incidents_dilemmas.md](missions_incidents_dilemmas.md)
- 战役组（`campaign_group_pooled_resources` 初始量）：[campaigns_payloads_mercenaries.md](campaigns_payloads_mercenaries.md)
