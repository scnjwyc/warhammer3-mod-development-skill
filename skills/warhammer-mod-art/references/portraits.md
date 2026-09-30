# 角色兵牌与头像

## 角色兵牌与立绘绘制规则

适用范围：传奇领主、事务官、英雄、可进自定义战斗的具名角色。**角色不是普通单位**：角色通常也有 `main_units_tables`、`land_units_tables`、`unit_variants_tables`，但还会额外依赖 `agent_subtypes_tables`、`units_custom_battle_permissions_tables`、`general_portrait`、`set_piece_character`、`general_uniform` 等角色专用链路。

### 角色与普通单位的资源差异

- 普通单位通常主要看 `unit_variants_tables.unit_card`，对应资源为 `ui/units/icons/<unit_card>.png`；大图通常在 `ui/units/infopics/<unit_card>.png`。

- 角色在自定义战斗中还要看 `units_custom_battle_permissions_tables.general_unit`、`unit`、`faction` 和 `general_portrait`。其中 `general_portrait` 通常直接写完整路径，例如 `ui/portraits/portholes/no_culture/<key>.png`。

- 不要把 `general_portrait`、`ui/portraits/units/no_culture/*.png`、`ui/units/icons/*.png` 混成同一个槽位。它们可能长得相似，但读取路径和使用场景不同。

- 如果角色在自定义战斗里不可见，先查 `units_custom_battle_permissions_tables` 是否绑定到正确派系、正确 `unit`、`general_unit=true`，再查 portrait/兵牌资源；不要只按普通单位的 `unit_card` 排查。

### 常见角色 UI 资源槽位

- `ui/portraits/portholes/no_culture/*.png`：角色头像/自定义战斗 `general_portrait` 常用槽位。必须先测量当前 MOD 的同槽位参考 PNG，不得沿用通用 `164x164` 假设；例如**无双英灵录**的 porthole 为 **`300x164`**、`Format32bppArgb`，参考 `wyccc_lord_xiahouji.png` 与 `wyccc_hero_suixiang.png`。

- `ui/portraits/units/no_culture/*.png`：竖版角色 portrait，原版女角色参考如 `brt_ch_fay_enchantress_0.png`、`ksl_katarin_0.png`，常见尺寸为 `60x130`。

- `ui/units/icons/*.png`：`unit_variants_tables.unit_card` 对应兵牌。若角色的 `unit_card` 指向此处，实际读取文件名是 `<unit_card>.png`，不是必然等于 `unit` key。

- `ui/units/infopics/*.png`：兵种/角色信息大图，常见尺寸为 `120x260`；可比 60x130 兵牌展示更多身体，但仍应符合原版 UI 构图。

### 角色 art set 与大地图 2D 头像完整性

- 绘制或补齐角色立绘前，必须先枚举该角色在 `campaign_character_art_sets_tables` 中的全部 `art_set_id`，包括主记录、备用服装记录和其他依赖文件记录；不能只检查与角色 key 同名的主 art set。

- 大地图 2D 头像的完整链路是：每一个可用 `art_set_id` → `ui/portraits/portholes/portrait_settings*.bin` 中的一条 art set 映射 → 一个实际存在的 porthole PNG。多个 art set 可以复用同一张 PNG，但每个 art set 都必须有登记。

- `campaign_character_arts_tables.portrait`、`units_custom_battle_permissions_tables.general_portrait`、`ui/portraits/units/no_culture/*.png` 和 `ui/units/icons/*.png` 不能互相替代。前两者或 60x130 兵牌存在时，仍必须单独确认大地图 `portrait_settings` 与 300x164 porthole；缺少 porthole 时不得把角色头像配置标记为完成。

- “全种族通用”只表示 art set 的 `culture`、`subculture`、`faction` 可以为空，不表示只有一条 art set，也不提供 porthole 自动回退。遇到多个 art set 或备用服装时，必须按 art set 全量比对并逐条验证路径。

### 绘制构图要求

- 角色的 60x130 兵牌/portrait 应参考原版角色，而不是普通部队方阵。女角色可优先参考费伊、妙影/昭明人形、卡捷琳等原版文件的镜头比例。

