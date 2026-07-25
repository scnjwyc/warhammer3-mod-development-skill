# DB 表总索引（MOD 相关表）

WH3 共有 1,521 张 DB 表，本索引收录 **MOD 开发实际会涉及的约 190 张表**。按业务域分组，每张表标注用途与所在详情文档。引擎内部表（`cai_*` 决策 AI、`audio_*` 音频、`loading_screen_*`、`frontend_*` 前端）已剔除——这些表 MOD 几乎不会改动。

## 如何使用本索引

1. **找表**：知道表名 → 在下方找域 → 点链接进详情文档
2. **找域**：想做"加成系统"→ 看「效果」域；想做"新单位"→ 看「单位与战斗」域
3. **找关联**：详情文档内有该表"被谁引用"的说明，据此追踪完整链路

## 域导航

| 域 | 详情文档 | 表数 | 核心表 |
|----|---------|------|--------|
| 效果 | [effects_and_bundles.md](effects_and_bundles.md) | 17 | `effects_tables`, `effect_bundles_tables` |
| 装备与特性 | [ancillaries_and_traits.md](ancillaries_and_traits.md) | 10 | `ancillaries_tables`, `character_traits_tables` |
| 单位与战斗 | [units_and_combat.md](units_and_combat.md) | 60+ | `main_units_tables`, `land_units_tables` |
| 建筑 | [buildings.md](buildings.md) | 13 | `building_levels_tables`, `building_effects_junction_tables` |
| 任务/事件/两难 | [missions_incidents_dilemmas.md](missions_incidents_dilemmas.md) | 17 | `incidents_tables`, `missions_tables`, `cdir_events_*_payloads_tables` |
| 仪式 | [rituals.md](rituals.md) | 16 | `rituals_tables`, `ritual_payloads_tables` |
| 池资源 | [pooled_resources.md](pooled_resources.md) | 5 | `pooled_resources_tables`, `pooled_resource_factor_junctions_tables` |
| 战役组/载荷/佣兵 | [campaigns_payloads_mercenaries.md](campaigns_payloads_mercenaries.md) | 30+ | `campaign_groups_tables`, `campaign_payload_ui_details_tables`, `mercenary_*` |
| 角色/技能/事务官 | [characters_skills_agents.md](characters_skills_agents.md) | 17 | `character_skills_tables`, `agent_subtypes_tables` |

---

## 全表速查（按字母序）

### A
| 表名 | 用途 | 文档 |
|------|------|------|
| `agent_actions_tables` | 事务官行动（刺杀/破坏等的成功率与结果） | [角色/技能/事务官](characters_skills_agents.md) |
| `agent_attributes_tables` | 事务官对抗属性（仅 key） | [角色/技能/事务官](characters_skills_agents.md) |
| `agent_subtypes_tables` | 事务官子类型主表（英雄/领主定义） | [角色/技能/事务官](characters_skills_agents.md) |
| `agent_uniforms_tables` | 事务官制服（战役/战斗外观） | [角色/技能/事务官](characters_skills_agents.md) |
| `ancillaries_included_agent_subtypes_tables` | 装备默认绑定事务官子类型 | [装备与特性](ancillaries_and_traits.md) |
| `ancillaries_required_skills_tables` | 装备穿戴所需技能 | [装备与特性](ancillaries_and_traits.md) |
| `ancillaries_tables` | **装备主定义表** | [装备与特性](ancillaries_and_traits.md) |
| `ancillary_info_tables` | 装备信息（声明存在，仅一列） | [装备与特性](ancillaries_and_traits.md) |
| `ancillary_set_ancillary_junctions_tables` | 装备套装 | [装备与特性](ancillaries_and_traits.md) |
| `ancillary_to_effects_tables` | 装备 ↔ 效果绑定 | [装备与特性](ancillaries_and_traits.md) |
| `army_special_abilities_tables` | 军队级特殊技能 | [单位与战斗](units_and_combat.md) |

