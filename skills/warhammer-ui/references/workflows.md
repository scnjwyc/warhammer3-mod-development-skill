# TWUI Studio操作与UI排错

适用工具基准：0.22.2 / `7e3e1be568fac3f5e9362d0494665fc549dc22eb`。以当前源文件为准；本页不改变用户现有MOD设计。

## 启动与资源

历史记录已验证Python 3.11.1、Tk 8.6、Pillow 12.3.0可运行。上游依赖约束见requirements.txt；批处理启动器会建立自己的.venv。

```powershell
Set-Location '..\vendor\TWUI_Studio'
python app.py
```

也可运行 `START_WINDOWS.bat`。工具没有Pack读取器；在Settings中把Original UI Resources指向提取后的最上层 `.../sources/ui`，不是游戏安装文件夹。MOD资源路径可以按文档标签单独设置，同路径优先使用MOD素材。当前ui里已有skins、templates、battle ui、campaign ui等目录。

原版提取目录是参考基准。打开目标MOD源XML后编辑；完成另存时写到已确定的MOD源位置。主工具没有MCP/HTTP服务或命令行批处理编辑协议；自动化读取使用本技能CLI，具体XML改动仍用可审查的源文件补丁。

## 保存的三个概念

| 操作 | 实际结果 |
|---|---|
| 保存项目 / Ctrl+S | `.twuiproj` JSON，包含多文档XML、原始对照、资源路径、视图和预览；不是游戏文件 |
| XML另存为 | 当前文档XML，可带原有BOM；才是UI定义交付物 |
| XML+images导出 | ZIP内一份XML与直接imagepath/富文本图片引用，保留ui相对路径 |

ZIP不会自动包含LOC、Lua、外部XML和完整模板依赖，也不是.pack。缺直接图片或非法路径时工具不写ZIP；但有结构诊断Error仍可能导出成功，因此“导出成功”只说明ZIP写入成功。

导出路径默认建议值可能是 `ui/campaign ui/mod/<文件名>`。覆盖原版面板必须用该面板在Pack中的真实原路径；新布局采用项目命名并由相应Creator/Lua明确加载，不能接受默认路径后以为覆盖已生效。

## 常用修改任务

### 按钮大小、坐标和皮肤

查完整组件与实际父容器，确认普通定义/模板实例及当前state。尺寸修改应覆盖实际会出现的状态；保持图片声明到图层引用一致。先按 [布局资料](layout-and-rendering.md) 判断是否由父列表控制位置。由用户在游戏内比较点击区、hover/down/disabled、遮挡与缩放。

### 新增按钮或复制一组UI

从同类可用组件复制，重分配组件、states、componentimages与内部图层GUID并维护引用；给同父下的新组件独立id。不能只copy XML外层标签。Studio剪贴板会为匹配的内部GUID属性值重新编号，但不会解析外部Lua/CCO语义，所以新增组件还需绑定真实动作。

当前工具移动入口 `hierarchy_edit.move` 允许移动后出现同父同名，操作后务必检查新父节点和duplicate_name；不要因为界面完成拖动就认为引用无冲突。`detach` 是断开父子关系：原孩子会成为游离组件，之后仅重新挂父组件不一定恢复整棵子树。复制/移动大组前记录子树GUID清单，完成后对照。

### 关联外部布局

先查 `ComponentCreator` 的layout路径和触发条件。Studio“导入外部布局”会复制该文件root子树为静态节点、分配GUID并加来源注释，同时保留原Creator回调。它不是只在画布临时展开引用。要研究动态内容可用独立研究副本；生产修改选择保留动态创建或静态化其中一种明确方案，并验证只创建一次。

### CCO文字或可见性

从原版对应callback读 `context_object_id`、`context_function_id` 和所在父组件上下文，再用metadata签名与CA callback文档追踪。预览输入框仅替代显示字符串，不执行表达式。值总不更新时查上下文是否有效、是否正确从父节点继承、ContextList是否重建，不立即用高频Lua轮询掩盖数据链问题。

### 点击没响应

先确定游戏运行时组件存在且有效，再查state交互标记、遮挡/priority、监听事件与context.string。用实际 `ComponentLClickUp`，必要时把context.component转为UIComponent检查Id和父树。已有回调与Lua监听可能同时触发动作，应沿真实触发链查重。

### 打开一次正常，第二次/读档失效

记录打开和关闭时真实组件树，检查Creator、ContextList和Lua重建。延迟回调执行时重新查找组件；重复初始化前移除同名listener或采用已验证的幂等注册方式。脚本加载完成不代表面板已经存在。

## 分层验收记录

1. 源文件：具体变化、前后SHA/diff、GUID/路径/LOC引用和Lua语法。
2. 工具：成功解析、属性修改是否只动目标、项目再开/ZIP清单、相对原版新增结构诊断。
3. Pack：映射路径、导入的具体内部路径、保存后Error扫描结果。
4. 用户游戏复测：版本/场景、动作、前后UI状态与日志；目标分辨率和UI缩放、关闭再开与必要的读档。

按已完成层次汇报。没有游戏证据时保留“待游戏复测”；原版样本的诊断不自动等于本次改动错误。
