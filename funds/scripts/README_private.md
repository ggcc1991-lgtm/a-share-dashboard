# 私募 private.json 再生（funds-private-v2）

源：
- MCP `user-lxwfof MCP` → `get_dataset(name=position)`（subjective / styles4 / zhizeng / text）
- 准确度补：同源站点 `/api/position` 的 accuracy / accuracy_zz（MCP 不含）
- 对照页：https://lxwfof.com/#/position

产出 `sections[]`：
1. `pri_abs` · tabs_abs · 主观私募绝对仓位（A股总仓位/港股/总股票仓位）
2. `pri_style` · tabs_style · 主观私募风格拆分（全部私募 + 四组）
3. `pri_quant` · tabs_quant · 量化私募风格拆分（300/500/1000/2000/A500；默认 500）

`universe: lxwfof_position_pri`；`funds`/`tables` 置空；不写完整公私募 combo。

同步目标：
- `data-dashboard/funds/data/private.json`
- `/workspace/funds/data/private.json`
- `ashd/funds/data/private.json`（若存在）

勿 git push；由 github助手推送。
