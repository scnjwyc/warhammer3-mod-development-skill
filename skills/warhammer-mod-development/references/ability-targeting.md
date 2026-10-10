# 按能力语义选择模板并比较完整行

制作或修复能力先把需求写成“谁激活、如何选目标、效果给谁、何时结束”，再选当前原版的同类记录。不要只因图标相似、同为法术或同一学派就复制。

## 选择模板

区分自体强化、友军单体、敌军单体、地面目标、范围光环、投射物、涡流、召唤和被动触发。还要匹配是否移动施法、是否持续施法、是否超载、是否需要效果启用。记录模板 key、来源版本及选它的理由。

同时读取三层，而不是只改一个布尔值：

1. `unit_abilities` 的挂载、可见性和 `requires_effect_enabling`。
2. `unit_special_abilities` 的 `affect_self`、`only_affect_target`、友敌单位数量/范围、目标拦截、激活位置和载荷字段。
3. phase junction 的 `target_self/target_friends/target_enemies`、phase 的持续时间及 stat/attribute 效果。显示链、invalid target/usage flags 和自动结束条件也要匹配该类能力。

**不存在所有自增益都必须 `num_effected_friendly_units>=1`、`only_affect_target=false` 的通用规则。** 2026-10-08 本地原版快照中，`lucky_banner` 的友军数量为 `0`；`reforge` 同时有 `affect_self=true`、`only_affect_target=true`。它们说明必须按语义与整条 phase 链选模板，不是要求新能力照搬这两个例子。

复合能力可分开配置不同对象的 phase；不要为对敌伤害误改自体增益目标，或把地面坐标和单位目标当成同一种输入。隐藏执行能力等项目已有流程见 [生命周期排查](debugging.md#隐藏执行技能的生命周期)。

## 精确比较

用随技能提供的 `scripts/diff_row.py` 比较完整行；支持复合主键，匹配及字段值均区分大小写，不自动忽略 ID、空值或其他差异。

```powershell
python <skill>/scripts/diff_row.py --template <vanilla.tsv> --mod <mod.tsv> --key-columns key --template-key <vanilla_key> --mod-key <mod_key> --allow key --allow unique_id --allow recharge_time
```

`<skill>` 替换为 `warhammer-mod-development` 的实际目录。复合键示例：`--key-columns effect bonus_value_id --template-key <effect> enable --mod-key <custom_effect> enable`。每个参数序列必须与键列数一致。

两份 TSV 必须表名、版本、列名及列顺序相同；元数据中的文件路径可以不同。脚本要求目标恰好一行，缺失或重复匹配立即失败。所有数据行检查列数，末尾空字段保留。`--allow` 只用于逐项审查后批准的改动；未提供允许列表时仍输出全部差异并以非零状态提示待审查。

退出码：`0` 无差异或差异全部在允许列表中；`1` 有未批准字段；`2` 输入、格式或定位错误。`--json` 输出结构化结果。该工具只读，不修改 TSV，也不证明机制在游戏内生效。

写入前保留字段差异表：哪些是新 key/ID，哪些是设计改动，哪些是为匹配目标语义必须更改。覆盖已有 key 时，非目标字段保持原值；克隆新能力时，不能因为“完整复制”就保留冲突 ID 或错误的 phase/载荷引用。

## 角色模板也按机制选

`unique_agents` 相关表按生成/唯一性机制决定是否需要，不能按“英雄必有、领主禁止”分配。当前原版中也有 general / `FACTION_LEADER` 记录。新角色先核对同类角色的生成路径、campaign group、组件及脚本，再复制相关链。

相关参考：[效果职责](effects_and_bundles.md)、[TSV 格式](tsv_format.md)、[版本维护](version-maintenance.md)。
