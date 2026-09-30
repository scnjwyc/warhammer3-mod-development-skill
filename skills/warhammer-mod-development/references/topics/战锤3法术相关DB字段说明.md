# 战锤3 法术相关 DB 字段说明

> 基于原版 `源码/db/`（WH3，表版本随游戏更新）整理。  
> 法术在引擎里属于 **Ability（能力）** 体系，与战役技能树 `character_skills` 不是同一套表。  
> 主要参考：原版 TSV、[Cryswar 能力指南](https://steamcommunity.com/sharedfiles/filedetails/?id=1698960734)、RPFM schema patches。

---

## 目录

1. [总览与数据流](#1-总览与数据流)
2. [法术类型对照](#2-法术类型对照)
3. [UI 层：`unit_abilities_tables`](#3-ui-层unit_abilities_tables)
4. [战斗核心：`unit_special_abilities_tables`](#4-战斗核心unit_special_abilities_tables)（含 [§4.3.1 诱饵/变形/共享血疲](#431-spawn_is_decoy--spawn_is_transformation--spawn_shares_health_and_fatigue)）
5. [阶段效果：`special_ability_phases*` ](#5-阶段效果special_ability_phases)
6. [投射物：`projectiles*` ](#6-投射物projectiles)
7. [轰炸：`projectile_bombardments*`](#7-轰炸projectile_bombardments)
8. [涡流 / 风系 / 吐息：`battle_vortexs*`](#8-涡流--风系--吐息battle_vortexs)
9. [学派 / 法术组：`special_ability_groups*`](#9-学派--法术组special_ability_groups)
10. [使用限制与强度](#10-使用限制与强度)
11. [AOE / 显示 / 音频](#11-aoe--显示--音频)
12. [如何挂到单位 / 技能 / 军队](#12-如何挂到单位--技能--军队)
13. [本地化](#13-本地化)
14. [常见坑](#14-常见坑)

---

## 1. 总览与数据流

```
unit_abilities_tables                    ← 名称/图标/类型/超载关联（偏 UI）
        │ key 一一对应
        ▼
unit_special_abilities_tables            ← 冷却、魔耗、目标、失误、施法姿态
        │
        ├── activated_projectile ──────► projectiles_tables
        │                                      ├─ explosion_type ► projectiles_explosions_tables
        │                                      ├─ projectile_display ► projectile_displays_tables
        │                                      └─ homing_params ► projectile_homing_params_tables
        │
        ├── bombardment ───────────────► projectile_bombardments_tables
        │                                      └─ projectile_type ► projectiles_tables
        │
        ├── vortex ────────────────────► battle_vortexs_tables
        │                                      └─ contact_effect ► special_ability_phases
        │
        ├── spawned_unit ──────────────► land_units_tables（召唤）
        │
        └── special_ability_to_special_ability_phase_junctions
                    └──► special_ability_phases_tables（增益/减益/治疗/DoT）
                              ├── special_ability_phase_stat_effects
                              └── special_ability_phase_attribute_effects
```

**判定“这是法术”的常见标志：**

| 表.字段 | 典型值 |
|---------|--------|
| `unit_abilities.source_type` | `spell`（也见 `bound` 绑定法术） |
| `unit_special_abilities.mana_cost` | `> 0` |
| `special_ability_groups` | `*lore_*` 学派组 |
| `projectiles.is_spell` / `battle_vortexs.is_spell` | `true` |

---

## 2. 法术类型对照

`unit_abilities.type` → `unit_ability_types_tables`，主要影响 **UI 图标分类与光标**，真正伤害形态由 `unit_special_abilities` 里填的 projectile / vortex / bombardment / phase 决定。

| type key | 含义（UI） | 常见实现 |
|----------|-----------|----------|
| `wh_type_magic_missile` / `wh_type_magic_missiles` | 魔法飞弹 | `activated_projectile` |
| `wh_type_bombardment` | 天降轰炸 | `bombardment` |
| `wh_type_vortex` | 涡流 | `vortex`（静止/游荡） |
| `wh_type_wind` | 风系 | 多为可移动 `vortex` |
| `wh_type_breath` | 吐息 | `vortex`（常带 shape/方向） |
| `wh_type_explosion` | 爆炸 | vortex 扩张 / explosion |
| `wh_type_direct_damage` | 直接伤害 | phase DoT/瞬时伤害 |
| `wh_type_augment` / `wh_type_area_of_augments` | 增益 | phase positive |
| `wh_type_hex` / `wh_type_area_of_hexes` | 诅咒 | phase negative |
| `wh_type_regeneration` / `wh_type_area_of_regeneration` | 治疗 | phase heal |
| `wh_type_ward_save` / `*_hex` | 守护/减守护 | phase 抗性 |
| `wh_type_summon_unit` | 召唤 | `spawned_unit` |
| `wh_type_transform` | 变形 | spawn + transformation 标志 |
| `wh_type_formation` | 阵型 | `formation` / behaviour |
| `wh_type_*_of_the_winds` | 魔风相关 UI | 仍走 phase/ability |

---

## 3. UI 层：`unit_abilities_tables`

表版本：`17`

| 字段 | 类型 | 含义 |
|------|------|------|
| `key` | string PK | 能力主键。整条法术链共用此 key。 |
| `requires_effect_enabling` | bool | `true`：需战役 effect 启用（技能解锁法术几乎都是）。`false`：可直接挂在 `land_units_to_unit_abilites`。 |
| `icon_name` | string | 战斗 UI 图标名，对应 `ui/battle ui/ability_icons/<name>.png`（无扩展名）。 |
| `overpower_option` | string FK | 超载版能力 key。基础版填超载版；超载版留空。 |
| `type` | string FK | → `unit_ability_types_tables.key`，UI 类型。 |
| `video` | string | 教程/预览视频（多数空）。 |
| `uniqueness` | string | UI 边框稀有度：`wh_main_anc_group_common` / `uncommon` / `rare` / `unique`（另有符文组）。 |
| `is_unit_upgrade` | bool | 是否单位升级类能力。 |
| `is_hidden_in_ui` | bool | 对己方 UI 隐藏。 |
| `source_type` | string FK | → `unit_ability_source_types`。法术常用 `spell`；绑定法术 `bound`；军队技 `army`；被动 `passive`；道具 `item` 等。 |
| `superseded_abilities_set` | string FK | 能力升级替换集合（黑方舟等少数用法）。 |
| `is_hidden_in_ui_for_enemy` | bool | 对敌方 UI 隐藏。 |

### `unit_ability_types_tables`

| 字段 | 含义 |
|------|------|
| `key` | 类型主键 |
| `show_cursor_trail` | 瞄准时是否显示光标拖尾 |
| `icon_path` | 类型分类小图标路径 |

### `unit_ability_source_types_tables`

仅一列 `key`。常见：`spell`、`bound`、`army`、`passive`、`item`、`character`、`unit`、`banner`、`rune`、`lore`、`cataclysm` 等。

---

## 4. 战斗核心：`unit_special_abilities_tables`

表版本：`74`。与 `unit_abilities.key` **同名一一对应**。这是法术最重要的表。

### 4.1 时间 / 次数 / 范围

| 字段 | 含义 |
|------|------|
| `key` | = `unit_abilities.key` |
| `active_time` | 施法者“占用”时长（秒）。冷却通常等主动结束再开始；`-1` 表示不占用持续（如火球发射即完）。 |
| `recharge_time` | 冷却（秒）。 |
| `num_uses` | 使用次数。`-1` = 无限（多数法术）；正整数 = 有限次数。召唤偶发 `-1` 异常，可改成较大正数。 |
| `effect_range` | 效果半径。`0` = 仅自身；`-1` = 全图；正数 = 米。 |
| `affect_self` | 是否影响施法者自身。 |
| `always_affect_self` | 无论目标如何，始终影响自身。 |
| `only_affect_target` | 只影响被点选目标（忽略范围扩散）。 |
| `only_affect_owned_units` | 只影响己方所属单位。 |
| `num_effected_friendly_units` | 最多影响友军单位数；`0` 通常表示不按此限制。 |
| `num_effected_enemy_units` | 最多影响敌军单位数。 |
| `update_targets_every_frame` | 每帧刷新作用目标（移动光环类）。 |
| `initial_recharge` | 开战初始冷却。军队技建议 >0，否则易出问题。 |
| `shared_recharge_time` | 共享冷却。`-1` = 不共享；正数则与其它共享该值的能力互锁。 |
| `min_range` | 最小施法距离（太近不能放）。 |
| `target_intercept_range` | 施法有效距离（需靠近目标到此距离内）。火球示例：`300`。 |

### 4.2 目标选择

| 字段 | 含义 |
|------|------|
| `target_friends` | 可点选友军 |
| `target_enemies` | 可点选敌军 |
| `target_ground` | 可点选地面 |
| `target_self` | 可点选自己 |
| `target_ground_under_allies` | 允许点友军脚下的地面 |
| `target_ground_under_enemies` | 允许点敌军脚下的地面 |

无点选、按键即放：上述目标多为 `false`。

### 4.3 法术效果出口（四选一或多组合）

| 字段 | 指向 | 典型法术 |
|------|------|----------|
| `activated_projectile` | `projectiles_tables.key` | 火球、谢姆灼视 |
| `bombardment` | `projectile_bombardments.bombardment_key` | 彗星、末日螺栓 |
| `vortex` | `battle_vortexs.vortex_key` | 烈焰风暴、放逐、风系 |
| `activation_effect` | phase / 效果 key | 部分瞬时激活 |
| `spawned_unit` | `land_units.key` | 召唤尸兵、变形目标形态、诱饵分身等 |

| 字段 | 含义 |
|------|------|
| `spawn_type` | `unit_position`（在施法者/点选位置生成）/ `unit_position_offset`（偏移）。普通召唤与诱饵常留空；**变形类原版几乎都填 `unit_position`**。 |
| `spawn_proxy_vfx` | 召唤/变形位置代理特效（如 `wh_main_targeting_pre_spawn_solo_ui_central`） |
| `spawn_is_decoy` / `spawn_is_transformation` / `spawn_shares_health_and_fatigue` | 见下方 **§4.3.1**（三者互斥组合在原版有固定模式） |
| `parent_ability` | 父能力（子能力/衍生） |
| `mom_vortex_key` | 魔法风暴（Storm of Magic）相关 vortex 覆盖 |

#### 4.3.1 `spawn_is_decoy` / `spawn_is_transformation` / `spawn_shares_health_and_fatigue`

这三个布尔值只在 **带 `spawned_unit`（或变形 behaviour）** 的能力上有意义；普通召唤法术（奈赫克、深渊召唤等）三者全为 `false`。

原版共现规律（全表扫描结论）：

| 模式 | decoy | transform | share HP/fatigue | 实际效果（按原版用法归纳） |
|------|-------|-----------|------------------|---------------------------|
| A. 诱饵分身 | `true` | `false` | `false` | **施法者本体仍在**，额外生成一个诱饵单位（假身/虚影）。诱饵有独立血条，可吸引仇恨；本体与诱饵互不继承血量/疲劳。 |
| B. 真变形 + 状态继承 | `false` | `true` | `true` | **本体被替换**为 `spawned_unit` 形态（人↔龙、无形恐怖换形、可怖巨口潜地/破土）。新形态继承当前血量比例与疲劳。 |
| C. 真变形 + 不继承 | `false` | `true` | `false` | **本体被替换**，但**不**走血量/疲劳共享（原版仅马鲁斯「扎坎」系）。常配合附身/切换脚本，与龙形那套「同一角色连续换皮」不同。 |
| D. 普通召唤 | `false` | `false` | `false` | 额外刷兵；召唤物独立血条，施法者不变。 |

补充：

- **`spawn_is_decoy` 与 `spawn_is_transformation` 在原版从不共用**（诱饵 ≠ 变形）。
- **`spawn_shares_health_and_fatigue=true` 在原版只与 `spawn_is_transformation=true` 一起出现**，从未单独用于普通召唤或诱饵。
- 变形能力常配 `spawn_type=unit_position`、`affect_self=true`；诱饵的 `spawn_type` 多为空。
- 变形还可叠 `behaviour`：`changeling_transformation`（无形恐怖选形态）、`go_underground` / `dig_yourself_out`（可怖巨口潜地）。
- 相关字段 `can_be_copied_to_transformation_unit`：变形后新形态是否带上该能力（多数法术/道具为 `true`；变形诱饵「虚影」为 `false`，避免诱饵再放诱饵）。

**原版 `spawn_is_decoy=true`（仅 4 条）**

| ability key | 中文名 | `spawned_unit` |
|-------------|--------|----------------|
| `wh2_dlc10_lord_abilities_mislead` | 误导 | `wh2_dlc10_hef_cha_alith_anar_summoned_0`（艾瑞安分身） |
| `wh2_dlc10_lord_abilities_deadly_mislead` | 暗影舞者之唤 | `..._alith_anar_summoned_1`（强化分身） |
| `wh2_dlc14_unit_abilities_doppelgang` | 二重身法 | 艾辛三影 ROR 召唤体 |
| `wh3_dlc24_lord_item_deceiving_shadows` | 虚影 | `wh3_dlc24_tze_cha_changeling_summoned_0`（奸奇骗术师诱饵） |

**原版 `spawn_is_transformation=true` + `spawn_shares_health_and_fatigue=true`（形态切换）**

| ability key | 中文名 | 说明 |
|-------------|--------|------|
| `wh3_main_lord_abilities_iron_dragon_{human,dragon}_form` | 化龙诀 | 昭明人↔龙 |
| `wh3_main_lord_abilities_storm_dragon_{human,dragon}_form` | 化龙诀 | 妙影人↔龙 |
| `wh3_dlc24_lord_abilities_jade_dragon_{human,dragon}_form` | 化龙诀 | 元博人↔龙 |
| `wh3_dlc24_lord_abilities_formless_horror` | 无形恐怖 | `behaviour=changeling_transformation`，选形态换身 |
| `wh3_dlc24_lord_abilities_formless_horror_changeling` | 无形恐怖 | 变回骗术师本体 |
| `wh3_dlc24_lord_abilities_formless_horror_quest_battle*` | 无形恐怖 | 任务战变体 |
| `wh3_dlc27_unit_abilities_dread_maw_underground` | 潜地 | `behaviour=go_underground` |
| `wh3_dlc27_unit_abilities_dread_maw_surface` | 破土而出 | `behaviour=dig_yourself_out` |

**原版 `spawn_is_transformation=true` 但 `share=false`（仅扎坎系）**

| ability key | 中文名 | `spawned_unit` |
|-------------|--------|----------------|
| `wh2_dlc14_lord_abilities_tzarkan` / `_mp` | 扎坎 | `..._malus_darkblade_tzarkan_0` |
| `wh2_dlc14_lord_abilities_tzarkan_spite` / `_mp` | 扎坎 | `..._tzarkan_1`（斯派克坐骑变体） |
| `wh2_dlc14_lord_abilities_tzarkan_snikch` | 扎坎 | 死亡大师史尼奇任务变体 |
| `wh2_dlc14_lord_passive_tzarkan` | 扎坎 | 被动；`spawned_unit` 为空 |

MOD 建议：要做「分身诱饵」抄误导/虚影（仅 decoy）；要做「同一角色换形态且血条连续」抄化龙诀/无形恐怖（transform+share）；不要给普通召唤开 decoy/transform/share。

### 4.4 施法表现 / 姿态

| 字段 | 含义 |
|------|------|
| `wind_up_time` | 前摇（施法抬手）秒数 |
| `wind_up_stance` | 前摇动画姿态（如 `cast_forward_short`） |
| `wind_down_stance` | 后摇姿态 |
| `use_loop_stance` | 是否循环施法姿态 |
| `passive` | 是否被动（自动生效，不点按） |
| `special_ability_display` | → `special_ability_displays`（学派施法光环/武器 VFX） |
| `composite_scene_group_on_wind_up` | 前摇 composite scene 组 |
| `composite_scene_group_on_active` | 生效时 composite scene 组 |
| `display_stops_when_display_expires` | 显示到期即停 |
| `audio` | → `audio_abilities.key` |
| `voiceover_state` | 语音状态（如 `vo_battle_special_ability_spell_cast_negative`） |
| `audio_switch_casting_override` | 施法音频 switch 覆盖 |
| `audio_switch_ui_override` | UI 音频 switch 覆盖 |
| `audio_vo_actor_override` | VO 演员覆盖 |

### 4.5 魔风 / 失误

| 字段 | 含义 |
|------|------|
| `mana_cost` | 魔风消耗。非法术多为 `0`。 |
| `miscast_chance` | 失误概率 `0.0`–`1.0`（0%–100%）。基础版多为 0，超载版常有。 |
| `miscast_explosion` | 失误爆炸 → `projectiles_explosions`（如 `wh_main_fire_miscast`） |
| `miscast_global_bonus` | 是否吃全局失误修正 |
| `current_mana_moves_to_reserve` | 当前魔风是否转入储备（部分机制） |

### 4.6 AOE 显示（瞄准圈）

| 字段 | 含义 |
|------|------|
| `targetting_aoe` | 瞄准阶段 AOE 显示 → `area_of_effect_displays` |
| `passive_aoe` | 被动光环 AOE 显示 |
| `active_aoe` | 激活后 AOE 显示 |

### 4.7 AI / 自动结算 / CP

| 字段 | 含义 |
|------|------|
| `ai_usage` | AI 使用策略标签（如 `projectile_homing_single`、`healing_area`、`vortex_wind`） |
| `ai_usage_template_group` | AI 模板组 |
| `autoresolver_usage` | 自动战斗用法（**不可空**，空会崩溃；常见 `damage_single` / `damage_aoe` / `default`） |
| `autoresolver_targets` | 自动战斗目标数权重 |
| `autoresolve_cp_multiplier` | 自动战斗 CP 倍率 |
| `additional_melee_cp` | 额外近战 CP（偏自动结算估值） |
| `additional_missile_cp` | 额外远程 CP |

### 4.8 其它行为标志

| 字段 | 含义 |
|------|------|
| `unique_id` | **必须全局唯一**的数字 ID（建议 ≤9 位）。冲突会导致能力不触发。 |
| `formation` | 阵型行为 key（布列塔尼枪阵等） |
| `behaviour` | → `special_ability_behaviour_groups`（召唤、传送、地底等特殊行为） |
| `update_phase_by_ability_duration` | phase 时长跟随 ability 持续时间 |
| `affect_siege_equipment` | 是否影响攻城器械 |
| `intensity_based_activation` | 是否按强度表激活（元素掌控等） |
| `ability_available_ui_event` | 能力可用时 UI 事件 |
| `can_be_copied_to_transformation_unit` | 单位发生 `spawn_is_transformation` 换形后，新形态是否仍拥有该能力。与 §4.3.1 配套；诱饵「虚影」自身为 `false`。 |

---

## 5. 阶段效果：`special_ability_phases*`

增益、诅咒、治疗、DoT、附魔攻击等走 **phase**。纯投射物/涡流伤害本身不需要 phase；但涡流命中可挂 `contact_effect` phase。

### 5.1 `special_ability_phases_tables`（版本 44）

| 字段 | 含义 |
|------|------|
| `id` | phase 主键（常与能力同名） |
| `duration` | 持续秒数；`-1` = 永久（被动） |
| `effect_type` | `positive` / `negative` / `neutral`（UI 绿/红） |
| `requested_stance` | 请求姿态（极少数，如自复活类） |
| `cant_move` | 期间禁止移动 |
| `freeze_fatigue` | 冻结疲劳变化（原版少用；完美精力更常走属性） |
| `fatigue_change_ratio` | 疲劳变化比例；**负值恢复，正值加重** |
| `inspiration_aura_range_mod` | 激励光环范围修正 |
| `ability_recharge_change` | 给能力冷却加减秒数 |
| `hp_change_frequency` | 跳血/跳伤间隔（秒），如 `0.5` |
| `damage_amount` | 每次跳伤伤害（绕过魔抗/物抗，仍吃结界等） |
| `max_damaged_entities` | 每跳最多伤害实体数（AOE DoT 必须限制，防按人头爆炸） |
| `resurrect` | 治疗是否可复活已死模型（奈赫克真，大地之血假） |
| `mana_regen_mod` | 魔风回复/秒修正（奥术导体） |
| `mana_max_depletion_mod` | 魔风上限/消耗相关修正 |
| `imbue_magical` | 攻击附魔魔法伤害 |
| `imbue_ignition` | 点燃值（常用 `10` 开火焰攻击） |
| `imbue_contact` | 命中时附加的 contact phase（毒、气馁等） |
| `phase_display` | → `special_ability_phase_displays` |
| `phase_audio` | phase 音频 |
| `is_hidden_in_ui` | UI 隐藏该 phase 图标 |
| `affects_allies` / `affects_enemies` | AOE phase 是否打友/打敌 |
| `replenish_ammo` | phase 开始时立刻回复弹药比例/量 |
| `composite_scene_group` | 场景特效组 |
| `spreading` | → `special_ability_spreadings`（传染扩散） |
| `freeze_recharge` | 冻结能力充能 |
| `heal_amount` | 每次治疗量（配合 `hp_change_frequency`） |
| `barrier_heal_amount` | 护盾/屏障回复量 |
| `remove_magical` | 移除魔法状态类效果 |
| `execute_ratio` | 斩杀比例（残血处决类） |

**自定义 phase 图标：** 需在 `ui/battle ui/ability_icons/` 放置与 phase `id` 同名的 png，否则 UI 为白方块。

### 5.2 `special_ability_to_special_ability_phase_junctions_tables`

| 字段 | 含义 |
|------|------|
| `order` | 多 phase 顺序（多数单 phase 填 `0` 或 `1`） |
| `special_ability` | → `unit_special_abilities.key` |
| `target_self` / `target_friends` / `target_enemies` | 该 phase 作用对象 |
| `phase` | → `special_ability_phases.id` |

同一能力可挂多个 phase（先强 buff 再 debuff、分段回弹药等）。

### 5.3 `special_ability_phase_stat_effects_tables`

| 字段 | 含义 |
|------|------|
| `phase` | phase id |
| `stat` | 属性名（见下表） |
| `value` | 数值 |
| `how` | `add` 加减；`mult` 乘法（`>1` 增强，`0~1` 削弱） |

**常用 `stat`：**

| stat | 含义 |
|------|------|
| `stat_melee_attack` / `stat_melee_defence` | 近战攻/防 |
| `stat_melee_damage_base` / `stat_melee_damage_ap` | 近战普伤/破甲 |
| `stat_charge_bonus` / `stat_armour` / `stat_morale` / `stat_mass` | 冲锋/护甲/士气/质量 |
| `stat_accuracy` / `stat_reloading` | 精度/装填 |
| `stat_bonus_vs_infantry` / `stat_bonus_vs_large` | 对步/对大 |
| `stat_resistance_physical` / `magic` / `missile` / `flame` / `all` | 抗性 |
| `stat_missile_block_chance` | 远程格挡 |
| `stat_healing_power` | 治疗力 |
| `stat_damage_reflection` | 反伤 |
| `scalar_speed` / `scalar_charge_speed` | 移速类 |
| `scalar_missile_damage_base` / `_ap` | 远程伤害倍率 |
| `scalar_missile_explosion_damage_base` / `_ap` | 爆炸伤害倍率 |
| `scalar_missile_range` | 射程 |
| `scalar_miscast_chance` | 失误率标量 |
| `scalar_spell_mastery` | 法术精通 |
| `scalar_visibility_sight_modifier` 等 | 视野/机动标量 |

非破甲与破甲伤害通常要 **各写一行**。

### 5.4 `special_ability_phase_attribute_effects_tables`

| 字段 | 含义 |
|------|------|
| `attribute` | 属性 flag（如 `stalk`、`unbreakable`、`causes_terror`） |
| `phase` | phase id |
| `attribute_type` | 通常 `positive` / `negative` |

仅在 phase 持续期间生效。永久属性更建议走战役 effect。

### 5.5 `special_ability_spreadings_tables`

| 字段 | 含义 |
|------|------|
| `key` | 扩散配置 key |
| `phase` | 扩散传播的 phase |
| `spread_radius` | 扩散半径 |

### 5.6 `special_ability_phases_to_additional_ui_effects_junctions_tables`

为 phase 挂额外 UI 说明条（纯展示）。

---

## 6. 投射物：`projectiles*`

魔法飞弹与弓箭/火炮共用投射物表；法术行通常 `is_spell=true`。

### 6.1 `projectiles_tables`（版本 53）

| 字段 | 含义 |
|------|------|
| `key` | 投射物主键 |
| `category` | 类别：`arrow`/`artillery`/`musket`/`grenade`/`misc` 等 |
| `shot_type` | 射击类型（与 category 配套） |
| `explosion_type` | → `projectiles_explosions.key`；空=不爆炸 |
| `spin_type` | 旋转类型（灼视类常用） |
| `projectile_number` | 同时生成弹数（霰弹/多发火球） |
| `trajectory_sight` | 弹道视线类型（`low` 等） |
| `effective_range` | 有效射程（面板射程） |
| `minimum_range` | 最小射程 |
| `max_elevation` | 最大仰角 |
| `muzzle_velocity` | 初速 |
| `marksmanship_bonus` | 射手加成（精度杠杆之一） |
| `spread` | 散布；多弹时需加大才能肉眼分开 |
| `damage` / `ap_damage` | 命中基础/破甲伤害 |
| `can_bounce` | 可否弹跳 |
| `high_air_resistance` | 高空气阻力 |
| `collision_radius` | 碰撞半径 |
| `base_reload_time` | 基础装填（武器用；法术常无关） |
| `calibration_distance` | 此距离内满精度 |
| `calibration_area` | 瞄准散布面积（越小越准） |
| `bonus_v_infantry` / `bonus_v_large` | 对步/对大加成 |
| `projectile_display` | → `projectile_displays` |
| `overhead_stat_effect` | 弹道飞过时对下方单位的 phase（地狱加农等） |
| `projectile_audio` | → `audio_projectiles` |
| `shockwave_radius` | 冲击波半径 |
| `can_damage_buildings` | 伤建筑 |
| `contact_stat_effect` | 命中附加 phase（破盾等） |
| `gravity` | 重力；`-1` 常用默认 |
| `burst_size` | 点射发数（喷火器等） |
| `burst_shot_delay` | 点射间隔 |
| `mass` | 弹体质量 |
| `homing_params` | → `projectile_homing_params` |
| `first_person_params` | 第一人称参数 |
| `ignition_amount` | 点燃；`1`=火焰攻击 |
| `is_magical` | 魔法伤害 |
| `can_target_airborne` | 可打飞行单位 |
| `can_damage_allies` | 可伤友军 |
| `fixed_elevation` | 固定仰角 |
| `projectile_penetration` | 穿透级别 |
| `expiry_range` | 绝对失效距离；`-1`=碰到才消失；应 ≥ effective_range |
| `is_beam_launch_burst` | 光束发射爆发 |
| `expire_on_impact` | 命中即消失 |
| `can_roll` | 可否滚动 |
| `trail_always_on` | 拖尾常开 |
| `shots_per_volley` | 每轮齐射数（吐息/风琴炮常用） |
| `fired_by_mount` | 由坐骑发射 |
| `lock_on_multiple_fire_pos` | 锁定多开火点 |
| `prefer_central_targets` | 优先中心目标 |
| `can_damage_vehicles` | 伤载具 |
| `building_damage_multiplier` | 建筑伤害倍率 |
| `scaling_damage` | → `projectiles_scaling_damages`（按目标血量缩放） |
| `is_spell` | 是否法术投射物 |
| `vegetation_ignore_time` | 忽略植被碰撞时间 |
| `missile_mirror_start_time` | 导弹镜像开始时间 |
| `spawned_vortex` | 命中/路径生成 vortex |
| `projectile_shot_type_display` | UI 射击类型显示 |

### 6.2 `projectiles_explosions_tables`

| 字段 | 含义 |
|------|------|
| `key` | 爆炸主键 |
| `detonator_type` / `detonation_type` | 引爆/爆炸类型枚举 |
| `detonation_radius` | 爆炸半径 |
| `detonation_duration` / `detonation_speed` | 爆炸持续/扩散速度 |
| `detonation_damage` / `detonation_damage_ap` | 爆炸伤害/破甲 |
| `shrapnel` | → `projectile_shrapnels`（破片再射弹） |
| `explosion_particle_effect` | 空中爆炸粒子 |
| `explosion_particle_effect_on_ground` | 地面爆炸粒子 |
| `fuse_distance_from_target` | 距目标引信距离 |
| `fuse_fixed_time` | 固定引信时间；`-1` 常用 |
| `explosion_audio` | 爆炸音效 |
| `contact_phase_effect` | 爆炸接触 phase |
| `ignition_amount` / `is_magical` | 点燃/魔法 |
| `camera_shake` | 镜头震动 |
| `detonation_force` | 爆炸击退力 |
| `affects_allies` | 伤友军 |
| `is_spell` | 法术爆炸 |

### 6.3 `projectile_shrapnels_tables`

| 字段 | 含义 |
|------|------|
| `key` | 破片配置 |
| `projectile` | 破片用的投射物 |
| `amount` | 数量 |
| `launch_type` | 如 `hemisphere` |
| `sector_angle` | 扇形角 |

### 6.4 `projectile_homing_params_tables`

| 字段 | 含义 |
|------|------|
| `key` | 追踪参数主键 |
| `lookahead_time` | 预判时间 |
| `max_target_angle_delta` | 最大转向角 |
| `start_time` | 开始追踪延迟 |
| `steering_coefficient` | 转向系数 |

### 6.5 `projectiles_scaling_damages_tables`

| 字段 | 含义 |
|------|------|
| `key` | 缩放配置 |
| `min/max_health_ratio` | 目标血量比例区间 |
| `min/max_damage_multiplier` | 对应伤害倍率 |

### 6.6 `projectile_displays_tables`

| 字段 | 含义 |
|------|------|
| `key` | 显示主键 |
| `display_model` | 模型 |
| `impact` / `launch_fx` / `trail_fx` / `stationary_fx` | 命中/发射/拖尾/静止特效 |
| `airborne_anim` / `landing_anim` | 空中/落地动画 |
| `tip_offset` | 弹尖偏移 |
| `trail_spin` | 拖尾旋转 |
| `launch_camera_shake` | 发射震屏 |
| `impact_bounce` / `impact_penetrate` / `impact_blood` 等 | 各材质命中变体 |
| `mirroring_start` / `mirroring_trail` | 镜像特效 |
| `scale` | 缩放 |

---

## 7. 轰炸：`projectile_bombardments*`

天降类法术：能力只负责点目标，弹幕由轰炸表生成投射物。

### `projectile_bombardments_tables`（版本 7）

| 字段 | 含义 |
|------|------|
| `bombardment_key` | 主键，被 `unit_special_abilities.bombardment` 引用 |
| `arrival_window` | 全部弹着落的时间窗（秒） |
| `num_projectiles` | 弹数 |
| `projectile_type` | → `projectiles.key`（伤害/弹道在投射物表） |
| `radius_spread` | 落点散布半径 |
| `start_time` | 开始延迟 |
| `launch_source` | → `projectile_bombardment_launch_sources` |
| `launch_vfx` | 发射特效 |
| `launch_height` | 生成高度 |
| `audio_type` | 音频类型 |
| `launch_height_underground` | 地下发射高度相关 |
| `randomise_launch` | `true`=在窗口内随机；`false`=均匀分割 |
| `deterministic_launch_cadence` | 确定性发射节奏 |

### `projectile_bombardment_launch_sources_tables`（原版自带说明）

| key | 含义 |
|-----|------|
| `above_activater` | 在施法者上方生成 |
| `above_target` | 在目标上方生成 |
| `activaters_entities` | 在施法者实体处生成（忽略 num shells） |
| `at_target` | 目标附近略上方 |
| `launch_and_explode` | 立即爆炸 |
| `off_map` | 从地图外沿射程偏移发射 |

---

## 8. 涡流 / 风系 / 吐息：`battle_vortexs*`

**注意拼写：`vortexs`（CA 原表名）。**  
风系、吐息、多数地面持续法术都是 vortex；创建后基本只按本表规则运行。

### 8.1 `battle_vortexs_tables`（版本 19）

| 字段 | 含义 |
|------|------|
| `vortex_key` | 主键 |
| `change_max_angle` | 每次转向最大角度；`0`=直线不转向；`360`=任意向 |
| `contact_effect` | 命中附加 phase |
| `damage` / `damage_ap` | 接触伤害/破甲 |
| `duration` | 存活时间（秒） |
| `expansion_speed` | 扩张速度（吐息/爆炸扩张用；负值收缩通常无效） |
| `start_radius` / `goal_radius` | 起始/目标半径 |
| `infinite_height` | 是否打到飞行单位（“无限高度”） |
| `move_change_freq` | 改变移动的频率（秒） |
| `movement_speed` | 移动速度；`0`=原地（暗影坑等） |
| `ignition_amount` / `is_magical` | 点燃/魔法 |
| `composite_scene` | 主特效 `.csc` 路径 |
| `composite_scene_blood` | 血腥版场景 |
| `composite_scene_group` | 场景组 |
| `detonation_force` | 击退力 |
| `launch_source` | → `battle_vortex_launch_sources` |
| `launch_source_offset` | 发射源偏移 |
| `building_collision` | → `battle_vortex_collision_responses` |
| `launch_vfx` | 发射特效 |
| `height_off_ground` | 离地高度（仅打飞行的风暴会用） |
| `delay` | 出现延迟 |
| `num_vortexes` | 同点生成多个 vortex（极强，慎用） |
| `delay_between_vortexes` | 多 vortex 间隔 |
| `affects_allies` / `affects_enemies` | 友伤/敌伤开关 |
| `is_spell` | 是否法术 vortex |
| `shape` | → `battle_vortex_shapes`：`circle` / `rectangle` / `arc`（**不可空**） |
| `start_height` / `goal_height` | 起始/目标高度 |
| `follow_target` | 是否跟随目标 |

### 8.2 `battle_vortex_launch_sources_tables`

| key | 含义 |
|-----|------|
| `activator_front` | 施法者正前方 |
| `target_centre` | 点选目标中心 |
| `target_near_edge` | 目标近边缘（若有） |

### 8.3 `battle_vortex_collision_responses_tables`

| key | 含义 |
|-----|------|
| `1.ignore` | 撞建筑继续走 |
| `2.expire` | 撞到即结束 |

### 8.4 `battle_vortex_shapes_tables`

仅 `shape` 列：`arc` / `circle` / `rectangle`。

### 8.5 Composite Scene 组

- `battle_vortex_composite_scene_groups_tables`：`group_id`、是否朝向目标、地面瞄准朝向  
- `battle_vortex_composite_scene_group_to_scenes_tables`：组内具体 scene

---

## 9. 学派 / 法术组：`special_ability_groups*`

### `special_ability_groups_tables`

| 字段 | 含义 |
|------|------|
| `ability_group` | 组 key（如 `wh2_dlc09_lore_nehekhara`） |
| `icon_path` | 学派图标 |
| `special_edition_mask` | 特典掩码 |
| `sort_order` | 排序 |
| `is_naval` | 是否海军 |
| `button_name` | UI 按钮名（如 `lore_nehekhara`） |
| `sound_event` | 点击音效 |
| `is_composite_group` | 是否复合组 |
| `unique_id` | 组唯一 ID |
| `sound_switch` | 音频 switch |
| `show_lore_icon` | 是否显示学派图标 |
| `colour_hex` | 学派色 |

### `special_ability_groups_to_unit_abilities_junctions_tables`

| 字段 | 含义 |
|------|------|
| `special_ability_groups` | 学派组 |
| `unit_special_abilities` | 能力 key |

把法术放进学派轮盘。通常 **只挂基础版**，不挂超载版。绑定法术可不进学派组。

---

## 10. 使用限制与强度

### 10.1 限制类 junction（结构均为 能力 + flag）

| 表 | 列 | 作用 |
|----|-----|------|
| `special_ability_to_invalid_usage_flags` | `invalid_usage_flag`, `special_ability` | **何时根本不能用**（攀爬、近战中、血量条件等） |
| `special_ability_to_invalid_target_flags` | `invalid_target`, `special_ability` | **不能选什么目标**（墙上、飞行中等） |
| `special_ability_to_auto_deactivate_flags` | `deactivate_flag`, `special_ability` | 条件不满足时 **自动关闭**（被动居多） |
| `special_ability_to_recharge_contexts` | `recharge_context`, `special_ability` | **仅在某情境下冷却**（如仅近战中充能） |

flag 全集见 `special_ability_invalid_usage_flags_tables`（`engaged_in_melee`、`climbing`、`health_above_50%`、`flying_currently`…）。

### 10.2 强度：`special_ability_intensity_*`

用于“元素掌控”等按强度改变效果的法术。

**`special_ability_intensity_settings_tables`**

| 字段 | 含义 |
|------|------|
| `ability` | 能力 |
| `default_amount` / `max_amount` | 默认/最大强度 |
| `intensity_source` | → intensity sources |
| `intensity_type` | `set` / `linear_multiplier` / `inverse_linear_multiplier` |
| `intensity_decay_delay` / `intensity_decay_duration` | 衰减延迟/时长；`-1` 常表示不衰减 |
| `reset_intensity_in_reinforcement_pool` | 增援池是否重置 |

**常见 `intensity_source`：** `mastery_of_elemental_winds`、`all_wom_spent`、`time_in_melee`、`kills_made`、`damage_taken`、`enemies_in_range`、`harmony` 等。

### 10.3 行为组：`special_ability_behaviour_groups_tables`

`behaviour` 字段可选值示例：`summon`、`teleport_move`、`go_underground`、`waaagh`、`missile_mirror`、`vortex_on_death`、`changeling_transformation`…

### 10.4 Contact phase 组

`special_ability_contact_phase_groups_tables`：把多个 contact phase 归组，供武器/投射物引用。

---

## 11. AOE / 显示 / 音频

### `area_of_effect_displays_tables`

瞄准圈/范围预览：

| 字段 | 含义 |
|------|------|
| `key` | 被 `targetting_aoe` 等引用 |
| `decal` | 地面贴花 |
| `vfx_central` / `vfx_ring` | 中心/环特效 |
| `spline_animation_speed` / `spline_tile_count` | 样条动画 |
| `composite_scene` | 组合场景 |
| `is_targetting_per_entity` | 是否按实体瞄准 |
| `vfx_ring_segment_length` | 环段长度 |
| `use_model_time` | 使用模型时间 |
| `custom_spline` | 自定义样条 |
| `spawn_no_proxy` | 无代理生成 |
| `spline_col_hex` / `spline_oor_col_hex` | 样条颜色/超距颜色 |

### `special_ability_displays_tables`

| 字段 | 含义 |
|------|------|
| `sa_display_key` | 主键 |
| `wind_up_aura_vfx` | 前摇光环 VFX |
| `wind_up_weapon_vfx` | 前摇武器 VFX |

### `special_ability_phase_displays_tables`

| 字段 | 含义 |
|------|------|
| `key` | phase 显示 |
| `active_vfx` / `banner_vfx` / `entity_vfx` | 激活/旗帜/实体特效 |
| `entity_vfx_attach_type` | 挂点（如 `bottom`） |
| `use_new_vfx_scaling` | 新缩放 |

### `unit_abilities_additional_ui_effects_tables` + junction

技能面板额外说明条（**不改机制，只改文案**）。junction：`ability` + `effect`。

### 音频（简述）

| 表 | 用途 |
|----|------|
| `audio_abilities_tables` | 能力启用/禁用/瞄准/前摇等事件 |
| `audio_projectiles_tables` | 投射物飞行/命中/限制器 |
| `audio_ability_phases_tables` | phase 音频 |
| `audio_projectile_bombardments_tables` | 轰炸音频 |

---

## 12. 如何挂到单位 / 技能 / 军队

### 12.1 直接绑单位（绑定法术、内建能力）

`land_units_to_unit_abilites_junctions_tables`（注意原版拼写 `abilites`）：

| 字段 | 含义 |
|------|------|
| `ability` | 能力 key |
| `land_unit` | → `land_units.key` |

永久拥有；适合 Frenzy、绑定火球等。

### 12.2 战役技能解锁（标准法术）

1. `effects_tables` 建 effect  
2. `effect_bonus_value_unit_ability_junctions_tables`：

| 字段 | 含义 |
|------|------|
| `effect` | effect key |
| `bonus_value_id` | 如 `enable`、`recharge_mod`、`wom_cost_mod` 等 |
| `unit_ability` | 能力 key |

3. `character_skill_level_to_effects_junctions` 把 effect 挂到技能等级  

能力侧需 `requires_effect_enabling=true`。

### 12.3 给单位集合加能力

`unit_set` → `unit_set_unit_ability_junctions` → `effect_bonus_value_unit_set_unit_ability_junctions`。

### 12.4 军队能力

`army_special_abilities_tables`：

| 字段 | 含义 |
|------|------|
| `army_special_ability` | 军队技 key |
| `unit_special_ability` | 底层能力 |
| `unique_id` | 唯一 ID |
| `enables_siege_assault` | 是否开启强攻（如瓦尔之锤） |

再用 `effect_bonus_value_military_force_ability_junctions` 挂到建筑/派系/将军 effect。

### 12.5 道具授予

`ancillary_to_effects` → 带 ability 的 effect（同 12.2）。

---

## 13. 本地化

| Loc 键前缀 | 用途 |
|------------|------|
| `unit_abilities_onscreen_name_<key>` | 能力名称 |
| `unit_abilities_tooltip_text_<key>` | 能力说明 |
| `unit_abilities_additional_ui_effects_localised_text_<key>` | 额外 UI 条文本 |
| `special_ability_phases_*`（若有） | phase 相关文本（按原版 loc 对照） |

超载版是 **另一条** ability key，需要单独两行 name/tooltip。

---

## 14. 常见坑

1. **`unique_id` 冲突或不合法** → 能力点了没反应；保持全局唯一且位数别太长。  
2. **只改 `unit_abilities` 不改 `unit_special_abilities`** → 没有战斗实体。  
3. **投射物法术给没有施法动画的单位** → 可能瞬放并退还冷却/魔风；需配 `battle_personalities` / 动画，或改用 vortex/轰炸/phase。  
4. **群体单位挂投射物能力** → 每个实体都会放，伤害×人数。  
5. **军队技 `initial_recharge=0`** → 易异常，给短初始冷却。  
6. **`autoresolver_usage` 留空** → 可能崩溃（RPFM patch 警告）。  
7. **`battle_vortexs.shape` 留空** → 可能崩溃。  
8. **超载**：基础版 `overpower_option` 指向超载 key；两套 special_ability / projectile / vortex 都要齐。  
9. **phase DoT 不设 `max_damaged_entities`** → AOE 按实体数爆炸级放大。  
10. **抄原版再改** 远比从零填 70+ 列安全。

---

## 附录 A：火球数据链示例

| 环节 | key |
|------|-----|
| `unit_abilities` | `wh_main_spell_fire_fireball`（超载 → `..._upgraded`） |
| `unit_special_abilities` | 同 key；`activated_projectile=wh_main_spell_fire_fireball`；`mana_cost=5`；`ai_usage=projectile_homing_single` |
| `projectiles` | `wh_main_spell_fire_fireball` |
| 学派 | `special_ability_groups_to_unit_abilities` → 火焰系 lore 组 |
| 解锁 | effect `enable` + 角色技能树 |

---

## 附录 B：相关表速查（按用途）

| 用途 | 表 |
|------|-----|
| UI 定义 | `unit_abilities`、`unit_ability_types`、`unit_ability_source_types` |
| 战斗参数 | `unit_special_abilities` |
| Buff/Debuff | `special_ability_phases`、`*_stat_effects`、`*_attribute_effects`、phase junction |
| 飞弹 | `projectiles`、`projectiles_explosions`、`projectile_displays`、`projectile_homing_params`、`projectile_shrapnels` |
| 轰炸 | `projectile_bombardments`、`projectile_bombardment_launch_sources` |
| 涡流/风/吐息 | `battle_vortexs`、`battle_vortex_shapes`、`battle_vortex_launch_sources`、`battle_vortex_collision_responses` |
| 学派 | `special_ability_groups`、`special_ability_groups_to_unit_abilities_junctions` |
| 限制 | `special_ability_to_invalid_*`、`*_auto_deactivate_*`、`*_recharge_contexts` |
| 强度 | `special_ability_intensity_settings`、`*_sources`、`*_types` |
| 挂载 | `land_units_to_unit_abilites_junctions`、`effect_bonus_value_unit_ability_junctions`、`army_special_abilities` |
| UI 补充 | `unit_abilities_additional_ui_effects`、`area_of_effect_displays`、`special_ability_displays` |
| 魔风战役侧 | `_kv_winds_of_magic_params`、`winds_of_magic_battle_thresholds`、`campaign_map_winds_of_magic_*`（非单法术定义） |
| 魔法风暴 | `storm_of_magic_*`（灾变/飞升，另成体系） |

---

## 附录 C：参考来源

- 原版 TSV：`源码/db/`  
- Cryswar：[Creating and Editing Abilities](https://steamcommunity.com/sharedfiles/filedetails/?id=1698960734)（WH2 为主，字段逻辑大部分仍适用；WH3 新增列已在本文按原版表头补全）  
- RPFM：[rpfm-schemas patches](https://github.com/Frodo45127/rpfm-schemas)  
- 本仓库技能类整理：`战锤3原版法术类角色技能整理.md`（偏技能树，非战斗 DB 字段）  
- `spawn_is_*` 三字段：以原版 `unit_special_abilities_tables` 全表共现为准（诱饵 / 化龙诀 / 无形恐怖 / 扎坎 / 可怖巨口）

---

*文档生成说明：字段含义以原版用法 + 社区指南为主；个别极少使用的列（空值占绝大多数）标为“原版少用/按同类法术抄写”。游戏更新后以最新 `data__.tsv` 表头为准。*
