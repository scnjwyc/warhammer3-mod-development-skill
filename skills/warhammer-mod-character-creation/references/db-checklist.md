## DB 全量清单

以下按功能分组。**必选**标记的表缺了角色就不成立；其余按设计依据裁剪。各表的列结构与 TSV 格式要求见 `warhammer-mod-development`。

### 单位主体链（必选）

| 表 | 主键 | 要点 |
|---|---|---|
| `main_units_tables` | `unit` | `caste`、`weight`、VO actor、`ui_unit_group_land` |
| `land_units_tables` | `key` | `man_animation`（**必须与模型骨骼一致**）、`man_entity`、`primary_melee_weapon`、`attribute_group`、短描述 key |
| `unit_variants_tables` | `unit` | `name`/`variant`/`unit_card` |
| `variants_tables` | `variant_name` | `variant_filename`→variantmeshdefinition、`scale`、`super_low_poly_filename` |
| `unit_variants_colours_tables` | 数字 id | soldier/officer 两行 |
| `agent_uniforms_tables` | `uniform_name` | filename/battle/porthole/politician 各列 |
| `battle_entities_tables` | `key` | 自定义实体或复用原版 |
| `melee_weapons_tables` / `missile_weapons_tables` | `key` | 用原版武器可跳过；自定义武器表只管数值，模型由 variantmeshes 挂载 |
| `unit_attributes_groups_tables` + `unit_attributes_to_groups_junctions_tables` | — | **只能用原版属性键**，禁止自定义属性 |
| `unit_set_to_unit_junctions_tables`、`units_to_groupings_military_permissions_tables`、`ui_unit_bullet_point_unit_overrides_tables`、`units_custom_battle_permissions_tables` | — | 单位分组、兵种说明、自定义战斗可见性 |
| `cdir_military_generator_unit_qualities_tables` | `unit_key` | **军事生成质量**：核对每个战役单位变体（含坐骑）的条目，见下节 |

### 军事生成质量（检查项）

`cdir_military_generator_unit_qualities_tables`（`group_key`/`unit_key`/`quality`）用于军事生成质量配置。当前 schema 决定表版本。历史案例中缺条目伴随异常战损，但这不证明该表是自动战斗估值的唯一来源或缺失必然产生低分；按当前同类原版和用户复测判断。

- 核对步行与每个战役坐骑变体的质量配置。仅战斗内生成的召唤物是否需要记录，按当前生成器用途与同类原版判断。
- `group_key` 采用同类角色基准，常见为 `wh3_default_land_characters`。
- `quality` 必须是原版 `unit_quality_progression_functions_tables` 已存在的键（offset 即基础分，slope 随等级加成）。以下为历史原版参照，当前值重新查表：

| 原版单位 | quality | 基础分 |
|---|---|---|
| 妙影（传奇领主） | `tier_4_step_3_units` | 58 |
| 元伯 / 艾查恩骑乘 | `tier_4_step_4_units` | 63 |
| 昊天狮（昊天将军坐骑） | `tier_4_step_1_units` | 48 |
| 高崔克（传奇英雄） | `tier_3_step_3_units` | 33 |
| 菲力克斯（传奇英雄） | `tier_2_step_4_units` | 24 |

- 推荐档位（无双英灵录实例，对比妙影）：传奇领主（步行+全部坐骑）`tier_4_step_5_units`（68）；英雄步行 `tier_3_step_3_units`（33）；英雄马匹坐骑 `tier_3_step_5_units`（43）；英雄巨兽/战争机器坐骑 `tier_4_step_1_units`（48）。原版惯例坐骑质量不低于步行（卡塔琳步行 12 → 雪橇 58）。

### 角色身份链（必选）

