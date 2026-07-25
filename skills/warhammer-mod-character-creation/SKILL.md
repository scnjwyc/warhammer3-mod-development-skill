---
name: warhammer-mod-character-creation
description: "全面战争：战锤3 MOD 新建传奇领主/英雄角色的通用流程与检查清单。涵盖设计稿确认（无设计稿时向玩家提问）、DB 表全量清单（单位链/身份链/技能树/能力链/坐骑/装备）、命名与 ID 分配调查方法、战役动作骨骼匹配、美术与本地化清单、验收。触发词：新建角色、创建角色、新领主、新英雄、加人物、新角色、传奇领主、传奇英雄、character creation"
---

# 战锤3 MOD 角色创建指南

本技能描述在任意战锤3 MOD 中新建一个传奇领主/英雄所需的**全部工作项**，不绑定特定 MOD。
配套技能：DB 表结构/TSV 格式/Lua 规范见 `warhammer-mod-development`；图标/兵牌/立绘/porthole 绘制见 `warhammer-mod-art`；本地化写入与术语见 `warhammer-mod-translation`。
文中以 `mod/无双英灵录/`（前缀 `wyccc`）的实现作为参考实例，仅用于说明"目标 MOD 现有角色长什么样"，**不构成强制约定**。

## 总流程

1. **确认设计依据**（见下节）。
2. **调查目标 MOD 现状**：现有角色的 key 前缀、命名规律、ID 分配段、文化/派系列表、动作骨骼用法——新角色的一切"约定"以该 MOD 现有实现为准。
3. 按"DB 全量清单"逐表创建/追加 TSV。
4. 配战役动作链（骨骼匹配，硬性规则见下）。
5. 配美术资源与本地化。
6. 需要时写脚本（开局发放、战斗机制）。
7. 按文末"验收清单"逐项核对；改完汇报文件清单，**不打包 pack**。

## 确认设计依据（第一步，必须做）

- **有设计稿**：在 MOD 目录找到该角色的设计文档时，**设计稿写什么就做什么，不擅自增减**。设计稿没有规定的内容（如某个具体字段值、某张表），再参照同类原版角色或该 MOD 现有角色补齐，并在汇报中说明哪些是设计稿外的补充。设计稿与引擎/DB 硬性规则冲突时（如跨骨骼动作、自定义 unit_attributes），指出冲突并按规则实现，同时告知用户。
- **没有设计稿**：不要凭想象开工，先向玩家问清关键决策，至少包括：
  - 领主还是英雄？属于哪个派系/文化（决定 faction_agent_permitted、黄线、海战 uniform 等）？
  - 角色定位：近战/法师/远程？法师的话用哪个法系？
  - 模型与骨骼：用哪个模型（自制或复用原版）？骨骼类型（hu1/hu1e/hu1b…）？
  - 武器与战斗动作（决定 `man_animation`）？
  - 需要几个主动/被动技能、什么效果？有没有 DB 表达不了、需要脚本的效果？
  - 有没有坐骑、几个、分别是什么？
  - 有没有专属装备？
  - 技能树：个人线节点、解锁等级、是否引用该 MOD 的共享红/黄线与"垃圾桶"技能？
  - 是否需要开局发放（脚本注入战役）？

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

### 角色身份链（必选）

| 表 | 主键 | 要点 |
|---|---|---|
| `agent_subtypes_tables` | `key` | `is_caster`、`associated_unit_override`→main_unit、`recruitment_category`（领主=`legendary_lords`）、`can_equip_ancillaries` |
| `campaign_character_art_sets_tables` | `art_set_id` | **含备用服装在内的全部 art set 都要登记** |
| `campaign_character_arts_tables` | 数字 id | `uniform`、`land_animation`（骨骼匹配）、海战 uniform/动画照抄同文化原版角色 |
| `campaign_to_agent_subtypes_tables` | subtype+campaign | 如 `wh3_main_combi` |
| `faction_agent_permitted_subtypes_tables` | agent+faction+subtype | **该文化全派系列表逐行登记**，照抄目标 MOD 现有同文化角色改 subtype |
| `names_tables` | 数字 id | 名字组、forename/surname、性别 |
| `unique_agents_tables` + `campaign_group_unique_agents_tables` + `unique_agent_component_junctions_tables` | — | **仅英雄**（全图唯一英雄）；领主不要 |

### 技能树链（必选）

