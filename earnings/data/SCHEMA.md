# earnings/ 数据结构

## data/earnings.json (schema `earnings-v1`)
- `updated` ISO时间(+08:00) · `consensusSource` · `consensusAsOf`
- `companies[]`: `symbol,name,region,currency`
  - `nextDate` ISO或YYYY-MM-DD(北京时间) | null；`dateStatus` confirmed/estimated/unknown；`dateSource`；`nasdaqText`(美股原文)
  - `consensus` 下个待披露季度：`epsAvg/epsLow/epsHigh/epsAnalysts/epsYearAgo, revAvg/revLow/revHigh/revAnalysts/revGrowth(小数), currency`
  - `lastReported` 最近已披露季度：`quarterEnd, reportDate, epsActual, epsEstimate, epsSurprisePct(小数), revenue, netIncome, revenueYoY(小数), netIncomeYoY(小数)` | null
  - 人工字段(重跑保留)：`guidance`(文本), `note`, `manual{revEstimate, revSource, epsEstimateAlt}`
## data/calendar.json (schema `earnings-calendar-v1`)
- `meetings[]`: `id,name,region(CN/US/EU/JP),start,end,decisionAt(ISO北京),status(done/upcoming/ongoing/scheduled/tbd),expectation,result,verdict,note,sources[{name,url}]`
- `macro[]`: `id,region,name,releaseAt(ISO北京),status(released/upcoming/pending),actual,forecast,previous,diff,verdict,note,impact,source{name,url}`；`id` 以 `ff-` 开头者由脚本自动生成，每次重跑覆盖。
- 任何取不到的值为 null 或 "暂无"，页面统一显示「暂无」。

## earnings-v2 增量字段
- `companies[].sources`: `{nextDate:{name,url,asOf}, consensus:[{name,url,asOf}], lastReported:[{...}]}`，按优先级排列。
- `lastReported` 新增（来自 overrides）：`epsGaap`,`epsGaapBasis`,`epsNonGaap`,`epsNonGaapBasis`,`epsCompareBasis`（epsActual/epsEstimate 的对比口径说明），`oneOff`（一次性项目说明），`adjNetIncome`,`adjNetIncomeYoY`,`netIncomeBasis`,`halfYear{period,revenue,revenueYoY,netIncome,netIncomeYoY,epsGaap,epsGaapBasis}`,`note`。
- `dateStatus`: confirmed（公告/Yahoo 确认）| estimated（算法预估）| unknown。

## v2.1 timeline 字段
- `importance` (1–3)：所有 company / meeting / macro 项都有，3=最重要，用于时间线节点大小。
- 超预期判断沿用 `verdict`/`diff`（宏观）和财报 surprise 字段。
- `surprisePct`（可选）：超预期幅度 %，正=超预期。财报=EPS surprise×100；宏观=(实际-预期)/|预期|×100（数值从文本解析，口径以 verdict 为准）。会议暂不提供。

## Tushare 接入
- `companies[].` 刷新时内部 co 携带 `ashare`（如 `688981.SH`），不写入 JSON。
- `sources` 链可含 `tushare_src`；`_src.name` 形如 `Tushare income 002594.SZ`。
- 宏观项 `source.name` 在 Tushare 补数后追加 ` / Tushare cn_*`。
