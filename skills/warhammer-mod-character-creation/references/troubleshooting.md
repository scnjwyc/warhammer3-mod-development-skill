## 常见问题

### 英雄「无法入队／角色面板属性区为空」——运行时 UnitDetails 绑定或嵌入资格错误

**症状**：角色能在大地图出现，点击后姓名、背景描述、头像等内容正常，但角色面板的属性/单位详情区域为空，角色不能加入军队；这不是面板 UI 打不开。姓名和描述正常只说明 agent、外观和本地化链部分成功，**不代表角色已经解析出可嵌入军队的 UnitDetails**。

**排查顺序**：先做 DB 静态链，再做运行时 CCO 诊断，最后才检查招募脚本。每一步都拿一个同文化、同类型且能正常入队的现有英雄做逐字段对照，不能只看 subtype 名称或 portrait。

1. **单位主链**：
   - `agent_subtypes_tables.associated_unit_override` 必须指向有效的 `main_units_tables.unit`；
   - 该 `main_units` 的 `land_unit` 必须命中有效的 `land_units_tables.key`，且 `main_units.caste=hero`；
   - `land_units` 的 `attribute_group` 必须在 `unit_attributes_groups_tables` 存在，属性 junction 只使用原版 `unit_attributes` key；
   - `unit_variants_tables`、`unit_set_to_unit_junctions_tables`、`units_to_groupings_military_permissions_tables` 必须有该步行单位行，并照抄正常英雄的 `cth_all`/`wh3_main_cth` 分组与权限配置。缺分组或权限时，单位可能能生成，但不能被嵌入军队。
2. **角色身份链**：核对 `campaign_to_agent_subtypes_tables` 的目标战役行、`faction_agent_permitted_subtypes_tables` 的派系全量行，以及 `agent_subtypes_tables` 的 `associated_unit_override`、`recruitment_category`、`recruitable`、`show_in_ui`、`can_equip_ancillaries`。英雄的 `agent` 必须与现有同类英雄一致（通常是 `champion`、`wizard` 或 `spy`），不能因为角色是近战英雄就随意改 agent 类型；`show_in_ui=false` 也应优先视为异常配置。
3. **若使用唯一英雄接口**：`unique_agents_tables`、`campaign_group_unique_agents_tables`、`unique_agent_component_junctions_tables` 三表必须同时存在，且 `unique_agents.agent_type` 与 `faction_agent_permitted_subtypes_tables.agent`、脚本中的 `entry.agent_type` 三者一致。非唯一英雄不要调用 `cm:spawn_unique_agent_at_character`。

**运行时判定（最有价值的证据）**：在 `CharacterSelected` 之后延迟调用 `CcoCampaignCharacter`，记录以下值：

```lua
AgentSubtypeRecordContext.Key
AgentSubtypeRecordContext.AssociatedUnitOverride.Key
UnitDetailsContext.UnitRecordContext.Key
CanBeEmbedded
```

正常结果应满足：`subtype` 是目标角色 key；`associated_unit` 是预期的 `main_units.unit`；`unit_details` 非空且与该单位一致；`can_be_embedded=true`。如果角色姓名/描述正常但 `unit_details` 为空、指向别的单位或 `can_be_embedded=false`，继续查 DB 单位链、分组权限和唯一英雄链，不要先改 UI。

**招募/发放脚本核对**：

- `cm:spawn_agent_at_position(faction, x, y, agent_type, subtype)` 的 `agent_type` 必须等于 DB 派系许可中的 `agent`，最后一个参数必须是完整的 `agent_subtype` key；
- `cm:spawn_unique_agent_at_character` 只能用于已经在三张 `unique_agents` 表注册的英雄，传入的 subtype、agent type 和目标派系必须能在 DB 中互相对应；
- `cm:create_force_with_general` 只用于领主/将军路径，英雄不要套用 `general` 参数；
- 脚本中的 `art_set`、改名、升级、行动点恢复都发生在角色创建之后，不能修复 UnitDetails 绑定；`CharacterCreated` 只证明角色被创建，不证明角色可入队；
- 监听 `CharacterCreated` 时应记录 `character:character_subtype_key()`，并与 `entry.key` 精确比较。若日志没有创建事件，查 spawn 参数/unique 注册；若创建事件有但 CCO 绑定异常，查 DB；若 CCO 正常仍不能入队，再查派系许可和单位分组权限。