`character_skill_node_sets_tables` → `character_skill_nodes_tables`（`indent/tier` 控制 UI 位置；背景特性 `points_on_creation=1,visible_in_ui=false`）→ `character_skill_node_links_tables`（`REQUIRED` / `SUBSET_REQUIRED` 前置关系）→ `character_skill_node_set_items_tables`（个人线 + 法术线 + 红/黄线全部挂进 set）→ `character_skills_tables`（`image_path`、`is_background_skill`）→ `character_skill_level_to_effects_junctions_tables`（注意 `effect_scope`）→ `character_skill_level_details_tables`（`unlocked_at_rank` 对应设计解锁等级）→ `character_skill_utilization_hints_junctions_tables`。

### 能力链（每个主动/被动/法术能力逐条落地）

`unit_abilities_tables`（`icon_name` 不带 .png、`requires_effect_enabling`）→ `unit_special_abilities_tables`（`unique_id` 在目标 MOD 未占用的新段分配；**自增益必须 `affect_self=true`、`num_effected_friendly_units>=1` 且 `only_affect_target=false`**——原版所有 `affect_self=true` 的行 `only_affect_target` 均为 false；地面目标类能力的"目标"是位置，`only_affect_target=true` 会导致自增益 phase 无人可施加；`vortex`/`spawned_unit`/`miscast` 按需）→ `special_ability_phases_tables`（对敌/对己拆正负 phase）→ `special_ability_to_special_ability_phase_junctions_tables`（`target_self/target_friends/target_enemies` 三布尔）→ `special_ability_phase_stat_effects_tables` / `special_ability_phase_attribute_effects_tables` → `special_ability_to_invalid_target_flags_tables` / `..._invalid_usage_flags` / `..._auto_deactivate_flags` → `battle_vortexs_tables`（可选）→ `land_units_to_unit_abilites_junctions_tables`（挂载）→ 效果侧 `effects_tables` + `effect_bonus_value_unit_ability_junctions_tables`（法术标准链：enable / overcast / cooldown / wom_cost / miscast）。法术字段详见仓库根目录《战锤3法术相关DB字段说明.md》。

### 坐骑链（可选）

- 单位：坐骑 `land_units`（`mount` 填原版坐骑 key、`man_animation` 用**骑手**动作、血量按设计倍率）、`main_units`（`mount` 列填战役镜头 `wh3_main_cam_mnt_*`）、`unit_variants`（variant 指骑马形态 `*_mounted`）、`battle_personalities_tables` + `land_units_to_battle_personalities_junctions_tables`（挂点 `ap_riderposition_0`/`ap_saddle_rider_00`）、abilities/unit_set/attributes/permissions 同单位链。
- 战役：`units_custom_battle_mounts_tables`（`base_unit`→`mounted_unit`）、`campaign_mount_animation_set_overrides_tables`（见下）。
- 发放：坐骑技能节点 + `character_skill_level_to_ancillaries_junctions_tables` + `ancillaries_tables`（`provided_bodyguard_unit` 指坐骑 land_unit）+ `ancillary_info_tables` + `ancillaries_included_agent_subtypes_tables`（**别漏行**）+ `ancillaries_required_skills_tables`。

### 装备链（可选）

`ancillaries_tables`（`immortal=true`、`randomly_dropped=false`；注意各装备槽数量限制，如同类法系装备要分到不同槽）+ `ancillary_info_tables` + `ancillaries_included_agent_subtypes_tables` + `ancillary_to_effects_tables` + 技能侧（skills/nodes/set_items/level_details/`character_skill_level_to_ancillaries_junctions`，skill key = ancillary key）+ `ancillaries_required_skills_tables`。

## 命名与 ID 调查方法（不假设，先查）

新角色的命名与数字 ID 一律先调查目标 MOD 再分配：

- **key 前缀**：看现有角色文件名与 unit key（如 `wyccc_lord_*`），沿用之。
- **art_set_id / uniform / variant 命名**：照现有角色的模式；variant_filename 对应 `variantmeshes/variantmeshdefinitions/<名>.variantmeshdefinition`。
- **数字 ID**（`campaign_character_arts.id`、`unit_special_abilities.unique_id`、`names_tables.id`、`unit_variants_colours.key` 等）：grep 现有文件找出已用段，**取未占用的新段**，并复查无跨文件撞号。
- **loc 键**：由「表前缀 + 完整 key」拼成，见 `warhammer-mod-translation`。

## 战役动作链（硬性规则）

