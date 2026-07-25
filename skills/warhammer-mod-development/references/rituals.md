# 仪式 DB 表（Ritual 域）

**Ritual（仪式）**：派系主动施放的有冷却的强力动作（如"召唤恶魔""迁移首都""召集佣兵"）。仪式有类别、链、载荷（开始/完成/失败时给什么）、目标、施放角色等。

## 核心数据流

```
ritual_categories  仪式类别
    └─ ritual_category_groups      类别归组
    └─ rituals                     仪式主表（引用 category）
         ├─ ritual_payloads              载荷（start/completion 等）
         │    └─ ritual_payload_*        各类载荷内容（效果/资源/佣兵/传送）
         ├─ rituals_to_ritual_chains     仪式 → 仪式链（顺序解锁）
         └─ ritual_performing_characters  施放角色
```

---

## `rituals_tables` — 仪式主表（核心）
关键列：
| 列 | 说明 |
|----|------|
| `key` | 仪式 key（主键） |
| `category` | → `ritual_categories_tables.id` |
| `cast_time` | 施放回合数 |
| `completion_payload` | 完成载荷 → `ritual_payloads_tables.key` |
| `start_payload` | 开始载荷 |
| `self_payload` | 自身载荷 |
| `cooldown_time` / `global_cooldown_time` | 冷却/全局冷却 |
| `failure_cooldown_time` | 失败冷却 |
| `target` | 目标类型 |
| `required_resources` / `expended_resources` | 所需/消耗资源 → `resource_costs_tables` |
| `target_required_resources` / `target_expended_resources` | 目标所需/消耗资源 |
| `target_cooldown` / `target_category_cooldown` | 目标冷却/类别冷却 |
| `effects_while_performing` | 施放期间效果 → `effect_bundles_tables.key` |
| `custom_cost_id` | 自定义消耗 id |
| `flags` | 标志位 |
| `percentage_cost_increase_per_use` | 每次使用消耗递增百分比 |
| `sort_order` | UI 排序 |
| `influence_cost` | 影响力消耗 |
| `icon` | 图标 |

**关联**：被 `rituals_to_ritual_chains_tables.ritual`、`ritual_performing_character_junctions_tables.ritual`、`campaign_group_rituals_tables.ritual`、`effect_bonus_value_ritual_junctions_tables.ritual` 引用。

---

## 仪式类别

### `ritual_categories_tables` — 仪式类别
| 列 | 说明 |
|----|------|
| `id` | 主键，被 `rituals_tables.category` 引用 |
| `trigger_events` | 触发事件 |
| `needs_tracking` | 是否需追踪 |
| `refund_on_cancel` | 取消是否退款 |
| `active_cooldown_can_be_increased` | 激活冷却可否增加 |
| `group` | 归组 → `ritual_category_groups_tables.key` |
| `sort_order` / `ui_icon` | 排序/图标 |

### `ritual_category_groups_tables` — 仪式类别组（仅 key + sort_order）
| 列 | 说明 |
|----|------|
| `key` | 主键 |
| `sort_order` | 排序 |

---

## 仪式链（ritual chains）

### `ritual_chains_tables` — 仪式链
| 列 | 说明 |
|----|------|
| `key` | 主键 |
| `category` | 类别 |
| `ritual_sites_required` | 所需仪式地点 |
| `sort_order` | 排序 |
| `colour_hex` | 颜色 |

### `rituals_to_ritual_chains_tables` — 仪式 → 仪式链
| 列 | 说明 |
|----|------|
| `order` | 顺序 |
| `chain` | → `ritual_chains_tables.key` |
| `ritual` | → `rituals_tables.key` |

**用途**：把多个仪式排成一条按顺序解锁的链（前置完成后才能做下一个）。

---

## 载荷系统（ritual payloads）

### `ritual_payloads_tables` — 仪式载荷主表
| 列 | 说明 |
|----|------|
| `key` | 主键，被 `rituals_tables.completion_payload` 等引用 |
| `human_only` | 仅人类玩家 |
| `payload_base` | 载荷基础内容（字符串） |

