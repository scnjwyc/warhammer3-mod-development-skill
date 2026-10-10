# 运行时内存与反汇编研究

用于 DB、Lua、CCO 或日志不足以解释的原生引擎行为。先明确待验证的机制和观测量，再沿字符串/常量 → 引用 → 函数范围 → 调用链 → 对象数据流建立证据。结合 [Lua 离线回归](lua-offline-testing.md) 校验外围脚本，但 mock 不能证明原生实现。

若用户已提供 Warhammer MCP 的 Lua、UI 或战役快照，先按 [MCP 证据工作流](wh3-mcp-workflow.md) 核对请求来源、上下文、版本和触发前后状态，用实际字段值、事件名及错误文本选研究锚点。MCP 没有原生 dump 或偏移恢复能力；快照缺字段、接口成员存在或 `pcall` 成功均不能证明引擎内部机制。

## 采集分工与样本身份

本项目不允许 Agent 启动、重启或间接启动游戏。游戏启动、进入目标场景和运行采集命令由用户操作；Agent 整理命令、检查用户提供的文件并离线分析。采集器只查询、读取已有 PID；没有启动游戏、调试附加、暂停线程、注入或写内存功能。跨页读取可能失败，运行中的数据也可能在采集期间变化，镜像不是原子快照。

把磁盘 EXE、按 RVA 排列的模块镜像、任意内存块和 Windows minidump 分开处理。磁盘文件的节原始偏移通常不等于 RVA；minidump 要解析流表和内存映射。只有本工具的 `mapped-pe` 镜像满足 `文件偏移 = RVA = VA - 本次模块基址`。原包的固定 `0x140000000`、固定函数/字段地址和“所有磁盘 EXE 都已加密”是样本经验，不能当版本规则。熵较高也不能单独证明 DRM；先查看本次磁盘代码节是否可用，再决定是否需要运行时样本。

每份研究记录：游戏版本/平台、磁盘模块路径与 SHA-256、PID、采集起止时间、用户操作与 MOD 组合、实际模块基址和 SizeOfImage、dump 与 layout 的 SHA-256、可读区间/空洞、分析工具与 Capstone 版本。跨样本引用优先用 `模块身份 + RVA`；实际 VA 按该样本基址计算。磁盘模块哈希与运行时 dump 哈希各有用途，不能互相替代。

## 用户采集入口

工具路径相对本 skill 根目录。Windows 64 位 Python；采集只需标准库，反汇编需 Capstone（当前验收版本 5.0.7，换版本后跑随附回归）。先查已有环境 `python -c "import capstone; print(capstone.__version__)"`，缺依赖时用随包 [依赖清单](../scripts/requirements-analysis.txt) 安装到选定 Python 环境。

用户手动启动并进入相关场景后，用实际 PID 和完整模块路径采集，输出目录放在专门的研究目录：

```powershell
python scripts/capture_module.py --pid <PID> --module "<实际模块完整路径>" --list-only
python scripts/capture_module.py --pid <PID> --module "<实际模块完整路径>" --out-dir "<研究目录>/capture"
```

`--module` 可指定 DLL；同名模块存在歧义时必须用完整路径。脚本自动枚举实际基址/SizeOfImage，跳过 guard、未提交和无读权限页面；失败/部分读取留零且记录空洞，零填充不能作为真实数据。拒绝访问、PID 退出或枚举失败时保留错误事实，不自动启用调试特权。采集期间退出可留下不完整文件；只有完整的 bin + layout 且哈希匹配才进入下步。

主模块采集不包含普通堆、动态生成代码或所有 DLL。后续若需要对象内存块，先确定指针所属分配、长度与生命周期，让用户用合适的只读采集器采集并记录原始 VA/可读区间；不要在主模块中找不到数据时断言对象不存在。处理已有 minidump 时可用 WinDbg/Ghidra 等解析格式，导出明确地址映射后再分析。

## 镜像校验与工具入口

```powershell
python scripts/wh3_dump.py --dump "<样本>.bin" --layout "<样本>.layout.json" info
python scripts/wh3_dump.py --dump "<样本>.bin" --layout "<样本>.layout.json" anchors --anchor "<RVA>=<空格分隔的十六进制字节>"
```

