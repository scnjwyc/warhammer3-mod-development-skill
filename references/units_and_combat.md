# 单位与战斗 DB 表（Unit / Combat 域）

WH3 的单位体系是分层结构：`main_unit`（招募槽位的单位）→ `land_unit`（战场实体规格）→ 武器/投射物/实体/能力等组件。新增/修改单位需理解这条链。

## 核心数据流

```
main_units_tables          招募层（成本、容量、人口、UI分组）
    └─ land_unit           战场规格（属性、武器、护甲、护盾、实体）
         ├─ melee_weapon / missile_weapon   武器
         ├─ unit_armour_type / shield       护甲/护盾
         ├─ battle_entity                   战斗实体（血量等）
         └─ mount                           坐骑
```

---

## 招募层（main_units）

### `main_units_tables` — 单位主表（招募层）
关键列：
| 列 | 说明 |
|----|------|
| `unit` | 单位 key（主键），如 `wh_main_emp_inf_spearmen` |
| `land_unit` | 指向 `land_units_tables.key`（战场实体规格） |
| `naval_unit` | 海军单位（多数空） |
| `caste` | 阶层（如 `infantry` / `cavalry` / `monster`） |
| `category` / `class` | 分类（在 land_unit 表中） |
| `campaign_cap` / `multiplayer_cap` | 战役/多人容量上限 |
| `create_time` | 招募回合数 |
| `recruitment_cost` / `upkeep_cost` | 招募费/维持费 |
| `num_men` | 单位人数 |
| `additional_building_requirement` | 额外建筑需求 |
| `resource_requirement` | 资源需求（指向 `resource_costs_tables`） |
| `ui_unit_group_land` | UI 分组（指向 `ui_unit_groupings_tables`） |
| `tier` | 招募层级 |
| `food_cost` | 食物消耗 |
| `use_hitpoints_in_campaign` | 战役是否用血量制 |
| `is_monstrous` / `is_renown` | 是否巨型/知名单位 |

**关联**：被 `units_custom_battle_permissions_tables.unit`、`building_units_allowed_tables.unit`、`units_to_groupings_military_permissions_tables.unit`、`mercenary_unit_groups_tables.unit_record`、`unit_to_unit_list_junctions_tables.unit`、`cdir_military_generator_unit_qualities_tables.unit_key` 引用。

---

## 战场规格层（land_units）

### `land_units_tables` — 战场实体规格（属性核心）
列极多（60+），关键分组：
| 列 | 说明 |
|----|------|
| `key` | 主键，被 `main_units_tables.land_unit` 引用 |
| `category` / `class` | 单位分类/职业（如 `infantry` / `spearmen`） |
| `primary_melee_weapon` | 主近战武器 → `melee_weapons_tables.key` |
| `primary_missile_weapon` | 主远程武器 → `missile_weapons_tables.key` |
| `mount` | 坐骑 → `mounts_tables.key` |
| `shield` | 护盾类型 → `unit_shield_types_tables.key` |
| `armour` | 护甲值（数字） |
| `unit_armour_type`（隐含） | 护甲类型 → `unit_armour_types_tables` |
| `man_entity` / `mount_entity` | 战斗实体 → `battle_entities_tables.key` |
| `melee_attack` / `melee_defence` / `charge_bonus` | 近战攻防/冲锋 |
| `accuracy` / `reload` | 远程命中/装填 |
| `morale` | 士气 |
| `bonus_hit_points` | 额外血量 |
| `attribute_group` | 属性组 → `unit_attributes_groups_tables.group_name` |
| `short_description_text` / `historical_description_text` | 描述文本 key |
| `campaign_action_points` | 战役移动力 |
| `can_skirmish` / `can_brace` | 散阵/架矛 |
| `spell_mastery` / `healing_power` | 法术精通/治疗 |

**关联**：被 `land_units_to_unit_abilites_junctions_tables`、`land_units_to_battle_personalities_junctions_tables`、`effect_bonus_value_unit_record_junctions_tables.unit_record_key` 引用。

---

## 武器系统