| 表 | 主键 | 要点 |
|---|---|---|
| `agent_subtypes_tables` | `key` | `is_caster`、`associated_unit_override`→main_unit、`recruitment_category`（领主=`legendary_lords`）、`can_equip_ancillaries` |
| `campaign_character_art_sets_tables` | `art_set_id` | **含备用服装在内的全部 art set 都要登记** |
| `campaign_character_arts_tables` | 数字 id | `uniform`、`land_animation`（骨骼匹配）、海战 uniform/动画照抄同文化原版角色 |
| `campaign_to_agent_subtypes_tables` | subtype+campaign | 如 `wh3_main_combi` |
| `faction_agent_permitted_subtypes_tables` | agent+faction+subtype | **按设计允许的派系列表登记**；需要全文化招募时枚举该文化全部派系，不把示例许可扩展给设计未授权的派系 |
| `names_tables` | 数字 id | 名字组、forename/surname、性别 |
| `unique_agents_tables` + `campaign_group_unique_agents_tables` + `unique_agent_component_junctions_tables` | — | **仅英雄**（全图唯一英雄）；领主不要 |

### 技能树链（必选）

`character_skill_node_sets_tables` → `character_skill_nodes_tables`（`indent/tier` 控制 UI 位置；背景特性 `points_on_creation=1,visible_in_ui=false`）→ `character_skill_node_links_tables`（`REQUIRED` / `SUBSET_REQUIRED` 前置关系）→ `character_skill_node_set_items_tables`（个人线 + 法术线 + 红/黄线全部挂进 set）→ `character_skills_tables`（`image_path`、`is_background_skill`）→ `character_skill_level_to_effects_junctions_tables`（注意 `effect_scope`）→ `character_skill_level_details_tables`（`unlocked_at_rank` 对应设计解锁等级）→ `character_skill_utilization_hints_junctions_tables`。

### 战役事务官行动 Dummy（必须与 agent 类型匹配）

- 角色技能树中的战役行动占位节点（`character_skill_nodes_tables` 的 `*_dummy_agent_actions_*`）必须使用与 `agent` 类型一致的原版 Dummy，不能让所有英雄共用法师 Dummy。
- 震旦 `wizard` 使用 `wh3_main_skill_all_dummy_agent_actions_cth_astromancer`；震旦 `champion` 使用 `wh3_dlc24_skill_all_dummy_agent_actions_cth_gate_master`。其他文化或 `agent` 类型必须对照同类型、已能执行事务官行动的原版角色确定 Dummy。
- 错误 Dummy 可能出现“技能卡能显示，但刺杀、袭击驻军、阻击军队等事务官行动全部不能执行”；在部分构造路径下还会使 CCO 的 `CanBeEmbedded` 变成 `false`，造成角色无法入队。
- 创建新角色时，逐项检查 `character_skill_node_sets_tables` → `character_skill_nodes_tables` → `character_skill_node_set_items_tables`，确认 campaign action Dummy、`wh3_main_skill_agent_action_success_scaling` 和六个通用战役行动节点均已挂入技能树；然后由用户对照同 `agent` 类型的正常英雄实测事务官行动可执行且 `CanBeEmbedded=true`。

### 能力链（每个主动/被动/法术能力逐条落地）

`unit_abilities_tables`（`icon_name` 不带 .png、`requires_effect_enabling`）→ `unit_special_abilities_tables`（`unique_id` 在目标 MOD 未占用的新段分配；**自增益必须 `affect_self=true` 且 `only_affect_target=false`**——原版所有 `affect_self=true` 的行 `only_affect_target` 均为 false；地面目标类能力的"目标"是位置，`only_affect_target=true` 会导致自增益 phase 无人可施加；`num_effected_friendly_units` 按目标模板取值，见下节"能力目标模板"；`vortex`/`spawned_unit`/`miscast` 按需）→ `special_ability_phases_tables`（对敌/对己拆正负 phase）→ `special_ability_to_special_ability_phase_junctions_tables`（`target_self/target_friends/target_enemies` 三布尔）→ `special_ability_phase_stat_effects_tables` / `special_ability_phase_attribute_effects_tables` → `special_ability_to_invalid_target_flags_tables` / `..._invalid_usage_flags` / `..._auto_deactivate_flags` → `battle_vortexs_tables`（可选）→ `land_units_to_unit_abilites_junctions_tables`（挂载）→ 效果侧 `effects_tables` + `effect_bonus_value_unit_ability_junctions_tables`（法术标准链：enable / overcast / cooldown / wom_cost / miscast）。法术字段见 [法术 DB 专题](../../warhammer-mod-development/references/topics/战锤3法术相关DB字段说明.md)。

