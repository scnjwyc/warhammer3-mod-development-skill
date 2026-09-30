# 离线 UI 资料与查询

本技能包括 [SQLite 索引](ui-catalog.sqlite)、[摘要](ui-catalog-summary.json)、[查询工具](../scripts/twui_kb.py)、[TWUI Studio 源码](../vendor/TWUI_Studio/README_EN.md) 和 `sources/` 内的资料快照。所有路径均可随技能目录移动。

## 内容边界

快照来自既有本地提取，包含 907 份 TWUI XML、CCO metadata、CA Lua/UI 文档和用于核对运行时算法的原版 Lua。源文件的提取时间不等于游戏版本；使用前与当前游戏对应文件/签名核对。索引可用每个文件的 SHA 回到随包原文，不要求作者工作区存在。

完整游戏贴图、模型、运行环境和玩家 MOD 不在此资料库中。Studio GUI 预览缺图时使用自己的当前游戏资源根；资料库用于阅读/查询/解析而非替代安装游戏。

## 从任意目录运行

把 `$skillRoot` 设置为实际安装后的技能目录：

```powershell
$skillRoot = '<实际技能目录>/warhammer-ui'
$probe = Join-Path $skillRoot 'scripts/twui_kb.py'
$catalog = Join-Path $skillRoot 'references/ui-catalog.sqlite'
$sources = Join-Path $skillRoot 'references/sources'
python $probe query --database $catalog --kind layout RadialList --limit 8
python $probe query --database $catalog --kind callback ContextCommandLeftClick --limit 8
python $probe query --database $catalog --kind cco CcoComponent --limit 10
python $probe inspect (Join-Path $sources 'ui/battle ui/hud_battle.twui.xml') --id spell_parent
python $probe check '<改后.twui.xml>' --baseline '<改前.twui.xml>'
```

`query` 只需 Python 标准库。`inspect/check/index` 默认加载随包 vendor 解析器，无需 GUI/Tk/Pillow；可用全局 `--studio`（置于子命令之前）或 `TWUI_STUDIO_ROOT` 指定其他可信版本。返回 `file` 为 `ui/` 起的资源路径，对应 `sources/<file>`；若要改实际 MOD，应另定位当前项目源文件，不能修改资料快照充当 MOD 修改。

## 重建与结果解释

```powershell
python $probe index --ui-root (Join-Path $sources 'ui') --database $catalog --report (Join-Path $skillRoot 'references/ui-catalog-summary.json')
```

`index` 写指定派生数据库和摘要；XML、图片、Lua、LOC、Pack 均不修改。它逐文件记录 SHA，解析失败返回 1，读取/参数错误返回 2，成功返回 0。目标数据库和报告不得在输入 ui 根内。

`check` 返回 1 表示 Studio 结构 Error；带 `--baseline` 时只让新增 Error 导致非零退出。已有原版同名组件可触发 Studio 诊断，不能为清零删除合法模板。`--limit` 是展示上限，不能当成所有匹配数量。资料证据边界见 [来源索引](source-map.md)，旧验证记录见 [历史验收](validation.md)。
