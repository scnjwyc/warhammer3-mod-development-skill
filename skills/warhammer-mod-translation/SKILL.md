---
name: warhammer-mod-translation
description: "翻译或校对战锤3 MOD 的 LOC/TSV：查证官方术语、核对本地化键与换行转义，修正第三方或旧译文本。"
---

# 战锤3 本地化

格式和键名见 [LOC 格式](references/loc-format.md)；写入完成后按 [源 Pack 工作流](../warhammer-mod-development/references/pack-workflow.md) 导入并读回。

## 术语与译文

1. 从待译原文提取人名、别称、地名、派系、兵种、装备、法术和机制词，建立逐项状态表；不把普通英文词当专名留下。
2. 先查目标项目的术语库；没有时用本包 [术语快照](references/glossary.md)。查找容忍大小写、复数、冠词、连字符和空格差异，但须核对语境，不能见子串就自动替换。
3. 未命中的术语走当前原版 EN 文本 → 对应 key → 当前 CN 文本，记录英文、中文与来源 key。可并行检索，逐项保留结果；一次搜索只命中部分词不代表整份清单完成。
4. 原版仍无证据时查可信来源；无可靠译名则保留原文并标为待查。正常句子由 Agent 翻译，但不凭印象编造已有专有名词的译名。
5. 用确认的映射翻译句子，统一同一术语。新确认项回填目标项目术语库（英文/中文/来源）；若无项目术语库，可基于随包快照建立本地库。快照与当前官方库冲突时以查证结果为准。

旧中文校对先按 key 找英文原文，再回到上述流程；不能用可疑中文译名自证正确。英文缺失时从 key 提取的词只能作为搜索线索。常见误译和示例见 [术语案例](references/terminology-cases.md)。

## 写入与检查

- LOC 的 `text` 保持单物理行，RPFM 导出约定的游戏换行字节为 `5C 5C 6E`；按 [LOC 格式](references/loc-format.md) 运行 [校正工具](scripts/fix_loc_newlines.py) 的 `--check`，再审查需要的修复。
- 人物技能、ability 和装备背景描述与机械效果行分开，见 [描述字段规则](references/description-fields.md)。超载名称、占位符和颜色见 [超载规范](../warhammer-mod-character-creation/references/overcast.md)。
- 保持 key、tooltip、占位符、颜色/图标标签及原有结构。逐项核对术语清单，扫描残留英文并判断是否专名；不得把“译文里出现标准词”当成整条翻译通过。
- 仅导入本次改动 LOC；读回确认键、文本、转义及记录数，完成 Error 诊断。游戏显示由用户检查。