工具验证 schema、bin 哈希、长度、AMD64/PE32+、SizeOfImage 和读区间，跳过空洞；`info` 列出函数范围数量、未读区和异常目录诊断。历史采集器的旧 layout 不能直接冒充当前 schema，迁移时必须从旧读失败/region 信息重建覆盖范围并保存来源。

首次研究先确认 PE 头、相关节、异常目录和独立的场景字符串；已知版本再验证相关函数字节与常量。锚点失败时先区分地址漂移、字节变化、读失败和按需解密，暂停依赖该锚点的结论。几个锚点通过只证明那些局部范围可用，不能宣布全镜像有效。工具不会自动选“最新 dump”。所有命令输出 JSON，可用 `--out <结果.json>` 保存，文件已存在则拒绝覆盖。

## 从锚点到函数和调用链

1. 选具有场景语义的错误消息、状态键、UI/CCO 名、DB key 或常量；分别搜 ASCII/UTF-8/UTF-16LE，并保留所有位置与实际总数。相同文本可能对应不同系统，先用邻近常量与原版脚本交叉筛选。
2. 定位 RIP-relative `lea`、`mov` 等内存操作数，不只扫一种 LEA 字节模式；记录引用指令、目标 RVA、函数范围和读取/写入/取地址区别。确认从可信入口沿控制流到达该指令，区分数据中的偶然指令字节。
3. 优先使用 PE 异常目录的 `RUNTIME_FUNCTION` 起止 RVA。它给出展开范围，可能缺少叶函数，也可能把一个逻辑函数拆成多个范围。工具按范围入口走条件分支、直接跳转和 fallthrough；遇到返回只终止当前分支。间接跳转/跳转表、异常处理路径和重叠入口仍需人工 CFG 核验。`CC` 填充、对齐和常见 prologue 只生成候选，未经核验不能宣称函数起点。
4. 建图保存 `调用指令 RVA → caller 范围 → target RVA → callee 范围`，再按函数范围做反向 BFS。跨模块目标保留 VA，间接调用保留操作数；尾跳转单独标记。原包用调用点继续 BFS 会漏掉第二层。图缓存绑定 dump/layout/工具/Capstone 身份，不匹配则重建。
5. 搜小端 64 位绝对函数地址，检查所在节、8 字节对齐、相邻指针和实际间接调用形态，提出虚表/回调候选。绝对地址命中本身不能证明虚表；缺少直接 call 与指针命中也不能证明调用方在主模块外，仍可能有间接调用、尾调用、内联、编码指针或采集缺口。

```powershell
python scripts/wh3_dump.py --dump <bin> --layout <layout> find --text "taking_damage" --encoding ascii
python scripts/wh3_dump.py --dump <bin> --layout <layout> find --text "<关键词>" --encoding utf-16le
python scripts/wh3_dump.py --dump <bin> --layout <layout> xref --target <字符串RVA> --out refs.json
python scripts/wh3_dump.py --dump <bin> --layout <layout> disasm --rva <指令RVA> --out function.json
python scripts/wh3_dump.py --dump <bin> --layout <layout> graph --out graph.json
python scripts/wh3_dump.py --dump <bin> --layout <layout> callers --target <函数RVA> --graph graph.json --depth 4
python scripts/wh3_dump.py --dump <bin> --layout <layout> pointers --target <函数RVA>
```

代码查询默认扫描异常目录范围；聚焦分析可加 `--range <入口RVA>:<结束RVA>`（也可重复指定）。这是由研究者核验的手工范围，工具不把它伪装为自动识别。没有可信范围时可以 `candidates --target <RVA>` 扫 E8 原始字节超集，用于找线索；它不参与已核验调用图。全图扫描成本较高，先围绕锚点聚焦，再按需要扩大。结果中的 decode stop、空洞、上限截断和间接分支均是覆盖限制，保留到报告中。

## 结构体与字段数据流

按下面顺序收敛；每一步都写下可推翻当前猜测的观测：

