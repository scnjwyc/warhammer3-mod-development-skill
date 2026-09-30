## 过载技能命名规则（法术 overcast 规范）

法术类角色的技能若带超载（overcast）版本，**名称、effect 描述、effect 配置必须全部对齐原版规范**，否则会出现"名称带（超载）后缀""解锁超载的 effect 文案不对""正面效果显示成红字""effect 只显示文字无数值"等问题。以下规则逐条对照原版（如放逐之光 `wh_main_spell_light_banishment` / 再生术 `wh_dlc05_spell_life_regrowth`）。

### 1. 超载版 ability 命名：「高级」前缀，非「（超载）」后缀

- 超载版 ability 的屏幕名（`unit_abilities_onscreen_name_<ability_key>_upgraded`）统一用 **`高级<基础名>`**，**不要**写 `<基础名>（超载）`。
- 对照原版：`放逐之光` → `高级放逐之光`、`再生术` → `高级再生术`。
- DB 侧无需改动：基础版 `unit_abilities_tables.overpower_option` 指向 `<key>_upgraded` 即可，超载版 `icon_name` **复用基础版 key**（原版超载版无独立图标，不要造 `*_upgraded.png`）。

### 2. effect 描述文案：按 effect 类型套固定句式

一个法术 skill 在 `character_skill_level_to_effects_junctions_tables` 里通常挂 7 个 effect（分 2~3 级），每个 effect 的 loc 文案句式固定，**括号内的法术名随版本切换**（基础版用基础名、超载版用「高级XXX」）：

| effect 类型 | loc key 后缀 | 文案句式 | 数值占位符 |
|---|---|---|---|
| enable（解锁基础版） | `enable_<spell>` | `法术：『<基础名>』` | 无 |
| overcast（解锁超载版） | `overcast_<spell>` | **`增幅法术：『高级<基础名>』`** | 无 |
| cooldown（冷却速率） | `cooldown_<spell>` | `法术冷却时间：『<基础名>』` | `%+n%` |
| wom_cost（基础版消耗） | `wom_cost_<spell>` | `魔法之风消耗：『<基础名>』` | `%n` |
| wom_cost（超载版消耗） | `wom_cost_<spell>_upgraded` | `魔法之风消耗：『高级<基础名>』` | `%n` |
| miscast（超载版失误） | `miscast_<spell>_upgraded` | `施法失误概率：『高级<基础名>』` | `%+n%` |

**关键纠错点（常见误写）**：
- ❌ `允许超载施放：『XXX』` → ✅ `增幅法术：『高级XXX』`（这是 overcast 的原版标准写法）
- ❌ `XXX（超载）` → ✅ `高级XXX`（凡涉及超载版的 cost/miscast 描述，括号内一律用「高级XXX」）
- ❌ overcast 写成「允许超载」、enable 写成「增幅法术」（两者别搞反：enable=基础版解锁，overcast=超载版解锁）

### 3. effect 数值占位符：缺了就只显示文字、无数值

- cooldown / miscast 文案**末尾必须有 `%+n%`**（带符号百分比，显示如 `-30%`）。
- wom_cost 文案**末尾必须有 `%n`**（整数，显示如 `-2`）。
- enable / overcast 文案**不带占位符**（纯文本）。
- **漏写占位符 = 技能树里该 effect 显示文字但不显示数值**。占位符填什么数值由 `character_skill_level_to_effects_junctions_tables` 的 value 列决定，loc 里只负责放占位符。

### 4. effect 红绿颜色：`is_positive_value_good` 必须按类型设置

`effects_tables.is_positive_value_good`（第 6 列）决定 effect 文本颜色。规则：value 正负 × 该字段 → 正面（绿）/负面（红）。cooldown/wom_cost/miscast 的 value 都是负数（"减少"是好事），**必须设 `false`**（含义"负值才是好的"），否则负值被当成坏事显示成**红字**。

| effect 类型 | value | `is_positive_value_good` | 显示颜色 |
|---|---|---|---|
| enable / overcast | 正 | **true** | 绿 |
| cooldown（-30%/-50%） | 负 | **false** | 绿 |
| wom_cost（-2/-3） | 负 | **false** | 绿 |
| miscast（-15%） | 负 | **false** | 绿 |

**症状**：正面效果（冷却减少、消耗减少）却显示红色 → 检查 `effects_tables` 该 effect 的 `is_positive_value_good` 是否误设为 true。

### 5. 排查与修复流程（实战）

1. 找超载版 key：`unit_abilities_tables` 里基础版的 `overpower_option` 列指向 `<key>_upgraded`。
2. 查 loc 缺失：在角色 loc 文件搜 `<key>_upgraded`，应有 `unit_abilities_onscreen_name_*_upgraded` + 涉及超载版的 `wom_cost_*_upgraded` / `miscast_*_upgraded` 三类行。
3. 查 effect 配置：`effects_tables` 该角色文件里 cooldown/wom_cost/miscast 行的 `is_positive_value_good` 是否为 false。
4. 查占位符：cooldown/miscast 文案带 `%+n%`、wom_cost 带 `%n`。
5. 修改只动 loc 文案与 `effects_tables` 的 `is_positive_value_good` 列；DB 结构（overpower_option、junction、bonus_value）与图标无需改动。

**无双英灵录实例（已修复）**：女娲的补天之力/创世之光、妲己的荆棘领域/退箭领域，均经历了"补超载版 loc → 补占位符 → 名称改「高级XXX」+ overcast 改「增幅法术」→ is_positive_value_good 改 false"四轮修复。新建法术角色时按本节规则一次性配齐，避免重复踩坑。
