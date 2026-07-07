# 装备与特性 DB 表（Ancillary / Trait 域）

**Ancillary（装备/随从物品）**：角色可装备的物品（武器、护甲、附魔物、护符、坐骑等）。**Trait（特性）**：角色随事件/行为获得的性格特征，通常带分级与加成。

---

## Ancillary（装备）

### `ancillaries_tables` — 装备主定义表（主键表）
| 列 | 说明 |
|----|------|
| `key` | 装备 key（主键），如 `wh_main_anc_weapon_ghal_maraz` |
| `type` | 装备类型，决定占用哪个槽位：`wh_main_anc_weapon` / `_armour` / `_talisman` / `_enchanted_item` / `_arcane_item` / `_mount` 等 |
| `applies_to` | 适用对象：`.`=全部 / 特定角色类型 |
| `transferrable` | 是否可在角色间转移 |
| `unique_to_world` | 全世界唯一（仅一件存在） |
| `unique_to_faction` | 派系内唯一 |
| `precedence` | 唯一性冲突时的优先级（数字大者优先） |
| `legendary_item` | 是否传奇物品 |
| `category` | 分类：`armour` / `weapon` / `enchanted_item` / `talisman` / `arcane_item` |
| `min_starting_age` / `max_starting_age` / `min_expiry_age` / `max_expiry_age` | 获取/失效年龄区间 |
| `immortal` | 是否不朽（不会因角色死亡消失） |
| `randomly_dropped` | 是否可随机掉落 |
| `can_be_stolen` / `can_be_destroyed` | 是否可被偷窃/摧毁 |
| `faction_set` | 关联的 `faction_sets_tables`（限定派系可用） |

**关联**：被 `ancillary_to_effects_tables.ancillary`、`ancillary_set_ancillary_junctions_tables.ancillary_key`、`character_skill_level_to_ancillaries_junctions_tables.granted_ancillary`、`character_skills_to_quest_ancillaries_tables.ancillary`、`ancillaries_included_agent_subtypes_tables.ancillary`、`ancillaries_required_skills_tables.ancillary` 引用。

⚠️ **复制装备做"副本"时**，需新建带 MOD 前缀的 key（如 `wyccc_wh_main_anc_weapon_ghal_maraz`），并在本表完整注册，否则发放脚本（`cm:add_ancillary_to_faction`）会静默失败。`基础前置` MOD 即用此模式复制了数百件原版装备。

---

### `ancillary_to_effects_tables` — 装备 ↔ 效果绑定
| 列 | 说明 |
|----|------|
| `ancillary` | 指向 `ancillaries_tables.key` |
| `effect` | 指向 `effects_tables.effect` |
| `effect_scope` | 作用域（见 effects_and_bundles.md） |
| `value` | 数值 |

**用途**：定义装备穿戴后提供的加成。装备自带效果不走 effect_bundle，直接走此表。

---

### `ancillary_set_ancillary_junctions_tables` — 装备套装
| 列 | 说明 |
|----|------|
| `ancillary_key` | 装备 key |
| `set_key` | 套装 key（对应装备集合） |

**用途**：把多件装备归入一个"套装"，配合套装效果系统。

---

### `ancillaries_included_agent_subtypes_tables` — 装备默认绑定事务官子类型
| 列 | 说明 |
|----|------|
| `agent_subtype` | 事务官子类型 key |
| `ancillary` | 装备 key |

**用途**：让某事务官子类型生成时自带某装备。

---

### `ancillaries_required_skills_tables` — 装备穿戴所需技能
| 列 | 说明 |
|----|------|
| `ancillary` | 装备 key |
| `required_skill` | 所需技能 key（指向 `character_skills_tables`） |
| `required_skill_level` | 所需技能等级 |

**用途**：装备的前置技能要求（如传奇武器需解锁某技能线才能装备）。

---

### `ancillary_info_tables` — 装备信息（仅一列）
| 列 | 说明 |
|----|------|
| `ancillary` | 装备 key（用于注册"该装备存在信息记录"） |

**用途**：仅用于声明装备存在，配合引擎检索。多数情况下新增装备时此表需同步加一行。

---

### `character_ancillary_quest_ui_details_tables` — 任务装备 UI 详情
| 列 | 说明 |
|----|------|
| `agent_subtype` | 事务官子类型 |
| `ancillary` | 装备 key |
| `rank` | 解锁等级 |
| `instant` | 是否即时（非任务战） |
| `is_quest_battle` | 是否通过任务战获取 |

**用途**：任务装备在角色技能面板的"任务解锁装备"提示 UI。

---

## Trait（特性）

### `character_traits_tables` — 特性主表
| 列 | 说明 |
|----|------|
| `key` | 特性 key（主键） |
| `no_going_back_level` | 不可逆等级阈值（达到后不可移除） |
| `hidden` | 是否隐藏（不显示在 UI） |
| `precedence` | 优先级 |
| `icon` | 图标路径 |
| `ui_priority` | UI 排序 |
| `remove_on_skill_reset` | 技能重置时是否移除 |

**关联**：被 `character_trait_levels_tables.trait`、`trait_info_tables.trait` 引用。

---

### `character_trait_levels_tables` — 特性等级
| 列 | 说明 |
|----|------|
| `key` | 等级记录 key（主键，通常为 `<trait>_level_<n>`） |
| `level` | 等级数字 |
| `trait` | 指向 `character_traits_tables.key` |
| `threshold_points` | 达到该级所需累计点数 |

**关联**：被 `trait_level_effects_tables.trait_level` 引用。

---

### `trait_level_effects_tables` — 特性等级 ↔ 效果绑定
| 列 | 说明 |
|----|------|
| `trait_level` | 指向 `character_trait_levels_tables.key` |
| `effect` | 指向 `effects_tables.effect` |
| `effect_scope` | 作用域 |
| `value` | 数值 |

**用途**：定义某特性达到某等级时提供的加成。链路：`trait → trait_level → effect`。

---

### `trait_info_tables` — 特性信息（仅一列）
| 列 | 说明 |
|----|------|
| `trait` | 特性 key |

**用途**：与 `ancillary_info_tables` 类似，声明特性存在的信息记录。

---

## Lua 发放装备

```lua
-- 把装备加入派系池（最常用）
cm:add_ancillary_to_faction(faction, ancillary_key, suppress_event)
-- 参数：faction 接口、装备 key、是否抑制事件弹窗（false=显示）
-- 返回：成功与否

-- 把装备直接给特定角色
cm:force_add_ancillary_to_character(character, ancillary_key, ...)
```

⚠️ **常见坑**：装备 key 必须在 `ancillaries_tables` 中已注册，否则 `cm:add_ancillary_to_faction` 会静默失败（无报错但装备不进包）。复制原版装备做副本时务必新建 key 并完整注册主表。

---

## 相关参考
- 效果与作用域：[effects_and_bundles.md](effects_and_bundles.md)
- 本地化（装备名/描述）：SKILL.md「本地化文本约定」章节（装备 onscreen_name 用 `ancillaries_onscreen_name_<key>`）