1. **步长候选**：查真实解码的 `imul imm`、地址递增、移位/LEA 组合及分配尺寸。立即数/聚集密度只能提出候选；还要核对循环边界、元素数、对象指针和相邻记录。一个乘数也可能是索引、二维数组或非对象常量。
2. **字段访问**：使用 Capstone 操作数类型、`op.size`、`mem.base/index/scale/disp/segment` 与 `CS_AC_READ/WRITE` 记录访问，不用格式化汇编文本正则判断读写。这样同时处理十进制小偏移、读改写指令和 SIMD 写入。排除 RIP/栈基址只是筛选条件，不能证明其余基址就是目标对象；FS/GS 相对寻址还需对应线程的 segment base。
3. **数据流核验**：从 stride/分配/调用参数追踪对象基址的寄存器来源、别名和跨块赋值，再核对写入宽度、整数有无符号、浮点转换、哨兵、clamp、时间顺序与读取用途。`血量 = 满血 - 伤害` 的解释须由源值、运算及后续消费者共同支持；同一函数里相邻的 imul 与写入不自动构成同一个对象的数据流。
4. **交叉证明**：用多个函数/锚点、相邻字段和用户提供的场景 A/B 样本验证。对 heap 对象检查父指针、数量、有效范围、对象类型和生命周期；重复数值/float 序列只能证明字节匹配，不能单独证明字段含义。保存字段访问直方图时同时记录基址类别、访问宽度、样本和候选类型。

```powershell
python scripts/wh3_dump.py --dump <bin> --layout <layout> fields --stride <候选步长> --offset <字段偏移> --out fields.json
python scripts/wh3_dump.py --dump <bin> --layout <layout> --range <入口>:<结束> fields --offset 0xb0 --offset 0xb4
python scripts/wh3_dump.py --dump <bin> --layout <layout> find --hex "<字节模式>" --context 32
python scripts/wh3_dump.py --dump <任意二进制> --format raw find --text "<关键词>"
```

`fields` 返回 stride 命中、内存读写和按基址/索引/位移/宽度分组的直方图；`--offset` 只筛候选位移，`--stride` 只筛出现该立即数的函数范围，**不会自动证明寄存器之间的对象归属**。`raw` 的搜索只报告文件偏移，适用于 pack/minidump 的字节线索；它不解析这些格式，也不生成 VA。

## 研究收尾与后续 MOD 接入

每条结论写出：待验证机制、样本身份、锚点、RVA/原始字节/解码指令、入口与关键分支、调用点和上下游、对象/字段推导、支持与反证、覆盖缺口及下一项用户操作。区分“字节命中”“有边界与数据流支持的静态推断”“用户运行时观测”“用户游戏效果确认”。有指令证据仍不等于该场景实际执行过，时间窗读数也不等于因果证明。

优先把研究结果映射到原生 DB、Lua、CCO 或现有兼容接口；研究本身不授权 hook、内存写入或持久补丁。需要这些实现时作为新的具体方案单独界定。实际 MOD 变更继续遵守本地源文件 → 映射 Pack → 关闭重开逐条读回 → Error 诊断的项目流程。

归档 bin/layout、原始来源与场景记录、可复现命令、JSON 图/命中/字段表及关键 ASM 摘录。只复用身份匹配的缓存；版本更新后重新验证锚点/函数范围/结构布局。

## 契约与验收来源

- 方法来源：分享版 `wh3-runtime-dump`；保留锚点、xref、调用链与字段研究路径，修正固定地址、自动启动游戏、函数边界与缓存假设。本文及随包工具已包含采用的方法，不需要另行提供原包。
- [Microsoft PE 格式](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format)：磁盘偏移、RVA、VA 和异常目录；[x64 展开范围](https://learn.microsoft.com/en-us/cpp/build/exception-handling-x64)：RUNTIME_FUNCTION 与叶函数边界。
- [ReadProcessMemory](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-readprocessmemory)、[VirtualQueryEx](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualqueryex) 与 [Toolhelp 模块枚举](https://learn.microsoft.com/en-us/windows/win32/api/tlhelp32/nf-tlhelp32-createtoolhelp32snapshot)：采集契约。
- [Capstone Python 接口](https://www.capstone-engine.org/lang_python.html) 与 [x86 操作数定义](https://github.com/capstone-engine/capstone/blob/5.0.6/bindings/python/capstone/x86.py)：detail/操作数访问属性，换版本后核验。
- 本工具回归：`python -B -m unittest discover -s scripts/tests -v`。合成镜像/假读取器验证算法，独立的 Python 测试进程验证 Windows x64 API 与端到端采集；实际 WH3 采集与游戏行为由用户提供样本验收。
