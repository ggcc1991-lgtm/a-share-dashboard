# 财报与会议 — 刷新方法
```
python3 -m venv /workspace/venv-earn && /workspace/venv-earn/bin/pip install yfinance
/workspace/venv-earn/bin/python earnings/scripts/refresh_earnings.py   # 日期+一致预期+最近财报 (Yahoo + Nasdaq)
python3 earnings/scripts/refresh_macro.py                              # 合并 ForexFactory 本周中美日历(预期/前值)
```
人工维护（无免费API）：`calendar.json` 中已公布宏观数据的实际值/对比、会议结果与市场预期；`earnings.json` 中 guidance/note/manual。
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
