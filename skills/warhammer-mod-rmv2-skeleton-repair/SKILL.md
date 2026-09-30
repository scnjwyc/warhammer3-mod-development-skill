---
name: warhammer-mod-rmv2-skeleton-repair
description: "诊断战锤3 RMV2 模型与骨架/真实动作不匹配造成的关节扭曲、拉伸、seam 开裂和 bind-pose 错误，执行有字节边界的权重或位置修复。"
---

# RMV2 骨架与变形修复

先排除 DB 动作键、挂点和外观接线问题，见 [动作与挂点](../warhammer-mod-development/references/animation-and-mounts.md)。只有活动 RMV2、骨架、真实动作或顶点证据指向模型层时进入本流程。

1. 按 [修复流程](references/repair-workflow.md) 追踪 variantmeshdefinition → wsmodel → RMV2，保存不可变基线、SHA 和结构信息。
2. 取得当前游戏的标准骨架与角色真实动作，在同一 armature 上验证。按 [诊断与重定向](references/diagnosis-and-retarget.md) 区分索引/权重、局部过渡和 bind-pose 位置问题。
3. 候选写到独立临时目录；按 [原始写入契约](references/raw-rmv2-patch-contract.md) 限定修改字节和顶点集合，同坐标 seam 保持一致。输入 SHA 不匹配时中止，已修复 SHA 不重复叠加修复。
4. 重新解析候选，比较真实动作下的畸变指标和多角度渲染；无关 mesh、结构、UV、材质和未选中数据保持不变。候选通过后才写回源，并按 [Pack 工作流](../warhammer-mod-development/references/pack-workflow.md) 导入、读回 SHA、诊断。

[案例经验](references/validated-case-lessons.md) 记录有效和失败方法，只作方法参考；不能复制案例骨索引、顶点号、SHA、阈值或动作键。

## 执行环境与完成标准

实际二进制修复需要 Blender、能正确处理目标 RMV2/ANIM 版本的导入器/解析器，以及用户的模型、骨架和动作。本包提供算法与审计文档，不附带缺失的 `tools/blender_fix` 或旧案例产物。先确认导入器处理骨索引、权重、坐标与 evaluated mesh 一致，缺少环境时只完成可证明的诊断，不能声称模型已修好。

交付包含活动资源链、修复分类、源/候选/最终 SHA、修改字节范围、动作指标、渲染与 Pack 结果。Agent 不启动游戏；让用户复测该角色实际存在的待机、攻击、施法、受击、战役及坐骑状态。
