# 常用Effect Key参考

## 经济/发展类

| Effect Key | 用途 | is_positive_value_good | 常用scope |
|-----------|------|----------------------|-----------|
| `wh_main_effect_economy_gdp_mod_all` | 所有收入修正 | true | `faction_to_faction_own_unseen` |
| `wh_main_effect_force_all_campaign_upkeep` | 部队维持费 | false | `faction_to_force_own_unseen` |
| `wh_main_effect_force_all_campaign_recruitment_cost_all` | 招募费用 | false | `faction_to_faction_own_unseen` |
| `wh_main_effect_technology_research_points` | 科研速率 | true | `faction_to_faction_own_unseen` |
| `wh3_main_effect_province_growth_faction` | 行省发展度 | true | `faction_to_province_own_unseen` |

## 建筑/招募类

| Effect Key | 用途 | is_positive_value_good | 常用scope |
|-----------|------|----------------------|-----------|
| `wh3_main_effect_building_construction_time_add_mod_all` | 建筑时间修正 | false | `faction_to_region_own_unseen` |
| `wh_main_effect_unit_recruitment_points` | 本地招募容量 | true | `faction_to_province_own_unseen` |
| `wh_main_effect_force_all_recruitment_points` | 部队招募点数（全局/游牧） | true | `faction_to_faction_own_unseen` |

## 军事/战斗类

| Effect Key | 用途 | is_positive_value_good | 常用scope |
|-----------|------|----------------------|-----------|
| `wh_main_effect_force_army_campaign_attrition_all_resistance` | 损耗抗性 | false | `faction_to_force_own_unseen` |
| `wh_main_effect_force_army_campaign_attrition_all_immunity` | 损耗免疫 | true | `faction_to_force_own_unseen` |
| `wh_main_effect_force_all_campaign_replenishment_rate` | 补员速率 | true | `faction_to_force_own_unseen` |
| `wh_main_effect_force_all_campaign_movement_range` | 移动范围 | true | `faction_to_force_own_unseen` |

## 外交类

| Effect Key | 用途 | 常用type |
|-----------|------|---------|
| `wh_main_faction_political_diplomacy_mod` | 外交态度修正 | `diplomatic_mod`（需在 effect_bonus_value_faction_junctions_tables 中绑定目标派系） |

`diplomatic_mod` 类型的效果需要：
1. 在 `effects_tables` 中注册 effect key
2. 在 `effect_bonus_value_faction_junctions_tables` 中用 `diplomatic_mod` 类型绑定到目标派系
3. 在 Lua 中用 `add_effect(key, "faction_to_faction_own_unseen", value)` 传入数值

## 自定义Effect Key

如果需要定义标准表中不存在的效果，需要：
1. 在 `effects_tables` 中注册新 key
2. 确认该 key 在实际游戏中有对应的游戏逻辑（纯自定义 key 可能无效）
3. 对于无法确定是否有效的自定义 key，应标注 `[需验证]`

## 数值正负规则

`is_positive_value_good` 决定数值的正负含义：
- **true**：正值=有益（如收入、发展、科研）
- **false**：负值=有益（如维持费、建筑时间、招募费用、损耗抗性）

示例：
- 减少维持费 30% → value = `-30`（is_positive_value_good=false）
- 增加收入 30% → value = `30`（is_positive_value_good=true）
- 减少建筑时间 1回合 → value = `-1`（is_positive_value_good=false）
