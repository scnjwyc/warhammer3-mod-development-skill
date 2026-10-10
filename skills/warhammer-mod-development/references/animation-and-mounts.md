# 动作键、骨架与骑手挂点

### 大地图与战斗骑手骨骼、动作匹配

- 大地图角色的 `campaign_character_arts_tables.land_animation`、`campaign_mount_animation_set_overrides_tables.character_animation_set` 与 `rider_animation_set` 必须和骑手模型的骨骼类型一致；不得因角色外观或性别而跨骨骼套用动作。
- 例如，穗香的骑手骨骼为 `hu1`，陆地及坐骑骑手动作只能使用 `cam_hu1_*`；不得使用 `cam_hu1e_*`。跨骨骼会造成十字摆姿或错误的默认外观。
- 排查大地图骑乘异常时，先沿上述三项动作键确认骨骼前缀一致，再检查 `agent_uniforms`、`variants` 和模型资源；战斗模型正常不代表大地图动作链有效。
- **战斗表是独立键域。** `battle_personalities_tables.man_animations_table` 与 `land_units_tables.man_animation` 都引用 `battle_animations_table.key`；即使 TSV 列数正确，键不存在也会被 RPFM 以 `Invalid reference` 拒绝导入。
- `cam_*` 仅属于大地图动作链，绝不能填入上述战斗字段，也不能靠删除 `cam_` 前缀推导战斗键。某个 `cam_hu1_empire_dr1_dragon_wb_sword_and_shield` 可以合法，但对应的 `hu1_empire_dr1_dragon_wb_sword_and_shield` 未必存在于战斗动画表。
- 修改坐骑战斗动作前，先在 `源码/db/battle_animations_table_tables/data__.tsv` 查找精确键，并核对本地 `schema_wh3.ron` 中字段的引用目标和可空性；再按骑手骨骼、武器和坐骑选用原版同类基准。相同骑手/坐骑的两张战斗表应使用同一或经原版证明兼容的键，战役覆盖表继续保留对应的 `cam_*` 键。
- 本例的女性持剑盾龙骑兵：`hu1_empire_dr1_dragon_wb_sword_and_shield` 为无效战斗键；可用且有原版女性龙骑兵先例的是 `hu1b_elf_dr1_dragon_wb_sword_and_shield`。这只是该骨骼/武器组合的基准，不能不经验证套用到其他角色。
- 导入前对所有改动的坐骑行验证：字段列数等于表头、每个战斗动画键存在于 `battle_animations_table.key`、无旧无效键残留，并运行 `git diff --check`；先改源 TSV，再按 Pack 工作流导入映射源 Pack。

### 骑手错位、挂点与飞行坐骑排查顺序

- 若骑手动作会播放、却没有正确坐在坐骑上，先查 `land_units_to_battle_personalities_junctions_tables.attach` 与 `riders_attachment_point`，不要继续盲换动作。必须以**相同 mount key 的原版单位**为基准；挂点名不可跨坐骑套用。例如高精耀星龙使用 `autonomous_rider` + `ap_riderpos_0`，`ap_riderposition_0` 是其他坐骑的不同挂点，拼写近似也会导致骑手错位。
- 挂点正确后，再同时核对 `land_units_tables.man_animation`、`battle_personalities_tables.man_animations_table` 与骑手 RMV2 骨骼；两张战斗表使用同一或原版证明兼容的动作键，且该键在 `battle_animations_table_tables` 中的骨骼必须匹配。不要由 `cam_*` 键名推导战斗键。
- 只有在活动 `.variantmeshdefinition` → `.wsmodel` → `.rigid_model_v2` 链明确显示根骨骼名称不一致时，才处理 `animroot`/`animRoot` 之类的大小写问题；先备份，确认替换为等长且仅改目标字节，并核对替换数量与文件长度。它不是挂点错误的替代诊断。
- 飞行坐骑不能只看 `mounts_tables`、`land_units` 的 `flying_*` AI 分组或 UI 的 `can_fly` 文案；必须沿 `land_units_tables.attribute_group` → `unit_attributes_to_groups_junctions_tables` 确认该单位实际获得原版 `flying` 属性。
- 若自定义坐骑复用了不含 `flying` 的原版属性组，不要给共享原版组补属性而影响其他单位；复制原组实际属性到 MOD 自有属性组，额外加入 `flying`，再仅让该自定义 `land_units` 指向新组。若仍无法飞行，再按同类原版单位核对 `unit_set_to_unit_junctions_tables` 的 `all_units_excluding_flying` 和是否应使用 `always_flying`。
- 最终验证除 TSV 列数与引用外，还要确认原版同类坐骑确实存在所选挂点、所有自定义属性键来自原版 `unit_attributes_tables`，并运行作用域化 `git diff --check`；按 Pack 工作流导入映射源 Pack。

[源 Pack 工作流](pack-workflow.md)。DB/挂点链排除后仍有模型层扭曲时，记录活动骨架、动作与模型证据，再用目标环境的模型工具检查权重与骨索引。

## 移动射击的分层排查

单位能移动、站定能开火，不代表移动射击动作链完整。先区分“命令/投射物未执行”和“已射击但持枪姿态错误”，再沿以下层次定位：

1. **DB 与活动资源。** 核对远程武器、移动射击属性/限制、`man_animation`、battle personality、文化到动画表的实际映射；记录当前步行/坐骑、骨架、武器与活动动作集。
2. **动作槽与元数据。** 解码实际 `.bin`，检查前/后/左/右移动开火槽及它们引用的 `.anim`、`.anm.meta`、`.snd.meta`，包括混合/上下身处理与事件。某 humanoid 样本的槽号为前 `1570`、左 `1572`、右 `1573`、后 `1574`；只可作为定位线索，不是所有骨架/版本的固定枚举。站立 rifle 动作能播放，不证明它适合移动射击混合。
3. **容器与加载路径。** 同一 Pack 内虚拟路径可能同时有独立 `.bin` 与 `.animpack` 内成员。先确认真实加载来源；双份保留时核对解码内容与目标修改一致，不能只改外层文件就宣称修复。解包、编辑和重包前先做不改内容的 round-trip，检查路径、条目集合、长度/内容是否变化，保留原始备份。
4. **模型层。** 动作键、槽、元数据、武器挂点均有正确证据后，若还有骨架拉伸或手指扭曲，再进入 RMV2 权重/骨索引修复。不能因上半身姿态异常就先改顶点。

一次只改有证据的一层，保持其他变量。不要把 `su_dgxl` 等个案的版本号、默认 blend time 或某套站立动作当成通用补丁；历史案例中“走路正常、上半身仍异常”只证明问题尚未完成，不证明具体骨骼遮罩机制。

离线验证包括动作键、各方向槽、资源路径、meta 引用、容器内外一致性及源 Pack 读回。由用户实机分别检查前后左右移动、转向、开始/停止、瞄准/装填与近战切换，并分别观察腿部移动、上身持枪、枪口/投射物和声音。静态 round-trip 成功不等于动作混合已正确。
