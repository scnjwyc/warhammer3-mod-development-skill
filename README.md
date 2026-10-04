# 战锤3 MOD 开发技能包

包含 8 个互相配套的技能。入口保持简短，详细规则、术语库、三份法术/动作专题、UI 原始文档、可查询索引和辅助工具都在 `skills/` 内。整体复制后不依赖作者的工作区、个人技能目录或记忆库。

## 技能导航

| Skill | 用途 |
|---|---|
| [warhammer-mod-development](skills/warhammer-mod-development/SKILL.md) | DB/TSV、Lua、法术、动作、日志、共用 Pack 工作流 |
| [warhammer-mod-character-creation](skills/warhammer-mod-character-creation/SKILL.md) | 领主/英雄、技能树、坐骑、装备、外观和入队故障 |
| [warhammer-mod-translation](skills/warhammer-mod-translation/SKILL.md) | LOC、术语查证、旧译校对、换行工具与术语快照 |
| [warhammer-mod-art](skills/warhammer-mod-art/SKILL.md) | 技能图标、兵牌、头像、裁切和封面 |
| [warhammer-character-textures](skills/warhammer-character-textures/SKILL.md) | DDS 格式、原图恢复、Alpha/Mip 与批次验证 |
| [warhammer-mod-rmv2-skeleton-repair](skills/warhammer-mod-rmv2-skeleton-repair/SKILL.md) | 模型骨架、权重、bind-pose、字节与动作验收 |
| [warhammer-ui](skills/warhammer-ui/SKILL.md) | TWUI XML、布局、CCO、运行时与离线查询 |

## 安装

把 `skills/` 中 **全部 8 个 `warhammer-*` 文件夹** 一起复制到使用客户端实际配置的技能目录，保持它们互为同级。技能之间有明确的相对依赖，不能仅复制某个 SKILL.md，也不要让旧版本同名技能覆盖新文件。推荐先备份旧目录，再整目录替换。

例如客户端已使用 `~/.agents/skills/`，就把这 8 个文件夹放进去；使用其他技能目录的客户端采用其本地配置。重新载入技能或开启新会话后使用。`docs/` 只保留旧专题入口与整理报告，不是技能运行依赖。

## 随包依赖与外部环境

- 技能文档、术语快照、907 份 UI XML、CA 脚本/UI 文档及引用的原版 Lua/CCO 快照均已随包保存。它们是参考快照，不宣称覆盖未来游戏版本。
- UI 查询、解析、检查和索引重建使用 Python 3.10+ 标准库与随包 TWUI Studio 源码，从任意当前目录可运行。完整编辑器界面另需 Tk/Pillow，见随包 [requirements](skills/warhammer-ui/vendor/TWUI_Studio/requirements.txt)。
- 实际 MOD 工作需使用者提供当前游戏数据、待修改 MOD、RPFM/schema 和确认的 Pack 映射。Lua 检查需要 Lua 5.1 兼容工具；模型变形执行需要 Blender 与兼容 RMV2/ANIM 导入器；图像生成和 DDS 转换使用当地配置的工具。
- 本包不含游戏程序、完整贴图/模型库、第三方 MOD 本体、个人密钥或缺失的旧 Blender 实验脚本。Agent 只执行静态/离线/Pack 检查，游戏测试由用户操作。

TWUI Studio 固定为 `7e3e1be568fac3f5e9362d0494665fc549dc22eb`，上游源文件未修改，保留 [许可证](skills/warhammer-ui/vendor/TWUI_Studio/LICENSE.txt) 和 [第三方声明](skills/warhammer-ui/vendor/TWUI_Studio/THIRD_PARTY_NOTICES.txt)。原版资料保留各权利人的归属；本地整理不改变其原有权利或授权。

## 验证与维护

从任意目录执行：

```text
python -X utf8 <本包目录>/tools/validate_bundle.py --relocate
python -X utf8 <本包目录>/tools/test_helpers.py -v
python -X utf8 <本包目录>/skills/warhammer-ui/scripts/test_twui_kb.py --studio <本包目录>/skills/warhammer-ui/vendor/TWUI_Studio -v
```

校验包含技能入口、本地文档链接、Python 语法、SQLite 完整性、索引到原文 SHA、全包文件清单，以及搬移后 UI CLI 冒烟检查。更新文件后需更新 [manifest.json](manifest.json)；完整整理取舍见 [整理报告](docs/整理报告-2026-09-30.md)。
