# 游戏更新后的版本指纹与审计

原版导出、schema、游戏 Pack 和脚本文档可能来自不同时间。沿用旧模板前先核对来源，不能仅因表版本号未变就认定数据没有变化。

## 建立本机基准

在已确认游戏版本和导出来源后，用随技能提供的 `scripts/audit-version.js` 建立**本机自己的**快照。分享者的版本基准不作为本机事实；不随技能打包整套原版导出。

```powershell
node <skill>/scripts/audit-version.js --source <export-root> --schema <schema_wh3.ron> --game <game-root> --game-version <verified-version> --snapshot <new-baseline.json>
```

导出根目录应包含 `db/<table>/data__.tsv`。基准记录导出文件内容 SHA-256、表名、表版本、列顺序和行数；可选记录 schema、游戏 `db.pack/local_cn.pack/local_en.pack/data_script.pack`、Steam build ID 以及导出目录 `script/_lib/` 下的脚本文件指纹。游戏版本是人工确认的标签，不能用它替代实际指纹。

`--snapshot` 是明确的写入操作，只创建新的 JSON，不覆盖已有基准；异常导出不能建立基准。平时比较为只读：

```powershell
node <skill>/scripts/audit-version.js --source <export-root> --baseline <baseline.json> --schema <schema_wh3.ron> --game <game-root> --json
```

必须明确传 `--baseline` 或 `--snapshot`，不自动选择外部作者的快照。未提供的游戏/schema 检查及缺失文件会报告检查范围或缺口；不得把跳过项说成已验证。初次快照允许未安装的 CN/EN 语言 Pack 缺席并记录范围；基准曾记录的文件后来缺失仍报告漂移。大 Pack 用分块哈希，避免把 GB 文件全部读入内存。工具不启动游戏、不重导原版、不修改 Pack。

## 如何处理漂移

| 差异 | 后续动作 |
|---|---|
| 表版本或列顺序改变 | 用当前工具/schema 重新导出，核对新增/删除/改类型的字段，再迁移 MOD |
| 版本和列相同，内容哈希改变 | 比较所用模板行及其引用链，确认数值、flags、能力/动画绑定是否变动 |
| schema 改变 | 核对所用字段的类型、主键、引用目标与可空性；不直接给旧数据补空值 |
| 游戏 Pack 改变，导出未变 | 检查导出是否刷新及来源是否一致；变化也可能来自其他语言/脚本资源 |
| Lua 库或文档变化 | 重新查所用接口签名和相关原版调用，再决定是否修改脚本 |

内容哈希包含格式和换行变化；“哈希不同”不等于某个玩法数值改变。表数、列数、原版能力例子及案例版本都是快照事实，不能作为永恒常量。只检查本次依赖的链，再做相称的离线验证和源 Pack 检查；实机行为仍由用户确认。

比较退出码：`0` 本次检查范围内一致；`1` 漂移、无效导出或基准范围中的文件缺失；`2` 参数、环境或基准格式错误。发现漂移后保留旧基准，确认新版本后另建新快照，不自动改写旧基准掩盖差异。

本流程吸收分享版 `warhammer-mod` 的版本审计方法，工具已适配本项目。相关参考：[行比较](ability-targeting.md#精确比较)、[源 Pack 工作流](pack-workflow.md)。
