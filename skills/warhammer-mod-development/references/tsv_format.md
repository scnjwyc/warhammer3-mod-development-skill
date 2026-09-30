# RPFM TSV 格式与增量修改

DB TSV 的第一行是 Tab 分隔列名，第二行是 `#<table>;<version>;db/<table>/<packed_name>`，第三行起为数据。格式、字段顺序和版本以当前 RPFM 导出与 schema 为准，不使用无表头“模式 B”。

```text
effect_bundle_key<TAB>effect_key<TAB>effect_scope<TAB>value<TAB>advancement_stage
#effect_bundles_to_effects_junctions_tables;3;db/effect_bundles_to_effects_junctions_tables/!my_bundle
my_bundle<TAB>wh_main_effect_force_all_campaign_upkeep<TAB>faction_to_force_own_unseen<TAB>-30.0000<TAB>start_turn_completed
```

示例的 `<TAB>` 表示真实制表符；版本 3 仅是示例。内部路径不带 `.tsv`，末段等于源文件去掉 `.tsv` 的名称。复制原版 `data__.tsv` 为增量文件后必须同步修改元数据路径。

## 整行数据完整性

补丁中参与覆盖的记录必须包含该行全部字段，空值不会自动继承被覆盖行。读取同 key 的完整基准行，只改目标字段，非目标列逐项保持一致。`!` 是文件命名/排序约定，不是 RPFM 的字段合并操作。

每条数据行的列数等于表头。末尾字段为空时保留必要尾部 Tab，不用 `strip()` 删掉它们。空字段用连续 Tab 表示。UTF-8 编码及 BOM 按当前工具导出保留，读取时兼容 BOM；不能靠统一增删 BOM 修复数据链问题。

## 字段与引用

- 数值 ID 先查 schema 类型；I32 范围为 -2147483648 至 2147483647，I64 为 -9223372036854775808 至 9223372036854775807。不能使用超过字段范围的 ID，不能把某个“大数区间”视为永远无冲突。
- 检查所有改动表和已加载依赖中的主键/组合主键。对浮点值保留合理精度，对 bool 使用导出格式。
- 用当前引用表验证键，而非从相似名称推导。不能向 `unit_attributes_tables` 添加自定义引擎属性；自有属性组组合原版合法属性即可。
- 表结构检查、引用检查与游戏机制是三个层次。导入成功后读回实际行数及关键列，确认无漏行、空表和意外清空字段。

文件命名见 [命名约定](naming_conventions.md)。LOC 转义和校验见 [本地化技能](../../warhammer-mod-translation/SKILL.md)。导入与诊断见 [Pack 工作流](pack-workflow.md)。
