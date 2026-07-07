# 任务、事件、两难 DB 表（Mission / Incident / Dilemma 域）

这三类是 WH3 的"弹出事件"体系。**Incident（事件）**：单向通知（只有一个确定选项，或无选项）。**Dilemma（两难）**：多选一（每个选项不同后果）。**Mission（任务）**：有目标、可完成/失败、带奖励。

三者共享 `cdir_events_*` 载荷（payload）系统，把"奖励内容"（金钱/资源/效果捆绑/装备/单位）以结构化方式挂到事件/任务上。

## 核心数据流

```
incidents / dilemmas / missions  事件/两难/任务 主表
    └─ cdir_events_*_payloads        载荷（决定完成后给什么）
         ├─ cdir_events_*_option_junctions   选项（两难的多选项）
         └─ campaign_payload_ui_details     载荷在 UI 上的显示
```

---

## 三类主表

### `incidents_tables` — 事件主表
| 列 | 说明 |
|----|------|
| `key` | 事件 key（主键） |
| `generate` | 是否允许引擎自动生成（多数自定义事件设 false，由脚本触发） |
| `ui_image` | UI 图片 |
| `prioritised` | 是否优先显示（弹窗置顶） |
| `event_category` | 事件类别（如 `zhaos_will`） |
| `override_icon` | 覆盖图标 |
| `is_large_incident` | 是否大型事件（全屏） |
| `additional_sound_event` / `sepia_fade` / `use_revealing_text` | 音效/视觉 |

**触发**：Lua `cm:trigger_event(faction_key, incident_key)` 或 `cm:trigger_incident(...)`。

### `dilemmas_tables` — 两难主表（多选一）
| 列 | 说明 |
|----|------|
| `key` | 两难 key（主键） |
| `generate` / `prioritized` | 自动生成/优先 |
| `localised_title` / `localised_description` | 标题/描述（loc 占位） |
| `ui_image` / `override_icon` | UI 图 |
| `event_category` | 事件类别 |
| `sound_popup_override` / `sound_click_override` | 音效覆盖 |
| `is_large_dilemma` | 是否大型 |

**触发**：Lua `cm:trigger_dilemma(faction_key, dilemma_key)`。选项通过 `cdir_events_dilemma_option_junctions` + payload 实现。

### `missions_tables` — 任务主表
| 列 | 说明 |
|----|------|
| `key` | 任务 key（主键） |
| `mission_type` | 任务类型（如 `DESTROY_FACTION`/`KILL_CHARACTER`/`CAPTURE_REGIONS`/脚本目标） |
| `localised_title` / `localised_description` / `localised_mission_completed_text` | 标题/描述/完成文本（loc 占位） |
| `ui_image` / `ui_icon` | UI 图 |
| `generate` / `prioritised` | 自动/优先 |
| `event_category` | 类别 |
| `set_piece_battle` | 关联的剧本战 |
| `location_x` / `location_y` | 地图位置 |
| `quest_mission` / `quest_mission_final` | 是否任务线/最终任务 |
| `trigger_radius` | 触发半径 |
| `quest_character` | 任务角色 |
| `sticky_by_default` | 是否默认常驻 |
| `can_be_manually_cancelled` | 是否可手动取消 |

**触发**：Lua 通过 `mission_manager:new(faction_key, mission_key)` 构造，或 `cm:trigger_mission(...)`。

---

## 载荷系统（cdir_events_*_payloads）

载荷（payload）定义"事件/任务完成后给玩家什么"。三类事件各有自己的 payload 表，但结构一致。

### `cdir_events_incident_payloads_tables` — 事件载荷
| 列 | 说明 |
|----|------|
| `id` | 主键（数字） |
| `incident_key` | → `incidents_tables.key` |
| `payload_key` | 载荷内容（见下方"载荷 key 语法"） |
| `value` | 数值 |
| `target_key` | 目标 key |

### `cdir_events_dilemma_payloads_tables` — 两难载荷
| 列 | 说明 |
|----|------|
| `id` | 主键 |
| `choice_key` | 选项 key（决定哪个选项给这个载荷） |
| `dilemma_key` | → `dilemmas_tables.key` |
| `payload_key` / `value` / `target_key` | 同上 |

⚠️ 两难载荷必须绑定 `choice_key`，否则选项无奖励。

### `cdir_events_mission_payloads_tables` — 任务载荷
| 列 | 说明 |
|----|------|
| `id` | 主键 |
| `mission_key` | → `missions_tables.key` |
| `payload_key` | 载荷内容 |
| `status_key` | 状态（如完成/失败时发放） |
| `value` / `target_key` | 数值/目标 |

---

### 载荷 key（payload_key）语法

`payload_key` 是字符串，描述发放内容。常见格式：