### `melee_weapons_tables` — 近战武器
| 列 | 说明 |
|----|------|
| `key` | 主键，被 `land_units_tables.primary_melee_weapon` 引用 |
| `damage` / `ap_damage` | 基础伤害/破甲伤害 |
| `bonus_v_large` / `bonus_v_infantry` | 对大型/步兵加成 |
| `weapon_length` | 武器长度（影响攻击距离） |
| `melee_weapon_type` | 武器类型 |
| `splash_attack_max_attacks` / `splash_attack_target_size` | 溅射攻击 |
| `building_damage_multiplier` | 对建筑伤害 |
| `ignition_amount` / `is_magical` | 点燃值/魔法伤害 |

### `missile_weapons_tables` — 远程武器
| 列 | 说明 |
|----|------|
| `key` | 主键，被 `land_units_tables.primary_missile_weapon` 引用 |
| `default_projectile` | 默认投射物 → `missile_weapons_to_projectiles_tables` |
| `precursor` | 是否先导射击（冲锋前射击） |
| `use_secondary_ammo_pool` | 是否用副弹药池 |

### `missile_weapons_to_projectiles_tables` — 远程武器 ↔ 投射物
| 列 | 说明 |
|----|------|
| `missile_weapon` | 远程武器 key |
| `projectile` | 投射物 → `projectiles_tables.key` |

### `unit_missile_weapon_junctions_tables` — 单位额外远程武器
绑定单位与其额外（副）远程武器。

---

## 投射物系统（projectiles）

### `projectiles_tables` — 投射物主表（弹道/伤害）
关键列：`effective_range`、`minimum_range`、`muzzle_velocity`、`damage`/`ap_damage`、`projectile_number`、`spread`、`base_reload_time`、`bonus_v_infantry`/`_large`、`can_damage_buildings`、`is_magical`、`projectile_display`、`explosion_type`（→ `projectiles_explosions_tables`）。

### `projectiles_explosions_tables` — 投射物爆炸
| 列 | 说明 |
|----|------|
| `key` | 主键，被 `projectiles_tables.explosion_type` 引用 |
| `detonation_radius` / `detonation_damage` / `detonation_damage_ap` | 爆炸半径/伤害/破甲伤害 |
| `shrapnel` | 破片 → `projectile_shrapnels_tables.key` |
| `contact_phase_effect` | 接触阶段效果 |

### `projectile_shrapnels_tables` — 爆炸破片
| 列 | 说明 |
|----|------|
| `key` | 主键 |
| `projectile` | 破片投射物 |
| `amount` / `launch_type` / `sector_angle` | 数量/发射方式/扇形角 |

### `projectile_bombardments_tables` — 轰炸模式（天降法术/炮击）
用于法术轰炸（如彗星）的配置：`num_projectiles`、`radius_spread`、`start_time`、`launch_vfx`。

### `projectile_displays_tables` — 投射物显示
投射物的视觉模型：`display_model`、`impact`、`launch_fx`、`trail_fx`。

### `projectile_shot_type_displays_tables` — 射击类型显示
| 列 | 说明 |
|----|------|
| `key` | 主键，被 `projectiles_tables.projectile_shot_type_display` 引用 |
| `ui_sound_event` / `icon_name` | UI 音效/图标 |

---

## 护甲/护盾/坐骑

### `unit_armour_types_tables` — 护甲类型
| 列 | 说明 |
|----|------|
| `key` | 主键 |
| `armour_value` | 护甲数值 |
| `audio_type` | 音效类型 |

### `unit_shield_types_tables` — 护盾类型
| 列 | 说明 |
|----|------|
| `key` | 主键 |
| `shield_defence_value` | 护盾防御 |
| `shield_armour_value` | 护盾护甲 |
| `missile_block_chance` | 远程格挡概率 |

### `mounts_tables` — 坐骑
| 列 | 说明 |
|----|------|
| `key` | 主键，被 `land_units_tables.mount` 引用 |
| `animation` / `entity` / `variant` | 动画/实体/变体 |
| `voiceover` | 语音 |

---

## 战斗实体与动画

### `battle_entities_tables` — 战斗实体（血量/质量/半径等）
单位在战场的基础物理属性。

### `battle_entity_stats_tables` — 战斗实体统计
实体衍生统计。

### `battle_personalities_tables` — 战斗人格
影响 AI 战斗行为模式。

### `land_units_to_battle_personalities_junctions_tables`
绑定 land_unit 到战斗人格。