- 三项必须同骨骼：`campaign_character_arts_tables.land_animation`、模型实际骨骼、`campaign_mount_animation_set_overrides_tables` 的 `character_animation_set`/`rider_animation_set`。**跨骨骼 = 大地图摆大字**。
- 骨骼前缀必须一致（hu1 模型只用 `cam_hu1_*`，hu1e 只用 `cam_hu1e_*`）；可用的 `cam_*` 键以原版 `源码/db/campaign_character_arts_tables/data__.tsv` 与 `campaign_mount_animation_set_overrides_tables/data__.tsv` 中出现的为准，**不得自创键名**（不存在的键会直接摆大字）。
- 常见基准：hu1 双手剑女性 = 赫潘丝 `cam_lord_hu1_dlc14_repanse_2handed_sword`（战马骑手 `cam_hu1_dlc14_hr1_warhorse_repanse_2handed_sword`）；hu1e 女法师 = `cam_hu1e_hr1_mage_female_hero`。
- 战斗侧 `land_units.man_animation` / `battle_personalities.man_animations_table` 引用 `battle_animations_table.key`，是**独立键域**，不能由 `cam_*` 删前缀推导；改前必须查 `源码/db/battle_animations_table_tables/data__.tsv`。
- 详细规则见 `warhammer-mod-development` 的"大地图与战斗骑手骨骼、动作匹配"章节。

## 美术与模型资源清单

- 模型链：`variants_tables.variant_filename` → variantmeshdefinition → `.wsmodel` → `.rigid_model_v2` + materials + 贴图。模型制作不在本技能范围。
- 每角色 PNG（绘制与验收规范见 `warhammer-mod-art`）：
  - `ui/units/icons/<key>.png` + `ui/portraits/units/no_culture/<key>.png`（60×130 兵牌，两处同步）
  - `ui/units/infopics/<key>.png`
  - `ui/portraits/portholes/no_culture/<key>.png`（尺寸量目标 MOD 同槽位参考图）+ portrait_settings 为**每个 art set** 登记映射
  - `ui/battle ui/ability_icons/`（主动 59×59 / 被动 38×38）与 `ui/campaign ui/skills/`（技能树图标）

## 本地化清单

每角色一个 loc 文件（三列 `key\ttext\ttooltip`）。常见键前缀：

- `land_units_onscreen_name_<key>`、`names_name_<id>`
- `agent_subtypes_onscreen_name_override_<key>`、`agent_subtypes_description_text_override_<key>`
- `unit_description_short_texts_text_<short_key>`
- 每技能：`character_skills_localised_name/description_<skill_key>` + `effects_description_<effect_key>`
- 每能力：`unit_abilities_onscreen_name/tooltip_text_<ability_key>` + `special_ability_phases_onscreen_name_<phase>`
- 装备：`ancillaries_onscreen_name/colour_text/explanation_text_<ancillary>`
- 坐骑：`units_custom_battle_mounts_mount_name_<base><mounted>`（两 key 无分隔拼接）+ `land_units_onscreen_name_<mount_unit>`
- **描述字段只写背景文本，禁止罗列机械数值**（见 `warhammer-mod-development` 的"描述规则"章节）。

## 过载技能命名规则（法术 overcast 规范）

法术类角色的技能若带超载（overcast）版本，**名称、effect 描述、effect 配置必须全部对齐原版规范**，否则会出现"名称带（超载）后缀""解锁超载的 effect 文案不对""正面效果显示成红字""effect 只显示文字无数值"等问题。以下规则逐条对照原版（如放逐之光 `wh_main_spell_light_banishment` / 再生术 `wh_dlc05_spell_life_regrowth`）。

### 1. 超载版 ability 命名：「高级」前缀，非「（超载）」后缀

- 超载版 ability 的屏幕名（`unit_abilities_onscreen_name_<ability_key>_upgraded`）统一用 **`高级<基础名>`**，**不要**写 `<基础名>（超载）`。
- 对照原版：`放逐之光` → `高级放逐之光`、`再生术` → `高级再生术`。
- DB 侧无需改动：基础版 `unit_abilities_tables.overpower_option` 指向 `<key>_upgraded` 即可，超载版 `icon_name` **复用基础版 key**（原版超载版无独立图标，不要造 `*_upgraded.png`）。

### 2. effect 描述文案：按 effect 类型套固定句式

一个法术 skill 在 `character_skill_level_to_effects_junctions_tables` 里通常挂 7 个 effect（分 2~3 级），每个 effect 的 loc 文案句式固定，**括号内的法术名随版本切换**（基础版用基础名、超载版用「高级XXX」）：