### B
| 表名 | 用途 | 文档 |
|------|------|------|
| `battle_animations_table_tables` | 战斗动画 | [单位与战斗](units_and_combat.md) |
| `battle_catchment_override_battle_mappings_tables` | 战场捕捉区映射 | [单位与战斗](units_and_combat.md) |
| `battle_entities_tables` | 战斗实体（血量/质量） | [单位与战斗](units_and_combat.md) |
| `battle_entity_stats_tables` | 战斗实体统计 | [单位与战斗](units_and_combat.md) |
| `battle_personalities_tables` | 战斗人格（AI 行为） | [单位与战斗](units_and_combat.md) |
| `battle_vortexs_tables` | 战场涡流（法术涡流） | [单位与战斗](units_and_combat.md) |
| `battlefield_engines_tables` | 战场攻城器械 | [单位与战斗](units_and_combat.md) |
| `building_chain_availability_sets_tables` | 建筑链可用性集 | [建筑](buildings.md) |
| `building_chain_set_items_tables` | 建筑链 → 集合项 | [建筑](buildings.md) |
| `building_chains_tables` | **建筑链主表** | [建筑](buildings.md) |
| `building_culture_variants_tables` | 建筑文化变体（图标/外观） | [建筑](buildings.md) |
| `building_effects_junction_tables` | **建筑 ↔ 效果绑定** | [建筑](buildings.md) |
| `building_level_armed_citizenry_junctions_tables` | 建筑等级 ↔ 武装市民 | [建筑](buildings.md) |
| `building_levels_tables` | **建筑等级主表** | [建筑](buildings.md) |
| `building_set_to_building_junctions_tables` | 建筑集 ↔ 建筑 | [建筑](buildings.md) |
| `building_sets_tables` | 建筑集定义 | [建筑](buildings.md) |
| `building_superchains_tables` | 建筑超级链 | [建筑](buildings.md) |
| `building_units_allowed_tables` | 建筑解锁单位 | [建筑](buildings.md) |

### C
| 表名 | 用途 | 文档 |
|------|------|------|
| `campaign_agent_subtype_factorial_effect_junctions_tables` | 战役事务官阶乘效果 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `campaign_character_art_sets_tables` | 角色美术集 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `campaign_character_arts_tables` | 角色美术（肖像/立绘） | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `campaign_cultural_relations_tables` | 战役文化关系 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `campaign_difficulty_handicap_effects_tables` | 难度让步效果 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `campaign_group_crafting_infos_tables` | 战役组制造信息 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `campaign_group_member_criteria_factions_tables` | 战役组成员派系条件（一对一！） | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `campaign_group_member_criteria_numeric_ranges_tables` | 战役组成员数值范围条件 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `campaign_group_member_criteria_pooled_resources_tables` | 战役组成员池资源条件 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `campaign_group_members_tables` | 战役组成员 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `campaign_group_post_battle_looted_pooled_resources_tables` | 战役组战后战利品 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `campaign_group_pooled_resource_effects_tables` | 战役组池资源效果 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `campaign_group_pooled_resources_tables` | 战役组初始资源 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `campaign_group_ritual_chains_tables` | 战役组解锁仪式链 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `campaign_group_rituals_tables` | 战役组解锁仪式 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `campaign_group_unique_agents_tables` | 战役组独特事务官 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `campaign_groups_tables` | 战役组定义 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `campaign_mercenary_unit_character_level_restrictions_tables` | 佣兵角色等级限制 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `campaign_payload_ui_details_tables` | **载荷 UI 详情** | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `campaign_to_agent_subtypes_tables` | 战役 → 事务官子类型 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `campaign_variables_tables` | 战役变量 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `cdir_events_categories_tables` | 事件类别 | [任务/事件/两难](missions_incidents_dilemmas.md) |
| `cdir_events_dilemma_choice_details_tables` | 两难选项详情 | [任务/事件/两难](missions_incidents_dilemmas.md) |
| `cdir_events_dilemma_option_junctions_tables` | 两难选项 | [任务/事件/两难](missions_incidents_dilemmas.md) |
| `cdir_events_dilemma_payloads_tables` | 两难载荷 | [任务/事件/两难](missions_incidents_dilemmas.md) |
| `cdir_events_incident_option_junctions_tables` | 事件选项 | [任务/事件/两难](missions_incidents_dilemmas.md) |
| `cdir_events_incident_payloads_tables` | **事件载荷** | [任务/事件/两难](missions_incidents_dilemmas.md) |
| `cdir_events_mission_issuer_junctions_tables` | 任务发布者绑定 | [任务/事件/两难](missions_incidents_dilemmas.md) |
| `cdir_events_mission_option_junctions_tables` | 任务选项 | [任务/事件/两难](missions_incidents_dilemmas.md) |
| `cdir_events_mission_payloads_tables` | 任务载荷 | [任务/事件/两难](missions_incidents_dilemmas.md) |
| `cdir_military_generator_unit_qualities_tables` | 军事生成器单位品质 | [单位与战斗](units_and_combat.md) |
| `character_ancillary_quest_ui_details_tables` | 任务装备 UI 详情 | [装备与特性](ancillaries_and_traits.md) |
| `character_skill_level_details_tables` | 技能等级详情 | [角色/技能/事务官](characters_skills_agents.md) |
| `character_skill_level_to_ancillaries_junctions_tables` | 技能等级 → 装备 | [角色/技能/事务官](characters_skills_agents.md) |
| `character_skill_level_to_effects_junctions_tables` | 技能等级 ↔ 效果 | [角色/技能/事务官](characters_skills_agents.md) |
| `character_skill_node_links_tables` | 技能节点前置关系 | [角色/技能/事务官](characters_skills_agents.md) |
| `character_skill_node_set_items_tables` | 技能集合项 | [角色/技能/事务官](characters_skills_agents.md) |
| `character_skill_node_sets_tables` | 技能节点集合 | [角色/技能/事务官](characters_skills_agents.md) |
| `character_skill_nodes_tables` | 技能节点 | [角色/技能/事务官](characters_skills_agents.md) |
| `character_skill_utilization_hints_junctions_tables` | 技能使用提示 | [角色/技能/事务官](characters_skills_agents.md) |
| `character_skills_tables` | **技能主定义** | [角色/技能/事务官](characters_skills_agents.md) |
| `character_skills_to_level_reached_criterias_tables` | 技能升级所需等级 | [角色/技能/事务官](characters_skills_agents.md) |
| `character_skills_to_quest_ancillaries_tables` | 技能 → 任务装备 | [角色/技能/事务官](characters_skills_agents.md) |
| `character_trait_levels_tables` | 特性等级 | [装备与特性](ancillaries_and_traits.md) |
| `character_traits_tables` | 特性主表 | [装备与特性](ancillaries_and_traits.md) |
| `culture_to_battle_animation_tables_tables` | 文化 → 战斗动画 | [单位与战斗](units_and_combat.md) |

