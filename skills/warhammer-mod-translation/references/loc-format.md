## 本地化键名命名规范

游戏从本地化文件加载文本时，键名必须遵循固定命名规范，由**表前缀** + **完整键名**组成。

**格式**：`{表前缀}_{完整键名}`

一个键通常对应两个本地化键：标题和描述。查询原版本地化文件获取用法示例。
例如，effects_tables 的键使用前缀 `effects_description_`。

### 常见错误

**错误**：直接将完整键名用作本地化键。

```tsv
-- 错误！游戏查找的键不是这个
wyccc_ogre_feast_warning_debuff	饕餮预警	debuff.png
```

**正确**：使用表前缀 + `_localised_title_` / `_localised_description_` 前缀。

```tsv
-- 正确！游戏查找这两个键
effect_bundles_localised_title_wyccc_ogre_feast_warning_debuff	饕餮预警
effect_bundles_localised_description_wyccc_ogre_feast_warning_debuff	食人魔大军逼近，城镇秩序下降，防御力量被削弱。
```

### 1. 换行符落盘必须是 `\\n`（两个反斜杠 + n）

RPFM 的 loc TSV 把游戏换行转义成 **两个反斜杠 + `n`**。打开文件必须看见 `\\n`，十六进制是 `5C 5C 6E`。看见单个 `\n`（`5C 6E`）或文件里真的断行，都是错的。

| 落盘形态 | 字节 | 结果 |
|----------|------|------|
| `\\n`（两个 `\` + `n`） | `5C 5C 6E` | ✅ RPFM 导入后游戏渲染成换行 |
| `\n`（一个 `\` + `n`） | `5C 6E` | ❌ 导入后常常变成字面 `\n` 或丢段 |
| 真实 LF / 按回车断行 | `0A` | ❌ 拆坏 TSV 行 |

`text` 列必须保持单行。Write / Edit / Python 里反斜杠会被再转义一层，手数层数必错——**不要靠手写对，写完立刻跑校正脚本**。

```text
python "<本技能目录>/scripts/fix_loc_newlines.py" "<本次改过的 loc TSV 或其所在目录>"
```

脚本会：把真实换行折回同一条记录，并把落盘的单个 `\n` 升级成 `\\n`；已经是 `\\n` 的不动。`--check` 只检查不写盘，有残留则退出码 1。


只对 RPFM 导出的 LOC TSV 使用校正脚本，先 `--check` 或 `--dry-run` 审查，再限定本次修改的文件写入。不要把二进制 .loc 或含普通 DB TSV 的上层目录交给校正脚本。
