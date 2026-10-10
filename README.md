# 战锤3 MOD 开发技能包

包含 5 个互相配套的技能。入口保持简短，详细规则、术语库、三份法术/动作专题、Lua 离线回归方法、MCP 证据工作流、内存分析与反汇编工具、UI 原始文档及可查询索引都在 `skills/` 内。整体复制后不依赖作者的工作区、个人技能目录、Downloads 文件或记忆库。

## 技能导航

| Skill | 用途 |
|---|---|
| [warhammer-mod-development](skills/warhammer-mod-development/SKILL.md) | 版本审计、DB/TSV、Lua 离线回归、MCP 证据、内存与反汇编、法术/动作、Pack 工作流 |
| [warhammer-mod-character-creation](skills/warhammer-mod-character-creation/SKILL.md) | 领主/英雄、技能树、坐骑、装备、外观和入队故障 |
| [warhammer-mod-translation](skills/warhammer-mod-translation/SKILL.md) | LOC、术语查证、旧译校对、换行工具与术语快照 |
| [warhammer-mod-art](skills/warhammer-mod-art/SKILL.md) | 技能图标、兵牌、头像、裁切和封面 |
| [warhammer-ui](skills/warhammer-ui/SKILL.md) | TWUI XML、布局、CCO、运行时与离线查询 |

## 安装

把 `skills/` 中 **全部 5 个 `warhammer-*` 文件夹** 一起复制到使用客户端实际配置的技能目录，保持它们互为同级。技能之间有明确的相对依赖，不能仅复制某个 SKILL.md，也不要让旧版本同名技能覆盖新文件。推荐先备份旧目录，再整目录替换。

例如客户端已使用 `~/.agents/skills/`，就把这 5 个文件夹放进去；使用其他技能目录的客户端采用其本地配置。重新载入技能或开启新会话后使用。`docs/` 只保留旧专题入口与整理报告，不是技能运行依赖。

## 随包依赖与外部环境

- 技能文档、术语快照、907 份 UI XML、CA 脚本/UI 文档及引用的原版 Lua/CCO 快照均已随包保存。它们是参考快照，不宣称覆盖未来游戏版本。
- UI 查询、解析、检查和索引重建使用 Python 3.10+ 标准库与随包 TWUI Studio 源码，从任意当前目录可运行。完整编辑器界面另需 Tk/Pillow，见随包 [requirements](skills/warhammer-ui/vendor/TWUI_Studio/requirements.txt)。
- TSV 比较和 MCP 现有文件整理只需 Python 标准库；版本指纹审计需要 Node.js 18+，无需 npm 包。反汇编与 CA 字符串契约测试另用 [requirements-analysis.txt](skills/warhammer-mod-development/scripts/requirements-analysis.txt) 安装 Capstone 5.0.7 / Lupa 2.8。
- 实际 MOD 工作需使用者提供当前游戏数据、待修改 MOD、RPFM/schema 和确认的 Pack 映射。Lua 检查需要 Lua 5.1 兼容工具；图像生成使用当地配置的工具。它们是运行环境和任务输入，随包文档与脚本无需作者电脑上的文件。
- 本包不含游戏程序、完整贴图/模型库、第三方 MOD 本体或个人密钥。MCP 指南包含版本、探针分工与文件证据整理；作者的 Workshop Pack/Node 服务由使用者按需安装，技能包不会自动注册服务或操作游戏。Agent 只执行静态/离线/Pack 检查，游戏测试由用户操作。

TWUI Studio 固定为 `7e3e1be568fac3f5e9362d0494665fc549dc22eb`，上游源文件未修改，保留 [许可证](skills/warhammer-ui/vendor/TWUI_Studio/LICENSE.txt) 和 [第三方声明](skills/warhammer-ui/vendor/TWUI_Studio/THIRD_PARTY_NOTICES.txt)。原版资料保留各权利人的归属；本地整理不改变其原有权利或授权。

## 验证与维护

从任意目录执行：

```text
python -X utf8 <本包目录>/tools/validate_bundle.py --relocate
python -X utf8 <本包目录>/tools/test_helpers.py -v
python -X utf8 <本包目录>/skills/warhammer-ui/scripts/test_twui_kb.py --studio <本包目录>/skills/warhammer-ui/vendor/TWUI_Studio -v
python -m pip install -r <本包目录>/skills/warhammer-mod-development/scripts/requirements-analysis.txt
python -X utf8 -B -m unittest discover -s <本包目录>/skills/warhammer-mod-development/scripts/tests -v
```

校验包含 5 个技能入口、本地文档链接、Python 语法、SQLite 完整性、索引到原文 SHA、全包文件清单，以及搬移后的 UI / DB / MCP / 内存工具冒烟检查。可选开发回归覆盖合成镜像、受控 Python 采集、MCP 文件证据和 CA 字符串契约；不启动游戏。更新文件后用 `python -X utf8 tools/validate_bundle.py --write-manifest` 更新 [manifest.json](manifest.json)，再运行完整校验。历史整理记录见 [整理报告](docs/整理报告-2026-09-30.md)，当前发布范围以本页为准。
