# 角色、技能、事务官 DB 表（Character / Skill / Agent 域）

**Character Skill（角色技能）**：角色的技能树系统。技能以 node（节点）形式组成树，node 归属 node_set（集合），通过 link 形成前置关系。技能等级通过 level_details + level_to_effects 提供加成。

**Agent（事务官）**：地图上的特殊角色（英雄/法师/工程师等），由 subtype（子类型）定义，有行动（agent_actions）、属性（attributes）、制服（uniforms）。

## 核心数据流

```
character_skills           技能定义
    └─ character_skill_nodes        节点（技能在树中的位置）
         └─ character_skill_node_links   节点前置关系
    └─ character_skill_node_sets    节点集合（按角色/派系/子文化）
    └─ character_skill_level_details     技能等级
         └─ character_skill_level_to_effects_junctions   等级 ↔ 效果
         └─ character_skill_level_to_ancillaries_junctions 等级 → 装备

agent_subtypes             事务官子类型
    ├─ agent_actions               行动
    ├─ agent_attributes            属性
    └─ agent_uniforms              制服
```

---

## 一、技能树系统（character_skills / nodes）

### `character_skills_tables` — 技能主定义
| 列 | 说明 |
|----|------|
| `key` | 技能 key（主键） |
| `image_path` | 图标路径 |
| `localised_name` / `localised_description` | 名称/描述（loc 占位） |
| `unlocked_at_rank` | 解锁所需角色等级 |
| `is_background_skill` | 是否背景特性技能 |
| `is_female_only_background_skill` / `is_male_only_background_skill` | 性别限定 |
| `background_weighting` | 背景权重 |
| `influence_cost` | 影响力消耗 |

**关联**：被 `character_skill_nodes_tables.character_skill_key`、`character_skill_level_details_tables.skill_key`、`character_skill_level_to_effects_junctions.character_skill_key`、`character_skills_to_quest_ancillaries_tables.skill`、`ancillaries_required_skills_tables.required_skill` 引用。

---

### `character_skill_nodes_tables` — 技能节点
| 列 | 说明 |
|----|------|
| `key` | 节点 key（主键） |
| `campaign_key` | 战役 key |
| `character_skill_key` | → `character_skills_tables.key` |
| `faction_key` | 派系 key |
| `indent` | 缩进（树中的列位置） |
| `tier` | 层级（行位置） |
| `subculture` | 子文化限定 |
| `points_on_creation` | 创建时点数 |
| `required_num_parents` | 所需前置数 |
| `visible_in_ui` | UI 可见 |

**关联**：被 `character_skill_node_links_tables.child_key`/`parent_key`、`character_skill_node_sets_tables`（间接）引用。

---

### `character_skill_node_links_tables` — 节点前置关系
| 列 | 说明 |
|----|------|
| `child_key` | 子节点 → `character_skill_nodes_tables.key` |
| `parent_key` | 父节点 → `character_skill_nodes_tables.key` |
| `initial_descent_tiers` | 初始下降层级 |
| `parent_link_position` / `child_link_position` | 父/子链接位置 |
| `parent_link_position_offset` / `child_link_position_offset` | 位置偏移 |
| `link_type` | 链接类型 |

**用途**：定义技能树的前置依赖（点了父节点才能点子节点）。

---

### `character_skill_node_sets_tables` — 节点集合
| 列 | 说明 |
|----|------|
| `key` | 集合 key（主键） |
| `agent_key` | 事务官 key |
| `for_army` / `for_navy` | 是否军队/海军将领用 |
| `faction_key` | 派系 |
| `campaign_key` | 战役 |
| `subculture` | 子文化 |
| `agent_subtype_key` | 事务官子类型 |

**用途**：把一组节点归为一个集合，绑定到特定角色类型/派系/子文化。决定"某角色看到哪棵技能树"。

---

### `character_skill_node_set_items_tables` — 集合项
| 列 | 说明 |
|----|------|
| `set` | → 集合 |
| `item` | 节点项 |
| `mod_disabled` | 是否被 MOD 禁用 |

---

### `character_skill_utilization_hints_junctions_tables` — 技能使用提示
| 列 | 说明 |
|----|------|
| `hint` / `key` | 提示/key |

---

## 技能等级与效果

### `character_skill_level_details_tables` — 技能等级详情
| 列 | 说明 |
|----|------|
| `campaign_key` / `faction_key` / `subculture_key` | 战役/派系/子文化 |
| `skill_key` | → `character_skills_tables.key` |
| `level` | 等级 |
| `image_path` | 图标 |
| `unlocked_at_rank` | 解锁等级 |

### `character_skill_level_to_effects_junctions_tables` — 等级 ↔ 效果（核心 junction）
| 列 | 说明 |
|----|------|
| `character_skill_key` | 技能 |
| `effect_key` | → `effects_tables.effect` |
| `level` | 等级 |
| `effect_scope` | 作用域 |
| `value` | 数值 |

**用途**：定义"技能升到 N 级时提供某加成"。链路：`skill → level → effect`。

### `character_skill_level_to_ancillaries_junctions_tables` — 等级 → 装备
| 列 | 说明 |
|----|------|
| `granted_ancillary` | → `ancillaries_tables.key` |
| `skill` | 技能 |
| `level` | 等级 |

**用途**：技能升到某级时授予装备（任务装备的另一种获取方式）。

### `character_skills_to_level_reached_criterias_tables` — 技能升级所需角色等级
| 列 | 说明 |
|----|------|
| `character_skill` | 技能 |
| `character_level` | 角色等级 |
| `upgrade_to_skill_level` | 升级到的技能等级 |

