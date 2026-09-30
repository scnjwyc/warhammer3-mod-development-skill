# 诊断与 Bind 重定向

本参考文件用于已确认故障落在 RMV2 模型层时的分类和计算。先阅读主技能的活动资产链和真实动作要求。

## RMV2、骨架与动作的职责

| 数据 | 保存位置 | 修复时的含义 |
|---|---|---|
| 顶点位置、法线、UV、索引、骨索引、权重、材质、LOD | `.rigid_model_v2` | 可作为模型局部修复对象。 |
| bind/rest pose、骨架层级、骨骼轴向 | `animations/skeletons/<skeleton>.anim` | 共享游戏骨架，模型局部修复不能修改它。 |
| 骨骼随时间的姿态 | 真实战斗/战役动作 `.anim` | 用于暴露变形，也用于最终验收。 |
| 活动模型引用 | `variantmeshdefinition -> wsmodel` | 先确定真正运行的 RMV2。 |

RMV2 中的骨索引必须通过 attachment palette 或导入器保存的 CA index 映射为骨骼**名称**。不同模型的同一数值索引不一定指向同一根骨骼。

## 故障分流

### 1. 错误骨索引或错误权重

典型证据：

- 扭曲局限在一根手指、手腕、膝盖等小区域；rest pose 外形合理。
- 顶点被分给错误的左右侧、相邻手指或跨越了骨链中间节。
- 某骨链的中间骨在真实动作中会旋转，但对应顶点没有该骨影响，导致从 `_0` 跨接到 `_2`。
- 权重整数总和异常、无权重顶点、超过四 influence，或过渡环从纯 A 突然跳到纯 B。

处理：先列出受影响顶点的非零 `bone name: weight`，按真实动作确认哪个 influence 造成反向/跨链移动。修复可以是：

- 修正已经证明错误的非零 bone-index slot。
- 在已有空 influence slot 中加入中间骨，同时按整数比例从现有 influence 转移权重。
- 对关节过渡带做小范围、duplicate-aware 的平滑。

不要从“某顶点组缺失”直接推导整条骨链都应前移。组名、静态 pose 和表面距离只提供线索，真实动作才是结论。

### 2. 局部权重过渡错误

典型证据：

- 影响骨名称正确，但某关节边界没有混合顶点或混合范围极窄。
- 变形表现为硬折，而不是整块区域持续偏移。
- 同位置 UV/material 副本权重不同，会在平滑后裂开。

处理：在当前模型自身拓扑中寻找边界环。将同位置、同原始权重签名的副本折叠为一个逻辑点，完成平滑后把结果同步回各个副本。每一 LOD 独立计算，不能假设 LOD0 权重可直接复制。

### 3. Bind-pose 顶点位置错误

典型证据：

- 活动 RMV2 与一个旧 skeleton family 的参考模型同拓扑，当前运行时却绑定到另一套游戏 skeleton。
- 局部权重名称与动作链均正确，但大片顶点在真实动作下仍整体偏移、折叠或持续拉伸。
- 反复权重平滑只转移折线，无法消除根因。
- 用旧/新 skeleton 的同名骨矩阵推导后，理论 rest position 与当前顶点有系统性差异。

处理：保留原始权重，用 old/new 游戏 skeleton 的 bind world matrix 计算理论位置。对模型局部需要的顶点位置做重定向，再对网格拓扑连续过渡，避免硬切边界。

## Blender 与游戏坐标

本仓库经过验证的导入器坐标关系为：

```python
# game -> Blender
blender = (-game.x, -game.z, game.y)

# Blender -> game
game = (-blender.x, blender.z, -blender.y)
```

不要把游戏四元数直接当作 Blender 右手系矩阵。通过实际 `import_anim` 导入结果或导入器同一矩阵逻辑取 bind world transforms。

## 线性蒙皮与 Bind Retarget

对顶点 bind/rest 位置 `p`，影响骨 `i` 的权重为 `w_i`，Blender pose 验证可使用：

```python
deform_i = pose_bone.matrix @ inverse(rest_bone.matrix_local)
posed = sum((deform_i @ homogeneous(p))[:3] * w_i for i)
```

手动结果必须先与 Blender evaluated mesh 对齐，才可用于诊断。差异显著时，先检查坐标基、armature object transform、骨名映射和动画导入，而不是修改模型。

跨 skeleton bind 重定向中，若 old/new 同名骨的 world matrices 分别为 `O_i` 与 `N_i`，则该骨对顶点的理论位置变换为：

```python
transform_i = N_i @ inverse(O_i)
theory = sum((transform_i @ homogeneous(old_position))[:3] * w_i for i)
```

判断 `theory` 与当前活动模型位置的误差时：

- 先确认旧参考模型和活动模型 body mesh 顶点数、三角形索引和骨名映射适合比较。
- 只在确有系统误差的区域创建临时候选。
- 核心高误差顶点可全量转到理论位置；外圈须按网格拓扑连续衰减。
- 空间 AABB 的硬阈值会把相邻面切开。以三角面相邻关系扩展核心区域；将同坐标 seam 副本折叠为同一逻辑节点后再计算 BFS 距离。

## 真实动作测试集

为每个任务建立该角色专属集合，至少包括：

1. 一个高运动攻击或跳劈。
2. 一个施法或技能动作。
3. 一个受击/击飞动作。
4. 普通待机与战斗待机。
5. 跑、走或移动动作。
6. 角色实际拥有时的战役、坐骑、武器姿态。

选择帧的方式：先用区域骨骼在动画中相对 bind pose 的旋转幅度排序，再用高位帧做渲染和量化。不要只挑一张“看起来最坏”的截图；候选之间必须使用同一动画/帧集合。

## 指标解释

| 指标 | 发现什么 | 注意事项 |
|---|---|---|
| edge log distortion | 邻接顶点拉伸或塌缩 | 最大值可能来自未修区域，需按区域与前 N% 汇总。 |
| triangle area log distortion | 面被拉长、压扁或反转 | 与 edge 一起使用，不能单独决定候选。 |
| non-adjacent overlap | 自交/穿插风险 | 区域过宽会把正常身体重叠也算入，需对照同一基线。 |
| dihedral angle | 相邻三角面形成折纸式硬折 | 特别适合定位腰腹、膝盖等视觉折线。 |
| duplicate separation | 同位置 seam 被不同骨影响拉开 | 同时看数量、距离和实际渲染。 |
| 全子网格渲染 | 服装、头发、脸等是否覆盖 body 边界 | 单独隐藏其他 mesh 的 body 渲染可发现问题，但不能把正常遮挡切口误判为缺口。 |

候选选择依据是同一组真实动作下的整体证据：已定位区域改善、周边不退化、二进制不变量成立、渲染无新增可见问题。
