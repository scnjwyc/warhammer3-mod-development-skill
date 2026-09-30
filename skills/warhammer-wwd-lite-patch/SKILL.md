---
name: warhammer-wwd-lite-patch
description: "与龙同行本体更新后同步精简补丁，保留 MCT 剧情开关、人物/神器/兵种解锁、关剧情合邦与补丁独有数值。"
---

# 与龙同行精简补丁同步

本体更新后，精简补丁不是重做，是 **rebase overlay**：以新本体同名文件为底，把补丁 delta 再打上去。TSV/Lua 规范见 [开发技能](../warhammer-mod-development/SKILL.md)，导入与诊断见 [Pack 工作流](../warhammer-mod-development/references/pack-workflow.md)。Agent 不启动游戏。

表中的 id 和路径来自作者项目；迁移时用目标项目已确认映射定位两份实际源，不能把示例路径当成写入授权。

## 两份源

| 角色 | pack_map id | 源目录 | 源 Pack |
|------|-------------|--------|---------|
| 本体（只读基准） | `第三方MOD/与龙同行` | `mod/第三方MOD/与龙同行` | workshop `DEER24Cathay.pack` |
| 精简补丁（唯一写入） | `已完工/与龙同行精简补丁` | `mod/已完工/与龙同行精简补丁` | 游戏 `data/!!DEER24Cathay_lite.pack` |

本体 Pack 只用来对照，禁止导入、复制或保存回本体。写入前 `list_open_packs` 确认 `pack_key` 指向 lite 映射路径。

## 补丁身份

精简补丁覆盖同名脚本/表，不替换整个本体 Pack。核心 delta：

- MCT 模组 `wwd_story`，选项 `wwd_enable_story`，**默认关**。
- 关剧情：跳过剧情监听与开局脚本；人物/神器/神兽解锁仍要发生。
- 开剧情：跑完整本体剧情，解锁改回本体自己的时机。
- 兵种强化、去友伤、适度扩编是补丁自有数值，不跟本体回退。

`wwd_is_story_enabled()` 只读上述 MCT 键，缺 MCT 时返回 `false`。

## 同步步骤

### 1. 确认本体已更新

完成条件：能指出「要不要动补丁」的证据，而不是感觉。

对照这三项，任一为真就进入步骤 2：

- workshop `DEER24Cathay.pack` 的修改时间新于 `!!DEER24Cathay_lite.pack`
- `git status` / `git diff` 显示 `mod/第三方MOD/与龙同行` 的脚本或补丁会覆盖的表有改动
- 本体源目录出现补丁尚未覆盖的**新** `script/campaign/mod/*.lua`

### 2. 列出覆盖集与本体新增

完成条件：覆盖集每个文件都有分类标签；每个本体新增战役脚本都有「要不要 overlay」结论。

覆盖集 = 精简补丁源目录里实际存在的相对路径（以当前目录为准，不要背清单）。再扫本体 `script/campaign/mod/`，找出补丁没有的新文件。

### 3. 分类后再改

对覆盖集每个文件贴且只贴一个标签：

| 标签 | 何时 | 做法 |
|------|------|------|
| **rebase** | 本体改了剧情/开局脚本，补丁只是开关包装 | 新本体为底，再打开关 delta |
| **story-off** | 关剧情后，本体新逻辑会永久锁死玩家内容 | overlay 同名文件，关剧情走放行，开剧情保持本体 |
| **keep-patch** | 补丁自有数值或关剧情生成逻辑，本体这次没改或改的是补丁要盖住的值 | 不拿本体覆盖 |
| **keep-base** | 补丁未覆盖，且关剧情无副作用 | 不写入补丁，让本体 Pack 生效 |

禁止：把新本体 `land_units` / `wwd_ror_units.lua` / `wwd_units_to_pools.lua` 整文件拷进补丁。那些是强化与扩编。

当前分类（本体再改时重判，不盲抄）：

