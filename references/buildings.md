# 建筑 DB 表（Building 域）

WH3 建筑采用 **chain（建筑链）→ level（等级）→ effect（效果）** 三层结构。一条建筑链包含多个等级，每个等级是独立的 building_level 记录，效果直接挂在 level 上。

## 核心数据流

```
building_superchain   超级链（同类的链集合，如"城墙类"）
    └─ building_chains       建筑链（如"震旦主城军事链"）
         └─ building_levels      具体等级（lv1, lv2, ...）
              ├─ building_effects_junction  效果（直接挂）
              ├─ building_units_allowed     解锁单位
              └─ building_culture_variants  文化变体（图标/描述）
```

---

## `building_superchains_tables` — 超级链（仅 key）
| 列 | 说明 |
|----|------|
| `key` | 主键 |

**用途**：把多条同类建筑链归类（如所有派系的"城墙"链归一个 superchain）。被 `building_chains_tables.building_superchain` 引用。

---

## `building_chains_tables` — 建筑链主表
关键列：
| 列 | 说明 |
|----|------|
| `key` | 链 key（主键），如 `wh_main_emp_fort_growth` |
| `building_superchain` | → `building_superchains_tables.key` |
| `chain_category` | 链分类 |
| `tech_category_tab` / `tech_category_position` | 科技面板标签/位置 |
| `in_encyclopedia` | 是否在百科显示 |
| `is_foreign_slot_chain` | 是否外槽链（盟友/附庸槽位） |
| `can_be_dismantled` | 是否可拆除 |
| `optional_required_horde_commander` | 游牧指挥官需求 |

**关联**：被 `building_levels_tables.chain`、`building_set_to_building_junctions_tables.building_chain`、`building_chain_availability_sets_tables.building_chain`、`building_chain_set_items_tables.chain`、`settlement_type_to_building_chains_junctions_tables.building_chain` 引用。

---

## `building_levels_tables` — 建筑等级（核心主表）
关键列：
| 列 | 说明 |
|----|------|
| `level_name` | 等级 key（主键），如 `wh_main_emp_fort_growth_1` |
| `chain` | 所属链 → `building_chains_tables.key` |
| `level` | 等级数字 |
| `create_time` / `create_cost` / `upkeep_cost` | 建造回合/成本/维持费 |
| `commodity` | 商品类型 |
| `only_in_capital` | 仅首都 |
| `faction_unique` / `first_in_world_bundle` | 派系唯一/世界首件 |
| `resource_requirement` | 资源需求 → `resource_costs_tables` |
| `resource_cost` | 资源消耗 |
| `can_convert` | 是否可转化（一键升级/转换） |
| `food_cost` | 食物消耗 |
| `development_point_cost` | 发展点消耗 |
| `slave_cap_contribution` | 奴隶容量贡献 |
| `primary_slot_building_building_level_requirement` | 主槽建筑等级需求 |
| `resource_transaction_on_complete` | 完成时资源交易 |
| `building_instance_key` | 建筑实例 key |
| `visible_in_ui` | UI 可见性 |
| `audio_building_type` | 音效类型 |

**关联**：被 `building_effects_junction_tables.building`、`building_culture_variants_tables.building`、`building_units_allowed_tables.building`、`building_set_to_building_junctions_tables.building_level`、`building_level_armed_citizenry_junctions_tables.building_level`、`slot_set_items_tables.building_level` 引用。

---

## `building_effects_junction_tables` — 建筑 ↔ 效果绑定（核心 junction）
| 列 | 说明 |
|----|------|
| `building` | → `building_levels_tables.level_name` |
| `effect` | → `effects_tables.effect` |
| `context_requirement` | 上下文需求（如某条件才生效） |
| `effect_scope` | 作用域（建筑效果常用 `province_to_region_own_factionwide`） |
| `value` | 数值 |
| `value_damaged` / `value_ruined` | 建筑受损/废弃时的数值 |

**用途**：定义某建筑等级提供的加成。建筑效果直接走 effect（不走 effect_bundle），scope 决定加成传导到行省/区域/全派系。

> ⚠️ 与 effect_bundle 不同，建筑效果不走 `effect_bundles_to_effects_junctions`，而是直接在此表绑定 effect。

---

## `building_culture_variants_tables` — 建筑文化变体
| 列 | 说明 |
|----|------|
| `building` | → `building_levels_tables.level_name` |
| `culture` / `subculture` / `faction` | 限定文化/子文化/派系 |
| `description` / `short_description` | 描述文本 key |
| `icon` | 图标 |
| `disables` | 是否禁用 |
| `display_tooltip` | 提示 |
| `building_frame_override` | 建筑外观覆盖 |

**用途**：让同一建筑等级在不同文化/派系下有不同图标、外观、描述。

---

## 建筑集（building sets）

### `building_sets_tables` — 建筑集定义
| 列 | 说明 |
|----|------|
| `key` | 主键 |
| `icon` / `sort_order` / `show_in_ui` | 图标/排序/UI 显示 |
| `audio_switch` / `colour_hex` | 音效切换/颜色 |

### `building_set_to_building_junctions_tables` — 建筑集 ↔ 建筑
| 列 | 说明 |
|----|------|
| `building_chain` / `building_level` / `building_set` | 链/等级/集 |
| `exclude` | 是否排除 |

**用途**：把建筑归组，配合"建筑集加成""同集互斥"等机制。

---

## 建筑可用性与解锁

### `building_chain_availability_sets_tables` — 建筑链可用性集
| 列 | 说明 |
|----|------|
| `building_chain` / `id` | 链/集合 id |

### `building_chain_set_items_tables` — 建筑链 → 集合项
| 列 | 说明 |
|----|------|
| `chain` / `set` / `super_chain` | 链/集/超级链 |
| `remove` | 是否移除 |

---

## 建筑解锁单位

### `building_units_allowed_tables` — 建筑解锁单位
| 列 | 说明 |
|----|------|
| `key` | 主键 |
| `building` | → `building_levels_tables.level_name` |
| `unit` | → `main_units_tables.unit` |
| `XP` | 解锁时单位初始经验 |
| `conditions` | 额外条件 |
| `faction` | 派系限定（空=全部） |
| `enabled` | 是否启用 |

**用途**：定义"建了某建筑后能招募某单位"。是招募链的关键。

---

## 武装市民与槽位

### `building_level_armed_citizenry_junctions_tables` — 建筑等级 ↔ 武装市民单位组
| 列 | 说明 |
|----|------|
| `id` | 主键 |
| `building_level` | → `building_levels_tables.level_name` |
| `unit_group` | 单位组 |

**用途**：守城时的武装市民（自动生成的守军）单位组配置。

### `slot_set_items_tables` — 槽位集合项
| 列 | 说明 |
|----|------|
| `id` | 主键 |
| `slot_template` / `slot_type` / `slot_set` | 槽模板/类型/集 |
| `building_level` | → `building_levels_tables.level_name` |

**用途**：外槽/特殊槽位的建筑配置。

### `settlement_type_to_building_chains_junctions_tables` — 定居点类型 ↔ 建筑链
| 列 | 说明 |
|----|------|
| `building_chain` / `settlement_type` / `exclude` | 链/定居点类型/排除 |

**用途**：定义某定居点类型（如城镇/城市/要塞）能建哪些建筑链。

---

## 相关参考
- 效果与作用域（建筑 scope）：[effects_and_bundles.md](effects_and_bundles.md)
- 单位（建筑解锁的单位）：[units_and_combat.md](units_and_combat.md)
- 资源消耗（`resource_requirement`/`resource_cost`）：[pooled_resources.md](pooled_resources.md)