- **硬性否决项：60x130 角色图必须是头部到胸肩的近景。** 脸部居中且可读，头饰接近顶部但不切脸，底部只保留领口、肩部或少量胸甲。**最终成图中必须以双眼中心所在的 `eye_y` 水平线为唯一验收位置：只计脸部和头发，不计头饰；该行的真实头部前景宽度必须至少为 `48px`（画布宽度的 `80%`），可更大。** 宽度不足时直接判定为过远，必须重裁切；不得把全身立绘缩进竖条里。

- `portholes` 应更接近头像/半胸像，优先保证脸部、头饰和身份特征清楚；不要用远景全身图。

- 无双英灵录的 `300x164` porthole 必须保留 alpha：以双眼中点/脸部中心而非披风、武器或姿势的可见边界为准，将头部居中到 `x=150` 附近；构图参考夏侯姬、穗香的横幅半身像，允许肩部、手臂或既有武器延伸到两侧，但不得让脸偏到一边。

- `infopics` 可以使用半身或接近全身构图，但要先看原版同类尺寸和裁切方式，避免 UI 中关键特征被截断。

- 禁止加入文字、水印、UI 边框、重复背景人脸或无关角色。AI 生成稿必须再经过本地确定性裁切/缩放，不能直接把大图改名塞进目标路径。

### 60x130 人物兵牌镜头标尺与裁切

- 必须先把目标兵牌与至少 3 张同类型原版或可靠参考兵牌按 `60x130` 原始尺寸并排比较。放大预览只用于量像素和查裁切，最终判断必须回到 `60x130` 原始尺寸。

- 眼线必须量双眼瞳孔中心或眼球中心，不得用眉毛、眼睑或宽泛的 `y=45-55` 区间代替。对每张参考图记录 `eye_percent_i = y_i / 130 * 100`，再用 `target_y = round((y_1 + y_2 + y_3) / 3)`；例如参考眼线为 `47、46、48` 时，目标为 `y=47`，即 `36.15%`。把测量值、公式和最终目标像素写入工作记录。

- 脸部中心接近 `x=30`，但不能只让脸居中而把头发缩小。**唯一有效的宽度测量在最终 `60x130` 坐标系的双眼中心行 `eye_y` 完成：建立只包含脸部和头发、明确排除头饰的前景掩码，计算 `eye_line_min_x`、`eye_line_max_x` 与 `eye_line_width = eye_line_max_x - eye_line_min_x + 1`。不得改用头顶、下巴、任意纵向并集、裁切框、源图宽度、缩放比例推算值或 `DrawImage` 的目标宽度。** 若深色头发与纯色背景难以从最终 RGB 区分，应在同一裁切/缩放后的 alpha/前景掩码上测量。**眼线宽度的掩码不得包含头饰、肩膀、手臂、武器或裁切边缘；若该行的头发触到裁切边缘而无法证明轮廓完整，直接重裁切，不得把边缘当作头部宽度。** `eye_line_width < 48px` 直接否决并重裁切；常规人物兵牌还应接近左右边缘（建议 `eye_line_min_x<=3`、`eye_line_max_x>=56`），同时保持眼睛不被横向裁断。头饰、冠冕、角、羽翼等特别高时允许顶部溢出画布，但永远不计入眼线宽度。

- 必须先抠出人物前景，再整体丢弃原背景并铺设单一纯色背景。禁止从 porthole、infopic、其他角色或生成图中拼接背景补片；禁止保留花纹、渐变、重复人脸、断层或明显色带。没有 alpha 的源图要建立前景掩码，并保护面部高光、白色头饰/衣饰、头发边缘和抗锯齿过渡。

- 用户提供明确设定图或原角色截图时，该图是面部、发型、服装、配色、饰品和装备的身份基准。不得擅自改脸、改衣服、换姿势、增加武器或补充不存在的装饰；有可用原图时优先做确定性裁切，不要用 AI 重绘替代。