### D–E
| 表名 | 用途 | 文档 |
|------|------|------|
| `dilemmas_tables` | 两难主表（多选一） | [任务/事件/两难](missions_incidents_dilemmas.md) |
| `effect_bonus_value_agent_subtype_junctions_tables` | 效果 → 特定事务官子类型 | [效果](effects_and_bundles.md) |
| `effect_bonus_value_basic_junction_tables` | 效果 → 基础 bonus value | [效果](effects_and_bundles.md) |
| `effect_bonus_value_basic_junctions_tables` | 效果 → 基础 bonus value（复数版） | [效果](effects_and_bundles.md) |
| `effect_bonus_value_faction_junctions_tables` | 效果 → 特定派系 | [效果](effects_and_bundles.md) |
| `effect_bonus_value_ids_unit_sets_tables` | 效果 → 单位集 | [效果](effects_and_bundles.md) |
| `effect_bonus_value_military_force_ability_junctions_tables` | 效果 → 军队能力 | [效果](effects_and_bundles.md) |
| `effect_bonus_value_missile_weapon_junctions_tables` | 效果 → 远程武器 | [效果](effects_and_bundles.md) |
| `effect_bonus_value_pooled_resource_factor_junctions_tables` | 效果 → 池资源因子 | [效果](effects_and_bundles.md) |
| `effect_bonus_value_ritual_junctions_tables` | 效果 → 仪式 | [效果](effects_and_bundles.md) |
| `effect_bonus_value_unit_ability_junctions_tables` | 效果 → 单位能力 | [效果](effects_and_bundles.md) |
| `effect_bonus_value_unit_list_junctions_tables` | 效果 → 单位列表 | [效果](effects_and_bundles.md) |
| `effect_bonus_value_unit_record_junctions_tables` | 效果 → 单位记录 | [效果](effects_and_bundles.md) |
| `effect_bonus_value_unit_set_special_ability_phase_junctions_tables` | 效果 → 单位集技能阶段 | [效果](effects_and_bundles.md) |
| `effect_bonus_value_unit_set_unit_ability_junctions_tables` | 效果 → 单位集能力 | [效果](effects_and_bundles.md) |
| `effect_bonus_value_unit_set_unit_attribute_junctions_tables` | 效果 → 单位集属性 | [效果](effects_and_bundles.md) |
| `effect_bundles_tables` | **效果捆绑主表** | [效果](effects_and_bundles.md) |
| `effect_bundles_to_effects_junctions_tables` | **bundle ↔ effect 绑定** | [效果](effects_and_bundles.md) |
| `effects_tables` | **效果类型定义（主表）** | [效果](effects_and_bundles.md) |
| `event_feed_strings_tables` | 事件提要字符串（仅 key） | [任务/事件/两难](missions_incidents_dilemmas.md) |

