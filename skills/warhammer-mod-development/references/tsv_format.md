# RPFM TSV 文件格式

以当前游戏导出和当前 RPFM schema 为准。普通 DB TSV 使用列名行、元数据行、完整数据行；不要因旧 MOD 中有无表头文件，就把无表头当成另一种导入模式。

```tsv
effect_bundle_key	effect_key	effect_scope	value	advancement_stage
#effect_bundles_to_effects_junctions_tables;3;db/effect_bundles_to_effects_junctions_tables/!wyccc_example
wyccc_example	wh_main_effect_force_all_campaign_upkeep	faction_to_force_own_unseen	-30.0000	start_turn_completed
```

上例只说明结构；版本、scope、阶段及 effect 必须再对照当前同类原版记录。Loc TSV 使用其自身导出格式，交给 `warhammer-mod-translation`。

## 写入与检查

1. 从当前同表导出复制**全部列名及其顺序**、元数据中的表名和版本。旧版本或缺列先重新导出，不通过补空列猜测迁移。
2. 元数据为 `#<表名>;<版本>;<Pack 内路径>`，例如 `db/effects_tables/!wyccc_example`，路径不带 `.tsv`。修改文件名时同步修改路径；元数据行允许导出器补齐空 Tab。
3. 使用 UTF-8、无 BOM 和实际 Tab。数据行列数必须等于表头；中间和末尾的合法空字段保留，不能 `strip()` 后丢失末列。禁止的是额外列，不是所有尾部 Tab。
4. 数值类型、可空性、主键和引用目标查当前 schema。整数按实际 `I32` / `I64` 范围检查；浮点格式可沿用模板。不要假定所有数字 ID 都是 `I32` 或某段 ID 天然未占用。
5. 覆盖已有 key 时复制完整行，再修改明确字段；空值会成为实际数据，不会保留原值。复合主键必须完整定位。
6. 用 [精确行比较](ability-targeting.md#精确比较) 核对非目标字段，再按 [源 Pack 工作流](pack-workflow.md) 导入、保存和读回。DB / Loc 用 `import_tsv`，禁止把 TSV 当裸文件塞进 Pack。

`!` 是项目命名和加载排序约定，不是 TSV 格式开关。`data__` 与增量文件的行为见 [命名规范](naming_conventions.md)。游戏更新后的版本和内容漂移见 [版本维护](version-maintenance.md)。
