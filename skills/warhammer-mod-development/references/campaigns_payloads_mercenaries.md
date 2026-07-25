# 战役组、载荷、佣兵 DB 表（Campaign Group / Payload / Mercenary 域）

**Campaign Group（战役组）**：WH3 把"派系专属功能"（解锁仪式、初始资源、独特事务官、战后战利品等）按 campaign_group 组织。通过 member + criteria 系统判断哪些派系/条件命中这个组，从而获得组内的功能。这是"给特定派系下功能"的标准机制。

**Payload UI Details**：任务/事件载荷在 UI 上的显示配置。

**Mercenary（佣兵）**：佣兵池系统（动态刷新的可招募佣兵单位）。

---

## 一、战役组系统（campaign_group_*）

### 核心数据流

```
campaign_groups                组定义（仅 id）
    └─ campaign_group_members        成员（组 + 优先级）
         └─ campaign_group_member_criteria_*   成员命中条件（派系/数值/资源）
    ├─ campaign_group_pooled_resources     组的初始资源
    ├─ campaign_group_rituals              组解锁的仪式
    ├─ campaign_group_unique_agents        组的独特事务官
    └─ campaign_group_post_battle_looted_pooled_resources  组的战后战利品
```

### `campaign_groups_tables` — 战役组定义（仅一列）
| 列 | 说明 |
|----|------|
| `id` | 组 id（主键） |

**关联**：被所有 `campaign_group_*_tables.campaign_group` 引用。

---

### `campaign_group_members_tables` — 组成员
| 列 | 说明 |
|----|------|
| `id` | 成员 key（主键） |
| `group` | → `campaign_groups_tables.id` |
| `priority` | 优先级 |

**关联**：被所有 `campaign_group_member_criteria_*` 表的 `member` 列引用。

---

### 成员命中条件（criteria）系列

每个 member 通过 criteria 决定"是否命中"。多个 criteria 表对应不同维度。

#### `campaign_group_member_criteria_factions_tables` — 派系条件（最常用）
| 列 | 说明 |
|----|------|
| `member` | → `campaign_group_members_tables.id` |
| `context` | 上下文（如 `ACTOR` 主角派系） |
| `faction` | 派系 key |

⚠️ **一对一约束**：每个 `member` 只能绑定**一个** `faction`。若同一 member 对应多个 faction，引擎只对第一个生效，其余被忽略。给多个派系下功能，必须为每个派系建独立 member key，再统一注册到同一 group。详见 SKILL.md「Campaign Group Member 一对一约束」。

#### `campaign_group_member_criteria_numeric_ranges_tables` — 数值范围条件
| 列 | 说明 |
|----|------|
| `member` | 成员 |
| `context` | 上下文 |
| `max_range` / `min_range` | 范围上下限 |

#### `campaign_group_member_criteria_pooled_resources_tables` — 池资源条件
| 列 | 说明 |
|----|------|
| `member` | 成员 |
| `pooled_resource` | 池资源 key |

---

### 组内功能绑定

#### `campaign_group_pooled_resources_tables` — 组的初始/池资源
| 列 | 说明 |
|----|------|
| `campaign_group` | 组 |
| `resource` | → `pooled_resources_tables.key` |
| `initial_amount` | 初始数量 |

#### `campaign_group_pooled_resource_effects_tables` — 组的池资源效果
| 列 | 说明 |
|----|------|
| `campaign_group` | 组 |
| `effect_bundle` | → `effect_bundles_tables.key` |
| `effect_type` | 效果类型 |
| `optional_icon` | 图标 |

#### `campaign_group_post_battle_looted_pooled_resources_tables` — 战后战利品
| 列 | 说明 |
|----|------|
| `campaign_group` | 组 |
| `resource_factor` | → `pooled_resource_factors_tables.key` |
| `base_multiplier` / `exponent` / `exponent_multiplier` | 基础乘数/指数/指数乘数 |
| `maximum` / `minimum` / `base_amount` | 上下限/基础量 |
| `scope` | 作用域 |

**用途**：战后掠夺自动转化为某池资源因子（如"洗劫后获军功"）。

#### `campaign_group_rituals_tables` — 组解锁仪式
| 列 | 说明 |
|----|------|
| `campaign_group` | 组 |
| `ritual` | → `rituals_tables.key` |
| `unlock_mission` | 解锁任务 |
| `unlock_turn` | 解锁回合 |
| `initially_unlocked` | 初始即解锁 |

#### `campaign_group_ritual_chains_tables` — 组解锁仪式链
| 列 | 说明 |
|----|------|
| `campaign_group` | 组 |
| `ritual_chain` | → `ritual_chains_tables.key` |
| `unlock_mission` / `unlock_turn` / `shared_progress` / `initially_unlocked` | 解锁任务/回合/共享进度/初始解锁 |

#### `campaign_group_unique_agents_tables` — 组的独特事务官
| 列 | 说明 |
|----|------|
| `campaign_group` | 组 |
| `unique_agent` | → `unique_agents_tables.agent_subtype` |
| `base_charges` | 基础充能数 |

#### `campaign_group_crafting_infos_tables` — 组的制造信息
| 列 | 说明 |
|----|------|
| `campaign_group` | 组 |
| `unique_resource` | 独特资源 |

---

## 二、Payload UI Details

### `campaign_payload_ui_details_tables` — 载荷 UI 详情
| 列 | 说明 |
|----|------|
| `component` | 组件 key（通常是 `text_display` 的 dummy key） |
| `icon` | 图标路径 |
| `state` | 状态（`positive`/`negative`） |
| `sort_order` | 排序 |

