# 日志与战斗能力排查

先读用户点名的日志，否则定位与本次现象对应的最新 `script_log_*.txt`。不要先要求用户粘贴本机可读取的日志。检查编码（UTF-8/UTF-16 LE）、文件尾和模块标记；`rg --encoding utf-16le` 可用于 UTF-16 日志。没有搜到输出需区分编码、截断、脚本未加载与回调未触发。

日志用于确认执行边界，DB/资源链和用户游戏观察用于确认实际效果；没有日志不能推断模型/DB 必然无效。`pcall` 成功只说明没抛错。

### 战斗能力目标链与涡流数值排查

先按日志边界定位故障层，再修改数据：`能力指令收到` → `手动目标捕获` → `瞬移/施法命令发出` → `命中或爆炸效果`。缺少哪一条，就只排查该边界；不要在目标尚未捕获时修改伤害或生命 API。

- 多段爆炸、连锁技能的隐藏 `unit_special_abilities` 可能没有独立伤害/半径；先沿其 `vortex` 字段回溯到同一条 `battle_vortexs` 记录。五个隐藏技能共享同一 `vortex_key` 时，只需修改共享行，并用 TSV 查询确认没有漏引用。
- `battle_vortexs.damage` 是普通伤害，`damage_ap` 是破甲伤害，`start_radius`/`goal_radius` 是涡流作用半径，`expansion_speed` 决定在 `duration` 内能否达到目标半径。扩大 `goal_radius` 时，若持续时间不变，按 `(goal_radius - start_radius) / duration` 同步检查扩张速度。
- `unit_special_abilities.effect_range`、`target_intercept_range` 与涡流半径不是同一字段：前者可为自体中心的 `0`，后者控制手动目标可选的施法距离；不要因隐藏爆炸行的 `effect_range=0` 就判定爆炸没有范围。
- `composite_scene` 只决定视觉特效资源；画面大小不变不能证明命中半径不变。分别验证 DB 数值和游戏内命中结果，必要时再单独处理 VFX。
- 手动目标标记必须使用原版 `unit_attributes_tables` 中已存在、可叠加的属性；`special_ability_phase_attribute_effects.attribute_type=positive` 才是施加属性，`negative` 用于移除属性。脚本 `has_attribute` 找不到标记时，先查主技能的 `target_enemies`/`only_affect_target`/`target_intercept_range`，再沿 `special_ability_to_special_ability_phase_junctions` → `special_ability_phases` → `special_ability_phase_attribute_effects` 核对目标相位的 `affects_enemies`、原版标记属性和正负类型，并核对脚本的存活、敌我、标记分数与距离边界；此阶段不要改伤害或 vortex。禁止新增自定义 unit attribute。
- 生命百分比交换必须先缓存双方 `unary_hitpoints()`，再写回：`heal_hitpoints_unary(desired_fraction, false)` 设为目标比例，`reduce_hitpoints_unary(current_fraction - desired_fraction)` 扣除差值。只有日志出现“目标已捕获”后，才诊断这两个 API。
- 静态回归至少断言：所有隐藏技能的 `vortex` 引用、涡流伤害/半径字段、目标 `target_intercept_range`、目标标记数量与 `positive` 类型；再检查 TSV 列数、运行 `luac -p`（有 Lua 改动时）和作用域化 `git diff --check`。

### 隐藏执行技能的生命周期

- 多段原生效果使用预挂到 `land_units_to_unit_abilites_junctions` 的独立隐藏执行技能：`unit_abilities.requires_effect_enabling=true`、`is_hidden_in_ui=true`，由父技能的 `effect_bonus_value_unit_ability_junctions` 以 `enable` 效果控制拥有权。每段效果使用独立 key，避免一段施法的冷却或使用次数污染下一段。
- 战斗开始立即启动短期 `register_repeating_timer` 守卫；每次找到目标单位都调用 `disable_special_ability(key, true)`，连续检查到初始化窗口结束后注销计时器。这样预挂技能从战斗开始保持禁用，技能栏也不会出现助手按钮。
- 主技能触发时按固定生命周期执行：重置助手技能冷却与使用次数 → `disable_special_ability(key, false)` → 按实际施法反馈设置等待窗口（旧案例约 500 毫秒） → `can_perform_special_ability` → `perform_special_ability_ground` → 在确认执行后禁用（旧案例约 100 毫秒）。凤凰之舞的六段、天龙乱舞的八段都遵循这一模式；`Complete` 阶段注销守卫并统一禁用。
- `bm:spawn_vortex` 的 `pcall` 成功只代表调用未抛错，不能作为特效已生成的证据。需要可靠的多段原生涡流时，以 `unit_special_abilities` 的 `vortex` 引用配合 `perform_special_ability_ground` 为实现路径，并用日志与游戏内效果分别验收。
- 回归检查至少覆盖：助手技能 UI 隐藏与单位预挂、战斗开始禁用、施法窗口内唯一启用点、施法后禁用、每段独立 key、无 `spawn_vortex` 依赖；随后运行 Lua/TSV 校验并对改动路径做 Pack Error 扫描。

## 五行罗盘专项

### 3.1 五行罗盘冷却注意事项

- `wh3_main_effect_campaign_compass_coodown_mod` 只影响罗盘选择冷却修正值，不能用来立即清除当前 `WOM_COMPASS_SCRIPT_INTERFACE:get_compass_cooldown()` 或 UI `CompassCooldown`。
- 不要把这个 effect 或临时自定义 effect bundle 当作“立即重置五行罗盘冷却”的修复方案。
- `cm:set_next_winds_of_magic_compass_selection_cooldown(faction, 0)` 可以设置派系下一次罗盘选择冷却，但未证明能清掉当前 `CompassCooldown`；必须用 `cm:model():world():winds_of_magic_compass():get_faction_cooldown(faction_key)`、`get_compass_cooldown()` 和最新 `script_log_*.txt` 验证。
- 如果需求是立即切换罗盘方向，应优先检查 UI/CCO 流程，例如 `CanChangeDirection`、`ChooseCompassDirection`、`skip_cooldown_confirmation_holder`，不要先猜 DB/effect workaround。
- 截至本地源码验证，没有 Lua setter 能直接把当前全局 `CompassCooldown` 写成 0；可实现的是走原版“跳过当前冷却”机制。
- 原版 `skip_cooldown_confirmation_holder` 的 `button_tick` 只播放动画/关闭确认框，不会执行 `ChooseCompassDirection`；实测只在 `button_tick` 中调用 `ChooseCompassDirection(StoredContext("CcoCampaignWomCompassDirection"))` 仍可能无效，因为弹窗确认时存储的方向上下文不可靠。
- 若要验证 UI 绕过路径，优先改方向按钮自身的 `ContextCommandLeftClick`。该回调已有 `CcoCampaignFactionWomCompass fac, CcoCampaignWomCompassDirection dir`，可直接测试 `fac.ChooseCompassDirection(dir)`，并用 `WoMCompassUserDirectionSelectedEvent` 日志确认是否进入模型层。
- 如果希望跳过当前冷却不消耗方向能量，将 `campaign_variables_tables` 的 `winds_of_magic_compass_selection_cost_per_turn_on_cd` 覆盖为 `0.0000`；再配合 `cm:set_next_winds_of_magic_compass_selection_cooldown(faction, 0)` 清掉派系层 `FactionCooldown`。
