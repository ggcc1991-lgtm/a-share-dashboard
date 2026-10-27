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
