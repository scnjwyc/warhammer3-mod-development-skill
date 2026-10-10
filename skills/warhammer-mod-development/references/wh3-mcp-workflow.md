# Warhammer MCP 证据工作流

用于真实 Lua/UI/战役状态、接口查询和脚本错误证据。游戏操作按当前项目 `AGENTS.md` 执行；本项目由用户启动、进入场景、操作和运行游戏端采集，Agent 准备探针并分析已有文件。把 MCP 证据接在 [Lua 离线回归](lua-offline-testing.md) 与 [运行时内存研究](runtime-memory-analysis.md) 之间；普通 DB 或 Pack 问题无需引入运行时采集。

## 工具与版本

[工坊工具](https://steamcommunity.com/sharedfiles/filedetails/?id=3786971022) 的 Pack 是游戏端 Lua；[作者仓库](https://github.com/PassingByPixels/wh3-mcp) 的 Node.js 服务是 MCP 客户端接入部分。Lua 每秒轮询游戏工作目录的 `wh3_mcp_command.json`，执行后写 `wh3_mcp_result.json`。只有订阅 Pack 不代表当前会话已具备 `wh3_*` 工具：先核对实际可调用工具，未注册时按文件证据流程工作。

2026-10-10 已核对的基准：上游提交 `91c70e38541be5de0bb25dc9d5a4c1845b0baad2`，服务版本 0.1.0、82 个 MCP 工具、5,325 条资料索引。Workshop Pack 的 Lua 与该提交一致，仅换行不同；Pack SHA256 为 `1d4ff5ca079d1b6962ed1d5bf124b575e219d108dc06f9135c7a64238e66022c`。安装位置由使用者确认：

- Pack：`<Steam 库>/steamapps/workshop/content/1142710/3786971022/wh3_mcp_server.pack`。
- 游戏目录：`<Steam 库>/steamapps/common/Total War WARHAMMER III`。

这是一份已核对的版本快照，使用前检查实际文件与版本。作者 Node 服务可通过注册表识别 Steam 安装位置；上游随附的两支发送脚本写死 C 盘，PowerShell 版本还以 ASCII 写命令。Lua 使用相对路径，用户提供的实际游戏工作目录优先于默认安装路径。本包的辅助脚本不依赖这些发送脚本或原作者工作区。

## 按问题选择证据

| 问题 | 首选证据 | 结论范围 |
|---|---|---|
| 面板、奖励或事件选项不符 | `wh3_get_situation`、`wh3_read_event`、`wh3_list_ui` 的原始输出和组件路径 | 能核对状态和文本；布局、图像和点击仍需用户实机结果 |
| 军队、角色或读档后状态变化 | `wh3_get_armies`，必要时设计固定的角色/地区/保存值 getter 探针 | 部分 getter 只有 Lua 命令，没有独立 MCP 包装；记录 CQI、subtype、目标对象及返回类型 |
| 寻找可用 API | 文档索引、原版脚本、`wh3_cm_search` | `exists_at_runtime` 仅检查成员非 nil，不证明其是函数、参数合法或已执行成功 |
| 操作后异常、游戏关闭后的错误 | 现有 `wh3_mcp_script_errors.log`、用户点名的 `script_log_*.txt` 和 MOD 日志 | 以原文和触发时间为依据；缺日志、没有匹配错误不等于测试通过 |
| 战斗变化 | `wh3_get_battle_units`、战斗阶段、目标与单位身份 | 现成输出主要是类型和存活人数；HP、伤害、治疗、AI 与精确时序另做探针 |
| 脚本接口不足以解释的原生行为 | 经核对的快照字段、错误消息和接口名，随后进入 dump/xref/调用链分析 | MCP 提供锚点与对照值，不能恢复原生函数地址或结构体偏移 |

直接授予技能、转移地区、造建筑等命令可搭建场景，却绕过了玩家点击、合法性判断与事件路径。只有真实玩家路径的操作前后证据，才能证明对应流程得到修复。

## 采集与分析

1. 写清用户实际触发路径和本次要比较的字段，区分前端、战役、战斗上下文。先检查相关源文件、映射 Pack 与离线结果，再决定缺哪些实机证据。
2. 准备针对目标对象的最小 getter 探针和预期输出，用户在目标场景执行。保留发出的请求及原始响应；`eval` 和任意 CCO expression 能修改状态，不能因名称是“查询”就当作只读。请求编号、上下文、回合、用户操作和版本应随用户采集记录一起保存。
3. 将已有日志和结果保存到独立的研究目录。下面的辅助脚本只读现有文件，不发命令、不操作游戏、不删除结果、不注册 MCP；输出目录须位于游戏目录之外。每次用一个新的输出目录：

```powershell
python "<skill 根目录>/scripts/wh3_mcp_evidence.py" --game-dir "<实际游戏工作目录>" --out "<研究目录>/runtime-before" --label "触发前" --pack "<Workshop Pack 完整路径>"
```

需要 MOD 日志时重复传 `--extra-log <文件名>`。作者服务通常会读走并删除结果文件；用户已另存响应时，用 `--result "<响应文件完整路径>"` 指定已有文件。`--pack` 可重复记录本次涉及的 Pack 哈希。输出包含 `manifest.json` 和 `files/` 原始字节；日志保存全量匹配行，不设 200 条上限。使用 `runtime-after` 再采集操作后文件，Agent 按源路径、时间、哈希和实际新增内容比较；历史错误不能算成本次新错误，日志重写或轮换要重新确定基准。

4. 先检查文件缺失、读取变化、编码、JSON 解析和响应内部 `status`，再解释业务字段。辅助脚本的 `log_scan` 只表示启发式匹配结果；`no_matches` 不能证明没有错误。`incomplete`、无有效响应、缺字段均保留为未知。输出标签不证明响应属于该请求：当前作者协议没有请求编号，必须由用户的请求记录和场景证据核对。
5. 对照触发前后状态、UI/事件和新增日志，说明哪一段已被证实。需要解释原生机制时，按内存研究专题绑定游戏模块与 dump 身份，使用同一场景的具体文本/数值作为锚点；不能把 Lua userdata 的 `tostring` 当成已经核验的原生对象指针。

采集不是原子快照。脚本发现读取期间文件变化会标记 `changed_during_read`；这类结果保留原始文件，但需要稳定场景下重新采集。辅助脚本的成功退出只代表完成文件整理，不代表游戏测试通过。

## 当前基准的已知缺陷

下列来自固定版本的源码和隔离探针；作者更新后重新核对，不能当所有版本的永久结论。

- **JSON 不完整。** Lua 编码遗漏反斜杠转义，Windows 路径可能成为非法 JSON 或改变文字；解码不支持 `\uXXXX` 且可能接受截断对象。保留原字节和解析错误，不能“修复”后声称这是游戏原始返回。
- **错误汇总漏报。** 额外日志中的错误不计入 `has_new_errors`；CA 日志仅返回前 200 条匹配行，却推进 offset 至文件末尾。分析原始日志和实际新增内容，不把该总标志作为验收门槛。
- **CA 字符串契约冲突。** 模式转义后的文本被交给不支持模式的 `string.find`，点号/连字符检索在契约替身下失败。按 [CA 字符串接口](ca-string-api.md) 使用 `find_lua` 或正确的字面量搜索，修复需离线契约回归与用户实机复测。
- **通信缺少关联与原子提交。** 命令/结果共用固定文件，客户端清理旧文件，同步忙等待阻塞 Node；多客户端、延迟回复或重试可能覆盖/误认。单客户端串行只能缩小风险，不能证明响应归属。未来适配需要两端校验请求/会话编号、原子写入及取消语义。
- **不是被动观察器。** 游戏脚本包装共享的 `script_error`，写额外日志和 marker；遗留自动战斗 marker 可恢复操作。`pcall` 不回滚引擎状态，错误捕获也不覆盖所有局部引用或原生崩溃。

以上源码证据可在 [JSON 与搜索实现](https://github.com/PassingByPixels/wh3-mcp/blob/91c70e38541be5de0bb25dc9d5a4c1845b0baad2/pack/script/_lib/mod/wh3_mcp.lua#L139)、[客户端通信](https://github.com/PassingByPixels/wh3-mcp/blob/91c70e38541be5de0bb25dc9d5a4c1845b0baad2/server/index.js#L171)、[日志汇总](https://github.com/PassingByPixels/wh3-mcp/blob/91c70e38541be5de0bb25dc9d5a4c1845b0baad2/server/index.js#L2214) 核对。

## 以后扩展 MCP 接入时

Skill 中的入口不等于已经安装或注册作者服务。当前规则下使用上述文件证据流程；若用户以后明确允许 Agent 查询或操控游戏，按当时项目规则确定范围，再接入经过审查的版本。

观测适配要同时限定客户端入口和游戏端命令、关闭自动运行状态机，并把任意 Lua/CCO 执行换成固定探针。作者 Node 服务启动会写入资料 TSV，不能把注册启动视为纯读取。完整游戏操作与场景搭建按用户授权范围处理；第三方 Workshop Pack 作为只读参考，自有实现先建立本地源目录和 Pack 映射，遵循源文件 → 映射 Pack → 回读及 Error 检查的现有流程。分发作者代码时保留上游 MIT 许可。
