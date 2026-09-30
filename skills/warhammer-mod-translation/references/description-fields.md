## 新建人物技能、战斗能力与装备描述规则

实现或修改人物专属内容时，下列“描述字段”必须只写角色背景、经历、性格、传说、招式意象、装备来历或世界观叙事：

- 人物技能：`character_skills_localised_description_*`
- 战斗 ability：`unit_abilities_tooltip_text_*`
- 装备：`ancillaries_colour_text_*`、`ancillaries_explanation_text_*`

这些字段禁止罗列或概括机械效果，包括数值、属性增减、解锁内容、技能类型、使用次数、持续时间、冷却时间、作用范围、目标、等级成长、作用域、获取方式和角色限制。

- 机械信息由 DB 效果链、`effects_description_*`、附加效果行及游戏自动生成的效果面板承载；不得为了“说明清楚”再复制进上述描述字段。
- `effects_description_*` 属于机械效果显示行，不属于背景描述字段；例如装备解锁节点可以用它显示“获得专属装备”，同时节点自身的 `character_skills_localised_description_*` 仍只写装备传说。
- 装备描述不写“解锁并获得”“仅限某角色装备”“达到某级”等获取机制。
- 完成新增人物技能、ability 或装备后，必须逐条审查上述对应字段，确认移除所有数值和机制信息后仍是完整、自然的背景文本。