| payload_key 格式 | 含义 |
|-----------------|------|
| `money <N>` | 发放金钱 N |
| `faction_pooled_resource_transaction{resource <R>;factor <F>;amount <N>;context absolute;}` | 池资源交易 |
| `effect_bundle{bundle_key <K>;turns <T>;}` | 效果捆绑（T=0 永久） |
| `add_ancillary_to_faction_pool{ancillary_key <K>;}` | 装备入派系池 |
| `text_display <DUMMY_KEY>` | **纯文本展示**（不实际发放，仅 UI 显示，需配合 Lua 单独发放） |

⚠️ **`text_display` 是关键坑点**：用 `text_display` 只在 UI 上展示"奖励：3件神器"，但**不会实际发放**。实际发放必须由 Lua 监听 `MissionSucceeded` 后调用 `cm:add_ancillary_to_faction` 等。`天廷诸军` MOD 的 `dummy_wyccc_cth_army_reward_3_artifacts` 即此模式。

---

## 选项系统（仅两难）

### `cdir_events_dilemma_option_junctions_tables` — 两难选项
| 列 | 说明 |
|----|------|
| `id` | 主键 |
| `dilemma_key` | 两难 |
| `option_key` | 选项 key（对应 payload 的 choice_key） |
| `value` / `target` | 值/目标 |

### `cdir_events_dilemma_choice_details_tables` — 选项详情
| 列 | 说明 |
|----|------|
| `choice_key` / `dilemma_key` | 选项/两难 |
| `audio_event_hover` / `audio_choice_vo` | 悬停/选择音效 |

### `cdir_events_incident_option_junctions_tables` / `cdir_events_mission_option_junctions_tables`
事件/任务的选项（事件通常单选项，任务多数无选项）。

---

## 事件类别与发布者

### `cdir_events_categories_tables` — 事件类别（仅一列）
| 列 | 说明 |
|----|------|
| `category_key` | 类别 key（如 `zhaos_will`、`random`） |

**用途**：事件/任务归类，用于 UI 过滤、脚本 `faction:active_missions(category)` 检索。

### `cdir_events_mission_issuer_junctions_tables` — 任务发布者绑定
| 列 | 说明 |
|----|------|
| `issuer_key` | 发布者（如 `CLAN_ELDERS` 长老、`PROVINCE` 行省） |
| `mission_key` | → `missions_tables.key` |

**用途**：定义任务的"发布来源"（影响 UI 显示谁给的任务）。

---

## UI 详情

### `campaign_payload_ui_details_tables` — 载荷 UI 详情
| 列 | 说明 |
|----|------|
| `component` | 组件 key（通常是 `text_display` 的 dummy key） |
| `icon` | 图标路径 |
| `state` | 状态（`positive`/`negative`） |
| `sort_order` | 排序 |

**用途**：让 `text_display` 类载荷在任务奖励 UI 上有图标和排序。`天廷诸军` 用此表给 `dummy_wyccc_cth_army_reward_*` 配图标。

### `event_feed_strings_tables` — 事件提要字符串（仅 key）
| 列 | 说明 |
|----|------|
| `key` | 主键 |

**用途**：事件提要（侧边栏通知）的文本 key 注册。

---

## 索泰克预言（特殊任务链）

### `prophecy_of_sotek_stages_tables` — 预言阶段
| 列 | 说明 |
|----|------|
| `stage` / `effect_bundle` / `order` / `tooltip_type` | 阶段/效果捆绑/顺序/提示类型 |

### `prophecy_of_sotek_stages_to_missions_tables` — 预言阶段 ↔ 任务
| 列 | 说明 |
|----|------|
| `stage` / `mission` / `order` | 阶段/任务/顺序 |

### `sotek_tooltip_types_tables` — 索泰克提示类型（仅一列 type）

> 这是蜥蜴人"索泰克预言"任务线的专用表组，通用 MOD 一般不涉及。

---

## 其他

### `twad_key_deletes_tables` — key 删除声明（仅用于全量替换删除）
| 列 | 说明 |
|----|------|
| （字段视引擎版本） | 声明要删除的原版 key |

**用途**：配合 `data__.tsv` 全量替换时，声明从原版表中删除哪些行。

---

## 版本参考
| 表名 | 原版版本 |
|------|---------|
| `incidents_tables` | 7 |
| `cdir_events_incident_payloads_tables` | 2 |

## 相关参考
- 效果捆绑（`effect_bundle{...}` 载荷）：[effects_and_bundles.md](effects_and_bundles.md)
- 装备（`add_ancillary_to_faction_pool` 载荷）：[ancillaries_and_traits.md](ancillaries_and_traits.md)
- 池资源（`faction_pooled_resource_transaction` 载荷）：[pooled_resources.md](pooled_resources.md)
- `text_display` 坑点实战：天廷诸军 `wyccc_cth_army_zhao_goals.lua` 的 `grant_zhao_goal_artifact_reward`
