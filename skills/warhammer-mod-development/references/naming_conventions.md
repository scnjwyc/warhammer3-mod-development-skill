# MOD命名规范

## 文件前缀规范

先调查目标 MOD 的前缀和现有命名，再分配自定义 key。本文的 `wyccc_` 是来源项目的例子，迁移时用目标 MOD 自有前缀；引用原版 key 时保留原名。

### DB 文件路径和行主键是两层覆盖

| 场景 | 做法 | 检查 |
|------|------|------|
| 新增少量行 | 独立 `db/<table>/!wyccc_<feature>` 文件 | 新主键未占用，引用存在 |
| 覆盖已有行 | 独立文件放目标 key 的完整行 | 只改变预定字段，确认覆盖链实际优先级 |
| 有意替换同路径文件 | 精确同路径，如 `db/<table>/data__` | 明确遮蔽哪个文件及所需保留行，调查其他 Pack |

`!`、`!!`、`!!!` 不是增量模式或固定的高/中/低优先级枚举。文件排序、Pack 加载顺序和其他同 key 记录共同影响结果，不能只凭叹号数量断言最终赢家。`data__` 也不是替换所有来源整张表的开关；同表其他路径的数据仍须调查。

### Lua文件命名

| 前缀 | 示例 | 用途 |
|------|------|------|
| `wyccc_` | `wyccc_cathay_internal_alliance.lua` | 普通功能脚本 |
| `@wyc_` | `@wyc_ancillary_list.lua` | 数据列表/配置脚本 |

### 禁止事项

- 默认使用 MOD 自有文件名，避免无意遮蔽整份原版 `data__`；确需同路径替换时记录目标与保留范围，不设绝对禁令。
- 文件名中的功能描述使用小写+下划线（snake_case）
- 允许在文件名末尾添加中文注释，如 `_效果绑定主表.tsv`

## 变量/键命名

- MOD前缀：沿用目标 MOD 的自有前缀；下列 `wyccc_` 仅为例子
- Effect key：`wyccc_<功能描述>`，如 `wyccc_hostile_towards_cathay`
- Bundle key：`wyccc_<功能>_lv1`，如 `wyccc_nonorder_buff_lv1`
- Module key：`wyccc_<功能名>`，如 `wyccc_cathay_nonorder_buffs`
- 派系key引用：使用官方key如 `wh3_main_cth_cathay`、`wh2_main_skv_clan_eshin`

## 目录名规范

- DB表目录名与源码 `db/` 下的表名完全一致（区分大小写）
- 战役 Lua 常在 `script/campaign/mod/`；战斗脚本、库和其他入口按当前真实加载链确认
- 文本目录固定为 `text/db/`

## 与其他MOD的一致性

生成文件前，先检查目标 MOD 与依赖中是否有同目录、同类型的文件，确保：
1. 目录名与源码一致
2. 叹号前缀用法一致
3. TSV 使用当前同表导出的完整表头及元数据，不照抄旧文件的无表头形态。

参见 [TSV 格式](tsv_format.md)、[版本维护](version-maintenance.md) 和 [源 Pack 工作流](pack-workflow.md)。
