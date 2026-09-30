# TWUI Studio 数据模型、编辑与持久化研究

研究基准：2026-09-27，`Backmechuisa/TWUI_Studio`，commit `7e3e1be568fac3f5e9362d0494665fc549dc22eb`。本报告来自克隆源码、上游测试源码和文末可重放探针。描述的是这个版本的工具行为；不把其容错、预览或诊断规则当成 CA 游戏引擎的完整规范。

## 1. 总体原理：保留 XML 原文，建立另一套可编辑索引

`Document` 先用 `validation_source()` 生成仅供 ElementTree 校验的副本，再对原文进行词法扫描。每个 `Node` 保存 `tag/start/end/attrs/parent/children`，有闭合标签时另记 `close_start`。`start/end` 是 Python 字符串偏移，不是 UTF-8 字节偏移。`Document.source` 始终保留输入字符串。属性读取仅解码 XML 实体，避免把 CCO 中的 `&not` 等片段按 HTML 实体误解码。[源码：model.py:5–55](../vendor/TWUI_Studio/model.py#L5-L55)

游戏文件的属性可能出现字面量 `&&`、`<`。校验副本将这些转义后交给 ET；原始内容不随之改写。该容错仅针对属性，不会顺手修复 XML 文本内容里的非法裸 `&`，也不会放过错误闭合标签。`patch()` 则定位指定开始标签，只替换、添加或删除指定属性，最后按位置倒序拼接，避免前一处长度改变使后续坐标失效。新写入的属性值用 `html.escape(..., quote=True)` 转义；未编辑的属性保持原样。[源码：model.py:13–21、78–119](../vendor/TWUI_Studio/model.py#L13-L21)；[补丁实现](../vendor/TWUI_Studio/model.py#L78-L119)；[兼容性测试](../vendor/TWUI_Studio/test_xml_compat.py)

因此，改一个布局数值时应沿用小范围属性补丁，不宜把整个文档经通用 XML serializer 重写。工具所谓“保留原始字节”主要由原始字符串保留、UTF-8 编解码、单独恢复 BOM 共同实现；不是直接修改字节数组。导入走 `read_bytes().decode('utf-8-sig')`，记录 BOM；保存时写 `doc.source.encode('utf-8')` 并按记录补 BOM。[导入：multidoc.py:136–150](../vendor/TWUI_Studio/multidoc.py#L136-L150)；[保存：app.py:172–178](../vendor/TWUI_Studio/app.py#L172-L178)

## 2. hierarchy 与 components：两种树，不可混淆

`layout/hierarchy` 表达组件父子关系；`layout/components` 是组件定义列表。层级节点的 `this` 与组件定义的 `this` 连接。组件定义内部的 `states`、`componentimages`、`callbackwithcontextlist` 等是组件内部数据，不能当作 UI 子组件。`Document` 要求根下同时存在 `hierarchy` 与 `components`，随后由 `inspect_document()` 构造 `by_guid/parents/children`。[源码：model.py:50–55](../vendor/TWUI_Studio/model.py#L50-L55)；[diagnostics.py:27–99](../vendor/TWUI_Studio/diagnostics.py#L27-L99)

索引生成不会简单做“相同 GUID 最后一项覆盖前一项”。它先看 GUID 与名称的唯一匹配，再考虑唯一 GUID、未占用的唯一名称；仍不能确认时用 placeholder 保留层级。重复层级项使用 `@hierarchy/...` 临时运行键，未被层级使用的定义作为 unlinked 节点保留。临时运行键只服务编辑器，不回写 XML。缺定义的父节点仍可显示有效子节点。这解释了为什么损坏的 XML 能打开、能显示红色诊断，但不等于连接已修好。[源码：diagnostics.py:40–105](../vendor/TWUI_Studio/diagnostics.py#L40-L105)；[测试](../vendor/TWUI_Studio/test_diagnostics.py)

### 常见字段的实际作用

| 位置 / 字段 | 工具如何使用 | 实操含义与边界 |
|---|---|---|
| `hierarchy/*@this` | 查找组件定义并建立父子索引 | 移动组件主要改这里，不能只移动 components 定义顺序 |
| `components/*@this` | 组件身份、编辑和选择键 | 新组件应有新 GUID；改 ID 不等于改 GUID |
| `uniqueguid` | 诊断组件身份一致性；复制时重映射 | 组件级存在且与 `this` 不同会报错；这不是对所有模板字段的完整规范 |
| `id` | 可读名字、兄弟重名判定、重命名入口 | 实际脚本可能按名字找组件，重命名后需另查 Lua/CCO |
| 组件标签名 | 与 hierarchy 标签、`id` 做一致性判断 | 编辑器会去除 ID 中的圆括号生成 XML 标签，ID 本身保留圆括号 |
| `currentstate` / `defaultstate` | 指向本地 state 的 `this` | 查找优先级见下一节；不能仅凭预览认定游戏状态切换正确 |
| `states/*@this`、`name` | 本地状态身份与显示名称 | 复制状态生成新身份；同一组件可有多组尺寸、图像度量、文本 |
| `componentimages/component_image@this`、`imagepath` | 图像声明身份与资源路径 | 声明与显示度量分开；单有图片声明不代表该状态会画它 |
| `states/*/imagemetrics/image@componentimage` | 连接同组件的图像声明 | 状态图像度量可以共享同一图片声明 |
| `template_id` | 给模板候选文件消歧，可向 hierarchy 祖先查找 | 不是完整继承展开器；只读候选文件路径 |
| `uniqueguid_in_template` | 解析实例所引用的模板组件 | 不应当成实例 `this` 任意重建 |
| `state_uniqueguids/state_uniqueguid@uniqueguid,name` | 模板实例的状态列表 | 这里使用 `uniqueguid`，与普通 `states` 的 `this` 路径不同 |
| `localised_texts/localised_text@state` | 按状态名称匹配本地文本覆盖 | 工具仅编辑已有对应项，未找到时不会自动创建 |
| `localised_text@text_label` | 模板实例的文本键字段 | 与普通 `component_text@textlabel` 拼写不同，不能互换 |
| `callback_with_context` | 编辑 callback、CCO context、表达式属性 | 保存字符串并不验证其游戏运行语义 |
| `LayoutEngine` | 容器布局配置，独立于 hierarchy | 重排 hierarchy 与修改布局引擎是不同操作 |

表中身份与状态字段来源见 [model.py](../vendor/TWUI_Studio/model.py#L56-L77)、[state_edit.py](../vendor/TWUI_Studio/state_edit.py#L16-L51)、[template_states.py](../vendor/TWUI_Studio/template_states.py#L6-L49)、[states_editor.py:137–176](../vendor/TWUI_Studio/states_editor.py#L137-L176)、[inspector.py:71–112](../vendor/TWUI_Studio/inspector.py#L71-L112)。这里只列源码已实际解释的作用，未给未知属性猜测引擎含义。

## 3. 本地状态与模板状态

`Document.state(c)` 只查看本组件的 `states`：如果存在 `currentstate` 属性就用它，否则用 `defaultstate`；找不到该 GUID 时返回第一个 state。具体边界是：**存在但无效的 currentstate 不会继续尝试有效的 defaultstate**。文末探针设 `currentstate=missing/defaultstate=second`，返回 `first`。这是预览模型的回退行为，不能据此改写游戏状态机。[源码：model.py:56–59](../vendor/TWUI_Studio/model.py#L56-L59)

新增本地状态默认生成 `NewState_N`、100×30 和新 UUID；只在当前/默认状态未设置时补这两个引用。复制状态为其 `this` 声明生成新 GUID，保留指向外部图像声明的 `componentimage`。删除状态时，引用它的 current/default 改到剩余第一个状态；最后一个状态删除后移除 states 容器与这些引用。新建 image metric 必须选择本组件已有图像声明。`merge_states()` 把状态子树和 current/default 合并回目标文档，保留其他属性页的修改。[源码：state_edit.py:16–78](../vendor/TWUI_Studio/state_edit.py#L16-L78)；[测试](../vendor/TWUI_Studio/test_state_edit.py)

`state_items()` 优先返回本地 `states`，只有不存在本地 states 才返回 `state_uniqueguids` 并进入模板模式。模板索引从原始 UI 根下 `templates/**/*.xml` 读取 components，将 `this` 和 `uniqueguid_in_template` 建索引。实例按 `uniqueguid_in_template` 匹配，再沿自己和 hierarchy 祖先的 `template_id` 缩小候选文件；不同候选只有内容完全一致才接受多重命中，否则返回未解析。索引按资源根缓存，文件改变后要手动刷新或重建索引。[源码：template_states.py:6–49](../vendor/TWUI_Studio/template_states.py#L6-L49)

模板模式禁用增删状态、复制状态、设为当前/默认等按钮。原始状态按 `name` 匹配，显示模板源码与图片路径，明确标为只读且可能不同于最终值。可编辑的是当前 XML 中已存在、`state` 匹配的 `localised_texts` 文本属性；没有项只显示提示。`merge_template_texts()` 对初始/草稿/当前三份文档逐项检查文本数量、state 对应关系，只应用实际修改的属性，避免覆盖其他页面改动。[源码：states_editor.py:50–63、109–176](../vendor/TWUI_Studio/states_editor.py#L50-L63)；[模板编辑](../vendor/TWUI_Studio/states_editor.py#L109-L176)；[合并](../vendor/TWUI_Studio/template_states.py#L51-L63)

**不要把这套模板支持理解为完整继承求值。** 模板读取发生在状态属性页；上游测试专门要求缩放/fit 不触发模板加载。`TemplateIndex` 没有递归计算模板链的最终覆盖值，且用严格 `ET.fromstring(path.read_bytes())`，并未使用 Document 的属性容错。文末探针确认：裸 `&&` 模板可被 Document 接受，但索引会记录解析错误，解析不到实例。[源码：template_states.py:17–23](../vendor/TWUI_Studio/template_states.py#L17-L23)；[模板测试](../vendor/TWUI_Studio/test_template_states.py)

## 4. 重命名、复制、删除、移动并不是通用引用重构

`Document.rename()` 修改目标定义的 `id`、定义起止标签、对应 hierarchy 起止标签，保持 GUID。它检查名字格式、同父级 ID 和不安全身份连接；圆括号保留在 ID 中、从标签名去除。它不扫描 Lua、不重写 CCO 名称路径、不替换任意属性内的旧名字。用户要求“改控件名”时，技能应另查依赖它的脚本/CCO，再修改运行时引用。[源码：model.py:60–77](../vendor/TWUI_Studio/model.py#L60-L77)；[测试](../vendor/TWUI_Studio/test_component_editing.py)

`copied_component()` 抽取整段 hierarchy 子树及其各组件定义，给其中 `this/uniqueguid` 声明创建新 UUID，默认根节点改名为 `_copy_N`。它先检查 `currentstate/defaultstate/componentimage` 是否有复制范围外且目标文档也没有的引用，再插入新定义和层级。需要特别注意：实际 remap 对**所有属性**生效，只要整个属性值恰好等于被重映射 GUID；不是仅改身份字段。因此 `text="旧GUID"` 也会被改，含 GUID 的长字符串则不改。对自动复制成果需要检查文本、模板身份与不在三个已知引用字段中的特殊引用。[源码：component_edit.py:7–51](../vendor/TWUI_Studio/component_edit.py#L7-L51)

`deleted_component()` 同时删 hierarchy 子树及全部关联 definitions，禁止删顶层 root；只检查其他节点的三个已知引用字段是否指向将删内容。它不证明 Lua/CCO、布局路径、其他 XML 或动态生成控件不存在外部使用者。另外，`subtree()` 在文档的 `unsafe_keys` 非空时会阻止复制/删除/重排，影响范围不只当前子树。[源码：component_edit.py:9–15、53–61](../vendor/TWUI_Studio/component_edit.py#L9-L15)；[删除实现](../vendor/TWUI_Studio/component_edit.py#L53-L61)

实际 UI 的剪切粘贴和改父节点调用 `hierarchy_edit.move()`，不是同仓库的旧 `component_edit.moved_component()`。前者检查 GUID 唯一、自指、循环并保留 definitions，但没有后者的同名兄弟拦截；探针已证实可以移动后留下 `duplicate_name`。剪切只是记录 `(source,key)`，真正粘贴才移动；如果其间文档改变，取消待剪切以免用旧偏移修改新文档。[入口：multidoc.py:190–244](../vendor/TWUI_Studio/multidoc.py#L190-L244)；[当前移动实现：hierarchy_edit.py:34–50](../vendor/TWUI_Studio/hierarchy_edit.py#L34-L50)；[旧实现](../vendor/TWUI_Studio/component_edit.py#L63-L73)

`detach()` 删除的是整段层级引用，保留所有定义；原子树的父和孩子都成为 unlinked。之后重新 attach 父节点时，仅创建该父节点单独的 hierarchy 项，原先孩子不会自动接回。上游 `test_detach_and_attach_unused` 和文末探针均确认这一点。若要保留整个子树关系，直接 move；不能把 detach→attach 当成可逆移父流程。删除缺定义的 wrapper 则是另一种操作：`remove_missing()` 只去外壳、保留里面孩子及其顺序。[源码：hierarchy_edit.py:19–50](../vendor/TWUI_Studio/hierarchy_edit.py#L19-L50)；[测试](../vendor/TWUI_Studio/test_hierarchy_edit.py)

`reordered_children()` 要求新顺序是所有直接孩子的完整、不重复排列，仅交换完整 hierarchy 片段；组件 definitions 保持不动。图片声明删除走 `inspector_structure.edit_section()` 时会同时删除本地 states 中引用它的 image metrics，避免留下已知悬空图片引用。[排序源码](../vendor/TWUI_Studio/component_edit.py#L75-L87)；[图片删除源码](../vendor/TWUI_Studio/inspector_structure.py#L54-L70)

## 5. 草稿、undo、项目与 XML 导出

属性窗口基于打开时的 baseline 编辑局部草稿。`collect_source()` 合并普通属性、states、布局和 user properties，最后 rename；应用前检查实际文档仍等于打开时基准，否则要求重新打开属性窗口。局部输入框、状态页各有 history，整文档提交后另记标签页操作快照，不能把正在填写但未应用的字段当成已经写回文件。[源码：inspector.py:149–175](../vendor/TWUI_Studio/inspector.py#L149-L175)；[输入框 history](../vendor/TWUI_Studio/edit_support.py#L3-L27)；[状态页 history](../vendor/TWUI_Studio/states_editor.py#L104-L136)

标签页 undo 保存整份 XML 及 locks、hidden、focus、root_lock、selected，最多 20 次；新操作清空 redo。恢复时重建 Document，因此会重新诊断。多标签各自保存 undo/redo 列表；项目 snapshot 只写 payload，不保存这两个内存历史栈。重开项目会保留当前/原始 XML 和视图等项目数据，但不能期待此前的 20 步 undo 还在。[源码：tab_history.py:3–35](../vendor/TWUI_Studio/tab_history.py#L3-L35)；[multidoc.py:54–81](../vendor/TWUI_Studio/multidoc.py#L54-L81)

应区分四种“保存”：

| 操作 | 实际产物 | 不能假定的事 |
|---|---|---|
| Tab checkpoint | 更新内存 `checkpoint_xml` 与标签 dirty 状态 | 不立即写磁盘 |
| Save project | `.twuiproj` JSON，version 2 装多个 version 1 文档 | 游戏不会直接加载项目文件；不是 Pack |
| Save XML as | 当前 XML 原文加可选 BOM | 不自动导入 RPFM，不连带输出 LOC/Lua |
| Export XML + images | ZIP，XML 与直接识别到的图片保留 `ui/` 路径 | 不收集全部依赖闭包；模板、其他 XML、LOC、Lua 仍需另准备 |

来源：[checkpoint](../vendor/TWUI_Studio/multidoc.py#L256-L270)、[项目验证与写入](../vendor/TWUI_Studio/project.py#L16-L58)、[导出提示](../vendor/TWUI_Studio/workspace.py#L116-L127)。

项目保存校验 XML 可解析、视图数据类型和有限数值等，再同目录写临时文件、`os.replace` 原子替换。ZIP 导出收集所有 `imagepath` 及属性中的 `[[img:ui/...]]`，要求路径从 `ui/` 开始，拒绝绝对路径、`.`、`..`、空路径段、冒号等；任一图片找不到或路径非法即不覆写旧 ZIP。成功时图片按大小写不敏感路径去重，XML按原文保存。**export_zip 没有把 diagnostics error 作为门禁**，文末探针已成功导出含 missing_definition 的 XML。[源码：project.py:7–14、60–96](../vendor/TWUI_Studio/project.py#L7-L14)；[导出实现](../vendor/TWUI_Studio/project.py#L60-L96)；[项目/导出测试](../vendor/TWUI_Studio/test_workspace.py)

## 6. XML 格式化的保护范围

`xml_format.format_xml()` 先后各构建一次 Document 校验，以词法 token 重排缩进。hierarchy 内保持属性同一行，其他节点可把属性拆行；属性片段直接复用，不重新转义其值。换行风格从原文是否含 CRLF 判断。遇到 token 之间非空白文本时拒绝自动整理，以免改变混合文本。它会改变标签间空白和文件末尾换行，因此“只改一个属性”时不应顺带全量格式化。上游测试检查格式化幂等、节点/属性语义保持、字面表达式保持，以及连续移动不累积空行。[源码：xml_format.py:6–36](../vendor/TWUI_Studio/xml_format.py#L6-L36)；[测试](../vendor/TWUI_Studio/test_xml_format.py)

## 7. 诊断实际覆盖、修复边界与使用规则

| code | 实际检查 |
|---|---|
| `missing_definition` / `unresolved` | 层级引用没有可确定的组件定义 |
| `guid_mismatch` | 可按名字辨认组件，但层级与定义 GUID 不同 |
| `name_mismatch` | hierarchy 标签、组件标签、ID 的关系不一致；纯 ID 差异常为 warning |
| `orphan` | 定义未被 hierarchy 使用，通常为 info |
| `duplicate_reference` | hierarchy 多次引用同一 GUID |
| `duplicate_guid` | 多个组件定义复用同一 `this` |
| `missing_guid` | 组件定义缺少 `this` |
| `identity_mismatch` | 组件 `uniqueguid` 存在却不等于 `this` |
| `duplicate_name` | 同一父节点下实际组件 ID 重名；不是全文件禁止重名 |
| `internal_duplicate` | 单组件内部多个节点重复声明同一 `this` |
| `dangling_reference` | `currentstate/defaultstate/componentimage` 在该组件的 `this` 声明集合中找不到 |

全部检查来自 [diagnostics.py:27–150](../vendor/TWUI_Studio/diagnostics.py#L27-L150)。若一个问题只涉及 unlinked 组件，严重性还会被降为 info。初次打开只弹 error，warning/info 仍在完整问题列表里。[严重性测试](../vendor/TWUI_Studio/test_diagnostic_levels.py)

这是一组身份结构检查，不是完整 TWUI schema 或游戏验证器。它没有验证 GUID 是否符合标准 UUID 字符格式；没有校验 CCO 函数/事件有效性、Lua 调用、字体/shader 运行时存在性、按钮是否接收输入；图片文件存在性由资源解析/导出阶段另外检查。其内部声明集合只收集 `this`，所以模板实例的 `state_uniqueguids/*@uniqueguid` 可被误判为悬空 current/default 引用。不能为了消除该诊断而把模板状态擅自展开或删掉引用；先核对对应模板、原版实例和游戏表现。[源码：diagnostics.py:123–132](../vendor/TWUI_Studio/diagnostics.py#L123-L132)；文末探针有最小复现。

自动修复同样受限：`repair_hierarchy_guids()` 只对唯一名称、唯一目标且没有竞争定义的可辨认连接更新组件 `this`，存在 `uniqueguid` 时一起更新；`repair_duplicate_guids()` 只复制无歧义的重复叶节点定义并更新已知身份/引用属性，故意不全局替换文本/CCO。非叶子重复、真正歧义或未知引用需要人工基于来源核对。[源码：diagnostics.py:152–193](../vendor/TWUI_Studio/diagnostics.py#L152-L193)；[对应测试](../vendor/TWUI_Studio/test_diagnostics.py)

供后续 UI 技能采用的实操规则：

1. 先读当前源 XML 与 diff，辨明是本地 states 还是模板 state_uniqueguids；保留未理解的属性、模板关联与表达式。
2. 定位控件时同时记 `id/this/hierarchy 父链`；不要只按可重名 ID 全文替换。
3. 普通属性小范围补丁；新组件同时创建 definitions 与 hierarchy；复制后审查 GUID、文字、模板字段与外部引用。
4. 移父时直接 move 完整子树，并核对兄弟重名；不要 detach 后期待自动恢复孩子。
5. 状态编辑后核对 current/default、每个状态尺寸/文本/图片连接；预览的首状态回退可能掩盖坏引用。
6. 读取并分类诊断结果；与当前原版/已知基线比较，不对模板特性或原版固有报告盲目自动修复。
7. XML、项目和 ZIP 各自确认真实落盘内容。源文件修改完成后遵循项目 AGENTS 的映射源 Pack 导入与 Error 诊断流程；本工具本身没有代办该流程。
8. 导出成功之后仍需游戏内验证 Lua/CCO、状态转换、真实字体、输入响应和布局。此研究未运行战锤3，不能用源码测试替代游戏结果。

## 8. 可重放的七项边界探针

以下独立 Python 片段已在该 commit 上通过执行，退出码 0。它只使用工具模块和标准库，不启动 GUI、不修改仓库/游戏文件；临时模板和 ZIP 位于自动清理的 TemporaryDirectory。计为七类行为（复制类同时输出精确匹配和嵌入字符串两项）。从 `../vendor/TWUI_Studio` 目录把代码保存到临时 `.py` 后 `python -B <文件>`，或 PowerShell here-string 管道给 `python -B -` 即可。

```python
import json
import tempfile
from pathlib import Path
from model import Document, Resources
from component_edit import copied_component
from hierarchy_edit import move, detach
from template_states import TemplateIndex
from project import export_zip

def xml(hierarchy, components):
    return ('<layout><hierarchy>' + hierarchy + '</hierarchy><components>'
            + components + '</components></layout>')

results = {}

source = xml('<root this="r"/>',
    '<root this="r" currentstate="missing" defaultstate="second">'
    '<states><first this="first"/><second this="second"/></states></root>')
doc = Document(source)
results['invalid_currentstate_falls_to'] = doc.state(doc.by_guid['r']).get('this')

source = xml('<button this="instance"/>',
    '<button this="instance" currentstate="local" defaultstate="local">'
    '<state_uniqueguids><state_uniqueguid name="active" uniqueguid="local"/>'
    '</state_uniqueguids></button>')
results['template_local_uniqueguid_issues'] = [i.code for i in Document(source).issues]

source = xml('<root this="r"><a this="a"/></root>',
    '<root this="r"/><a this="a" id="a" text="a" expression="prefix a suffix"/>')
cloned, guid = copied_component(source, 'a', source, 'r')
doc = Document(cloned)
results['clone_text_equal_guid_remapped'] = doc.by_guid[guid].get('text') == guid
results['clone_embedded_guid_untouched'] = (
    doc.by_guid[guid].get('expression') == 'prefix a suffix')

source = xml('<root this="r"><a this="a"/><p this="p"><a this="b"/></p></root>',
    '<root this="r"/><a this="a" id="a"/><p this="p"/><a this="b" id="a"/>')
results['move_same_name_accepted_with_issues'] = [
    i.code for i in Document(move(source, 'a', 'p')).issues]

source = xml('<root this="r"><a this="a"><b this="b"/></a></root>',
    '<root this="r"/><a this="a"/><b this="b"/>')
doc = Document(move(detach(source, 'a'), 'a', 'r'))
results['reattach_after_detach_orphans'] = sorted(doc.unlinked_keys)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    (root / 'templates').mkdir()
    template = xml('<button this="base"/>',
                   '<button this="base" expression="A && B"/>')
    Document(template)
    (root / 'templates/button.twui.xml').write_text(template, encoding='utf-8')
    doc = Document(xml('<button this="inst"/>',
        '<button this="inst" uniqueguid_in_template="base" template_id="button"/>'))
    index = TemplateIndex(str(root))
    results['raw_cco_template_document_accepts_index_resolves'] = (
        index.resolve(doc, 'inst') is not None)
    results['raw_cco_template_errors'] = len(index.errors)
    invalid = Document(xml('<missing this="x"/>', '<root this="r"/>'))
    exported = export_zip(root / 'errors.zip', invalid, Resources([]), 'ui/errors.xml')
    results['export_with_diagnostic_errors_written'] = exported['written']

expected = {
    'invalid_currentstate_falls_to': 'first',
    'template_local_uniqueguid_issues': ['dangling_reference', 'dangling_reference'],
    'clone_text_equal_guid_remapped': True,
    'clone_embedded_guid_untouched': True,
    'move_same_name_accepted_with_issues': ['duplicate_name'],
    'reattach_after_detach_orphans': ['b'],
    'raw_cco_template_document_accepts_index_resolves': False,
    'raw_cco_template_errors': 1,
    'export_with_diagnostic_errors_written': True,
}
assert results == expected, results
print(json.dumps(results, ensure_ascii=False, indent=2))
```

升级上游后这些期望可能改变；届时应复核源码并更新本节，不能把旧版本边界当作永恒规则。与本报告直接相关的上游回归入口是 `test_xml_compat.py`、`test_component_editing.py`、`test_state_edit.py`、`test_template_states.py`、`test_hierarchy_edit.py`、`test_diagnostics.py`、`test_diagnostic_levels.py`、`test_tab_history.py`、`test_workspace.py`、`test_xml_format.py`。本文对这些测试的引用用于说明覆盖意图；全量测试执行记录由主研究验收文档维护。