- 不要把带大面积透明边缘的整张画布或全身像直接缩放为 `60x130`。先读取 alpha 可见边界，定位脸部、双眼和肩部，再裁出头肩近景；否则人物会显得过小、头部偏下。

- 裁切框必须保持 `60:130 = 6:13`。若源裁切高度为 `H`，则裁切宽度应为 `H * 6 / 13`；缩放比例为 `s = 130 / H = 60 / W`。可用 `crop_x = face_center_x - 30 / s`、`crop_y = source_eye_y - target_eye_y / s` 求初始框，再根据头饰和肩部微调。

- 调整幅度只有 1-2 个目标像素时，游戏内通常几乎看不出差异。若反馈为“完全没改”，必须并排对比修改前后图并检查 SHA-256，确认文件确实变化；随后按眼线或头顶位置做足够明显但不过度的位移。

- 人物兵牌的最终 `60x130` 成图必须同时写入 `ui/units/icons/<key>.png` 与 `ui/portraits/units/no_culture/<key>.png`。两者是独立槽位，不能只改其中一张后假定另一处会自动更新；写回后用尺寸与 SHA-256 确认两处完全同步。

- **最终逐项验收必须先输出眼线单行的真实掩码数据**，例如 `eye_y=47, eye_line_min_x=2, eye_line_max_x=57, eye_line_width=56px, headgear_excluded=true`；缺少任一项即视为未验证。随后确认画布为 `60x130`、`eye_line_width>=48px`、眼线等于计算出的目标 `y`、脸未变形、下巴高度接近参考、头饰裁切合理、肩部填满底部、无新增武器。逐点检查背景是否为同一个纯色 RGB 值、边缘是否有残留原背景或断层；即使 `*.png` 被 `.gitignore` 忽略，也要用文件元数据和哈希验证实际写回结果。**不得用裁切框、头顶、纵向并集或头饰替代眼线单行的真实头部宽度验收。**

- 若写入 porthole，额外验证其尺寸、`Format32bppArgb`、四角透明，以及双眼中点/脸部中心是否位于横幅中线附近；不得只因人物披风或武器延伸而误判为“居中”。

### 推荐制作流程

1. 修改前先读取当前 DB 行和 PNG：至少确认 `unit_variants_tables.unit_card`、`units_custom_battle_permissions_tables.general_portrait`、现有 PNG 尺寸/像素格式。

2. 先枚举全部 `art_set_id`，逐条核对 `portrait_settings*.bin` 和 porthole PNG；任何备用 art set 未登记或 porthole 缺失，都先记录为配置未完成。

3. 先从 `源码/ui/portraits/units/no_culture/`、`源码/ui/portraits/portholes/no_culture/` 找同类原版角色，并在至少 3 张 `60x130` 参考图上量出眼线百分比和头部横向边界。

4. 先用原始角色图建立前景掩码并检查抠图边缘，再把背景整体替换为一个明确的纯色 RGB；背景参考图只能用于选色或构图，不得直接复制背景像素。

5. 生成图只作为源素材；最终用 Pillow/System.Drawing 等本地工具抠图、裁切、缩放和铺设纯色背景到精确尺寸，例如 `60x130`、`120x260`，以及由当前 MOD 参考决定的 porthole 尺寸（无双英灵录为 `300x164`）。生成式工具不得改变角色身份、服装、武器状态或镜头位置。

6. 绘制人物兵牌时，将同一张最终 `60x130` 近景同步写入 `ui/portraits/units/no_culture/<key>.png` 与 `ui/units/icons/<key>.png`；即使其中一处当前不可见，也不可遗漏。确认 DB 的实际读取路径，但不得以此跳过其中任一资源。

7. 写回后必须目视检查原始尺寸和放大预览，复核眼线目标像素、头部贴边比例、脸部和头饰裁切、纯色背景边界，缩略图下仍能识别角色。

8. 验证最终 PNG 的尺寸、像素格式和路径；如果仓库 `.gitignore` 忽略 `*.png`，最终回复中说明文件已写入但 `git status` 可能不显示。

9. 只改工作区源文件；按 [源 Pack 工作流](../../warhammer-mod-development/references/pack-workflow.md) 同步本次资源。
