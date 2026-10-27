# 财报与会议 — 刷新方法
```
python3 -m venv /workspace/venv-earn && /workspace/venv-earn/bin/pip install yfinance
/workspace/venv-earn/bin/python earnings/scripts/refresh_earnings.py   # 日期+一致预期+最近财报 (Yahoo + Nasdaq)
python3 earnings/scripts/refresh_macro.py                              # 合并 ForexFactory 本周中美日历(预期/前值)
```
人工维护（无免费API）：`calendar.json` 中已公布宏观数据的实际值/对比、会议结果与市场预期；`earnings.json` 中 guidance/note/manual/feedExtracts（信息流摘录无 url）。
发布后用 Playwright 检查 1280/375/414 宽度。

## 数据源适配层（2026-10-27 起）

```
scripts/
  refresh_earnings.py   # 编排：按 sources.json 的优先级链逐字段合并，记录 sources{nextDate, consensus[], lastReported[]}
  sources.json          # 字段级优先级配置
  sources/
    base.py             # Adapter 接口：next_date / consensus / last_reported，stamp() 生成 {name,url,asOf}
    overrides.py        # 读 data/overrides.json（人工核对的公告/IR 数据，最高优先级）
    hkex.py             # 港交所披露易：自动找“董事会会议通告”并解析会议日期 → 已确认日期（需 pdftotext）
    yahoo.py            # yfinance：日期、一致预期（港股用 .HK 代码）、利润表
    nasdaq.py           # Nasdaq/Zacks 日期（文本含 expected*/estimated 时标为“预估”）
    fmp.py finnhub.py wind.py   # 付费源占位，读取 FMP_API_KEY / FINNHUB_API_KEY / WIND_API_KEY
```

**合并规则**：链上靠前的源先写入；后面的源只补“尚不存在”的字段。高优先级源显式写 `null` 的字段不会被低优先级源覆盖（用来防止把 Yahoo 的不同口径数字混入公告数据）。不同季度（quarterEnd 不同）的数据不混合。日期取链上第一个给出“未来日期”的源。

**换成付费 API**：
1. 在 `sources/fmp.py`（或 finnhub/wind）里实现需要的方法，返回字段名同 SCHEMA.md，并附 `"_src": stamp("FMP", url)`。
2. `export FMP_API_KEY=...`（未设置时该适配器自动跳过）。
3. 在 `sources.json` 中把 `"fmp"` 放到对应字段链里，例如 `"consensus": ["overrides","fmp","yahoo"]`。页面无需改动。

**人工核对数据**：`data/overrides.json`，每家公司可写 nextDate/dateStatus/dateSource、lastReported（含 epsGaap/epsNonGaap 及口径、oneOff 一次性项目、adjNetIncome、halfYear、source{name,url,asOf}）、guidance、note。新季度公告发布后需更新或删除对应条目，否则旧季度数据会被保留（不同季度不会与 Yahoo 混合，但 Yahoo 新季度会被挡掉）——更新时把 quarterEnd 改成新季度。

免费源的限制：东方财富/新浪/雪球的一致预期多为年度口径且无稳定公开接口，当前未接入；季度一致预期仅来自 Yahoo。

## Tushare（A 股 + 国内宏观，2026-10-27）

- 适配器：`scripts/sources/tushare_src.py`，通过 `/workspace/tushare/client.py` 的 `get_pro()`（datahubco 镜像）与 `fallback.py` 粘性降级。
- 映射：中芯 `0981.HK` → `688981.SH`；比亚迪 `1211.HK` → `002594.SZ`。其余公司无 `ashare` 字段，适配器直接跳过（不调用港股/美股接口）。
- 财报字段：`disclosure_date`→nextDate；`income`/`express`/`fina_indicator`/`forecast`→lastReported；`report_rc`→consensus。
- 宏观：`refresh_macro.py` 在 ForexFactory 合并后，用 `cn_cpi` / `cn_ppi` / `cn_pmi` / `cn_m` / `cn_gdp` 补 CN 项的 `actual`/`previous`；**不覆盖已有 forecast**；保留 `importance`、`surprisePct`（缺则在 actual+forecast 均为数值时重算）。
- `sources.json` 优先级：`overrides > tushare_src > hkex > yahoo > nasdaq`。
- 失败时（含 `api_or_ip_policy` 多 IP、积分/权限不足）打印 `[tushare] … → sticky backup` 并继续用下游源，不中断刷新。

## 信息流 → 面板（机构数字摘录，2026-10-27）

```
/workspace/venv-earn/bin/python earnings/scripts/extract_feed_earnings.py
# --dry-run 只汇报；--feed / --earn 可改路径
```

从 `data-dashboard/data/feed.json` 按 20 家公司别名 + 财报关键词筛条目，只抽取 title/summary 里**明确写出**的数字（总营收共识、分部一致预期、EPS 实际/预期等），写入对应公司的 `note` 与可选 `feedExtracts`（**不写 url、不挂研报链接**）。与 Yahoo/overrides 一致则标注「信息流·机构名·日期」；冲突只记 note，不覆盖面板。`refresh_earnings.py` 会保留 `feedExtracts`。

### Tushare 字段修正（按 earnings_field_samples.json）
- `cn_gdp` 参数改为 `start_q="2024Q1", end_q="2026Q4"`（YYYYQn）。
- `disclosure_date` 加 `start_date` 窗口；`income`/`fina_indicator` 按 `period=20260930→20260630` 逐期查询（旧 2025 报告期不写入）。
- `report_rc`：`np`/`op_rt` 单位万元；`quarter=2026Q4` 即当年年度预测 → `consensus.ashareAnnual`。修正前旧逻辑会把 2028Q4 年度 EPS 混入季度 `epsAvg`（中芯曾显示 1.607 CNY），已移除。
- Tushare A股实际值不再进 `last_reported` 链，改写 `lastReported.ashareYtd`。IP 紧张：每次刷新只跑一轮，遇 `api_or_ip_policy` 立即粘性降级，不重试。

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
