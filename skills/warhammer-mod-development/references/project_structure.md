# 环境与项目结构

文中路径相对目标 MOD 工作区，首次使用时由使用者的目录映射定位，不绑定作者电脑。

| 名称 | 含义 / 常见位置 |
|---|---|
| workspace | 当前 MOD 工作区；读取它的 AGENTS.md（若有） |
| mod source | 本地编辑源，如 `mod/<MOD>/` |
| game source | 从当前游戏合法安装导出的原版 DB、脚本、UI、模型，例如 `源码/` |
| localisation | 当前游戏 EN/CN 本地化导出，如 `多语言/EN/`、`多语言/localisation__.loc_CN.tsv` |
| pack map | 项目确认的源目录到 Pack 映射，例如 `pack_map.json` |
| schema | 本机 RPFM 配置中的 `schema_wh3.ron`，随游戏版本核对 |

本包包含编写的参考文档、术语快照、离线 UI 资料和辅助脚本；游戏资源、RPFM、Lua 5.1、Blender 和生成图片服务是按任务需要提供的运行环境。找不到当前原版/第三方源时，先说明哪一步需要该输入，不能把历史快照当成当前安装。

技能包中的同级技能及 references 使用相对链接。安装时一起复制全部 `warhammer-*` 技能目录；不需要作者的个人技能目录、记忆库或原工作区。
