# RPFM TSV 文件格式规范

## 基本规则

TSV文件用于覆盖战锤3的数据库表，必须严格遵循RPFM读写的格式。

## TSV格式

```
列名1	列名2	列名3	...             ← 第1行：列名（Tab分隔）
#表名;版本号;相对路径                  ← 第2行：元数据
数据1	数据2	数据3	...             ← 第3行起：数据
```

示例（effect_bundles_to_effects_junctions_tables）：
```
effect_bundle_key	effect_key	effect_scope	value	advancement_stage
#effect_bundles_to_effects_junctions_tables;3;db/effect_bundles_to_effects_junctions_tables/!!wyccc_cathay_nonorder_buffs				
wyccc_nonorder_buff_lv1	wh_main_effect_force_all_campaign_upkeep	faction_to_force_own_unseen	-30.0000	start_turn_completed
```

## 元数据行格式

`#<表名>;<版本号>;<相对路径>`

- `<表名>`：与源码db目录下的表目录名完全一致
- `<版本号>`：格式版本。如果不确定，查找源码中的同表格版本号
- `<相对路径>`：从db/开始的完整相对路径，如 `db/effects_tables/!!wyccc_cathay_internal_alliance.tsv`

## 如何判断使用哪种模式

**必须检查源码中对应表的 `data__.tsv` 和已有MOD中同表的文件：**

1. 打开 `源码/db/<table_name>/data__.tsv` 查看格式
2. 打开 `mod/*/db/<table_name>/` 查看已有MOD文件的格式
3. 保持与已有MOD文件一致的格式

**一般规律**：
- 大多数表使用模式A（带表头）
- 少数表（如 `effects_tables`）在MOD文件中使用模式B（无表头）
- 如果源码和已有MOD格式不同，优先使用已有MOD的格式

## RPFM兼容性检查要点

1. **列数据不能包含未转义的Tab**：确保数据中无多余Tab
2. **元数据行中空列用Tab填充**：`#` 行中版本号后的路径部分，空字段用Tab占位
3. **数值格式**：带小数的值使用4位小数（如 `-30.0000`），整数可以不用小数
4. **末尾无多余空行**：文件末尾不要有多余的空行或Tab
5. **编码**：UTF-8 with BOM（RPFM默认）
6. **空值处理**：空字段用连续Tab表示（如 `value1\t\tvalue3`）
7. **隐藏文本**：本地化字段使用 `[hidden]` 表示该bundle不显示给玩家
8. **没有尾部Tab**：每行末尾不要有多余的Tab字符
