---
name: warhammer-mod-character-creation
description: "创建战锤3传奇领主/英雄，连接单位、身份、技能、能力、坐骑、装备与外观；排查英雄无法入队、行动不可用、解锁或头像链缺失。"
---

# 角色创建与数据链

先读取 [通用源文件/Pack 工作流](../warhammer-mod-development/references/pack-workflow.md)。Agent 不启动游戏；运行时资格、行动和战斗表现由用户复测。

## 设计与基准

沿用已提供的设计和会话决定，不反复请求确认。设计缺项只追问影响实现的选择：领主/英雄、目标派系/文化、定位/法系、模型/骨架、武器、能力、坐骑、装备、技能树和获取方式。可从目标 MOD 现有实现确定的 ID、字段和命名自行调查。

`wyccc`、无双英灵录、示例等级和数值只是项目实例。新 key/ID 先查当前 MOD 与依赖数据；设计与引擎限制冲突时指出具体字段并完成可行部分。

## 实施与资料

1. 按 [DB 清单](references/db-checklist.md) 接单位主体、角色身份与技能树；可选部分按设计裁剪。坐骑变体逐条核对单位、动作、质量与发放链，不用 Lua 掩盖缺失的原生解锁记录。
2. 能力按 [目标模板](references/ability-targets.md) 配 `target_*`、`affect_self`、目标数量、phase、AI 和 UI 附加词条。设计含超载时读 [超载效果与文本](references/overcast.md)。
3. 战役 `cam_*`、战斗 `battle_animations_table` 与骑手骨架/挂点分别验证，见 [动作与坐骑](../warhammer-mod-development/references/animation-and-mounts.md)。
4. 外观、Variant Selector、portrait_settings 和各类 loc key 见 [外观与本地化清单](references/appearance-and-localisation.md)；绘制读 [美术技能](../warhammer-mod-art/SKILL.md)，译名与换行读 [本地化技能](../warhammer-mod-translation/SKILL.md)。
5. 只有 DB 表达不了的机制才加脚本。每次会话恢复与新局发放分开，初始化规则见 [Lua 参考](../warhammer-mod-development/references/lua_api.md)。
6. 已有角色无法入队、装备效果栏空白、坐骑不解锁或载具乘员复制角色时，从 [故障排查](references/troubleshooting.md) 的对应链开始，不重做整个人物。

## 验收

- TSV 列数、元数据路径、schema 版本与 ID 无误；单位/身份/技能/能力引用完整，unit_attributes 只使用原版合法键。
- 英雄 `agent`、行动 Dummy、associated_unit、派系许可与 unique-agent 注册（如需）一致；技能树包含该类型实际需要的行动节点。
- 坐骑的 enable_mount、rank 条件、技能发放、ancillary 许可一致；载具只让预期 captain 使用英雄 uniform，其他乘员按同类原版基准处理。
- 所有实际外观和兵牌槽位存在，背景描述与机械效果分工明确，特殊机制有 UI 词条。
- Lua/TSV/LOC 静态检查通过，本次源改动已导入映射 Pack、读回并完成 Error 诊断。报告仍需用户检查的 UnitDetails、CanBeEmbedded、事务官行动与战斗状态。
