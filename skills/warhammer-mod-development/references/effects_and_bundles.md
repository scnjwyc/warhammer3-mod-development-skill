# 效果系统：定义、机制映射、载体

排查一个效果时分别回答三件事：**叫什么、实际修改什么、由谁以什么数值和 scope 施加**。UI 描述存在只证明显示层有数据。

| 职责 | 数据 | 检查重点 |
|---|---|---|
| 定义与显示 | `effects_tables`、图标、`effects_description_<key>` | key 注册、正负值语义、显示文本 |
| 机制与目标 | 对应的 `effect_bonus_value_*` 表及其引用目标 | 引擎支持的 `bonus_value_id`、目标 key、目标类型 |
| 载体、数值与作用域 | 建筑/科技/技能/装备/特性 junction，或 bundle 与 Lua | 生效时机、value、scope、适用对象 |

自定义 effect 可以映射到原版支持的 bonus 机制。`bonus_value_id` 是该表指定的机制键，**不是任意生成的唯一 ID**；从相同机制的原版记录复制，再查 schema 的引用目标。例如 faction junction 的机制键引用 `campaign_bonus_value_ids_factions`。

## 载体选择

| 需求 | 常见载体 |
|---|---|
| 建筑、科技 | `building_effects_junction_tables`、`technology_effects_junction_tables` |
| 角色技能、装备、特性 | `character_skill_level_to_effects_junctions_tables`、`ancillary_to_effects_tables`、`trait_level_effects_tables` |
| 事件奖励、临时或持久的动态加成 | `effect_bundles_tables` + `effect_bundles_to_effects_junctions_tables`，或自定义 bundle 接口 |

前两类可直接绑定 effect，不需要先创建 bundle。旗帜还有 `provided_banner` → `banners` → bundle 的专用链，见 [场景配方](db-scenarios.md#旗帜赋予单位效果)。

`effect_scope` 同时描述来源与接收者。选择**同载体、同目标层级、同机制**的原版 scope；不要把 faction scope 套给技能、旗帜或区域效果。bundle 的 `bundle_target` 和 UI 配置不能代替 effect scope。`advancement_stage` 按同表原版记录填写，可能是 `start_turn_completed` 等字符串，不默认填数字 `0`。

## Bonus junction 的精确结构

以下是 2026-10-08 本地导出的列顺序示例，更新后重新核对：

| 表 | 列顺序 | 常见用途 |
|---|---|---|
| `effect_bonus_value_unit_ability_junctions_tables` | `effect, bonus_value_id, unit_ability` | 能力 enable、overcast、cooldown 等 |
| `effect_bonus_value_unit_attribute_junctions_tables` | `bonus_value_id, effect, unit_attribute` | 原版单位属性 |
| `effect_bonus_value_faction_junctions_tables` | `bonus_value_id, effect, faction` | 特定派系外交等 |
| `effect_bonus_value_unit_list_junctions_tables` | `bonus_value_id, unit_list, effect` | 单位列表容量 |
| `effect_bonus_value_unit_set_unit_ability_junctions_tables` | `bonus_value_id, effect, unit_set_ability` | 指定 unit set 的能力 |

表之间列顺序与目标语义不同，禁止用一种通用三列模板直接生成所有 junction。`effect_bonus_value_basic_junction_tables` 的实际名称是单数 `junction`；不要猜测存在等价复数表或版本迁移规则。其他表逐个读取当前表头和 schema。

`unit_set_ability` 引用 `unit_set_unit_ability_junctions_tables.key`，不是直接填 `unit_sets.key`。资源消耗的 `resource_cost_pooled_resource_junctions_tables.pooled_resource_factor` 引用 `pooled_resource_factor_junctions_tables.unique_id`，不是 `pooled_resource_factors.key`；同名记录容易掩盖这个错误。

## 静态和动态 bundle

已有 DB bundle 按 key 应用：

```lua
cm:apply_effect_bundle(bundle_key, faction_key, duration)
```

自定义 bundle 对象使用对应对象接口，不能把对象传给上述 key 接口：

```lua
local bundle = cm:create_new_custom_effect_bundle(bundle_key)
bundle:set_duration(0)
bundle:add_effect(effect_key, scope, value)
cm:apply_custom_effect_bundle_to_faction(bundle, faction)
```

`bundle_key` 必须是 `effect_bundles` 中存在的基底记录；CA 接口从该记录创建自定义对象。`faction` 是已核实的有效 faction 接口。动态效果可由 `add_effect` 添加，不要求在 DB bundle junction 中预先定义同一组效果；检查基底已有内容，避免带入多余效果。所有 key、scope 和参数先对照当前 CA 文档/同类脚本，持久化、重建与重复应用按具体玩法的保存流程检查。

## 定向启用和移除

先分清“从某个单位解绑能力”“对一组单位施加 disable”“删除全局能力记录”。新能力通常沿原版同类能力的直接挂载与 `requires_effect_enabling` 机制接线；unit set 的过滤路径是否适合主动能力，需用对应原版链和用户实机结果确认，不能把某个失败案例写成所有 unit-set enable 都不支持主动技能。

需要局部禁用时建立自己的 unit set、ability junction 和 effect，再交给实际载体施加；不要给共享原版 disable effect 新增目标，扩大到原本引用该 effect 的所有载体。具体链和删除替代方案见 [场景配方](db-scenarios.md#定向禁用能力)。

## 验收

从载体沿 effect → bonus 机制 → 实际目标逐段查引用，再反向查共享 effect/集合的所有使用者。分别核对显示、数值和目标范围。TSV 及 Pack Error 检查只能证明静态结构；实际施加与引擎效果由用户在游戏中确认。

相关参考：[常用效果键](common_effect_keys.md)、[能力模板与行比较](ability-targeting.md)、[源 Pack 工作流](pack-workflow.md)。
