# MOD命名规范

## 文件前缀规范

所有文件必须使用 `wyccc_` 作为开发者前缀。

### TSV文件叹号前缀（控制加载优先级）

| 前缀 | 示例 | 用途 |
|------|------|------|
| `!!!wyccc_` | `!!!wyccc_cathay_school.tsv` | 最高优先级，核心主表 |
| `!!wyccc_` | `!!wyccc_cathay_internal_alliance.tsv` | 中等优先级，关联表/辅助表 |
| `wyccc_` | `wyccc_cth_court.tsv` | 默认优先级，普通数据表 |
| `!wyccc_` | `!wyccc_cathay_school.tsv` | 较低优先级 |

### Lua文件命名

| 前缀 | 示例 | 用途 |
|------|------|------|
| `wyccc_` | `wyccc_cathay_internal_alliance.lua` | 普通功能脚本 |
| `@wyc_` | `@wyc_ancillary_list.lua` | 数据列表/配置脚本 |

### 禁止事项

- **绝对禁止**使用 `data__` 作为MOD文件名——那是源码占位文件名
- 文件名中的功能描述使用小写+下划线（snake_case）
- 允许在文件名末尾添加中文注释，如 `_效果绑定主表.tsv`

## 变量/键命名

- MOD前缀：`wyccc_`（所有自定义key的前缀）
- Effect key：`wyccc_<功能描述>`，如 `wyccc_hostile_towards_cathay`
- Bundle key：`wyccc_<功能>_lv1`，如 `wyccc_nonorder_buff_lv1`
- Module key：`wyccc_<功能名>`，如 `wyccc_cathay_nonorder_buffs`
- 派系key引用：使用官方key如 `wh3_main_cth_cathay`、`wh2_main_skv_clan_eshin`

## 目录名规范

- DB表目录名与源码 `db/` 下的表名完全一致（区分大小写）
- Lua目录固定为 `script/campaign/mod/`
- 文本目录固定为 `text/db/`

## 与其他MOD的一致性

生成文件前，先检查其他MOD（如"天廷"、"难度大修"）中是否有同目录、同类型的文件，确保：
1. 目录名与源码一致
2. 叹号前缀用法一致
3. TSV格式模式（表头行/无表头行）一致
