## Pack 封面文件命名与位置

- 源封面仍以 `mod/<MOD名>/cover.png` 作为唯一编辑入口；生成或修改美术后先更新源文件；MOD封面图尺寸必须是500*500
- 每次交付或更新 MOD 封面时，必须将源 `cover.png` 复制到该 MOD 已映射源 Pack 的同一目录；副本文件名必须与 Pack 完全同名，仅把扩展名从 `.pack` 改为 `.png`。例如 `wyccc_ai_overhaul.pack` 必须配套 `wyccc_ai_overhaul.png`。
- 该同名 PNG 是发行目录的外部封面文件，不能用 Pack 内部的通用 `cover.png` 替代；复制后检查尺寸、PNG 格式和文件名。
- 不要把封面改名为与 MOD 文件夹不同的随机名称，也不要只在源目录保留封面而遗漏 `data` 目录中的同名 PNG。
