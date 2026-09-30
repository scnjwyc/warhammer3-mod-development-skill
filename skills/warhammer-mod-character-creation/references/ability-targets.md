# 能力目标模板

### 能力目标模板（常见踩坑，先对照设计稿确认技能作用对象，再套模板）

设计稿写"只对自己生效""以自身为中心强化友军"等字样时，**是否弹选择目标光标由 `unit_special_abilities` 的 `target_friends/target_enemies/target_ground/target_self` 决定**，与 `unit_abilities.type`、phase junction 无关。junction 的三布尔只控制 phase 施加给谁，不影响是否选目标。两种免选目标模板均取自原版，逐字段照抄：

**模板 A：瞬发自身增益**（原版基准：致命突袭 `wh_main_character_abilities_deadly_onslaught`、信仰壁垒 `wh_main_hero_abilities_faiths_bastion`）

| 字段 | 值 | 说明 |
|---|---|---|
| `affect_self` | `true` | "作用于自身"靠它表达 |
| `target_self` / `target_friends` / `target_enemies` / `target_ground` | 全 `false` | **注意：`target_self=true` 反而会弹出选取目标的光标**，这是最常见的错误 |
| `num_effected_friendly_units` / `num_effected_enemy_units` | `0` / `0` | 非 0 会让技能 UI 多出"受影响部队"行；纯自身增益必须为 0（早期文档"自增益必须 >=1"的说法有误，已更正） |
| `effect_range` / `target_intercept_range` | `0.0000` | |
| `targetting_aoe` | `wh_abilities_generic_buff_no_ring` | 自身技能不画范围圈 |
| `unit_abilities.type` | `wh_type_augment` | |
| `autoresolver_usage` | `buff_self` | |
| junction | `target_self=true`，其余 false | phase 只施加给自己 |

**模板 B：自身中心范围友军增益**（原版基准：`wh_main_character_abilities_rally`、昊天将军 `wh3_dlc24_lord_abilities_lord_of_grand_cathay`）

| 字段 | 值 | 说明 |
|---|---|---|
| `affect_self` | `true`；`target_*` 全 `false` | 点击即生效，不选目标 |
| `num_effected_friendly_units` | `-1` | 范围内友军不限数量；**写 1 会导致范围内只 buff 到一个友军** |
| `effect_range` | 半径（米）；全屏用 `-1.0000` | |
| `targetting_aoe` | `wh_abilities_generic_buff`；全屏范围用 `wh_abilities_generic_buff_no_ring` | |
| `unit_abilities.type` | `wh_type_area_of_augments` | |
| `autoresolver_usage` | `buff_unit` | |
| junction | `target_self=true, target_friends=true` | 自身与范围内友军都吃到 phase |

**从其他角色/技能克隆 ability 行时的"身份字段"清单**——克隆来的行带着源技能的定位，增益技能若漏改会显示成减益/爆炸且要求选目标。必须逐项覆盖或核对：

- `unit_abilities.type`：`wh_type_hex`/`wh_type_explosion` → `wh_type_augment`/`wh_type_area_of_augments`
- `targetting_aoe`：`wh_abilities_generic_debuff`/`wh_abilities_generic_explosion` → `wh_abilities_generic_buff`（或 `_no_ring`）
- `autoresolver_usage`：`debuff_unit`/`damage_aoe` → `buff_self`/`buff_unit`
- `num_effected_enemy_units`、`target_intercept_range`：按模板清零
- `unit_abilities_to_additional_ui_effects_juncs_tables`：**UI 词条就是这张表的行**；源技能残留的词条（如爆炸误伤 `wh2_main_spell_friendly_fire_explosion`、反大不佳 `wh_main_all_poor_vs_large`）与增益无关，必须整行删除，不要只改 ability 表
- `miscast_global_bonus`：原版增益类普遍为 `true`，含义与失误无关，不要想当然改 `false`

**生成器/批量脚本注意**：后处理（如"自增益 `num_effected_friendly_units` 强制 >=1"这类钳制）会悄悄覆盖显式配置。改字段后如果产出值不对，先全局搜该字段名，确认没有后处理回改；确需豁免时在脚本里显式列出豁免 key 并注释原版依据（无双英灵录实例：`PURE_SELF_BUFF_ABILITIES`）。

模板来自历史原版基准；使用前在当前游戏中核对完整行、phase、AI 和自动战斗引用。
