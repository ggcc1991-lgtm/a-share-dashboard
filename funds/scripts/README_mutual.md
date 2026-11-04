# 公募 mutual.json 再生（funds-mutual-v2）

源：
- 主数据：lxwfof `/api/position/pub`（combo / pub_abs / pub_style / pub_quant + accuracy）
- ETF：`/api/position/etf`
- MCP `user-lxwfof MCP` → `get_dataset(name=position)` **仅私募**，公募四块不在此；可另存 `position-raw.json` 备查
- 对照页：https://lxwfof.com/#/position

产出 `sections[]`：
1. `combo` · 公私募全风格合计（chips 含主动/量化公募与主动/量化私募；私募侧详情不在本文件重复）
2. `pub_abs` · 主观公募绝对仓位
3. `pub_style` · 主观公募风格拆分
4. `pub_quant` · 量化公募风格拆分
5. `etf` · ETF 持仓拆分（可选）

`universe: lxwfof_position_pub`；`funds` 置空。

## 顶层 `note`（页脚）规则

模板（按实际 asOf 填）：

> 主数据 /api/position/pub（asOf=\<pub_asOf\>），ETF 来自 /api/position/etf；MCP dataset \`position\` 仅含私募侧（asOf=\<mcp_asOf\>），已另存 position-raw.json。部分信息参考自lxwfof MCP。

**禁止**再写入「产品自助拆分未入库。」（用户要求页脚不出现）。产品自助 / ppos / pubpri_excess 只写在 `source.gaps`。

同步目标：
- `data-dashboard/funds/data/mutual.json`
- `/workspace/funds/data/mutual.json`
- `ashd/funds/data/mutual.json`（GitHub Pages 源）

推送约定：改完数据后由本 bot 或 github助手推 `ashd`；重生截面务必遵守上述 note 规则。
