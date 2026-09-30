---
name: warhammer-character-textures
description: "检查和恢复战锤3角色 DDS 颜色贴图，按原始 BC1/BC1a/BC3/BC7 分类，验证尺寸、Alpha、Mip 与哈希，再同步映射源 Pack。"
---

# 角色 DDS 贴图

LDR `base_colour` / `base_color` 的目标格式由可信原图决定。BC6H 不保存 Alpha，不能用它作为统一颜色贴图输出；normal、material、roughness、metallic 等不进入此流程。

## 工作流

1. 解析活动材质引用，确定用户指定 MOD 的源目录。把可信原始字节复制到批次 `input_original`，记录来源、相对路径、SHA-256、尺寸、Mip；此目录不得被转换工具覆盖。
2. 按 [批次规范](references/batch-workflow.md) 分类和交给用户转换。当前已坏的 BC6H 不能作为原始格式依据；Alpha 丢失时必须回到原始来源。
3. 用 [DDS 头检查工具](scripts/dds_utils.py) 读取头信息；它不解码像素，不承担 Alpha 视觉验收或自动转换。
4. 整批预检：原始 SHA 未变；输出唯一且无缺失/额外文件；路径不越出源目录；格式合法且不为 BC6H；宽高和 Mip 完全一致；解码检查 Alpha 保留及方向。任何失败均不开始覆盖。
5. 备份将被覆盖的当前源文件，只写本批清单路径，逐张读回 SHA 并记录报告；写入中途失败则用备份回滚已写文件，不能报告整批成功。
6. 按 [源 Pack 工作流](../warhammer-mod-development/references/pack-workflow.md) 导入本次 DDS 并诊断。恢复来自已验证的 `input_original`，恢复后同样同步 Pack。

## 辅助工具与边界

`python <技能目录>/scripts/dds_utils.py <文件.dds> ...` 仅输出 JSON 信息与 SHA，不修改图片。旧 BC7→BC6H 的 prepare/apply/restore 自动流程已退役，避免与本流程冲突；它们不是本包的依赖。

DDS 编码/解码工具（如用户的 Photoshop DDS 插件）由执行环境提供。每次操作先读工具参数；不能把头检查通过当成像素、Alpha 或完整压缩数据已经验证。报告批次、原始来源、分类计数、尺寸/Mip/Alpha、覆盖/恢复数量以及 Pack 结果。