- **rebase**：`script/campaign/mod/wwd_story.lua`
- **story-off**：`script/campaign/mod/wwd_no_cathay_confederation.lua`（关剧情允许玩家合邦全部存活震旦；AI 互合仍禁；固定外交限制始终保留）
- **keep-patch**：`z_wwd_lord_spwan.lua`、`wwd_units_unlock.lua`、`!deer_wei_jin_captured.lua`、`wwd_ror_units.lua`、`wwd_units_to_pools.lua`、补丁 `db/land_units_tables` 与扩编表
- **keep-base**：`wwd_feats_ui.lua`、战斗 `shengqi_*.lua`、本体 DB/loc 文本（补丁未覆盖）

### 4. rebase `wwd_story.lua`

完成条件：

- `luac -p` 通过
- `wwd_story()` 函数体内不再注册神器/神兽任务监听器
- 文件后部有 MCT 包装：`wwd_artifacts_and_beasts()` 与关剧情角色任务**始终**注册；`wwd_story()` 与 `first_tick_callback_new` 开局脚本受开关控制
- 开局脚本正文来自**新本体**（不要把旧补丁开局粘回去）

做法：

1. 读新本体 `wwd_story.lua` 全文结构：`local function wwd_story()`、`cm:add_first_tick_callback(function() wwd_story() end)`、`cm:add_first_tick_callback_new`。
2. 把 `----------------------神器-------------------` 到 `---------------------神器战斗-----------------` 之前的块从 `wwd_story()` 里剪掉，留一句「已移到 `wwd_artifacts_and_beasts()`」。神器**战斗**任务留在剧情函数内。
3. 把上一版补丁里 `-- MCT剧情开关` 到 `first_tick_callback_new` 之前的包装函数整段接在 `wwd_story()` 的 `end` 之后，替换本体那行裸 `add_first_tick_callback`。
4. 在新本体的 `first_tick_callback_new` 函数体开头插入开关：关则 `return`，开则继续新本体开局。
5. 抽出的神器/神兽函数不能引用 `wwd_story()` 的 local。文化用 `"wh3_main_cth_cathay"`；玄武弃城转交用 `cm:get_faction("wh3_main_cth_imperial_wardens")` 与 `"wh3_dlc20_chs_vilitch"`，并做 null 检查。

关剧情角色一阶段任务（仅开关关闭时，第 30 回合、限人类震旦）仍是：

```
mission_wwd_yiqu_wh3_1
mission_wwd_cth_yawei_wh3_1
mission_wwd_zhouyu_mission_1
mission_wwd_guojin_wh3_1
mission_wwd_meihouwang_wh3_1
mission_wwd_mike_wh3_1
```

本体若新增同类「关剧情会丢」的人物/兵种任务，补进这张表，不要靠剧情事件发放。

### 5. 处理本体新增的战役脚本

完成条件：每个新 `script/campaign/mod/*.lua` 都有结论；若关剧情会锁玩家内容，补丁源目录已有同名 overlay。

典型：`wwd_no_cathay_confederation.lua` 先禁全部震旦合邦，再靠影响力 bundle 与剧情 `saved_value` 解锁。关剧情时开局脚本不发 `wwd_ll_power_up_Z`、剧情两难也不跑，天廷/长垣会永久合不上。overlay 必须在 `disable` 之后对玩家重新 `force_diplomacy(..., true, true)` 全部存活未合邦震旦。

### 6. 验收并导入 lite Pack

完成条件：

- 改过的 Lua 全部 `luac -p` 通过
- 只把**本次改动路径**导入映射的 `!!DEER24Cathay_lite.pack` 并保存
- `open_pack_info` 的路径集合 = 原集合，或仅增加有意 overlay 的新文件；无裸 `.tsv`、无本体 Pack 路径
- `diagnostics_check` 的 Error 为 0（普通 Warning 单独记录；依赖缓存缺失时补建缓存后再判断引用诊断）

导入按共用 Pack 工作流使用 RPFM MCP。Lua 走 `add_packed_files`，不要当 TSV 导。
