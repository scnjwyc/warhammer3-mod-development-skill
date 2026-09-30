# 战锤 3 UI 运行时资料

核验日期：2026-09-27。适用范围：WH3 的 Lua UIComponent、core、CCO 和源 Pack 接入。本文依据本机 CA 原版文档和已提取的原版 Lua；已核对公开 CA 文档镜像，但镜像站点由社区维护，不能当成 CA 官方域名。本文没有运行游戏，示例是已核对签名的参考实现，不能据此宣称游戏内验收通过。

## 一手资料与版本边界

下列 sources 路径相对本参考文档目录。`sources/vanilla/script/` 是已有原版脚本提取目录，不能作为 MOD 的修改入口。

|编号|来源|用途|
|---|---|---|
|S1|`sources/documentation/script/campaign/uicomponent.html`|UIComponent 引擎接口；具体行号见下文|
|S2|`sources/documentation/script/campaign/core.html`|core 对 UI 根、生命周期和组件创建的包装|
|S3|`sources/vanilla/script/_lib/lib_common.lua:385-433`|实际查找算法|
|S4|`sources/vanilla/script/_lib/lib_core.lua`|创建、生命周期、监听器的实际实现|
|S5|`sources/documentation/ui/callback_documentation.html`|原生 UI callbacks 的行为与 user properties|
|S6|`sources/documentation/ui/documentation.html`|CCO 类型、方法、参数、返回类型和事件；文件压成一行，应按类型/方法定位|
|S7|`sources/documentation/ui/context_viewer_doc.odt`|CA Context Viewer 使用说明；见其中 What are contexts / How do I use it|
|S8|`sources/documentation/script/campaign/common.html`|本地化、CCO 脚本入口|
|S9|`sources/vanilla/script/events.lua`|原版事件名清单|
|S10|`sources/documentation/script/campaign/campaignui.html:838-898`|UITrigger 同步入口|