| effect 类型 | loc key 后缀 | 文案句式 | 数值占位符 |
|---|---|---|---|
| enable（解锁基础版） | `enable_<spell>` | `法术：『<基础名>』` | 无 |
| overcast（解锁超载版） | `overcast_<spell>` | **`增幅法术：『高级<基础名>』`** | 无 |
| cooldown（冷却速率） | `cooldown_<spell>` | `法术冷却时间：『<基础名>』` | `%+n%` |
| wom_cost（基础版消耗） | `wom_cost_<spell>` | `魔法之风消耗：『<基础名>』` | `%n` |
| wom_cost（超载版消耗） | `wom_cost_<spell>_upgraded` | `魔法之风消耗：『高级<基础名>』` | `%n` |
| miscast（超载版失误） | `miscast_<spell>_upgraded` | `施法失误概率：『高级<基础名>』` | `%+n%` |

**关键纠错点（常见误写）**：
- ❌ `允许超载施放：『XXX』` → ✅ `增幅法术：『高级XXX』`（这是 overcast 的原版标准写法）
- ❌ `XXX（超载）` → ✅ `高级XXX`（凡涉及超载版的 cost/miscast 描述，括号内一律用「高级XXX」）
- ❌ overcast 写成「允许超载」、enable 写成「增幅法术」（两者别搞反：enable=基础版解锁，overcast=超载版解锁）

### 3. effect 数值占位符：缺了就只显示文字、无数值

- cooldown / miscast 文案**末尾必须有 `%+n%`**（带符号百分比，显示如 `-30%`）。
- wom_cost 文案**末尾必须有 `%n`**（整数，显示如 `-2`）。
- enable / overcast 文案**不带占位符**（纯文本）。
- **漏写占位符 = 技能树里该 effect 显示文字但不显示数值**。占位符填什么数值由 `character_skill_level_to_effects_junctions_tables` 的 value 列决定，loc 里只负责放占位符。

### 4. effect 红绿颜色：`is_positive_value_good` 必须按类型设置

`effects_tables.is_positive_value_good`（第 6 列）决定 effect 文本颜色。规则：value 正负 × 该字段 → 正面（绿）/负面（红）。cooldown/wom_cost/miscast 的 value 都是负数（"减少"是好事），**必须设 `false`**（含义"负值才是好的"），否则负值被当成坏事显示成**红字**。

| effect 类型 | value | `is_positive_value_good` | 显示颜色 |
|---|---|---|---|
| enable / overcast | 正 | **true** | 绿 |
| cooldown（-30%/-50%） | 负 | **false** | 绿 |
| wom_cost（-2/-3） | 负 | **false** | 绿 |
| miscast（-15%） | 负 | **false** | 绿 |

**症状**：正面效果（冷却减少、消耗减少）却显示红色 → 检查 `effects_tables` 该 effect 的 `is_positive_value_good` 是否误设为 true。

### 5. 排查与修复流程（实战）

1. 找超载版 key：`unit_abilities_tables` 里基础版的 `overpower_option` 列指向 `<key>_upgraded`。
2. 查 loc 缺失：在角色 loc 文件搜 `<key>_upgraded`，应有 `unit_abilities_onscreen_name_*_upgraded` + 涉及超载版的 `wom_cost_*_upgraded` / `miscast_*_upgraded` 三类行。
3. 查 effect 配置：`effects_tables` 该角色文件里 cooldown/wom_cost/miscast 行的 `is_positive_value_good` 是否为 false。
4. 查占位符：cooldown/miscast 文案带 `%+n%`、wom_cost 带 `%n`。
5. 修改只动 loc 文案与 `effects_tables` 的 `is_positive_value_good` 列；DB 结构（overpower_option、junction、bonus_value）与图标无需改动。

**无双英灵录实例（已修复）**：女娲的补天之力/创世之光、妲己的荆棘领域/退箭领域，均经历了"补超载版 loc → 补占位符 → 名称改「高级XXX」+ overcast 改「增幅法术」→ is_positive_value_good 改 false"四轮修复。新建法术角色时按本节规则一次性配齐，避免重复踩坑。

## 脚本（按需）