**用途**：让 `text_display` 类载荷（不实际发放、仅展示的"虚拟奖励"）在任务/事件 UI 上有图标和排版。配合 Lua 单独发放实际奖励。

---

## 三、佣兵系统（mercenary_*）

### 核心数据流

```
mercenary_pools           佣兵池（招募来源）
    └─ mercenary_pool_to_groups_junctions   池 ↔ 佣兵组（含初始数量/派系需求）
         └─ mercenary_unit_groups           佣兵组（含单位/补充规则）
faction_to_mercenary_set_junctions    派系 → 佣兵集
```

### `mercenary_pools_tables` — 佣兵池
| 列 | 说明 |
|----|------|
| `key` | 主键 |
| `recruitment_source` | 招募来源 |
| `ui_recruitment_info` | UI 招募信息 |

### `mercenary_unit_groups_tables` — 佣兵单位组
| 列 | 说明 |
|----|------|
| `key` | 主键 |
| `chance_to_replenish` | 补充概率 |
| `max_count` | 最大数量 |
| `unit_record` | → `main_units_tables.unit` |
| `use_partial_replenishment` | 是否部分补充 |
| `max_replenish_per_turn` | 每回合最大补充量 |

### `mercenary_pool_to_groups_junctions_tables` — 池 ↔ 组（核心 junction）
| 列 | 说明 |
|----|------|
| `key` | 主键 |
| `group` | → `mercenary_unit_groups_tables.key` |
| `initial_unit_count` | 初始单位数 |
| `pool` | → `mercenary_pools_tables.key` |
| `faction_requirement` | 派系需求 |
| `subculture_requirement` | 子文化需求 |
| `tech_requirement` | 科技需求 |

### `faction_to_mercenary_set_junctions_tables` — 派系 → 佣兵集
| 列 | 说明 |
|----|------|
| `faction` | 派系 |
| `mercenary_set` | 佣兵集 |

### `campaign_mercenary_unit_character_level_restrictions_tables` — 佣兵角色等级限制
| 列 | 说明 |
|----|------|
| `unit` | 单位 |
| `faction_override` | 派系覆盖 |
| `character_level` | 角色等级要求 |

---

## 四、派系集与 UI 特性

### `faction_sets_tables` — 派系集（仅 key）
| 列 | 说明 |
|----|------|
| `key` | 主键 |

**用途**：把多个派系归入一个集合，供 `faction_set` 列引用（如限定某装备/功能只对某派系集生效）。被 `ancillaries_tables.faction_set`、`faction_set_items_tables`、`ritual_region_target_criterias.permitted_faction_set` 引用。

### `faction_set_items_tables` — 派系集成员项
| 列 | 说明 |
|----|------|
| `id` | 主键 |
| `culture` / `subculture` / `faction` | 文化/子文化/派系 |
| `remove` | 是否移除 |
| `set` | → `faction_sets_tables.key` |

### `ui_features_to_factions_tables` / `ui_features_to_cultures_tables` — UI 特性 → 派系/文化
| 列 | 说明 |
|----|------|
| `faction` / `culture` | 派系/文化 |
| `ui_feature` | UI 特性 key |

**用途**：按派系/文化启用/禁用特定 UI 特性（如某派系隐藏某面板）。

---

## 五、其他战役表

### `campaign_to_agent_subtypes_tables` — 战役 → 事务官子类型
| 列 | 说明 |
|----|------|
| `agent_subtype` | 子类型 |
| `campaign_type` | 战役类型 |

### `campaign_character_arts_tables` / `campaign_character_art_sets_tables` — 角色美术/美术集
角色肖像、立绘、制服等美术资源按派系/文化/等级配置。

### `campaign_cultural_relations_tables` — 战役文化关系
| 列 | 说明 |
|----|------|
| `campaign` / `source` / `target` | 战役/源文化/目标文化 |
| `attitude_base` / `negative_attitude_multiplier` / `positive_attitude_multiplier` | 基础态度/负向乘数/正向乘数 |

**用途**：不同文化间的外交态度基础。

### `campaign_difficulty_handicap_effects_tables` — 难度让步效果
| 列 | 说明 |
|----|------|
| `campaign_difficulty_handicap` | 难度让步 |
| `human` | 是否人类 |
| `effect` / `effect_scope` / `effect_value` | 效果/作用域/数值 |
| `optional_campaign_key` | 可选战役 |

### `campaign_variables_tables` — 战役变量
| 列 | 说明 |
|----|------|
| `variable_key` / `value` | 变量 key/值 |

### `campaign_agent_subtype_factorial_effect_junctions_tables` — 战役事务官阶乘效果
| 列 | 说明 |
|----|------|
| `key` / `agent_subtype` / `factorial_effect` / `value` / `scope` | 主键/子类型/阶乘效果/值/作用域 |

---

## 相关参考
- 池资源（`campaign_group_pooled_resources`）：[pooled_resources.md](pooled_resources.md)
- 仪式（`campaign_group_rituals`）：[rituals.md](rituals.md)
- 事务官（`unique_agents`）：[characters_skills_agents.md](characters_skills_agents.md)
- 单位（佣兵 `unit_record`）：[units_and_combat.md](units_and_combat.md)
- 任务载荷 UI（`campaign_payload_ui_details`）：[missions_incidents_dilemmas.md](missions_incidents_dilemmas.md)
- campaign_group_member 一对一约束：SKILL.md
