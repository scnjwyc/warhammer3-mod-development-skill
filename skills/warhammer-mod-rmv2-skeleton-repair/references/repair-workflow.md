## 修复闭环

每次修复均按以下顺序完成。不要跳过中间诊断，也不要先覆盖源 RMV2 或 pack。

1. **锁定活动资产。**
   - 从当前角色的 `variants`、`agent_uniforms`、`campaign_character_art_sets`、`campaign_character_arts` 追到实际 `.variantmeshdefinition`。
   - 继续解析 `variantmeshdefinition -> .wsmodel -> .rigid_model_v2`，记录真正运行的模型路径，不能把同目录旧模型或参考模型当活动文件。
   - 读取 `pack_map.json`，确认 MOD 的映射源 pack；本地源文件始终是唯一修改入口。

2. **建立不可变基线。**
   - 读取待修 RMV2 的当前字节，记录 SHA-256、长度、版本、骨架名、每个 LOD 的网格/顶点/三角形数、材质 ID 和顶点格式。
   - 在 `tmp/<repair>/backups/` 保存带来源 SHA 的备份。候选只写入 `tmp`，不要覆盖源文件。
   - 为任何写入脚本设置输入 SHA allowlist；输入不在 allowlist 时中止。已是最终 SHA 时可以明确报告 no-op，不能重新叠加修复。

3. **取得真实游戏骨架和动作。**
   - 从 RMV2 的 skeleton name 取得对应标准 `animations/skeletons/<name>.anim`。RMV2 不保存 bind pose，骨架 rest/bind 信息来自该 `.anim`。
   - 从活动角色实际战斗/战役动作链选择攻击、施法、受击、移动、待机等真实 `.anim`。参考 pose 只能验证导入器兼容性，不能验收变形。
   - 在 Blender 中按顺序导入：标准骨架，再导入 RMV2 并绑定该 armature，最后把真实动作导入同一 armature。确认动作文件声明的骨架与 armature 一致。

4. **先分类，再动顶点。**
   - 在真实动作帧上用 Blender evaluated mesh 检查受影响区域。读取骨索引时先映射为**骨骼名称**，不能只按数字猜测。
   - 在“权重/索引错误”“局部过渡错误”“bind-pose 位置错误”三类中确定一类主因。判断规则见 [诊断与重定向](diagnosis-and-retarget.md)。
   - 结论必须说明：活动资产、骨架、动作帧、受影响 mesh/LOD/顶点区域，以及为什么选择权重或位置修复。

5. **生成独立候选。**
   - 所有候选输出独立 RMV2、JSON 审计报告、动作指标和 Blender 场景/渲染；基线保持不变。
   - 权重或骨索引问题：只修改已证明错误的非零 influence slot 或过渡带；保持每个顶点的整数权重和与最多四个 influence。
   - bind-pose 问题：用旧/新游戏 skeleton 的 world matrices 和原始权重推导理论 rest position。先修核心高误差顶点，再沿**三角面拓扑**连续衰减；不能在空间盒边界做硬切。
   - 同坐标 seam 必须作为逻辑簇同步处理。对权重平滑，只有同位置且原始权重签名相同的副本可合并；对顶点位置重定向，同位置副本应写成同一目标位置。详细约束见 [原始 RMV2 写入契约](raw-rmv2-patch-contract.md)。

6. **做字节级和动作级验收。**
   - 用 RMV2 解析器重新读取候选。文件长度、版本、skeleton name、LOD/model 结构、材质、attachment、顶点格式、三角形、法线、切线、副法线、UV、颜色和无关 mesh 必须保持不变。
   - 位置修复：未选中的顶点位置保持完全一致。权重修复：只允许审计表列出的 influence slots 改变。
   - 全文件 byte diff 必须等于预期的原始顶点块偏移集合。记录 source/output SHA、修改字节数、顶点数、slot 数和样本审计。
   - 在相同真实动作帧比较基线与候选的边长对数畸变、三角面积对数畸变、非相邻三角面重叠、相邻面二面角以及 duplicate seam 分离距离。渲染正后、斜后、前侧等能看清故障的近景，并保留全子网格渲染。
   - 使用候选的必要条件是：已定位区域改善、邻近关节没有回归、二进制约束通过、画面没有新的撕裂/尖刺/开口。数值指标和画面出现分歧时，先定位指标覆盖的实际顶点区域，再继续生成候选。

7. **写回源和 Pack。**
   - 仅在验收候选确定后，备份当前源 RMV2，再替换 `mod/<MOD>/.../*.rigid_model_v2`。
   - 用 RPFM MCP 打开 `pack_map.json` 映射的源 pack，只导入本次改动的 RMV2 内部路径并保存。不能另存新 pack，不能改第三方 pack，不能把模型修复和全量 pack 重建混在一起。
   - 读取 pack 内原始字节，计算 SHA 并确认与本地源逐字节一致。
   - 运行 RPFM diagnostics。处理真实 Error；诊断无法完成时明确报告未完成；Warning 需记录是否既有、是否与本次模型路径有关。
   - 最终由用户在游戏内复测角色实际存在的待机、攻击、施法、受击、战役和坐骑状态。默认当前映射源 pack 已加载，排查直接聚焦模型、动作和游戏机制。

[共用 Pack 工作流](../../warhammer-mod-development/references/pack-workflow.md) 是保存、隔离与诊断的统一规则。
