---
name: warhammer-mod-development
description: "开发和排查战锤3 MOD 的 DB/TSV、战役与战斗 Lua、效果链、法术、动作引用及源 Pack 同步。UI、角色创建、翻译、图像和模型变形由配套专项技能处理。"
---

# 战锤3 MOD 开发

先读取目标项目的规则、当前源文件和 Pack 映射；按 [源文件与 Pack 工作流](references/pack-workflow.md) 完成交付。Agent 不启动游戏，游戏内验证由用户执行。

## 按任务读取

| 任务 | 资料 |
|---|---|
| 编辑 DB、补丁行、字段类型、导入异常 | [TSV 格式](references/tsv_format.md)、[命名](references/naming_conventions.md) |
| 查表用途、引用关系、实现某项机制 | [DB 索引](references/db_index.md)，再进入对应领域文档 |
| Lua 监听、初始化、存档、API | [Lua 约定与示例](references/lua_api.md) |
| 脚本未生效、战斗目标/伤害异常 | [日志与战斗能力排查](references/debugging.md) |
| 法术/战斗能力字段 | [法术 DB 专题](references/topics/战锤3法术相关DB字段说明.md)、[能力目标模板](../warhammer-mod-character-creation/references/ability-targets.md) |
| 原版法术技能树 | [法术技能专题](references/topics/战锤3原版法术类角色技能整理.md) |
| 战役/战斗动作、坐骑挂点、飞行属性 | [动作与挂点](references/animation-and-mounts.md)、[原版动作专题](references/topics/战锤3原版领主与英雄动作整理.md) |
| 新建领主/英雄、无法入队、事务官行动 | [角色创建](../warhammer-mod-character-creation/SKILL.md) |
| XML 布局、Lua UIComponent、CCO、界面交互 | [UI](../warhammer-ui/SKILL.md) |
| LOC、术语、名称与效果描述 | [本地化](../warhammer-mod-translation/SKILL.md) |
| 图标、兵牌、立绘、MOD 封面 | [美术](../warhammer-mod-art/SKILL.md) |
| DDS 格式、Alpha、Mip、颜色异常 | [贴图](../warhammer-character-textures/SKILL.md) |
| 模型拉伸、关节扭曲、RMV2 权重 | [骨架修复](../warhammer-mod-rmv2-skeleton-repair/SKILL.md) |
| 与龙同行本体更新后的精简补丁 | [精简补丁同步](../warhammer-wwd-lite-patch/SKILL.md) |

## 实施

1. 确认用户指定的文件、日志和症状；新功能以设计和当前同类实现为基准。资料中的 `wyccc`、MOD 名和路径是实例，迁移规则见 [环境与项目结构](references/project_structure.md)。
2. 定位完整数据链，读取当前 schema 和同 key 的完整行。只改目标字段；增量覆盖不能把其余字段留空。数值 ID 核对字段类型范围与冲突。
3. 单位属性只引用当前原版 `unit_attributes` 的合法键；自定义属性组可组合原版键。战斗动画键、战役 `cam_*` 键和 RMV2 骨架分别验证，不按字符串猜配。
4. Lua 改动按实际生命周期初始化；运行 Lua 5.1 兼容语法检查。DB 核对列数、内部路径、引用和预期行数；LOC 核对转义与键；运行作用域化 `git diff --check`。
5. 把本次改动导入映射的源 Pack，保存前核对会话与条目集合，保存后读回并扫描 Error。报告静态/Pack 结果和留给用户的具体游戏复测步骤。

资料快照用于导航，当前游戏 schema、原版数据与用户明确设计决定最终取值。不要把案例数值、旧日志结论或编辑器预览当成当前游戏实测。
