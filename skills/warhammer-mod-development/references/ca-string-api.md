# CA 字符串接口与共享上下文故障

适用于 WH3 Lua 字符串搜索、离线测试，以及一次操作后多个 MOD 的 UI/日志同时异常。接口签名以 CA 文档为依据；下述原生损坏机制来自 2026-10-05 本机游戏程序的静态核验，没有启动游戏。

## 写代码时选择正确接口

| 接口 | 参数及语义 | 用途 |
|---|---|---|
| `string.find(subject, needle[, start])` | CA 的 UTF-8 字面量搜索，2～3 个参数，不支持 Lua 模式 | 需要 UTF-8 字符位置的搜索；按 CA 签名传参 |
| `string.find_lua(subject, pattern[, start[, plain]])` | 原始 Lua 的字节搜索，支持模式和第四参数 `plain` | ASCII 技能 key、文件错误文本、模式校验及按字节处理的文本 |

`subject:find(needle, 1, true)` 等价于 `string.find(subject, needle, 1, true)`，冒号隐含的接收者也计入参数。这种标准 Lua 写法不符合 CA 的签名。

在模块内部保存正确实现，兼容标准 Lua 测试环境：

```lua
local find_text = string.find_lua or string.find

-- 字面量搜索：第四参数属于原始 Lua 接口。
local is_auto = find_text(tostring(status), 'auto', 1, true) ~= nil
local missing = find_text(message, 'cannot find the file', 1, true) ~= nil

-- 模式搜索：不传 plain=true。
local has_control_byte = find_text(skill_key, '%c') ~= nil
local has_extra_fields = find_text(index_tail, '%S') ~= nil
```

回退的 `string.find` 只用于没有 CA 扩展的标准 Lua 环境；WH3 内应选到 `string.find_lua`。保持这个别名局部化，不要在 MOD 中改写全局 `string.find` 而影响其他脚本。

两参数 `key:find('%c')` 虽没有参数数目错误，在 CA 实现中仍会搜索字面量 `%c`，无法检测控制字符；`tail:find('%S')` 同理，可能漏掉未知索引字段。检查参数数目之外，还要检查模式语义。需要 UTF-8 字符位置的业务不能直接批量替换为字节索引，应先核对返回位置的使用方式。

## 识别跨 MOD 的故障链

在已核验的本机版本中，四参数 `string.find` 会将栈顶布尔值误交给原生字符串读取器，读取失败后清除共享脚本上下文的有效标志。后续原生接口可能停止压入正确返回值，却仍声明返回若干结果，于是原参数被当作结果：例如 `string.len(timestamp)` 返回字符串，UI 查询返回 boolean/table。

因此故障可能表现为队列加点停止、窗口不能关闭、切换角色后 UI 错乱，继而闪退；错误日志却落在日志库、控制台或其他 UI MOD。`pcall` 只能捕获 Lua 错误，不能恢复上述原生状态。暂时去掉日志、延迟回调或改用另一升级事件，也不会修复仍存在的违规调用。

出现这种组合症状时：

1. 找到触发操作前最后一条正常日志，沿真实调用链检查紧接着执行的 API。不要因为最后一条日志是内存读取完成，就直接认定读取器损坏了状态。
2. 查看当前 `script_log_*.txt`，并按实际安装情况查看其他错误捕获日志。多个无关模块同时出现返回类型异常，是检查共享原生接口的线索，不是单凭症状判定 `string.find` 的证据。
3. 搜索 `string.find(`、`:find(` 及函数别名，计入冒号接收者，核对参数数目、参数类型和模式。纯文本搜索只能筛选候选，不能证明动态拼接或多行调用全部正确。
4. 若参考 MOD 对同一角色已实际完成队列自动加点，比较两条执行路径独有的原生调用。不要把事件名、延迟时间或提交节奏的差异自动当作原因。
5. 需要解释原生损坏时，读取当前 EXE/文档并记录版本或 SHA；更新后的程序必须重新核验，不能直接复用历史 RVA。退出清理阶段的二次崩溃栈不等于最初故障点。

## 离线测试必须覆盖 CA 的契约

标准 Lua 原本支持四参数 `string.find` 和模式匹配，因此单元测试甚至真实 memreader DLL 配合标准 Lua 宿主的检查，也可能全部通过，却遗漏 CA 的替换接口。

对涉及字符串搜索的 WH3 离线测试，在加载待测模块前保存原始 `string.find` 为测试进程的 `string.find_lua`，再用替身模拟 CA 的关键契约：

- `string.find` 拒绝第四参数，并把每次违规独立记录；每个用例结束时检查记录，使被待测代码 `pcall` 吞掉的违规仍会导致测试失败。
- 两参数/三参数 `string.find` 使用字面量搜索，不能让 `%c`、`%S` 在替身中继续按模式工作。
- 待测代码的 `string.find_lua` 保持原始 Lua 的四参数和模式功能。测试框架自己的搜索也应使用它，避免框架误触替身。
- 用玩家实际路径做回归：已有技能与队列 → 保存/读档 → 升级事件 → 规划 → 加点提交 → 审计；另覆盖无 errno 的文件缺失错误、含控制字节的技能 key、未知索引字段。
- 先证明旧代码在此契约下失败，再验证修复。替身通过只能证明这些契约及业务路径；若只模拟字节搜索，它不能证明完整 UTF-8 索引行为，更不能声称复刻实际原生崩溃或替代用户游戏复测。

仅在测试进程中替换全局函数，不把测试替身装进游戏。随包提供 [ASCII 契约替身](../scripts/tests/wh3_strings.lua) 与 [独立契约回归](../scripts/tests/test_ca_string_contract.py)，无需原作者的 MOD 或测试目录。安装本技能的 [分析与测试依赖](../scripts/requirements-analysis.txt) 后，在本技能目录运行 `python -X utf8 -B -m unittest discover -s scripts/tests -p test_ca_string_contract.py -v`。该替身只校准参数个数、ASCII 字面量/模式及违规记录；玩家业务路径仍在目标 MOD 的测试中补齐。用户禁止单元测试时，执行静态签名核对并明确留下测试边界。

## 来源与本次案例边界

- CA 原文快照：[lua.html](../../warhammer-ui/references/sources/documentation/script/campaign/lua.html)，按 `function:string:find` 与 `function:string:find_lua` 锚点查找。当前快照相关行是 1058–1062、1126–1130；其中说明文字有将 `find` 误写成 `len` 的复制笔误，签名和模式说明仍可核对。
- 2026-10-05 本机 EXE SHA256：`fec656f433dd7eb2bf47c889d91dd36b8242b0e631b3608a0453838e373f3785`。该版本的 `find` 注册至 RVA `0x135b728`，字符串读取失败在 `0x1359ffb` 清除上下文有效标志；这些地址是案例证据，不是稳定 API。
- SkillPreset 的规划路径在快照完成后执行四参数查找，随后日志库发生字符串算术错误，其他 UI MOD 得到错误类型。改用 `find_lua` 后，新增 4 项离线回归由失败变为通过，两份 Pack 回读测试各 150/150，Error 0；当时游戏内恢复仍待用户确认。这些验证结果不能推广为所有闪退都已解决。