### `ritual_payload_effect_bundles_tables` — 载荷 → 效果捆绑
| 列 | 说明 |
|----|------|
| `effect_bundle` | → `effect_bundles_tables.key` |
| `payload` | → `ritual_payloads_tables.key` |
| `duration` | 持续回合 |

### `ritual_payload_resource_transactions_tables` — 载荷 → 资源交易
| 列 | 说明 |
|----|------|
| `payload` | → `ritual_payloads_tables.key` |
| `transaction` | 交易内容 |
| `is_transfer` | 是否转移 |

### `ritual_payload_spawn_mercenaries_tables` — 载荷 → 生成佣兵
| 列 | 说明 |
|----|------|
| `id` | 主键 |
| `payload` | → `ritual_payloads_tables.key` |
| `spawnable_unit` | 可生成单位 |
| `add_mercenaries_to_performing_faction` | 是否加入施放派系佣兵池 |

### `ritual_payload_teleport_armies_tables` — 载荷 → 传送军队
| 列 | 说明 |
|----|------|
| `payload` | 载荷 |
| `region` | 目标区域 |
| `vicinity_radius` | 周围半径 |
| `teleport_same_faction_armies_only` | 仅同派系军队 |
| `teleport_only_to_sea` / `teleport_only_from_sea` | 仅传送至海/从海传 |
| `include_vassal_armies` | 含附庸军队 |

### `ritual_payload_add_foreign_slots_tables` — 载荷 → 增加外槽
| 列 | 说明 |
|----|------|
| `payload` | 载荷 |
| `slot_set` | → `slot_set_items_tables.slot_set` |

### `ritual_payload_change_unit_allowance_capacities_tables` — 载荷 → 改单位容量上限
| 列 | 说明 |
|----|------|
| `payload` | 载荷 |
| `unit_list` | → `unit_lists_tables.key` |
| `capacity` | 容量变化 |

---

## 施放角色

### `ritual_performing_characters_tables` — 施放角色定义
| 列 | 说明 |
|----|------|
| `key` | 主键 |
| `agent_subtype` / `agent_type` | 事务官子类型/类型 |
| `recovery_time` | 恢复时间 |
| `minimum_level` | 最低等级 |
| `effects_while_performing` | 施放期间效果 → `effect_bundles_tables.key` |

### `ritual_performing_character_junctions_tables` — 仪式 ↔ 施放角色
| 列 | 说明 |
|----|------|
| `character` | → `ritual_performing_characters_tables.key` |
| `ritual` | → `rituals_tables.key` |
| `amount` | 数量 |

---

## 目标与目标条件

### `ritual_targets_tables` — 仪式目标
（定义仪式可选的目标类型）

### `ritual_region_target_criterias_tables` — 区域目标条件
关键列：`require_foreign_slot_set_present`、`required_subculture`、`own`、`targets_ruins`、`require_walls_present`、`minimum_settlement_level`、`diplomacy_status`、`require_war_declaration_ability`、`targets_besieged`、`permitted_faction_set`、`is_human` 等。

**用途**：仪式施放时，对目标区域的一系列合法性校验条件。

---

## Lua 触发仪式

```lua
-- 让派系触发某仪式
cm:trigger_ritual(faction_key, ritual_key, ...)
```

⚠️ 多数仪式由玩家在 UI 主动施放，脚本触发较少。脚本触发时需确认仪式已解锁（冷却/前置满足）。

---

## 相关参考
- 效果捆绑（`completion_payload` → effect_bundle）：[effects_and_bundles.md](effects_and_bundles.md)
- 池资源（`expended_resources`）：[pooled_resources.md](pooled_resources.md)
- 单位列表（`unit_list` 容量）：[units_and_combat.md](units_and_combat.md)
- 战役组（仪式解锁通过 `campaign_group_rituals`）：[campaigns_payloads_mercenaries.md](campaigns_payloads_mercenaries.md)
