# DDS 还原、分类与应用

## 格式判定（必须以原始 DDS 为准）

BC6H 是 HDR 格式。把原本的 DXT1/DXT5 颜色贴图统一改成 BC6H，会导致整体发灰发白、透明/眼部区域异常；不要根据当前 BC6H 反推目标格式。

| 原始格式 | 目标目录/导出格式 | DXGI 头（若使用 DX10 DDS） | 备注 |
|---|---|---:|---|
| DXT1，无 Alpha | `BC1_UNORM_SRGB` / BC1 RGB 4 bpp | 72 | 允许传统 `DXT1` 头；无透明 |
| DXT1a，1-bit Alpha | `BC1a_UNORM_SRGB` / BC1a RGBA 4 bpp | 71/72 | 检查源 Alpha 后再归类 |
| DXT5 | `BC3_UNORM_SRGB` / BC3 RGBA 8 bpp | 78 | 选择 interpolated alpha，保留 Alpha |
| BC7_SRGB | `无需转换/BC7_UNORM_SRGB` | 99 | 已是合适的 LDR sRGB 格式 |
| BC7_UNORM、未知 DXGI、其它 FourCC | `需人工确认` | — | 不要自动转换 |

校验器应同时接受传统 `DXT1`/`DXT5` 头和 DX10 的 BC1/BC3 sRGB 头，但必须拒绝 DXGI 94/95/96（BC6H typeless/UF16/SF16）作为本批次最终输出。颜色贴图应使用 sRGB；normal/material 等线性贴图不进入本流程。

## 批次结构与来源解析

推荐结构如下，所有分类目录保留 MOD 相对路径：

```text
BC6还原分类_角色_时间戳/
├─ input_original/                 不可修改的原始字节
├─ 待转换/BC1_UNORM_SRGB/
├─ 待转换/BC1a_UNORM_SRGB/
├─ 待转换/BC3_UNORM_SRGB/
├─ 已转换/BC1_UNORM_SRGB/          用户导出的结果
├─ 已转换/BC1a_UNORM_SRGB/
├─ 已转换/BC3_UNORM_SRGB/
├─ 无需转换/BC1_UNORM_SRGB/
├─ 无需转换/BC7_UNORM_SRGB/
├─ manifest.csv
└─ README.txt
```

来源优先级：

1. 用户提供的原始 `variantmeshes/_variantmodels` 目录，按完整相对路径匹配。
2. 原始包中明确的 `model/daji`、`props/chinese/rigid` 等已核实映射。
3. 若外部原始目录缺失，使用嵌套 MOD Git HEAD 中的原始 Blob；在 `manifest.csv` 写明 `source_reference`，不能静默跳过。

预检必须确保每个当前 BC6H 文件都有来源，且来源与当前文件的宽、高、Mip 数一致，然后才创建批次并恢复 MOD。

用户有时会用 Photoshop/NVIDIA DDS 插件把结果平铺到 `已转换/BC1_UNORM_SRGB` 或 `已转换/BC3_UNORM_SRGB` 根目录。应用时可以在“完整相对路径”查找失败后按“目标分类 + 唯一文件名”匹配；同名多于一个必须报错，不能猜测。清单外文件也必须报错。

## 用户转换提示

- DXT1 无 Alpha：导出 BC1 RGB / DXT1 no alpha。
- DXT1a：导出 BC1a RGBA / DXT1a 1-bit alpha。
- DXT5：导出 BC3 RGBA / DXT5 interpolated alpha；导入时要保留源 Alpha（需要时勾选“Load Alpha as Channel Instead of Transparency”）。
- 不要选择 BC6H 作为本批次的输出格式；不要把这批 BC6H 输出再转成 BC1/BC3，因为 BC6H 不保存原 DXT5 Alpha，应从 `待转换` 或 `input_original` 重新导出。
- 保持原始宽高、Mip 数和文件名；不要垂直翻转。输出应为颜色贴图 sRGB。
- Read Properties 对话框是读取设置，不是压缩格式选择；BC1/BC3/BC7 在 DDS 导出时选择。

## 应用前的逐张预检

对每个 `manifest.csv` 行检查：

1. 已转换文件存在且能解析 DDS 头。
2. 目标格式为 BC1/BC1a/BC3 的允许头，不能是 BC6H。
3. 宽、高、Mip 数与 manifest/原始文件一致；Mip 不足也要拒绝。
4. `input_original` SHA-256 仍与 manifest 一致。
5. 文件名匹配唯一，没有缺失、重复或清单外 DDS。

预检通过后才把已转换文件写回 MOD 相对路径；写入后逐张重新计算 SHA-256，并生成 `apply_report.csv`。原始已正确的 BC1/BC7 文件不需要重复转换，但应保留在 `无需转换` 并保持 MOD 中的原始字节。

DXGI 枚举依据：[Microsoft DXGI_FORMAT](https://learn.microsoft.com/en-us/windows/win32/api/dxgiformat/ne-dxgiformat-dxgi_format)。传统 DXT1 头不能单独证明是否有有效透明像素；需解码 Alpha/检查块后确认 BC1a。
