# 来源与源码导航

核对日期：2026-09-27。工具commit：`7e3e1be568fac3f5e9362d0494665fc549dc22eb`；本地clone在项目 `../vendor/TWUI_Studio`。上游是源码可读、非商业授权的软件，许可证留在clone的LICENSE.txt及THIRD_PARTY_NOTICES.txt；本包附带该版本未修改的上游源码与全部授权文件；独立说明和 CLI 修改不表示上游认可。

## TWUI Studio模块

下面链接固定到研究commit。行号与重要函数的进一步证据在 [内部研究](twui-studio-internals.md)。

| 主题 | 原始代码 | 定位入口 |
|---|---|---|
| 主窗口/渲染/属性提交 | [app.py](../vendor/TWUI_Studio/app.py) | Studio、commit、apply、draw_scene、release |
| 词法XML/资源定位 | [model.py](../vendor/TWUI_Studio/model.py) | Document、validation_source、patch、state、Resources、LayeredResources |
| 非破坏诊断 | [diagnostics.py](../vendor/TWUI_Studio/diagnostics.py) | inspect_document、unsafe_keys、Issue |
| 树操作/复制 | [component_edit.py](../vendor/TWUI_Studio/component_edit.py)、[hierarchy_edit.py](../vendor/TWUI_Studio/hierarchy_edit.py) | copied_component、pasted_component、move、detach、delete |
| 状态与模板 | [state_edit.py](../vendor/TWUI_Studio/state_edit.py)、[template_states.py](../vendor/TWUI_Studio/template_states.py) | TemplateIndex、state_items、merge_template_texts |
| 布局停靠/列表 | [layout_geometry.py](../vendor/TWUI_Studio/layout_geometry.py)、[transform.py](../vendor/TWUI_Studio/transform.py) | component_format、component_position、list_positions、offset_delta |
| 圆环近似与示意 | [radial_geometry.py](../vendor/TWUI_Studio/radial_geometry.py)、[radial_preview.py](../vendor/TWUI_Studio/radial_preview.py)、[layout_preview_geometry.py](../vendor/TWUI_Studio/layout_preview_geometry.py) | radial_layout与radial_guide是不同用途 |
| 图片处理/缓存 | [rendering.py](../vendor/TWUI_Studio/rendering.py) | dimensions、_raster、raster、ZoomImageCache、visible_crop |
| 工程/导出 | [project.py](../vendor/TWUI_Studio/project.py)、[workspace.py](../vendor/TWUI_Studio/workspace.py)、[multidoc.py](../vendor/TWUI_Studio/multidoc.py) | save_project、export_zip、refresh_resources、import_xml |
| 历史与视图 | [tab_history.py](../vendor/TWUI_Studio/tab_history.py)、[view_state.py](../vendor/TWUI_Studio/view_state.py) | action_state、history_travel、shown |
| 外部布局导入 | [layout_links.py](../vendor/TWUI_Studio/layout_links.py) | ComponentCreator路径发现、静态复制、来源注释 |
| 候选字段与输入 | component_options.py、layout_options.py、input_completion.py、cco_catalog.json | 候选来自观察，不是引擎完整schema |
| 启动、版本和授权 | README_EN.md、requirements.txt、CHANGELOG.md、LICENSE.txt | 当前状态与旧版本撤回说明 |

## 本地CA资料

从本参考文档目录解析 sources 路径；原文件由用户既有游戏资源提取提供。它们比社区经验更适合核对签名，但仍可能有文档自身的示例不一致或随游戏更新落后。

| 路径 | 用途 |
|---|---|
| `sources/documentation/ui/documentation.html` | CCO类型、方法、参数和返回值说明；具体callback行为见独立回调文档 |
| `sources/documentation/ui/callback_documentation.html` | ContextList、ContextTextLabel、ComponentCreator等具体callback |
| `sources/documentation/ui/context_viewer_doc.odt` | Context Viewer、真实树和事件调试器 |
| `sources/documentation/script/campaign/uicomponent.html` | UIComponent及Find、IsValid、SetState、Adopt等API |
| `sources/documentation/script/campaign/core.html` | UI根和组件创建、监听器 |
| `sources/documentation/script/campaign/common.html` | Context查询等common函数，注意文档自身签名/示例差异 |
| `sources/ui/metadata.json` | 本地实际CCO类型、符号、参数与返回值 |
| `sources/ui/templates/*.twui.xml` | 原版模板定义和GUID来源 |
| `sources/ui/battle ui/hud_battle.twui.xml` | 战斗HUD、技能父容器和RadialList实例 |
| `sources/ui/campaign ui/units_panel.twui.xml` | 招募面板静态定义，运行时树仍需调试器确认 |

公开API镜像与本地原文的核对链接、锚点及语义说明放在 [运行时研究](runtime-api.md)。镜像站点不是CA官方域名；内容来源为游戏文档，使用时保留这一身份区别。没有一手依据的“引擎必然如此”不写成确定规则。
