## Variant Selector 兼容（使用此依赖的项目）

- **当前作者项目要求所有新角色配置 Variant Selector；其他项目仅在设计或现有依赖要求接入时执行本节。** 新角色完成 DB 链后，必须在该 MOD 的 `marthvs/mod/` 下添加或更新注册 Lua，使用 `return { [subtype_key] = { art_set_id, ... } }` 注册角色的主 `art_set`。
- 单套外观也必须登记；这样 Variant Selector 能在模型刷新、读档重建或手动重新套用时明确恢复该角色的外观。不能因为“没有可切换的第二套外观”而跳过注册。
- 多套外观必须把全部可用 `art_set` 按稳定顺序登记，并额外检查每套外观的 `variants`、`agent_uniforms`、`campaign_character_art_sets`、`campaign_character_arts` 和对应的 `portrait_settings` 条目；需要跨会话保留选择时，同时提供该角色的持久化切换脚本。
- 验收以“每个新角色 subtype 都能在注册表找到，且每个注册的 art-set 在 DB 与 portrait settings 中有对应链”为完成条件；修改 Lua 后运行语法检查，再把该文件导入映射的源 Pack 并做 Error 诊断。

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
- **描述字段只写背景文本，禁止罗列机械数值**（见 [背景描述与机械效果](../../warhammer-mod-translation/references/description-fields.md)）。

## 多外观跨会话与头像

`marthvs/mod/<mod>.lua` 返回 `{ [subtype] = { art_set_1, art_set_2 } }`。保持 art-set 顺序稳定，删外观时迁移已保存索引，不能让旧索引指向另一套外观。

model override 不能当作自动持久化数据。接入目标 Variant Selector 的选择事件后保存选择；每次会话首 tick 恢复，对需要的 PendingBattle 等重建时机按当前实现重套。注册表、模型覆盖、portrait_settings 是三条独立链。

对所有 art-set 同时核对 portholes 与 units 的 `portrait_settings*.bin`：entry id、variant filename 和 file_diffuse 指向真实模型/PNG；克隆相机设置需取同槽位可靠基准。修改二进制时也先生成并验证本地源候选，再导入映射 Pack。RPFM 仅用于解码/编码的临时转换不能变成“先改生产 Pack 再回写源”。

Variant Selector 属于运行时 MOD 依赖，本包提供接线规范，不含第三方 MOD 本体。当前项目要求所有新角色登记，包括单套外观；移植到未使用它的项目时，先依据目标项目设计判断是否接入，不能擅自新增强制依赖。
