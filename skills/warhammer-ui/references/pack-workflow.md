# UI 源文件接入 Pack

保存、隔离、原版只读依赖、导入和 Error 诊断统一使用 [源 Pack 工作流](../../warhammer-mod-development/references/pack-workflow.md)。

UI 专项：XML/PNG/Lua 用 `add_packed_files`，DB/LOC TSV 用 `import_tsv`；覆盖布局必须使用实际原路径。`.twuiproj` 和编辑器 ZIP 都不是可直接加载的 Pack。检查本次修改的模板、图像、loc key 和脚本引用，不为消除依赖诊断而把原版资源库复制到补丁。

Studio 结构诊断与 RPFM Pack 诊断是不同层次，均不等于游戏验证。Agent 不启动游戏；交互、UI 缩放、重开和读档由用户复测。