### `character_skills_to_quest_ancillaries_tables` — 技能 → 任务装备
| 列 | 说明 |
|----|------|
| `ancillary` | → `ancillaries_tables.key` |
| `skill` | 技能 |
| `use_quest_for_prefix` | 是否用任务做前缀 |

**用途**：技能线对应的任务装备（点技能触发任务战，胜后得装备）。

---

## 二、事务官系统（agent_*）

### `agent_subtypes_tables` — 事务官子类型（主表）
关键列：
| 列 | 说明 |
|----|------|
| `key` | 子类型 key（主键），如 `wh_main_hero_empire_wizard_heavens` |
| `agent_type`（隐含） | 事务官类型（英雄/领主） |
| `auto_generate` | 是否自动生成 |
| `is_caster` | 是否施法者 |
| `small_icon` | 小图标 |
| `associated_unit_override` | 关联单位覆盖 |
| `show_in_ui` | UI 显示 |
| `cap` | 容量上限 |
| `can_gain_xp` | 可否升级 |
| `loyalty_is_applicable` | 忠诚度适用 |
| `contributes_to_agent_cap` | 计入事务官容量 |
| `recruitment_category` | 招募类别 |
| `magic_lore` | 魔法学派 |
| `names_group` | 名字组 |
| `can_be_loaned` | 可否外借 |
| `recruitable` | 可招募 |
| `can_equip_ancillaries` | 可装备装备 |
| `cost` | 成本 |

**关联**：被 `faction_agent_permitted_subtypes_tables.subtype`、`ancillaries_included_agent_subtypes_tables.agent_subtype`、`ritual_performing_characters_tables.agent_subtype`、`campaign_to_agent_subtypes_tables.agent_subtype`、`campaign_agent_subtype_factorial_effect_junctions_tables.agent_subtype` 引用。

---

### `agent_actions_tables` — 事务官行动
列极多（25+），关键：
| 列 | 说明 |
|----|------|
| `unique_id` | 主键 |
| `ability` | 行动能力 |
| `agent` | 事务官 |
| `attribute` / `target_attribute` | 属性/目标属性 |
| `cannot_fail` / `succeed_always_override` | 不可失败/必成功覆盖 |
| `critical_failure` / `critical_success` / `failure` / `success` / `opportune_failure` | 各结果数值 |
| `chance_of_success` | 成功率 |
| `critical_success_proportion_modifier` 等 | 比例修正 |
| `voiceover` / `icon_path` | 语音/图标 |
| `show_action_info_in_ui` | UI 显示信息 |
| `subculture` | 子文化 |
| `order` | 顺序 |

**用途**：事务官在地图上的行动（刺杀、破坏、煽动等）的成功率与各结果数值。

---

### `agent_attributes_tables` — 事务官属性（仅 key）
| 列 | 说明 |
|----|------|
| `key` | 属性 key |

**用途**：事务官对抗属性（如"潜行""侦测"）的注册。

### `agent_uniforms_tables` — 事务官制服
| 列 | 说明 |
|----|------|
| `uniform_name` | 制服名（主键） |
| `filename` / `battle_filename` | 战役/战斗制服文件 |
| `campaign_porthole_filename` / `campaign_politician_filename` | 战役头像/政客文件 |
| `campaign_override_skeleton` | 战役骨骼覆盖 |

---

## 三、独特事务官（unique_agents）

### `unique_agents_tables` — 独特事务官
| 列 | 说明 |
|----|------|
| `agent_subtype` | 子类型 |
| `clan_name` / `forename` / `other_name` / `surname` | 名字各部分 |
| `agent_type` | 类型 |
| `spawn_behaviour` / `spawn_via_ui` | 生成行为/通过 UI 生成 |

### `unique_agent_component_junctions_tables` — 独特事务官组件
| 列 | 说明 |
|----|------|
| `component` | 组件 |
| `unique_agent` | → `unique_agents_tables.agent_subtype` |
| `value` | 值 |

**用途**：传奇英雄（如戈德里克、格里姆格）的专属配置。

---

## 四、派系事务官许可

### `faction_agent_permitted_subtypes_tables` — 派系允许的事务官子类型
| 列 | 说明 |
|----|------|
| `agent` | 事务官类型 |
| `faction` | 派系 |
| `subtype` | → `agent_subtypes_tables.key` |
| `mod_disabled` | 是否被 MOD 禁用 |

**用途**：限定某派系能招募哪些事务官子类型。新增自定义事务官时需把派系加入此表。

---

## 五、事件类别（事务官行动用）

### `cdir_events_categories_tables` — 事件类别（仅一列）
| 列 | 说明 |
|----|------|
| `category_key` | 类别 key |

**用途**：事件/任务/事务官行动的类别归类（与 mission 域共用）。

---

## Lua 操作角色技能

```lua
-- 给角色加技能经验
cm:add_skill_experience_to_character_list(cm:char_lookup_str(cqi), xp)

-- 给角色添加特性
cm:force_add_trait(character_lookup, trait_key, level)

-- 检查角色是否有某技能/特性
character:has_skill(skill_key)  -- 在 character 接口上
character:trait_level(trait_key)
```

---

## 相关参考
- 效果（`character_skill_level_to_effects`）：[effects_and_bundles.md](effects_and_bundles.md)
- 装备（`character_skill_level_to_ancillaries`、任务装备）：[ancillaries_and_traits.md](ancillaries_and_traits.md)
- 战役组（独特事务官 `campaign_group_unique_agents`）：[campaigns_payloads_mercenaries.md](campaigns_payloads_mercenaries.md)
- 仪式（施放角色 `ritual_performing_characters`）：[rituals.md](rituals.md)