### F
| 表名 | 用途 | 文档 |
|------|------|------|
| `faction_agent_permitted_subtypes_tables` | 派系允许的事务官子类型 | [角色/技能/事务官](characters_skills_agents.md) |
| `faction_set_items_tables` | 派系集成员项 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `faction_sets_tables` | 派系集（仅 key） | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `faction_to_mercenary_set_junctions_tables` | 派系 → 佣兵集 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |

### I–L
| 表名 | 用途 | 文档 |
|------|------|------|
| `incidents_tables` | **事件主表** | [任务/事件/两难](missions_incidents_dilemmas.md) |
| `land_units_tables` | **战场实体规格（属性核心）** | [单位与战斗](units_and_combat.md) |
| `land_units_to_battle_personalities_junctions_tables` | land_unit → 战斗人格 | [单位与战斗](units_and_combat.md) |
| `land_units_to_unit_abilites_junctions_tables` | land_unit → 单位能力 | [单位与战斗](units_and_combat.md) |

### M
| 表名 | 用途 | 文档 |
|------|------|------|
| `main_units_tables` | **单位主表（招募层）** | [单位与战斗](units_and_combat.md) |
| `melee_weapons_tables` | 近战武器 | [单位与战斗](units_and_combat.md) |
| `mercenary_pool_to_groups_junctions_tables` | 佣兵池 ↔ 组 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `mercenary_pools_tables` | 佣兵池 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `mercenary_unit_groups_tables` | 佣兵单位组 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `missions_tables` | **任务主表** | [任务/事件/两难](missions_incidents_dilemmas.md) |
| `missile_weapons_tables` | 远程武器 | [单位与战斗](units_and_combat.md) |
| `missile_weapons_to_projectiles_tables` | 远程武器 ↔ 投射物 | [单位与战斗](units_and_combat.md) |
| `mounts_tables` | 坐骑 | [单位与战斗](units_and_combat.md) |

### P
| 表名 | 用途 | 文档 |
|------|------|------|
| `pooled_resource_factor_junctions_tables` | **因子 ↔ 资源绑定** | [池资源](pooled_resources.md) |
| `pooled_resource_factors_tables` | 因子定义 | [池资源](pooled_resources.md) |
| `pooled_resources_tables` | **资源主表** | [池资源](pooled_resources.md) |
| `projectile_bombardments_tables` | 轰炸模式 | [单位与战斗](units_and_combat.md) |
| `projectile_displays_tables` | 投射物显示 | [单位与战斗](units_and_combat.md) |
| `projectile_shot_type_displays_tables` | 射击类型显示 | [单位与战斗](units_and_combat.md) |
| `projectile_shrapnels_tables` | 爆炸破片 | [单位与战斗](units_and_combat.md) |
| `projectiles_explosions_tables` | 投射物爆炸 | [单位与战斗](units_and_combat.md) |
| `projectiles_tables` | 投射物主表 | [单位与战斗](units_and_combat.md) |
| `prophecy_of_sotek_stages_tables` | 索泰克预言阶段 | [任务/事件/两难](missions_incidents_dilemmas.md) |
| `prophecy_of_sotek_stages_to_missions_tables` | 预言阶段 ↔ 任务 | [任务/事件/两难](missions_incidents_dilemmas.md) |