### `battle_animations_table_tables` — 战斗动画表
| 列 | 说明 |
|----|------|
| `key` | 主键 |

### `culture_to_battle_animation_tables_tables` — 文化 → 战斗动画
不同文化使用不同战斗动画集。

### `battle_vortexs_tables` — 战场涡流（法术涡流）
### `battlefield_engines_tables` — 战场攻城器械
### `warscape_animated_tables` / `warscape_animated_lod_tables` — 动画资源
### `battle_catchment_override_battle_mappings_tables` — 战场捕捉区映射

---

## 单位能力与特殊技能（special abilities）

### `unit_abilities_tables` — 单位能力
| 列 | 说明 |
|----|------|
| `key` | 主键（能力 key） |
| `type` | 能力类型 |
| `requires_effect_enabling` | 是否需效果启用 |
| `icon_name` | 图标 |
| `is_unit_upgrade` / `is_hidden_in_ui` | 是否升级用/隐藏 |
| `source_type` / `uniqueness` | 来源/唯一性 |

**关联**：被 `land_units_to_unit_abilites_junctions_tables`、`unit_abilities_to_additional_ui_effects_juncs_tables`、`army_special_abilities_tables`、`effect_bonus_value_unit_ability_junctions_tables` 引用。

### `unit_special_abilities_tables` — 特殊技能（主动/被动）
列极多（60+），定义主动技能（如法术、号角）：`active_time`、`recharge_time`、`effect_range`、`activated_projectile`、`bombardment`、`spawned_unit`、`activation_effect`、`vortex`、`mana_cost`、`passive` 等。

**关联**：被 `army_special_abilities_tables.unit_special_ability`、`special_ability_to_special_ability_phase_junctions_tables` 引用。

### `army_special_abilities_tables` — 军队级特殊技能
把单位特殊技能提升为军队级（全军可用）。
| 列 | 说明 |
|----|------|
| `army_special_ability` | 军队级能力 key |
| `unit_special_ability` | → `unit_special_abilities_tables.key` |
| `enables_siege_assault` | 是否启用攻城强攻 |

### `special_ability_phases_tables` — 特殊技能阶段
技能持续生效的阶段：`duration`、`effect_type`、`hp_change_frequency`、`damage_amount`、`mana_regen_mod`、`imbue_magical`/`_ignition`/`_contact`、`affects_allies`/`_enemies` 等。

### `special_ability_to_special_ability_phase_junctions_tables` — 技能 ↔ 阶段
| 列 | 说明 |
|----|------|
| `special_ability` | 特殊技能 |
| `phase` | → `special_ability_phases_tables.id` |
| `target_self` / `target_friends` / `target_enemies` | 作用目标 |

### `special_ability_phase_stat_effects_tables` — 阶段属性效果
| 列 | 说明 |
|----|------|
| `phase` | 阶段 |
| `stat` | 属性 |
| `value` / `how` | 数值/应用方式 |

### `special_ability_phase_attribute_effects_tables` — 阶段属性标志效果
| 列 | 说明 |
|----|------|
| `attribute` / `phase` / `attribute_type` | 属性/阶段/类型 |

### `special_ability_to_recharge_contexts_tables` / `_invalid_target_flags` / `_invalid_usage_flags` / `_auto_deactivate_flags`
分别控制：重充上下文、无效目标标志、无效使用标志、自动停用标志。每张表两列：`special_ability` + 标志 key。

### `special_ability_intensity_settings_tables` — 技能强度设置
| 列 | 说明 |
|----|------|
| `ability` | 能力 |
| `default_amount` / `max_amount` | 默认/最大强度 |
| `intensity_source` / `intensity_type` | 强度来源/类型 |

---

## 单位变体与外观

### `unit_variants_tables` — 单位变体（阵营配色）
| 列 | 说明 |
|----|------|
| `faction` / `unit` / `name` | 派系/单位/变体名 |
| `variant` | → `variants_tables.variant_name` |
| `unit_card` | 单位卡 |

### `variants_tables` — 变体资源
| 列 | 说明 |
|----|------|
| `variant_name` | 主键 |
| `variant_filename` / `low_poly_filename` | 变体模型文件 |
| `scale` / `scale_variation` | 缩放 |

