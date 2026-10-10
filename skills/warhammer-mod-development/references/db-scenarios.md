# 场景化 DB 配方

这里给出调查顺序和最小数据链，不提供脱离版本的万能 TSV。实施时读取当前表头、schema 和同机制的原版完整行；按 [效果职责](effects_and_bundles.md) 核对机制、载体和 scope。新增记录使用 MOD 自有 key，只有确需覆盖的行才沿用原版 key。

## 定向禁用能力

**目标：只让选定单位失去指定能力。**

1. `unit_sets_tables` 创建目标集合，`unit_set_to_unit_junctions_tables` 精确指定成员或过滤条件，查 schema 确定 `unit_record` 实际引用；不要混用 main/land unit key。
2. `unit_set_unit_ability_junctions_tables` 建立 `key, unit_ability, unit_set`。
3. `effects_tables` 注册自有 effect；`effect_bonus_value_unit_set_unit_ability_junctions_tables` 用当前原版支持的 `disable` 机制，将 `unit_set_ability` 指向第 2 步的 **junction key**。
4. 由建筑、技能、装备或 bundle 等实际载体施加该 effect，复制同类 disable 的 value 和适合载体的 scope。
5. 反查集合成员、effect 使用者和原始挂载。区别永久解绑与随载体存在的禁用；共享原版 disable effect 不追加自己的目标。

若需求只是从某单位永久移除直接挂载，先调查 `land_units_to_unit_abilites_junctions_tables` 的具体行。支持 `twad_key_deletes` 的当前游戏/RPFM 可以按完整主键定向删除原版记录，但须先确认版本支持、编码和工具输出，并检查其他记录是否仍引用它。它不是普通空值覆盖，也不是删除全局 ability 主表的默认方案；常规诊断不能代替删除后的引用审计。不要为此运行会重写整个 Pack 的优化器。

## 真实单位容量

**目标：增加可拥有/招募的某兵种容量，而非增加池内库存。**

常见列表链：`main_units` → `unit_to_unit_list_junctions_tables` → `unit_lists`；`unit_allowances_tables` 按 `unit_list + faction_set` 定义基础 `point_cap`。动态加成由自有 effect → `effect_bonus_value_unit_list_junctions_tables` 的 `unit_allowance_point_cap_mod` → 实际载体施加。

先查目标单位已有机制：部分机制还使用 unit set 和 `unit_cap`；不能把列表链套给所有单位。检查列表是否含其他单位、派系集是否过宽、重复来源是否累加，以及旧存档的持久状态和迁移。

区分三个结果：**容量改变、佣兵/RoR 池库存改变、现有军队立刻得到单位**。`cm:add_unit_to_faction_mercenary_pool` 改的是池子，不能替代已确认的真实容量链。永久购买容量应保存已购数量，并重建或更新对应永久 bundle；读档后不得再次扣款或重复叠加。

## 两难选择购买与立即发兵

**目标：付费后给指定现有军队单位或奖励。**

调查 `dilemmas_tables`、`cdir_events_dilemma_choice_details_tables`、`cdir_events_dilemma_option_junctions_tables` 的选择与目标；载荷放在 `cdir_events_dilemma_payloads_tables`。扣款、bundle 和发兵分别对照同类原版 payload key/字符串，不能凭字段名拼语法。

发兵可沿 `CAMPAIGN_PAYLOAD_RECORD` → `campaign_payloads_tables` → `campaign_payload_unit_components_tables`，核对单位、数量、经验和 `ignore_unit_cap`。购买容量本身不等于发兵；是否忽略容量必须符合设计，不默认设为 true。每张表的数字 ID 类型分别查 schema，不能把 incident、dilemma、option 的 ID 当成同一种类型。

验证真实流程：触发条件 → 目标军队选取 → 选择可用性与余额 → 扣款 → 发兵/加成 → 保存与读档。目标不存在、军队已满、余额不足、容量不足、取消与重复事件都需有明确结果。脚本同时记录“已发出选择”和“已结算”时，按失败位置处理重试，不能把未结算的奖励提前记成完成。新开档和旧存档迁移分开设计。

## 旗帜赋予单位效果

**目标：旗帜拖给哪个单位，效果就给哪个单位。**

`ancillaries_tables.provided_banner` → `banners_tables.banner` → `banners_tables.effect_bundle` → bundle/effect junction → 对应 bonus 机制。允许挂载的单位集合由 `banners_permitted_unit_sets_tables` 约束。

普通装备的角色加成可直接走 `ancillary_to_effects_tables`；旗帜赋予单位的效果要检查上面的专用链和同类原版 banner scope，例如 `character_to_character_own_banner`。拥有旗帜不等于已分配给单位，拥有者加成不等于分配单位加成。

赋予能力还要检查能力主表、phase、单位挂载及 `requires_effect_enabling`。旗帜、bundle、effect 和 ability 使用各自正确 key，不能靠全部同名掩盖断链；`provided_banner` 必须填 banner key。按同类旗帜核对分配限制、已有能力是否重复、移除/换单位后是否撤销，以及旧存档是否仍引用旧 key。

## 交付与证据

仅写本地源，精确比较修改行，再按 [源 Pack 工作流](pack-workflow.md) 导入本次路径、保存、关闭重开、读回和 Error 诊断。不创建额外安装 Pack、不往补丁塞原版表以消除依赖误报。上述静态检查不能宣称扣款、容量或旗帜在游戏中已生效；用户提供实机结果后再定位缺失边界。
