# 项目结构说明

## 顶层目录

| 目录 | 用途 |
|------|------|
| `/多语言` | 战锤3原版多语言文件。`localisation__.loc_CN.tsv` 为中文翻译，`/EN` 为英文原文 |
| `/源码` | 战锤3原版脚本、UI、DB文件。所有官方数据在此，用于参考原始表结构和API |
| `/mod` | 战锤3 MOD文件夹，包含所有MOD的子目录 |

## MOD内部目录结构

每个MOD文件夹（如 `难度大修`）的标准结构：

```
mod/<MOD名称>/
├── db/                              # 数据库表覆盖
│   ├── <table_name>/               # 表名目录（与源码db目录同名）
│   │   ├── !!!wyccc_xxx.tsv        # 三级叹号 = 主表/核心表
│   │   ├── !!wyccc_xxx.tsv         # 二级叹号 = 关联表
│   │   ├── wyccc_xxx.tsv           # 无叹号 = 普通数据表
│   │   └── ...
│   └── ...
├── script/
│   └── campaign/
│       ├── mod/                     # 自定义脚本（新建MOD功能放这里）
│       │   └── wyccc_xxx.lua
│       └── <原版脚本名>.lua        # 直接覆盖原版脚本（少用）
├── text/
│   └── db/
│       ├── wyccc_xxx_CN.loc.tsv     # 中文本地化
│       └── en/
│           └── wyccc_xxx_EN.loc.tsv # 英文本地化
└── <备注文件>                       # 如 备注.txt, xlsx等
```

## 已有MOD一览

| MOD | 路径 | 用途 |
|-----|------|------|
| 五行罗盘大修 | `mod/五行罗盘大修/` | 修改震旦罗盘效果 |
| 南皋工坊 | `mod/南皋工坊/` | 炮术学院系统（最复杂） |
| 天廷 | `mod/天廷/` | 震旦天廷/职位置换系统 |
| 抽奖系统 | `mod/抽奖系统/` | 抽装备/英雄/领主 |
| 难度大修 | `mod/难度大修/` | 外交态度、非秩序buff、食人魔合邦 |
| 参考MOD | `mod/参考MOD/` | 空文件夹（预留） |

## 关键路径约定

- Lua自定义脚本：`script/campaign/mod/wyccc_<功能>.lua`
- DB表文件：`db/<table_name>/!!wyccc_<功能>.tsv`
- 本地化文本：`text/db/wyccc_<功能>_CN.loc.tsv` 和 `en/wyccc_<功能>_EN.loc.tsv`
- 所有文件使用 `wyccc_` 前缀
