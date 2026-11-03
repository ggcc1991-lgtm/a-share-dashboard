# OpenRouter 周度数据 · schema

站内约定路径：`openrouter/data/openrouter.json`  
`schemaVersion`: **`openrouter-weekly-v1`**

只读数据契约（本目录不放 API key）。UI 由「数据追踪UI」负责 `index.html` / 顶栏 / 总览卡。

## 刷新

1. 在 `/workspace/openrouter_replicate` 拉取 rankings-daily + models catalog（见该目录 `scripts/`、`methodology_notes.md`）。
2. 运行 `python3 /workspace/openrouter_replicate/scripts/aggregate.py` 生成 `canvas_data_min.json` / CSV / `weekly_embed.json`。
3. 将结果编译为本文件（或等价脚本复制/整形）→ `data/openrouter.json`。
4. **刷新节奏（跟原数据）**：OpenRouter `rankings-daily` 按 **UTC 日**更新；有新完整日截面后，重跑 replicate 聚合并写回本 JSON（incomplete trailing week 滚动）。headline KPI 仅用完整周（恰好 7 个 UTC 日）。无新日数据则可不推。
5. **禁止**把 `openrouter_api_key.txt` 或任何 Bearer token 写入 `data-dashboard/`。

## 顶层字段

| 字段 | 类型 | 说明 | 空值 |
|------|------|------|------|
| `schemaVersion` | string | 固定 `openrouter-weekly-v1` | 否 |
| `asOf` | string | 数据截止展示时间，Asia/Shanghai 文本（如 `2026-11-03 11:36 Asia/Shanghai`） | 否 |
| `updatedAt` | string | 本 JSON 生成/同步时间；当前与 `asOf` 同口径 | 否 |
| `asOfUtc` | string\|null | UTC ISO（来自 replicate embed） | 可 null |
| `source` | object | 溯源：路径、endpoint、窗口、收入公式摘要 | 否 |
| `providers` | string[] | 厂商图例顺序（11 家含 Other） | 否 |
| `kpis` | object | **最新完整周** headline | 否 |
| `incompleteWeek` | object\|null | 不足 7 日的 trailing 周；不进 KPI | 可无完整周时仍可有 trailing |
| `token` | object | 完整周 token 序列（单位 T） | 否 |
| `revenue` | object | **仅完整周** 拟合流水序列（单位 $M） | 否 |
| `revenueIncompletePoint` | object\|null | 不完整周单点（可选脚注） | 可 null |
| `providersLatest` | object[] | 最新完整周按 token 降序的厂商拆分 | 否 |
| `meta` | object | 周界 / 完整周规则 / UI 提示 | 否 |

## `kpis`（最新完整周）

| 字段 | 单位 | 说明 |
|------|------|------|
| `weekStart` / `weekEnd` | YYYY-MM-DD | Mon–Sun UTC 完整周 |
| `tokens_T` | 万亿 token | 周合计 |
| `tokensWowPct` | % | vs 上一完整周；首周可为历史值已算好 |
| `revenue_M` | 百万 USD | fitted |
| `revenueWowPct` | % | vs 上一完整周 |
| `openTokenSharePct` / `closedTokenSharePct` | % | 开源 / 闭源 token 份额（另有 other，三者不必在本对象展开） |
| `openRevenueSharePct` / `closedRevenueSharePct` | % | 开源 / 闭源收入份额 |

## `token` / `revenue` 序列

公共形状：

- `starts: string[]` — 每周 `week_start`（周一 UTC）
- `labels: string[]` — 稀疏横轴标签（可与 starts 等长，空串表示跳过）
- `series: { [provider]: number[] }` — 与 `providers` / `starts` 对齐
- `totals: number[]`
- `wowPct`（token）或 `wow`（revenue）：周环比 %；revenue 侧历史字段名 `wow`（与 replicate 一致）
- `openSharePct` / `closedSharePct` / `otherSharePct`：份额 %，同长度

单位：

- token：`tokens_trillions`（T）
- revenue：`USD_millions`（$M）；**完整周 only**（incomplete 不进 `revenue.series`）

`null`：`wow`/`wowPct` 在序列第一周或不可比时可为 `null`（revenue incomplete 点的 wow 亦为 null，不进入 complete 数组）。

## `providersLatest[]`

| 字段 | 说明 |
|------|------|
| `provider` | 厂商名 |
| `tokens_T` / `tokenSharePct` | 量与占比 |
| `revenue_M` / `revSharePct` | 拟合流水与占比；分母为完整周合计 |

## `incompleteWeek`

| 字段 | 说明 |
|------|------|
| `weekStart` | trailing 周起始 |
| `nDays` | 已有 UTC 日数（&lt;7） |
| `tokens_T` / `revenue_M` | 累计（非年化） |
| `note` | 固定说明：不进 headline |

## 口径摘要

- Token：rankings-daily `total_tokens` 加总。
- Revenue：`tokens × (0.9×0.5×input + 0.1×output)`（$/token）；`:free`/stealth 等为 0；详见 replicate `methodology_notes.md`。
- 与晨会截图 Y 轴量级可能不同；趋势同向即可。

## UI 消费建议

1. KPI 条读 `kpis.*`。
2. 堆积图 / WoW / 开闭源读 `token` 或 `revenue`；不要把 `incompleteWeek` 混进主序列。
3. 厂商表读 `providersLatest`。
4. 页脚 / tooltip 展示 `asOf` + `source.revenueFormula` 短注。