### 特殊机制的技能 UI 词条（必选）

创建或修改技能时，凡是游戏效果面板**不会自动完整显示**的特殊机制，都必须配置技能 UI 词条，不能只藏在背景描述、脚本注释或设计文档中。典型情形包括复活兵模、召唤单位、变身、脚本附加机制，以及其他无法由 phase 数值/属性行直接表达的效果。

- 新建 `unit_abilities_additional_ui_effects_tables` 行，并在 `unit_abilities_to_additional_ui_effects_juncs_tables` 将其绑定到对应 ability。
- 补齐 `unit_abilities_additional_ui_effects_localised_text_<effect_key>` 本地化；词条应直接、简短地说明特殊效果，例如“召唤一个 XXX 单位”“变身为 XXX”。
- 仅描述自动面板无法表达的机制；已有 phase 数值、范围、持续时间或属性效果继续交由游戏原生面板显示，避免重复或互相矛盾。

### 能力目标模板

自身增益、范围友军增益和克隆字段核对见 [能力目标模板](ability-targets.md)。

### 坐骑链（可选）

- 单位：坐骑 `land_units`（`mount` 填原版坐骑 key、`man_animation` 用**骑手**动作、血量按设计倍率）、`main_units`（`mount` 列填战役镜头 `wh3_main_cam_mnt_*`）、`unit_variants`（variant 指骑马形态 `*_mounted`）、`battle_personalities_tables` + `land_units_to_battle_personalities_junctions_tables`（挂点 `ap_riderposition_0`/`ap_saddle_rider_00`）、abilities/unit_set/attributes/permissions 同单位链，**cdir 质量条目也要按坐骑变体逐条登记**（与步行条目分别核对）。
- 战役：`units_custom_battle_mounts_tables`（`base_unit`→`mounted_unit`）、`campaign_mount_animation_set_overrides_tables`（见下）。
- 战役战斗乘员：`main_units.mount` → `campaign_mounts_tables` 只决定战役大地图坐骑模型，**不决定战斗乘员**；战斗乘员由 `land_units_to_battle_personalities_junctions_tables` 选出。载具坐骑（飞艇/蒸汽坦克等带乘员组）的非 captain 乘员必须建 MOD 自己的 `battle_personalities` 副本、`autonomous_rider_hero=false`，见 [载具坐骑排查](troubleshooting.md)。
- 发放（技能解锁坐骑，四段缺一不可）：
  - 技能树侧：坐骑技能节点（挂进 node_set）、`character_skills_tables`、`character_skill_level_details_tables`（`unlocked_at_rank` = 设计解锁等级）
  - **效果侧：`character_skill_level_to_effects_junctions_tables` 必须绑 `wh_*_effect_enable_mount_<坐骑>`（`character_to_character_own`、value 1）**——技能面板「解锁坐骑：XXX」由它提供；缺失则技能点了毫无效果
  - **升级条件：`character_skills_to_level_reached_criterias_tables` 每个坐骑技能一行（skill、等级、1）**，等级与 level_details 对齐（如战马/机械骏马 8，玉龙马/玉麒麟/雷霆飞艇 18）；缺失则技能永远不可用
  - 发放：`character_skill_level_to_ancillaries_junctions_tables` + `ancillaries_tables`（`provided_bodyguard_unit` 指坐骑 land_unit）+ `ancillary_info_tables` + `ancillaries_included_agent_subtypes_tables`（**别漏行**）+ `ancillaries_required_skills_tables`

### 装备链（可选）

`ancillaries_tables`（`immortal=true`、`randomly_dropped=false`；注意各装备槽数量限制，如同类法系装备要分到不同槽）+ `ancillary_info_tables` + `ancillaries_included_agent_subtypes_tables` + `ancillary_to_effects_tables` + 技能侧（skills/nodes/set_items/level_details/`character_skill_level_to_ancillaries_junctions`，skill key = ancillary key）+ `ancillaries_required_skills_tables`。
