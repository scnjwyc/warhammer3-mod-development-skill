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

本包包含编写的参考文档、术语快照、离线 UI 资料和辅助脚本；游戏资源、RPFM、Lua 5.1 和图像工具是按任务需要提供的运行环境。找不到当前原版/第三方源时，先说明哪一步需要该输入，不能把历史快照当成当前安装。

技能包中的同级技能及 references 使用相对链接。安装时一起复制本包的 5 个 `warhammer-*` 技能目录；不需要作者的个人技能目录、记忆库或原工作区。

## 辅助工具环境

- Python 3.10+：TSV 比较、MCP 现有文件整理、镜像读取与 UI CLI 使用标准库。Windows 进程采集还要求 64 位 Windows/Python；Agent 不启动游戏。
- Node.js 18+：`scripts/audit-version.js` 只用 Node 内置模块，不需要 npm 安装或外部作者基准。
- Capstone 5.0.7：反汇编与调用图分析；Lupa 2.8 的 `lupa.lua51`：随包 CA 契约回归。安装到使用者选定的 Python 环境：`python -m pip install -r <skill 根目录>/scripts/requirements-analysis.txt`。不做反汇编或 Lua 回归时无需这两个库。
- 工具路径相对本 skill 根目录，输入与输出参数按目标项目指定。随包回归使用合成样本或测试进程，不要求原作者的 MOD、日志、Downloads 目录或 Steam 安装路径。