**避免重复误判**：不要把“角色面板能打开”当成 UI 故障，也不要只补 `faction_agent_permitted_subtypes` 或只改招募接口。必须完成“静态单位链 → 运行时 `UnitDetailsContext`/`CanBeEmbedded` → 脚本参数 → 派系入队权限”的闭环，并保留一份正常角色与故障角色的逐字段差异记录。

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

### 坐骑技能「毫无效果／不显示解锁坐骑」——缺 enable_mount 效果行或升级条件行

**症状**：技能树里的坐骑技能（战马、玉龙马、玉麒麟、机械骏马、雷霆飞艇等）点开后效果栏空白或没有「解锁坐骑：XXX」，实际也无法获取该坐骑；同一 MOD 里其他角色正常，唯独某组角色失效。

**根因**：坐骑链缺最容易漏的两行——
1. `character_skill_level_to_effects_junctions_tables` 缺 `wh_*_effect_enable_mount_<坐骑>` 效果行：「解锁坐骑：XXX」文案来自这些 effect 的 loc 描述；
2. `character_skills_to_level_reached_criterias_tables` 缺坐骑技能的行：技能没有升级条件，永远不会生效。

技能节点、node_set、`character_skill_level_to_ancillaries_junctions`、ancillaries 各表齐全时最易误判发放链没问题（无双英灵录实例：貂蝉/黄月英/关银屏/吉尔四角色的坐骑技能即因此无效）。

**修复**：
- 效果行：`<坐骑技能key>` → `wh_*_effect_enable_mount_<坐骑>`（`character_to_character_own`、value 1），effect key 与 `ancillaries_tables` 的 `type`（`wh_main_anc_mount_<坐骑>`）一一对应，如 `wh_main_effect_enable_mount_warhorse`、`wh3_main_effect_enable_mount_jade_longma`、`wh3_dlc24_effect_enable_mount_celestial_lion`、`wh3_dlc25_effect_enable_mount_mechanical_steed`、`wh3_dlc25_effect_enable_mount_steam_tank`。
- 条件行：`<坐骑技能key>` + 等级 + 1，等级与 `character_skill_level_details_tables` 的 `unlocked_at_rank` 一致（战马/机械骏马 8，玉龙马/玉麒麟/雷霆飞艇 18）。
- loc 用原版效果键即可（中文文案齐全），无需自建。

**排查方法**：把坐骑技能 key 分别 grep 这两张表，无命中即缺。

### 载具坐骑「战役进战斗乘员全变成角色本人」——非 captain 乘员没建 autonomous_rider_hero=false 副本

**症状**：自定义战斗正常；战役进战斗乘员大部分/全部变成角色本人；战役大地图坐骑模型正常。

**根因**：引擎把 agent uniform 套到所有 `autonomous_rider_hero=true` 的乘员上；原版载具（如飞艇）22 个乘员 true，直接复用则全员变角色本人。`campaign_mounts_tables` 只决定战役大地图模型，不决定战斗乘员；自定义战斗不走 uniform 链所以正常，不能据此排除问题。

**修复**：非 captain 乘员全部建 MOD 前缀的 `battle_personalities` 副本（其他字段照抄原版），置 `autonomous_rider_hero=false`，只留 captain 为 true（如飞艇 1 true + 28 false）；junction 表切到新 key，挂点/布局列不变。参照：原版蒸汽坦克只有工程师 true；坐骑合集幽灵工程师飞艇 1 true + 28 false。

**排查方法**：统计 junction 选出的乘员 personality 中 `autonomous_rider_hero=true` 的数量，载具坐骑应恰为 1；若为原版载具的 N（如 22），即踩坑。

本文中的运行时检查由用户启动游戏并提供日志；Agent 只准备诊断和分析已有输出。
