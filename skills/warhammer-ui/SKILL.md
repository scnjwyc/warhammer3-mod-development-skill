---
name: warhammer-ui
description: 开发和排查全面战争：战锤3的TWUI界面：XML布局、模板与状态、图片和本地化、Lua UIComponent交互、CCO数据绑定，以及TWUI Studio编辑和源Pack接入。用于面板、按钮、HUD、列表、锚点、界面错位或点击失效；单纯技能图标绘画、兵牌绘画和玩法DB数值不由本技能处理。
---

# 战锤3 UI

把修改落实到本地 UI / Lua / LOC 源文件，完成离线验证并列出用户的游戏复测动作。TWUI Studio 是可选编辑器和格式研究工具；它的预览、诊断和导出都不能代替游戏引擎。

## 从问题选择资料

| 当前任务 | 按需读取 |
|---|---|
| 不知道面板/按钮定义在哪，找原版先例或 CCO 签名 | [资料库与查询](references/knowledge-base.md)；按组件 ID、图片路径、LayoutEngine 或 callback 查询本地索引 |
| 改 XML、GUID、状态、模板、文字或图层 | [TWUI结构](references/twui-format.md)；复制、移动、模板操作同时查 [工具内部实现](references/twui-studio-internals.md) |
| 偏移、锚点、列表、圆环、缩放、裁切 | [布局与渲染](references/layout-and-rendering.md) |
| Lua按钮、动态面板、CCO数据与点击事件 | [运行时与CA资料](references/runtime-api.md) |
| Lua 面板开关、延迟回调、角色切换或 CCO 提交回归 | [Lua 离线回归](../warhammer-mod-development/references/lua-offline-testing.md)，按 UI/CCO 分支验证生命周期与状态 |
| 一次操作后多个 MOD 窗口异常，或日志/UI 接口返回错误类型 | [CA 字符串接口与共享上下文故障](../warhammer-mod-development/references/ca-string-api.md)；核对 `string.find` 的参数与模式语义 |
| 使用/研究 TWUI Studio、保存或导出不对 | [工具内部实现](references/twui-studio-internals.md) 和 [工作流与排错](references/workflows.md) |
| 将已修改源文件接入本项目 Pack | [源Pack工作流](references/pack-workflow.md)，并先读取当前项目 AGENTS.md / pack_map.json |
| 判断资料可信度、复测或升级工具 | [来源索引](references/source-map.md) 和 [已执行验证](references/validation.md) |

## 实施顺序

1. 明确目标是战役、战斗还是前端界面；记录现有组件路径、截图/日志和期望变化。先读当前源文件与限定范围的 `git diff`。同一位置由 XML、父 LayoutEngine、CCO 或 Lua 谁控制，必须查到实际控制者再改。
2. 查同类原版先例。已有 `.codegraph` 时先用它定位代码；XML/JSON/HTML未被索引时用资料库或 `rg`。索引是本地提取快照，改动前重读它指向的当前源文件，核对版本或 SHA。不能把候选属性列表当完整格式规范。
3. 修改源文件：普通属性用局部补丁，保留未知节点、回调、引号/换行和编码；复制组件须维护 hierarchy、components 与内部 GUID 引用；模板沿原版 template 引用和局部覆盖修改。最小修改不触发全文件格式化。
4. 做与改动对应的静态检查，保留前后差异。`scripts/twui_kb.py check` 只给出 Studio 的结构诊断；原版模板也可能触发它的 Error，先与基准及真实模板引用对照，不为清零而删合法内容。Lua 修改运行 `luac -p`，涉及事件/延迟、面板生命周期或 CCO 提交时按离线回归指南选择相关行为场景；LOC/DB 核对格式与键，图片核对路径和实际尺寸。
5. 需要交付 MOD 时按映射导入本次改动、保存并扫描源 Pack 的 Error；普通 XML/PNG/Lua 用 `add_packed_files`，DB/LOC TSV 用 `import_tsv`。Pack扫描与Studio结构检查是不同层次。
6. 由用户在游戏内按目标动作验收：初次打开、关闭再开、相关状态切换、实际点击、目标分辨率/UI缩放、必要的读档或场景重建。检查组件后状态与相关日志。Agent 不启动游戏，尚无用户结果时标注游戏未验证，并提供具体复测动作；截图或静态测试通过不能称为功能已验证。

## 容易改错的边界

- `hierarchy` 表示静态树，`components` 保存平铺定义，以 `this` 关联。`id`、XML标签、组件GUID、state GUID和image GUID分属不同用途。原版同名组件可以出现在不同父节点下。
- 常见普通定义用 `docking + dock_offset`，模板实例用 `dock_point + offset`，图层另用 `dockpoint`。这是当前源码与样本观察，先确认文件形状；不要批量互换或添加已撤回的 `dock_position`。
- `find_uicomponent` 的每一步会递归找后代，可能命中同名组件；`core:get_or_create_component` 查直接孩子。用运行时树和明确父节点限定目标，参考运行时资料中的同名处理方法。
- 原版 Lua 鼠标释放事件是 `ComponentLClickUp`，不要凭空缩成 `ComponentLClick`。XML callback 名也不是 Lua 事件名。
- ContextList/Creator 与 Lua 能重建组件树。跨面板关闭、回调延时或读档操作时重新查组件；检查 `IsValid()` 后再用，监听注册保持可重复初始化。
- 编辑器隐藏/锁定/动态文字预览是工作视图；不会自动成为游戏中的可见性、禁用状态或文本逻辑。`currentstate` 与 `defaultstate` 的修改则会进入 XML。
- Studio 的外部布局“导入”会真实复制节点，而原 ComponentCreator 回调仍保留。先决定由静态还是动态结构负责创建，避免游戏里出现两份。

## 资料与工具的维护

本技能核心参考固定于 TWUI Studio `7e3e1be568fac3f5e9362d0494665fc549dc22eb`。索引内有来源路径、源文件 SHA、生成时间和解析器版本。游戏/工具更新后按资料库说明重建，不手改 SQLite。研究结论分为源码事实、原版样本、工具近似和游戏实测；保留这四种证据的边界。