公开定位入口：[UI scripting](https://chadvandy.github.io/tw_modding_resources/WH3/ui_scripting.html)、[UIComponent](https://chadvandy.github.io/tw_modding_resources/WH3/campaign/uicomponent.html)、[Core](https://chadvandy.github.io/tw_modding_resources/WH3/campaign/core.html)、[CCO symbols](https://chadvandy.github.io/tw_modding_resources/WH3/cco/documentation.html)。本文详细 API 说明以本机原文为证据，网页只提供可访问的对照入口。

本机 `uicomponent.html` 修改时间是 2026-09-25；提取时间不等于游戏版本。更新游戏后应重新提取、比较接口和布局。核验快照 SHA-256：

```text
S1 d0de5aecae16b3e1490e9f14ba93f3a011d3c71121f974b0facd4e0d6bf28406
S3 058a7c24752322658c5687e7cebe660dd398674cac160b4d3dc30e20d5ae008f
S4 be850ad9855e9d6d23ae1023dfccff7d80a795463a3fc220fe3c7dd8d4bc43d7
S5 60e3ab1728ce2a5c1e68923a1543d7d152eaa1bef78396937e1ad943bea10d6f
S6 cf422c1820db820f8379413cec06d275459bf1b9fc796ff1bfc09f2d360164bd
S7 630f92141db73b0eaafd8dbebf6bb2f3e00e77e9061b5dfc9d5fde6b6974da31
```

## 找组件：递归搜索和严格逐层遍历必须区分

`find_uicomponent(parent, "a", "b")` 先在 parent 的所有后代里找第一个叫 a 的组件，再在该 a 的后代里找 b。每段都能跨层；不是严格的直接孩子路径。省略 parent 时从 `core:get_ui_root()` 开始；没有找到返回 `false`。因此只写常见名字如 `button_confirm` 可能命中别的面板；应先限定已知面板，再给足够明确的后代路径。[S3:385-433]

底层 `parent:Find("name", false)` 返回地址或 nil，字符串参数进行递归搜索；第二个 false 关闭未找到时的 assert。`parent:Find(index)` 则查直接孩子，索引从 0 到 `ChildCount()-1`；返回值使用前经 `UIComponent(address)` 转换。[S1:1467 起；S3:359-403]

`core:get_or_create_component(name, template_path, parent)` 的现有组件判断只扫描 parent 的直接孩子，找到同名直接孩子就返回它和 false，否则调用 `CreateComponent` 并返回组件和 true。它不检查同名组件来自哪个模板，也不会用新模板覆盖已有实例。[S4:1832-1859]

严格直接孩子查找可以使用这个经过签名核对的辅助函数：

```lua
local function direct_child(parent, name)
    if not is_uicomponent(parent) or not parent:IsValid() then
        return false
    end
    for index = 0, parent:ChildCount() - 1 do
        local address = parent:Find(index)
        if address then
            local child = UIComponent(address)
            if child:IsValid() and child:Id() == name then
                return child
            end
        end
    end
    return false
end
```

这是保守的逐层遍历实现；它不改变游戏状态。调用前仍应确认当前游戏区域的 UI 已创建。

## 生命周期和监听器

`core:get_ui_root()` 在 UI 创建前会报错。先用 `core:is_ui_created()` 判断，或通过 `core:add_ui_created_callback(fn)` 初始化纯 UI 工作。CA 建议用 core 的回调包装：它先设置 root，再通知客户端；不要为了抢先初始化而直接监听 `UICreated`。[S2:356-465；S4:306-326]

`core:add_ui_created_callback` 仅把回调追加到列表；此实现不会因为 UI 已存在就立刻执行新注册回调。因此晚注册时需要自行检查 `is_ui_created()` 并调用幂等初始化。不要把第三方 MCT 同名方法的“已创建则立即调用”语义当作 core 语义。[S4:293-302]

`core:add_ui_destroyed_callback(fn)` 运行前，core 已把 `ui_is_created` 设为 false、`ui_root` 设为 false。销毁回调应清理保存的句柄和取消自己的后续工作，不能在其中重新获取 root。[S4:329-362]

`is_uicomponent(x)` 是接口类型检查；`x:IsValid()` 才检查其内部组件指针是否还存在。面板重建后不要仅凭变量非 nil 就继续调用旧句柄。`Destroy()` 销毁当前组件，`DestroyChildren()` 销毁其全部孩子；不要对原版容器调用后者清理自己的一颗按钮。[S1:351、1846-1875]

CCO 的 `ContextList` 刷新默认会重新创建列表项，相关属性可改变重建方式。因此即便顶层面板仍开着，列表项句柄也可能失效。操作时重新查找目标、检查 IsValid，并重新取得它绑定的数据对象。[S5:167 起的 ContextList]

`core:add_listener(name, event, condition, callback, persistent)` 第三个参数为函数或 true；第五个 true 表示持续监听，false 表示条件匹配并执行后移除。实现不会按 name 自动覆盖旧监听器；重复注册前用自己唯一的名字 `core:remove_listener(name)`。不要删除其他 MOD 的监听器。[S4:1883-1920、1967-2008、2090-2106]

对于延迟刷新，回调中重查组件，并用面板打开代次标记使关闭前排队的任务失效。延迟 0.1 秒只是重试策略，不能写成“所有面板 0.1 秒必定加载完成”的引擎保证。应限制重试次数，记录失败的面板名/路径。这一段是由生命周期事实推导的工程做法。

## 事件：不要虚构 ComponentLClick

本机原版 `events.lua:162` 注册的左键释放事件是 `ComponentLClickUp`，没有叫 `ComponentLClick` 的条目。`PanelOpenedCampaign`、`PanelClosedCampaign` 分别在 288、286 行。`ContextCommandLeftClick` 是 XML callback 名称，不是上述 Lua 事件名。[S9；S5:149]

面板打开的 `context.string` 是面板名；原版 `autorun.lua:138-167` 用它区分面板，并以 `UIComponent(context.component)` 取得事件组件。原版 `campaign/scripted_tours/campaign_tours.lua:3954-3958` 以 `context.string == "dlc24_matters_of_state"` 匹配经世济民面板。具体名字必须从原版布局或实机事件得到，不应猜测。

鼠标移入、移出、动画完成等高频事件通常需要组件附带 `ScriptEventReporter`，可在 XML 中添加或用 `uic:AddScriptEventReporter()`。不能推断每个组件自动发出这些事件；也不必为了普通 ComponentLClickUp 盲加 reporter。[S1:556 起；S5:15]

以下纯观察脚本使用已核对的原版面板名。放到测试 MOD 的战役脚本后可用于核对打开、关闭和点击日志；本次只把它记录在资料中，没有安装或运行：

```lua
local prefix = "wyccc_ui_probe_"
local panel_id = "dlc24_matters_of_state"

local function find_panel()
    if not core:is_ui_created() then return false end
    local panel = find_uicomponent(core:get_ui_root(), panel_id)
    if panel and panel:IsValid() then return panel end
    return false
end

for _, event in ipairs({"PanelOpenedCampaign", "PanelClosedCampaign"}) do
    local event_name = event
    local listener_name = prefix .. event_name
    core:remove_listener(listener_name)
    core:add_listener(listener_name, event_name,
        function(context) return context.string == panel_id end,
        function(context)
            out("[UI probe] " .. event_name .. ": " .. context.string)
            if event_name == "PanelOpenedCampaign" then
                local panel = find_panel()
                out("[UI probe] panel found: " .. tostring(panel ~= false))
            end
        end,
        true
    )
end

core:remove_listener(prefix .. "click")
core:add_listener(prefix .. "click", "ComponentLClickUp",
    function(context)
        local panel = find_panel()
        if not panel or not panel:VisibleFromRoot() or not context.component then
            return false
        end
        local clicked = UIComponent(context.component)
        if not clicked:IsValid() then return false end
        local current = clicked
        while current and current:IsValid() do
            if current:Address() == panel:Address() then return true end
            local parent_address = current:Parent()
            if not parent_address then return false end
            current = UIComponent(parent_address)
        end
        return false
    end,
    function(context)
        out("[UI probe] clicked: " .. tostring(context.string))
    end,
    true
)
```

示例 Parent/Address 来自 S1 的 Searching and Hierarchy、General Queries；监听器来源 S4。它每次重查面板，点击范围限定为该面板的后代，不保存跨打开周期的 UI 句柄。只有拥有该面板的对应战役流程打开它时才有日志。

## 状态、尺寸、可见性和输入

|操作|核验语义|来源|
|---|---|---|
|`SetState(name)`|切换到已存在的状态，返回是否成功；状态名字来自具体模板，不能假设都有 disabled 或 selected|S1:600 起|
|`SetVisible(bool)`|改变自身可见标记；不等价于销毁，也不保证祖先可见|S1:3248 起|
|`VisibleFromRoot()`|检查自身、所有祖先可见，且树连接到 root；排查“Visible 为 true 但看不见”用它|S1:3234 起|
|`MoveTo(x, y)`|相对游戏窗口左上角的屏幕坐标；不是父组件内坐标|S1 的 MoveTo / Position|
|`Resize(w, h, resize_children)`|可能先要开启 SetCanResizeWidth/Height；第三参默认 true，可能同时缩放孩子|S1:868 起|
|`ResizeTextResizingComponentToInitialSize(w, h)`|用于自动随文字改变尺寸的组件；普通 Resize 可能被文字布局覆盖|S1 的同名条目|
|`Layout()`|请求重新执行组件布局，不能保证用户设定不会再被布局逻辑覆盖|S1 的 Layout|
|`PropagatePriority(n)`|设置自身与所有孩子的优先级，返回原优先级|S1:3976 起|
|`LockPriority([n])`|禁用较低优先级组件；之后必须调用 UnLockPriority 恢复|S1:3913 起|
|`RegisterTopMost()`|让组件脱离普通层级绘制顺序、绘于最上层；适合 tooltip，不是常规错位修复|S1:4009 起|

尺寸改完又跳回去时，先查谁拥有布局：原生 LayoutEngine、CCO 的 setter、自动文本大小或 Lua。`ContextStateSetter`、`ContextVisibilitySetter` 明确会依据上下文更新相应值；在 Lua 中反复强写会与其竞争。[S5:259、263] 这是代码/回调职责问题，不应先靠每帧 MoveTo 或加大 priority 掩盖。

## CCO 是游戏运行时数据和命令接口

CA 的 Context Viewer 文档将 CCO 描述为游戏对象面向 UI 暴露的上下文接口：既有查询，也有改变状态的命令。实例包括 CcoBattleUnit、CcoCampaignCharacter、CcoCampaignSettlement。`ContextTextLabel` 获取文本，`ContextVisibilitySetter` 控制可见，`ContextList` 生成列表，`ContextCommandLeftClick` 在点击或快捷键时发出命令。[S7 的 What are contexts；S5:149、167、207、263]

`uic:SetContextObject(cco)` 设置用于初始化 ContextCallbacks 的对象；`uic:GetContextObject("CcoCampaignBuildingSlot")` 从组件取出对应类型对象。实例上下文不是 XML 自身的数据。`ContextObjectStore` 负责存储与取回上下文，回调可利用多种上下文完成操作。[S1:454-555；S5:189]

`sources/ui/cco/components.cco:1-12` 定义基于当前状态的表达式，`sources/ui/cco/characters.cco:1-24` 包含角色 InitiativeSetList 的过滤表达式。这是 CCO 表达式语言，不能当 Lua 直接执行。UI 静态预览只能展示它实际实现的解析和渲染；显示出按钮不代表引擎里的 CCO 数据、命令、事件与权限都已执行。本段后半是由运行时依赖推导的验收边界，具体 Studio 支持程度应另查其源码。

**已确认的文档不一致：** S8:2147-2251 的 `common.get_context_value` / `common.call_context_command` 标题签名只有两个形式参数，但同页示例出现三个实参和 `effect.*` 名字。不要照抄这些示例后宣布接口已核验。需要执行这类操作时，以当前游戏中的真实调用源码、上下文对象类型和实机查询结果补齐证据；本文不提供未经核验的 CCO 执行包装。

Context Viewer 的 CA 说明提供了更可靠的现场调查路径：在游戏设置开启后用 Grave 键打开；中键检查 UI/单位/角色等上下文，Alt+中键列出指针下的 UI 对象；Component tree 看真实层级，Events 看实际触发事件。查询返回的上下文或列表未必自动刷新，可用刷新按钮更新。文档说明它在多人模式下禁用。[S7 的 How do I use it / limitations]

## 本地化、图片与模板引用

`common.get_localised_string(full_key)` 从数据库取本地化文本，找不到返回空字符串。`SetText(text, source_key)` 改全部状态的文字；`SetStateText(text, source_key)` 只改当前状态。文字已渲染但 hover 后恢复旧文案时，应查是否只改了当前状态。第二参数是文字来源键，不能把待显示 loc key 直接冒充已解析文本。[S8:1699 起；S1:1882、1926]

`SetImagePath(path, image_index, resize)` 改的是组件关联图片；未给索引时优先使用 `script_icon_index` 属性，否则用 0。第三参数默认 false：新图按原有图片度量显示，不会自动按新图尺寸重建布局。组件可有多张图，应结合 NumImages/GetImagePath 确认目标索引。[S1:2131 起]

原版 `sources/ui/templates/square_medium_button.twui.xml:60-98` 同时关联 Button/CallbackAnimTrigger 回调及 active、hover、pressed、inactive、underlay 等图片。换错图片索引可能只改边框或底层；修改默认态的一项也不等于所有状态都会一致。检查组件图片 GUID 与状态图片引用，再看实际受影响的状态。此模板实际 layout version 为 142。[该 XML:1-8、60-98]

本地路径仅供编辑器读文件；游戏中的引用应是 Pack 内路径，如 `ui/skins/default/...png`、`ui/templates/...`。模板创建路径来自 working data 的相对路径，不能写 `C:/...`。外部模板、图片、本地化要同时检查当前游戏依赖是否已提供，不应把所有原版资源复制进补丁。[S1 CreateComponent / SetImagePath；工作区 AGENTS.md 的 Pack 隔离规则]

## UI 事件与多人同步

UI 状态是每台机器本地的；在点击或面板打开回调里直接改战役模型可能导致多人不同步。CA 推荐模型相关初始化使用 first tick。需要从 UI 触发战役模型修改时，现有官方入口是 `CampaignUI.TriggerCampaignScriptEvent(faction_cqi, event_id)`，随后在 `UITrigger` 监听器里用 `context:trigger()` 和 `context:faction_cqi()` 接收。两个参数需同时给或同时省略；第一个明确是 faction CQI，不应仅因类型是 number 就塞 character CQI。[`sources/documentation/script/ui_scripting.html` 的 Modifying the Game State；`campaign/campaign_manager.html:1650`；S10:838-898]

具体命令仍要检查当前状态、目标与资源条件，再执行模型修改。上述接口说明只解决传递事件的途径，不能替代游戏逻辑授权或结果校验；纯 UI 文本/布局刷新无需转成战役模型事件。

## 接入本项目

实际修改UI/Lua/LOC后，按 [源Pack工作流](pack-workflow.md) 执行。本文研究阶段没有修改任何MOD或Pack，因此没有执行导入、诊断或游戏测试。

## 后续 UI 任务的最小证据

保存修改前/后的源差异、具体 Pack 内路径、布局/资源检查结果、运行时面板和组件路径，以及点击后真正改变的 UI 或模型状态。日志需带事件名和目标 ID；界面验收需覆盖重开后仍正确，必要时覆盖 ContextList 重建与 UI 缩放。涉及锁输入时还要观察关闭后原版 UI 恢复操作。

未核验范围：当前游戏执行中的全部 CCO Lua 构造/Call 签名；各类面板的构建时序；具体 MOD 的加载冲突；所有 DPI/超宽屏组合；任何 Studio 预览与游戏渲染完全一致的保证。API 原文存在签名与示例冲突时应保留问题，不能为了让示例完整而补造参数。