- **开局发放**：仅当设计要求开局注入角色时，参照目标 MOD 现有发放脚本或原版 `cm:spawn_agent_at_position` / `cm:create_force_with_general` 模式。监听器必须在 `cm:add_first_tick_callback` 内注册；Lua 5.1（无 goto）；详见 `warhammer-mod-development`。
- **战斗脚本**：仅当 DB 表达不了效果时（血量互换、多段瞬移等），可用 Special Ability 指令监听 + phase 挂原版属性（如 stalk/unspottable）作标记捕获目标单位的模式。

## 常见问题

### 装备技能"效果栏空白"——unlock effect 缺少 loc 文本

**症状**：传奇领主/英雄通过"学技能获得装备"（`character_skill_level_to_ancillaries_junctions_tables`）发放的专属装备，技能节点本身**能正常显示在技能面板**（有名称和描述），但点开后**"效果栏"什么都没有**；而装备本身能正常获得、佩戴后属性加成也生效。表现为：同一 MOD 里有的角色装备技能效果栏正常（显示"获得专属装备：XXX"），有的角色却空白。

**根因**：装备技能在技能面板"效果栏"显示的内容，来自 `character_skill_level_to_effects_junctions_tables` 里绑定的 effect——这类装备技能通常绑一个 `wyccc_effect_unlock_<...>` 之类的占位 effect（value=1，无数值加成）。这个 effect 本身不提供属性，**它显示什么文字，完全由其 loc 描述键 `effects_description_<effect_key>` 决定**。如果该 loc 键缺失，效果栏就空白。

对照（无双英灵录实例）：
- 正常显示的亚迪安娜：`effects_description_wyccc_effect_unlock_lord_yadianna_weapon` = `获得专属装备：[[col:yellow]]『帕拉斯之剑』[[/col]]` ✅
- 空白的女娲：`wyccc_effect_unlock_lord_nvwa_arcane_item_2` 在 loc 里**没有对应 `effects_description_` 键** ❌

> 注意区分两条链：技能面板"效果栏"看 `character_skill_level_to_effects_junctions`（技能→effect）；装备佩戴后的实际属性加成看 `ancillary_to_effects_tables`（ancillary→effect）。后者齐全只代表"装备有效果"，不等于"技能面板效果栏有内容"。

**修复**：为缺失的 unlock effect 补 loc 文本。格式与同类装备技能一致：
```
effects_description_<unlock_effect_key>	获得专属装备：[[col:yellow]]『<装备中文名>』[[/col]]	true
```
装备中文名取自该装备的 `ancillaries_onscreen_name_<ancillary_key>` loc 键。补完后所有装备技能效果栏都会显示"获得专属装备：XXX"。

**排查方法**（定位是哪些装备缺 loc）：
1. 从 `character_skill_level_to_effects_junctions_tables` 提取所有装备技能绑定的 unlock effect key 列表（`grep "effect_unlock_" 该表`）。
2. 在 `text/db/` 下搜 `effects_description_<每个 unlock key>`，有匹配=已补，无匹配=缺失。
3. 对缺失项，按上面格式补 loc，装备名从 `ancillaries_onscreen_name_` 取。

**已踩的坑（避免重蹈）**：曾误判为 `character_skill_nodes_tables` 的 `tier` 过高导致节点不渲染，去改 tier——**无效**。tier/indent/node_links 与本问题无关；本问题纯粹是 unlock effect 的 loc 文本缺失。

## 验收清单

- [ ] 设计依据已确认：有设计稿则逐条对照实现，无设计稿则关键决策都经玩家确认。
- [ ] 所有 TSV 文件名/表头/版本/制表符/列数符合 `warhammer-mod-development` 的 TSV 规范。
- [ ] 命名与数字 ID 沿用目标 MOD 现有规律，且 grep 验证无撞号。
- [ ] `land_animation`、模型骨骼、坐骑覆盖三链骨骼前缀一致；所有 `cam_*` 键存在于原版表；战斗 `man_animation` 存在于 `battle_animations_table`。
- [ ] 自增益能力 `affect_self=true`、`num_effected_friendly_units>=1` 且 `only_affect_target=false`；junction 目标布尔与 phase 正负一致。
- [ ] 英雄有 unique_agents 三表（如需要全图唯一）；领主没有。
- [ ] 坐骑/装备的 `ancillaries_included_agent_subtypes_tables` 行已补齐。
- [ ] `unit_attributes` 只引用原版键。
- [ ] 兵牌两个槽位内容一致；porthole 的每个 art set 都有 portrait_settings 映射。
- [ ] 描述类 loc 字段无机械数值。
- [ ] 只改工作区源文件，**不打包 pack**；汇报改动文件清单请用户打包测试。