### R
| 表名 | 用途 | 文档 |
|------|------|------|
| `resource_cost_pooled_resource_junctions_tables` | 资源消耗 ↔ 池资源因子 | [池资源](pooled_resources.md) |
| `resource_costs_tables` | 资源消耗定义 | [池资源](pooled_resources.md) |
| `ritual_categories_tables` | 仪式类别 | [仪式](rituals.md) |
| `ritual_category_groups_tables` | 仪式类别组 | [仪式](rituals.md) |
| `ritual_chains_tables` | 仪式链 | [仪式](rituals.md) |
| `ritual_payload_add_foreign_slots_tables` | 载荷 → 增加外槽 | [仪式](rituals.md) |
| `ritual_payload_change_unit_allowance_capacities_tables` | 载荷 → 改单位容量 | [仪式](rituals.md) |
| `ritual_payload_effect_bundles_tables` | 载荷 → 效果捆绑 | [仪式](rituals.md) |
| `ritual_payload_resource_transactions_tables` | 载荷 → 资源交易 | [仪式](rituals.md) |
| `ritual_payload_spawn_mercenaries_tables` | 载荷 → 生成佣兵 | [仪式](rituals.md) |
| `ritual_payload_teleport_armies_tables` | 载荷 → 传送军队 | [仪式](rituals.md) |
| `ritual_payloads_tables` | **仪式载荷主表** | [仪式](rituals.md) |
| `ritual_performing_character_junctions_tables` | 仪式 ↔ 施放角色 | [仪式](rituals.md) |
| `ritual_performing_characters_tables` | 施放角色定义 | [仪式](rituals.md) |
| `ritual_region_target_criterias_tables` | 区域目标条件 | [仪式](rituals.md) |
| `ritual_targets_tables` | 仪式目标 | [仪式](rituals.md) |
| `rituals_tables` | **仪式主表** | [仪式](rituals.md) |
| `rituals_to_ritual_chains_tables` | 仪式 → 仪式链 | [仪式](rituals.md) |

### S
| 表名 | 用途 | 文档 |
|------|------|------|
| `settlement_type_to_building_chains_junctions_tables` | 定居点类型 ↔ 建筑链 | [建筑](buildings.md) |
| `slot_set_items_tables` | 槽位集合项 | [建筑](buildings.md) |
| `sotek_tooltip_types_tables` | 索泰克提示类型 | [任务/事件/两难](missions_incidents_dilemmas.md) |
| `special_ability_intensity_settings_tables` | 技能强度设置 | [单位与战斗](units_and_combat.md) |
| `special_ability_phase_attribute_effects_tables` | 阶段属性标志效果 | [单位与战斗](units_and_combat.md) |
| `special_ability_phase_stat_effects_tables` | 阶段属性效果 | [单位与战斗](units_and_combat.md) |
| `special_ability_phases_tables` | 特殊技能阶段 | [单位与战斗](units_and_combat.md) |
| `special_ability_to_auto_deactivate_flags_tables` | 技能 → 自动停用标志 | [单位与战斗](units_and_combat.md) |
| `special_ability_to_invalid_target_flags_tables` | 技能 → 无效目标标志 | [单位与战斗](units_and_combat.md) |
| `special_ability_to_invalid_usage_flags_tables` | 技能 → 无效使用标志 | [单位与战斗](units_and_combat.md) |
| `special_ability_to_recharge_contexts_tables` | 技能 → 重充上下文 | [单位与战斗](units_and_combat.md) |
| `special_ability_to_special_ability_phase_junctions_tables` | 技能 ↔ 阶段 | [单位与战斗](units_and_combat.md) |

