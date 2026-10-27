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

## v2.2 信息流摘录（feedExtracts）
- `companies[].feedExtracts[]`（可选）：从 `/workspace/data-dashboard/data/feed.json` 抽取的机构提到的财报数字，供详情展示；**不含 url**（不挂研报/条目链接）。
  - `sourceName, publishedAt, excerpt, fields{...}, agreeWith[]?, conflictWith[]?`
  - `fields` 仅含文中明确写出的数字（如 `revConsensusUsd/revConsensusYoY/revConsensusText`、分部 `cloudRevConsensus*`、`searchYoY`、`youtubeAdsYoY`、`epsActual/epsEstimate` 等）。
- 合并规则：与面板 `consensus/lastReported` 交叉比对；相对误差<2% 视为一致，在 `note` 标注「信息流·机构名·日期」；冲突则 `note` 写两边数值，**不覆盖** overrides / 已有一致预期 / 公司公告确认值。分部数字只进 `note`+`feedExtracts`，不写入公司级 `consensus`。
- 脚本：`scripts/extract_feed_earnings.py`（条目≤120 用全部，否则近 14 天）；刷新时 `feedExtracts/note/guidance/manual` 会被保留。

## v2.3 A股 Tushare 子字段（2026-10-27）
- `consensus.ashareAnnual`（仅 0981.HK/1211.HK，A股代码映射）：`{fiscalYear, basis:"年度预测（非季度）", eps{avg,high,low,n}, netProfit{...}, revenue{...}（元）, orgs, window, source:"Tushare report_rc <code>", asOf(最新研报日), unit, stale?}`。来自 report_rc `quarter=<当年>Q4`，同一机构取最新一篇；**不覆盖** Yahoo 季度 `eps*/rev*`。拉取失败时保留上次值并标 `stale:true`。
- `lastReported.ashareYtd`：Tushare income（report_type=1，年初至报告期末累计，CNY）+ fina_indicator 同比；只查 20260930/20260630，且仅当报告期**晚于**现有 `lastReported.quarterEnd` 才写入；不改季度/港股口径字段。

## v2.4 calendar.meetings.category
- 可选字段 `category`；`"us-election"` = 美国2026中期选举时间线（region=US）。日期仅取有来源者，州认证日为按州法推算；result/verdict 暂留空。前端 #mf 筛选「美国大选」，时间线节点蓝色描边。

## v2.5 地区扩展（TW/KR/JP/EU）
- `companies[].region` 现覆盖：US / CN / TW / KR / JP / EU。
- 2026-10-27 新增台/韩/日/欧半导体与科技龙头（现股优先；台积电保留 ADR `TSM` + 现股 `2330.TW`；索尼用 ADR `SONY`，东京现股 `6758.T` 见 note）。
- `importance`：半导体龙头 3，其余 2。日期/一致预期来自 Yahoo；已过期的 nextDate 记 null/`unknown`（页面「暂无」），不编造。

## v2.6 细分龙头扩展
- 在 TW/KR/JP/EU/US 补光学、硅片、电源、驱动IC、动力电池、生物CDMO、互联网、FA传感、测分/切割/检测设备、电子材料、被动元件、功率半导体、ALD/先进封装设备、支付、代谢药、前道设备与模拟芯片等**替代性低**的细分龙头。
- 代码勘误：环球晶 `6488.TWO`（非 `.TW`）；ASM International `ASM.AS`（`ASMI.AS` 404）；诺和诺德用 ADR `NVO`。`AVGO` 已在池，跳过。
