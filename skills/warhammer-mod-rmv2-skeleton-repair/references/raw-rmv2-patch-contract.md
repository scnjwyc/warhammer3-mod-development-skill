# 原始 RMV2 写入契约

本参考文件定义脚本直接修改 `.rigid_model_v2` 时必须证明的二进制不变量。优先修改原始顶点块，不做广义导出重写；广义导出可能改变未知区段、LOD、材质、attachment 或顶点量化。

## 修改前的最低调查

1. 使用兼容当前 RMV2 版本的解析器读取字节。历史实现为 `io_scene_rmv2.rmv2_format`，本包不提供该插件；下文 rf/mesh 等名称是接口示意，须映射到实际工具。
2. 记录版本、skeleton name、LOD 数、每 LOD 各 model 的材质名/ID、顶点格式、顶点数、三角形数和 attachment palette。
3. 找到目标 body mesh，确认每个 LOD 的顶点数与拓扑是否与算法假设一致。
4. 以原始 `mesh.raw_block` 搜索其在源字节中的确切偏移。无法唯一定位时停止，不猜测偏移。
5. 提前声明允许修改的顶点、influence slot 或 position 字段。候选的完整 byte diff 必须完全落在该 allowlist。

## 顶点格式与位置编码

常见 Cinematic/weighted4 顶点布局包含：

```text
pos      half4
bidx     uint8[4]
bwgt     uint8[4]
normal   uint8[4]
uv       half2
binormal uint8[4]
tangent  uint8[4]
```

不能用普通 half3 写入代替 CA 的位置编码。对需要写位置的顶点，使用插件的高精度 half4 编码：

```python
encoded = rf.encode_position_half4(points, high_precision=True)
```

只对选中顶点写 `pos` 对应字节；未选顶点必须保留原始 half4 bytes。位置编码、骨索引和权重的实际字段偏移必须由 `_vertex_dtype(vertex_format, version)` 取得，不能硬编码为适用于全部版本/格式的常数。

## 权重和骨索引

- `bidx` 是字节索引；先通过 attachment palette 映射为骨骼名称，再判断是否正确。
- 仅修改非零权重的 influence slot，除非任务明确证明存在空 slot 且需要填入中间骨。
- 量化后的每顶点 `bwgt` 字节和必须与修改前相同。
- 最多四个非零 influence；不得产生无权重顶点。
- 需要重分配时，按原始整数总和量化。将目标权重归一化后乘以原始整数总和，先取各项下整，再按小数余量从大到小分配剩余整数（并列按固定 slot 顺序）。保留骨骼与 slot 的映射，拒绝负权重/总和为零；量化后复核总和与最多四 influence。
- 不把骨索引数字、Daji/A2 的旧映射或某个角色的空 slot 假定为通用规律。

## 同坐标 Seam

RMV2 常以不同 UV 或材质槽复制同一位置的顶点。它们不是可以删除的重复面。

- 对平滑权重：以“位置量化键 + 原始非零权重签名”建立逻辑簇，避免本来不同的材质/权重边界被错误合并。
- 对 bind position 重定向：同位置副本需要写为同一目标位置，防止 seam 在不同骨影响下打开。
- 对 seam 权重修复：修改的副本必须由动作分离、原始权重对照或对侧参考证明；各副本保留各自原始整数总和。
- 动画验收时测量同位置簇的 posed separation。静态同坐标不等于动作中仍重合。

## 重解析与差异审计

写出候选后必须重新 `rf.load(patched_bytes)` 并断言：

| 分类 | 必须保持 |
|---|---|
| 文件 | 长度、RMV2 版本、skeleton name、LOD/model 数量 |
| 资源 | 材质 ID/名称、attachment palette、顶点格式 |
| 几何 | 三角形索引、法线、切线、副法线、UV、颜色、无关 mesh |
| 位置候选 | 所有未选中的 body 顶点位置 |
| 权重候选 | 每顶点整数权重和、最多四 influence、无未加权顶点 |
| 原始字节 | diff 集合精确等于写入时记录的 offsets |

最小审计报告字段：

```json
{
  "source": "...",
  "output": "...",
  "source_sha256": "...",
  "output_sha256": "...",
  "bytes": 0,
  "changed_byte_count": 0,
  "changed_vertices_per_lod": {},
  "allowed_change_kind": "position | bone_index | weight",
  "structure_before": {},
  "structure_after": {},
  "non_target_data_identical": true,
  "weight_sums_preserved": true,
  "max_four_influences": true
}
```

候选写入、重解析或 diff 审计任一项失败时删除候选或标记为失败；不能把它覆盖源文件。

## Pack 回填契约

本地源 RMV2 通过上述验证后才可回填：

1. 读取 `pack_map.json` 确认目标 MOD 的已登记 source pack。
2. 用 RPFM 打开该 pack；若 MCP session 失效，重新初始化、设置 `warhammer_3`、重新打开 pack，不能继续用失效 handle。
3. 使用 `add_packed_files` 只导入该 RMV2，内部路径与源相对路径一致。
4. 保存 pack。
5. 用 `get_packed_file_raw_data` 读取内部 RMV2，转换 `VecU8` 后计算 SHA；必须等于本地源 SHA。
6. 重建当前 MOD 所需的依赖并运行 diagnostics。真实 Error 解决后才完成；无法识别或完成诊断时报告未完成；Warning 按类型、路径和与本次变更的关联记录。

RPFM 的表/Loc diagnostics 不直接验证 RMV2 顶点质量。它们只验证 pack 结构层；模型结构和动画质量仍由本文件的原始字节审计与 Blender 回归负责。
