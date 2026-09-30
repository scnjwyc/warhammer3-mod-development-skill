# TWUI XML结构与编辑依据

这份资料描述本地原版样本与 TWUI Studio 0.22.2 能读取的形式，不是CA公开的完整XML规范。源码锚点见 [来源索引](source-map.md)，具体原版例子用 [资料库](knowledge-base.md) 查到后读当前文件。

## 两份结构通过GUID关联

一个 `layout` 中，`hierarchy` 是轻量树，节点通常只有标签和 `this`；`components` 是组件定义的平铺集合，保存状态、图片、回调、布局等。修改父子关系应改 hierarchy；不能靠移动 components 中的定义行改变父子关系。

```xml
<layout version="141">
  <hierarchy><root this="ROOT"><wyccc_button this="BUTTON"/></root></hierarchy>
  <components>
    <root this="ROOT" id="root"/>
    <wyccc_button this="BUTTON" id="wyccc_button"
                  currentstate="STATE" defaultstate="STATE">
      <states><active this="STATE" name="active" width="80" height="30"/></states>
    </wyccc_button>
  </components>
</layout>
```

上面仅是结构示意，简写GUID不可直接作为生产素材。真实新组件应从同类已知有效组件复制，生成新的内部GUID并维护引用，而不是用这个片段替代完整原版组件。

| 字段/节点 | 作用及编辑约束 |
|---|---|
| `layout.version` | 序列化版本。示例是141；保留来源版本，不猜测升级 |
| component `this` | hierarchy指向该组件定义的标识 |
| component `uniqueguid` | 常与this相同，但先保留原版约定，不能把全部GUID字段统一替换 |
| `id` | 组件名字；Lua查找经常依赖它；重命名后还需查Lua/CCO字符串引用 |
| XML标签 | 通常与id接近；Studio会处理含括号id对应的标签差异，不等于可无条件强制一致 |
| `currentstate` / `defaultstate` | 指向state的GUID，和state可读名字是不同层 |
| `states/*` | 普通定义的局部状态。状态可包含尺寸、交互标记、字体、图片层 |
| state `this` / `name` | 标识与可读状态名；Lua `SetState` 使用名字，XML引用使用GUID |
| state `width` / `height` | 该状态的组件尺寸；需要关注其他状态是否一起调整 |
| `dimensions` | 模板实例等无局部state形式可能使用的尺寸；不要因为缺states就补一套 |
| `part_of_template` / `template_id` / `uniqueguid_in_template` | 模板实例标记、模板名与模板内组件标识；结合原版模板文件解析 |
| `state_uniqueguids` | 模板状态引用形式，不能当普通states全量编辑 |
| `localised_texts` | 模板实例现有的本地文字覆盖位置；结合模板state和textlabel解析 |
| `componentimages/component_image` | 声明图片资源和image GUID；声明并不等于已经画到某状态 |
| `states/*/imagemetrics/image` | 状态中使用的图层，`componentimage`引用图片GUID |
| `callbackwithcontextlist/callback_with_context` | CCO/引擎回调绑定，不是Lua代码块 |
| `LayoutEngine` | 父容器自动布局；可能覆盖子组件手动坐标 |
| `userproperties/property` | 组件用户属性，name/value；值的业务含义由读取方决定 |

## 状态与模板

普通按钮常有 active/hover/down/disabled 等状态，但不是所有按钮都必须具备同一套；以目标模板实际名称为准。改按钮大小、文字、纹理时逐个查看会在游戏中出现的状态，不能只看Studio当前选中状态。

Studio `Document.state` 先尝试 `currentstate`（该属性缺失才用 `defaultstate`），找不到时退回第一个局部state。**无效currentstate并不会再尝试一个有效defaultstate**，因此预览可见不等于引用正确。

模板实例的形状在本地大量存在：`part_of_template=true`，有 `state_uniqueguids` 而没有局部 `states`。Studio会在已提取的 `ui/templates` 中建立只读模板索引，供状态说明/已有文字覆盖使用；主画布不会展开完整模板继承。详见 [工具内部实现](twui-studio-internals.md)。修改实例时优先保留引用式形状，不把预览缺图误判为模板损坏。

## 图片、文字与本地化

图片链是 `imagepath → component_image.this → imagemetrics.image.componentimage`。组件位置、图层位置和纹理透明留白是三个不同问题。更换路径后还须查看图层width/height、offset、dockpoint、dock_offset、margin、tile、colour和canresizewidth/height。

Studio按RGBA解释8位 `colour`，对各通道乘色；这是预览实现事实。九宫格margin在该工具里按上、右、下、左解释，但源码明确写为 provisional，应查同类原版和游戏验证再作为生产依据。

普通局部文本节点是 `component_text`。Studio预览按以下顺序取文本：组件预览覆盖 → 导入LOC中 `uied_component_texts_localised_string_` + `textlabel` → XML `text`。它用Arial近似字体，剥除 `[[...]]` 标记，不执行CCO文本回调或富文本的实际图标/样式渲染。不能按这个画布精确决定中文换行、字宽或截断。

实际本地化键与模板/回调应追到相应LOC源。对 `textlabel` 增补译文时遵守项目LOC TSV规则，经 `import_tsv` 导入二进制Loc。Studio导入的LOC仅供预览；XML+images导出不包含LOC、Lua和外部XML依赖。

## 原文保留

一些游戏属性包含裸 `&&`、`<` 等CCO表达式。标准 `ElementTree.parse` 可能拒绝它们。Studio只在验证副本转义，保存时在原字符串位置替换请求修改的属性。不要为了让严格XML解析器接受就重写整个文件或误转义CCO原文。

普通属性补丁与结构操作不是同样程度的“无损”：结构增删/移动会重新排版相应片段；显式格式化会有更大差异。读取用 `read_bytes().decode('utf-8-sig')` 并另存BOM标志，可避免通用文本读取把CRLF规范化。编辑后重新解析并查看限定范围diff。

## 引用检查

检查定义/树连接、重复GUID、同父同名、state引用、image引用；再查不在XML内部的Lua名字、外部布局和模板。Studio对这几个层次的覆盖并不完整，且模板状态引用可能被报成dangling_reference。`check --baseline` 能区分新增结构诊断，但不能证明未新增游戏错误。
