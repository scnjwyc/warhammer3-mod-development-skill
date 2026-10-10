# 文档快照修正

2026-09-30 打包时修正两处原始断链：

- scripted_events.html 中 Model Hierarchy 实际位于同目录 scripting_doc.html，已修正相对链接。
- battle_index.html 所指旧 EmpireBattleScript.rtf 在可用原版文档中不存在；保留文件名和缺失说明，移除无效超链接，不伪造内容。当前 battle API HTML 文档已全部包含。

其他文档与游戏/界面源快照保留原内容。完整游戏图像/模型不属于该文档闭包。

2026-10-10 发布同步时，文本统一为 LF 行尾并添加 Git 行尾规则，防止 Windows checkout 改变字节后导致文件清单或索引 SHA 失配；UI 索引据随包文件重建，907 份 XML 的结构与内容未改。摘要与数据库的 roots 保持相对 references 目录，搬移后仍可定位原文。
