# 历史验证记录（2026-09-27）

日期：2026-09-27。系统：Windows；Python 3.11.1、Tk 8.6、Pillow 12.3.0。工具基准：0.22.2 / `7e3e1be568fac3f5e9362d0494665fc549dc22eb`。不以旧CHANGELOG的测试数替代本次实际结果。

## 上游测试

`python -m unittest discover -v` 实际发现158项。第一次环境读取英文界面设置，3项断言失败：InspectorApplyTests的“应用属性”标签、UsabilityTests的“父隐藏”标签、ViewTests的禁用“属性”菜单标签。断言硬编码韩文，实际返回英文；其余155项通过。

阅读i18n.py与三项测试后，仅为该测试进程设置 `TWUI_STUDIO_LANGUAGE=ko`，未修改用户设置或上游代码，重跑158/158通过、退出0、无跳过。Pillow的Image.getdata有面向未来版本的弃用提示，不是本次失败。

```powershell
Set-Location '..\vendor\TWUI_Studio'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:TWUI_STUDIO_LANGUAGE = 'ko'
python -m unittest discover -v
```

## 本技能脚本

`scripts/test_twui_kb.py`：6/6通过、退出0。覆盖：

- 可索引/查询原版形状的合成XML，正确记录CCO签名和来源；不复制文档prose。
- UTF-8 BOM、CRLF、裸 `<` / `&&` 的读取，行号和SHA正确；源字节不变。
- baseline相同诊断不被误计为新增，新增断裂state引用返回1。
- 某文件解析失败时记录失败并保留其他文件索引，返回1。
- 查询下划线按字面匹配；SQLite只读查询不改数据库、不创建不存在的数据库。
- 拒绝覆盖源XML、拒绝把派生数据库/report写入源ui目录； malformed check返回2。

```powershell
python '<skill-root>\scripts\test_twui_kb.py' `
  --studio '..\vendor\TWUI_Studio' -v
```

## 真实编辑器烟雾验证

`scripts/studio_smoke.py` 创建真实Tk Studio窗口并立即withdraw，配置/产物使用自动清理的临时目录。结果PASS、退出0：示例6个组件、6个几何框、0缺图；改slaves_icon.dock_offset、保持原始对照、undo、redo、项目save/load、导出XML和3张实际引用图片、检查ZIP字节、源示例未变、无Tk callback异常。

示例目录有4张PNG，但该XML只引用3张。验证按实际依赖而非目录图片数量断言。该烟雾验证没有运行战锤游戏。

```powershell
python '<skill-root>\scripts\studio_smoke.py' `
  --studio '..\vendor\TWUI_Studio'
```

## 原版样本全量解析与索引

907/907个TWUI XML解析成功，0解析失败。SQLite `PRAGMA integrity_check` 返回ok。原版样本的Studio诊断共有62项error:duplicate_name及364项warning:name_mismatch。仅记录基准，没有改动原版。hud_battle等原版文件自身亦有同名结构诊断，说明不能把Studio Error清零作为修改原版内容的唯一依据。

5,562处布局为List 3,692、HorizontalList 1,822、RadialList 48。在44,948个组件属性中没有发现dock_position。以上只描述这份本地提取快照，不能据此证明其他游戏版本不会出现某字段。

CLI成功定位 `ui/battle ui/hud_battle.twui.xml:35270` 的spell_parent，读到Center停靠、(-3,-4)偏移、225×200的NewState、6个静态孩子和BattleAbilityHolder回调；同时按layout类型查到RadialList原版例子。索引数据与现读文件SHA关联。

## 仍需实测的部分

本轮未修改生产MOD文件、未导入或保存游戏Pack、未运行战锤。没有验证CA引擎的完整九宫格规则、圆环扩半径算法、动态皮肤、shader/动画、真实字体排版和某具体MOD的生命周期。新Skill要求在实际UI任务中补齐对应运行时证据。

## 独立使用验收

独立Agent只读使用新Skill处理一个组合情境：模板滑条向左8单位、点击监听不响应、面板重开后旧按钮对象失效。它查本地索引和原版文件，给出的最小源修改是offset从-5改到-13，保持模板形状；事件改为ComponentLClickUp；每次操作重查当前组件并校验有效性，重复注册先移除自有监听。内存几何探针与query/inspect命令均通过，未要求展开模板或重做面板。

验收没有发现已尝试命令不可执行或资料语义冲突；当时尚未合入的内部研究链接已补齐。两个Lua参考片段经主线再次 `luac -p` 验证通过。通用warhammer-mod-development技能原先“find_uicomponent只搜直接孩子”的一条错误说明同步纠正，并引向本专用Skill，避免新旧指导冲突。

主线重放内部研究末尾七类边界探针，全部断言通过。Skill官方quick_validate通过，10份Markdown的本地链接均可解析，3个Python脚本的语法解析通过。
