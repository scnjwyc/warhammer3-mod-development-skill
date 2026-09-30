# 布局、坐标与预览边界

本页的公式来自固定commit的工具源码。凡涉及引擎是否完全按该公式工作，均需同类原版与游戏内实测。

## 找到控制位置的一层

从外到内依次是：实际运行时父组件 → 父LayoutEngine/CCO列表 → 组件停靠与偏移 → 状态尺寸 → 状态内图层的停靠与偏移 → PNG透明留白。Lua计时回调可能在这些计算后再次移动组件。

观察错位时先记录组件 `Position/Width/Height`、父组件相同数据、当前state和相关回调，而不是仅量贴图可见边缘。父布局和Lua同时移动同一批按钮会产生跳回或不断修正，应为该布局确定一个位置控制者。

## 三种不同拼写

| 对象 | 常见序列化字段 | Studio判别 |
|---|---|---|
| 普通组件定义 | `docking`, `dock_offset`, 可选 `component_anchor_point` | 有states、无state_uniqueguids、part_of_template不为true |
| 模板实例 | `dock_point`, `offset` | 无states、有state_uniqueguids、part_of_template=true |
| state内图片层 | `dockpoint`, `dock_offset`, `offset` | imagemetrics下的image |

混合/不明形状由工具保守处理，不自动删字段。0.22.2撤回了早期 `dock_position` 方案，后续工作不要根据旧CHANGELOG重复加它。[layout_geometry.py](../vendor/TWUI_Studio/layout_geometry.py)、[CHANGELOG.md](../vendor/TWUI_Studio/CHANGELOG.md)。

## 组件停靠公式

工具中的局部坐标为：

```text
child_x = parent_dock_x + offset_x - anchor_x * child_width
child_y = parent_dock_y + offset_y - anchor_y * child_height
screen_xy = parent_screen_xy + child_xy
```

例如父400×200、子80×30，Center Right、默认右中锚点、偏移(-5,0)，结果是(315,85)。普通定义若显式设置 `component_anchor_point` 则使用该值；模板dock_point按方向推导锚点。External会反转对应边的默认锚点。没有停靠值则直接读取offset。

在这个工具中修改停靠方向会更新锚点；只改dock_offset保留已有锚点。缩放组件时 `offset_delta` 会补偿锚点偏移，避免改变尺寸时另一条边意外移动。原版缺字段的引擎默认值未完全确认，不依工具默认值批量补字段。

## 自动列表

主画布 `list_positions` 只布局 `List` 和 `HorizontalList`：

- List按itemsperrow分行；HorizontalList按一行处理。
- 每一行按实际组件宽度（或特定情况下columnwidths的较大值）与spacing.x前进，行高取该行最大高度加spacing.y。
- reverse_order影响顺序；horizontal_alignment影响行对齐；sizetocontent与min_dimensions影响容器尺寸。
- 多列List在该工具中不使用固定columnwidths槽宽；已有XML值仍保留。
- margins与secondary_margins按纵/横列表方向映射；这些是近似算法，不是通用CSS外边距。

主画布隐藏某个组件是编辑视图隐藏，`draw_scene` 仍用全体孩子计算几何，因此隐藏不会让相邻项自动补位。这和运行时CCO过滤列表是不同操作。

列表项改offset后游戏又排回去时，先查父LayoutEngine、ContextList和排序，而不是反复增大offset。布局检查应覆盖空列表、1项、刚好一行、多一项换行、长文字和不同缩放。

## RadialList

XML角度使用弧度，界面AngleEditor提供角度换算；360°=2π，不能把界面度数原样写回XML。`radial_geometry.py` 的模型按每项角度预算 `arc/count` 约束spacing，并在挤压时以弦长估算扩半径。该文件明确表示它不是CA的求解器。

尤其注意：主画布的 `draw_scene → list_positions` 没有RadialList分支；属性窗口 `RadialPreview.draw` 使用 `radial_guide` 展示5个虚拟按钮，某些扩展示意会假设第6个槽。**示意图既不是实际孩子数量，也不是主画布的布局实现。** 不应看示意圆环就认定生产HUD布局正确。

需验证起始角、旋转方向、真实数量、可见项过滤、按钮大小、费用标签等附属内容、不同UI缩放时的屏幕边界；测量围绕实际美术中心的圆心而非假设透明画布中心。

## 图像渲染链

`Resources.resolve` 按完整路径逐段匹配并保留大小写，不做全库同名文件兜底。`LayeredResources` 让当前文档的MOD资源覆盖原版同路径。资源根建议是提取后的最上层ui目录。

`raster` 用Pillow解码RGBA、九宫格或铺贴/拉伸、通道乘色。按路径、mtime、文件大小、目标尺寸和图层属性缓存，基础位图LRU上限64 MiB。`ZoomImageCache` 再缓存缩放的Tk PhotoImage，另有64 MiB上限；画面外部分裁切用于节省绘制，不代表游戏父组件clipchildren裁切。缩放使用NEAREST；基础拉伸用LANCZOS；单张预览尺寸上限4096。

主画布按hierarchy遍历次序画图，未实现游戏完整priority排序、shader、动画、species skin替换、真实字体布局或完整模板继承。编辑器中的“上面盖住下面”不能直接证明游戏priority关系。

## 精确排错顺序

| 现象 | 首先核对 |
|---|---|
| 整块移动错位 | 实际父节点、父坐标、停靠家族、锚点、布局控制者 |
| 组件边框正确但图案偏 | imagemetrics的offset/dockpoint、图层尺寸、图片透明边 |
| 鼠标点击区与图案不同 | state组件尺寸、interactive/disabled/visible、运行时遮挡及priority |
| 编辑器有字游戏无字 | LOC键、实际state、CCO文本回调、模板局部覆盖 |
| 游戏有图编辑器缺图 | 完整ui路径、MOD覆盖、动态skin、外部模板/Creator，不先改游戏路径 |
| 一次打开正常，再开失效 | 原节点被销毁重建、监听初始化、过期引用 |
| 1080p正常，缩放后越界 | UI实际坐标尺度、父尺寸、底部/右侧附属标签边界 |