### `unit_variants_colours_tables` — 变体配色
按派系/子文化定义单位的主/副/第三色（hex）。

---

## 单位集与列表（用于条件化加成/生成）

### `unit_sets_tables` — 单位集定义
| 列 | 说明 |
|----|------|
| `key` | 主键 |
| `use_unit_exp_level_range` / `min/max_unit_exp_level_inclusive` | 经验等级范围 |
| `special_category` | 特殊分类 |

### `unit_set_to_unit_junctions_tables` — 单位集 ↔ 单位
| 列 | 说明 |
|----|------|
| `unit_set` | → `unit_sets_tables.key` |
| `unit_record` | → `main_units_tables.unit` |
| `unit_caste` / `unit_category` / `unit_class` | 也可按阶层/分类/职业批量指定 |
| `exclude` | 是否排除 |

### `unit_lists_tables` — 单位列表（仅 key）
| 列 | 说明 |
|----|------|
| `key` | 主键 |

### `unit_to_unit_list_junctions_tables` — 单位列表 ↔ 单位
| 列 | 说明 |
|----|------|
| `unit_list` | → `unit_lists_tables.key` |
| `unit` | → `main_units_tables.unit` |

### `unit_set_special_ability_phase_junctions_tables` / `unit_set_unit_ability_junctions_tables` / `unit_set_unit_attribute_junctions_tables`
单位集与特殊技能阶段/单位能力/单位属性的绑定（配合 bonus_value 效果定向加成）。

---

## 属性组

### `unit_attributes_groups_tables` — 属性组
| 列 | 说明 |
|----|------|
| `group_name` | 组名（主键） |

### `unit_attributes_to_groups_junctions_tables` — 属性 ↔ 组
| 列 | 说明 |
|----|------|
| `attribute` / `attribute_group` | 属性/组 |

---

## UI / 描述 / 权限

### `unit_description_short_texts_tables` / `unit_description_historical_texts_tables`
单位简短/历史描述文本（仅 key 列，实际文本走 loc）。

### `ui_unit_bullet_point_enums_tables` / `ui_unit_bullet_point_unit_overrides_tables`
单位卡"要点"枚举与按单位覆盖。

### `ui_unit_groupings_tables` — UI 单位分组
招募面板的单位归类。

### `units_custom_battle_permissions_tables` — 自定义战斗权限
| 列 | 说明 |
|----|------|
| `faction` / `unit` | 派系/单位 |
| `general_unit` / `siege_unit_attacker` / `siege_unit_defender` | 是否将领/攻城攻方/守方 |
| `campaign_exclusive` | 战役专属 |
| `supports_upgrades` | 支持升级 |

### `units_to_groupings_military_permissions_tables` — 单位 → 军事分组
| 列 | 说明 |
|----|------|
| `unit` / `military_group` | 单位/军事组 |

### `unit_banner_unit_height_offsets_tables` — 旗帜高度偏移
### `unit_allowances_tables` — 单位容量许可

---

## 可购买效果（单位升级）

### `unit_purchasable_effects_tables` — 可购买效果定义
| 列 | 说明 |
|----|------|
| `key` | 主键 |
| `cost` | 消耗 |
| `effect_bundle` | → `effect_bundles_tables.key` |
| `category` | 分类 |
| `pre_requisite_set` | 前置集合 |

### `unit_purchasable_effect_sets_tables` — 单位 ↔ 可购买效果
| 列 | 说明 |
|----|------|
| `unit` | 单位 |
| `purchasable_effect` | → `unit_purchasable_effects_tables.key` |
| `is_exclusive` | 是否互斥 |

### `unit_purchasable_effect_lock_reasons_tables` — 锁定原因（仅 key）

---

## AI 生成器

### `cdir_military_generator_unit_qualities_tables` — 军事生成器单位品质
| 列 | 说明 |
|----|------|
| `group_key` / `unit_key` / `quality` | 组/单位/品质权重 |

**用途**：AI 自动生成军队时各单位的出现品质权重。

---

## 相关参考
- 效果与作用域：[effects_and_bundles.md](effects_and_bundles.md)
- 装备（坐骑类装备）：[ancillaries_and_traits.md](ancillaries_and_traits.md)
