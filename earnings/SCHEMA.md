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

## v2.7 AI 上下游
- 新增数据中心电力/散热、AI 服务器与 ODM、网络、AI 互联芯片、光模块，以及企业软件/云安全/电商等下游应用。
- 跳过已有 AMD/NVDA；未上市 CoreWeave 跳过；施耐德用 `SU.PA`；光模块取 `COHR`（未并入 LITE）。importance：上游/芯片 3，应用 2。

## v2.8 A股全产业链
- 新增半导体设备/材料、AI芯片设计、先进封装与 PCB/CCL、光模块、算力服务器、液冷、办公/语音软件等 A 股卡位龙头。
- **Yahoo 沪市代码用 `.SS`（`.SH` 常 404）**；深市 `.SZ`。本批未挂 `ashare`，避免触发 Tushare IP 配额。
- 多数 Yahoo `earningsTimestamp` 仍停在 2025 年年报季 → `nextDate` 记 null/`unknown`（不编造）；consensus / lastReported 仍有值。
- 跳过已有中芯 `0981.HK`、比亚迪 `1211.HK`；精简未纳入：立昂微、龙芯、卓胜微、通富、兴森、飞荣达、曙光、科华、恒生等。

## v2.9 Wind / 同花顺 MCP（2026-10-27）
- 适配器：`scripts/sources/wind_src.py`、`ths_src.py`；缓存：`data/wind_cache.json`、`data/ths_cache.json`（Python 不直连 MCP，由 agent CallDynamicTool 小批量写入）。
- **Wind 能补**：`get_stock_events`→A 股预约/实际披露日 → `nextDate`（`dateStatus=confirmed`）；`get_stock_fundamentals`→当年一致预期 EPS/营收/净利 → `consensus.ashareAnnual`（不覆盖 Yahoo 季度 `eps*/rev*`）；`user-wind-econ`→宏观一致预期 forecast（如 `cn-cpi-2026-10`）。
- **Wind 暂不能**：未预约的下一报告期（已披露三季报、年报预约未出）→ `nextDate` 仍 null/「暂无」；单季一致预期/surprise 无稳定字段。
- **同花顺能**：财务三表/指标/估值/行情（可填 `ashareYtd` 累计口径，需写入 ths_cache）。
- **同花顺不能**：披露日历、卖方一致预期（MCP 无对应工具）→ `next_date`/`consensus` 恒空。
- `sources.json`：`next_date` 含 `wind_src`（overrides 之后）；`consensus` 含 `wind_src`（写 ashareAnnual）；`macro_actual` 含 `wind_src`。
- 旧 `wind.py` 占位 `available=False`，请用 `wind_src`。