### T–U
| 表名 | 用途 | 文档 |
|------|------|------|
| `trait_info_tables` | 特性信息（仅一列） | [装备与特性](ancillaries_and_traits.md) |
| `trait_level_effects_tables` | 特性等级 ↔ 效果 | [装备与特性](ancillaries_and_traits.md) |
| `twad_key_deletes_tables` | key 删除声明（全量替换用） | [任务/事件/两难](missions_incidents_dilemmas.md) |
| `ui_features_to_cultures_tables` | UI 特性 → 文化 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `ui_features_to_factions_tables` | UI 特性 → 派系 | [战役组/载荷/佣兵](campaigns_payloads_mercenaries.md) |
| `ui_unit_bullet_point_enums_tables` | 单位要点枚举 | [单位与战斗](units_and_combat.md) |
| `ui_unit_bullet_point_unit_overrides_tables` | 单位要点覆盖 | [单位与战斗](units_and_combat.md) |
| `ui_unit_groupings_tables` | UI 单位分组 | [单位与战斗](units_and_combat.md) |
| `unique_agent_component_junctions_tables` | 独特事务官组件 | [角色/技能/事务官](characters_skills_agents.md) |
| `unique_agents_tables` | 独特事务官 | [角色/技能/事务官](characters_skills_agents.md) |
| `unit_abilities_additional_ui_effects_tables` | 单位能力额外 UI 效果 | [单位与战斗](units_and_combat.md) |
| `unit_abilities_tables` | 单位能力 | [单位与战斗](units_and_combat.md) |
| `unit_abilities_to_additional_ui_effects_juncs_tables` | 单位能力 ↔ UI 效果 | [单位与战斗](units_and_combat.md) |
| `unit_allowances_tables` | 单位容量许可 | [单位与战斗](units_and_combat.md) |
| `unit_armour_types_tables` | 护甲类型 | [单位与战斗](units_and_combat.md) |
| `unit_attributes_groups_tables` | 属性组 | [单位与战斗](units_and_combat.md) |
| `unit_attributes_to_groups_junctions_tables` | 属性 ↔ 组 | [单位与战斗](units_and_combat.md) |
| `unit_banner_unit_height_offsets_tables` | 旗帜高度偏移 | [单位与战斗](units_and_combat.md) |
| `unit_description_historical_texts_tables` | 单位历史描述 | [单位与战斗](units_and_combat.md) |
| `unit_description_short_texts_tables` | 单位简短描述 | [单位与战斗](units_and_combat.md) |
| `unit_lists_tables` | 单位列表 | [单位与战斗](units_and_combat.md) |
| `unit_missile_weapon_junctions_tables` | 单位额外远程武器 | [单位与战斗](units_and_combat.md) |
| `unit_purchasable_effect_lock_reasons_tables` | 可购买效果锁定原因 | [单位与战斗](units_and_combat.md) |
| `unit_purchasable_effect_sets_tables` | 单位 ↔ 可购买效果 | [单位与战斗](units_and_combat.md) |
| `unit_purchasable_effects_tables` | 可购买效果定义 | [单位与战斗](units_and_combat.md) |
| `unit_set_special_ability_phase_junctions_tables` | 单位集 ↔ 技能阶段 | [单位与战斗](units_and_combat.md) |
| `unit_set_to_unit_junctions_tables` | 单位集 ↔ 单位 | [单位与战斗](units_and_combat.md) |
| `unit_set_unit_ability_junctions_tables` | 单位集 ↔ 单位能力 | [单位与战斗](units_and_combat.md) |
| `unit_set_unit_attribute_junctions_tables` | 单位集 ↔ 单位属性 | [单位与战斗](units_and_combat.md) |
| `unit_sets_tables` | 单位集定义 | [单位与战斗](units_and_combat.md) |
| `unit_shield_types_tables` | 护盾类型 | [单位与战斗](units_and_combat.md) |
| `unit_special_abilities_tables` | 特殊技能 | [单位与战斗](units_and_combat.md) |
| `unit_to_unit_list_junctions_tables` | 单位列表 ↔ 单位 | [单位与战斗](units_and_combat.md) |
| `unit_variants_colours_tables` | 变体配色 | [单位与战斗](units_and_combat.md) |
| `unit_variants_tables` | 单位变体 | [单位与战斗](units_and_combat.md) |
| `units_custom_battle_permissions_tables` | 自定义战斗权限 | [单位与战斗](units_and_combat.md) |
| `units_to_groupings_military_permissions_tables` | 单位 → 军事分组 | [单位与战斗](units_and_combat.md) |

### V–W
| 表名 | 用途 | 文档 |
|------|------|------|
| `variants_tables` | 变体资源 | [单位与战斗](units_and_combat.md) |
| `warscape_animated_lod_tables` | 动画资源 LOD | [单位与战斗](units_and_combat.md) |
| `warscape_animated_tables` | 动画资源 | [单位与战斗](units_and_combat.md) |

---

## 已排除的引擎内部表（不在本索引）

以下前缀的表是引擎内部/低频使用，MOD 开发通常不涉及，故未收录：
- `cai_*`（约 177 张，战役 AI 决策）
- `audio_*`（约 86 张，音频）
- `loading_screen_*`、`frontend_*`（启动画面、前端）
- `_kv_*`（键值参数表）

如需查询这些表，直接在 `源码/db/<表名>/data__.tsv` 查看原版数据，表头第一行即列名。

---

## 查表不在本索引？

1. 该表可能是引擎内部表（见上"已排除"）→ 查 `源码/db/<表名>/data__.tsv` 看表头
2. 该表 MOD 未使用过 → 判断是否真的需要；需要时可在对应域文档补充
