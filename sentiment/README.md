# A股情绪看板（静态版）

- `index.html`：自包含页面（无外部依赖），运行时 `fetch('./data/history.json')`。需经 HTTP 访问（`file://` 下浏览器会拦截 fetch），可直接放主站任意子目录或 iframe 嵌入。
- `data/history.json`：数据文件，格式同 `market-emotion-dashboard/data/history_export.json`：
  `{ algoVersion, exportedAt, source, days: [{ date, emotionScore, regime(strong|neutral|weak), regimeLabel, suggestedPosition, positionTier, allowOpen, hs300Close, hs300ChangePct, volumeRatio, gates[{key,label,current,threshold,passed}], factors[{id,name,score,weight,contribution,rawValue}] }], failed: [] }`

## 更新数据
1. 在 `market-emotion-dashboard` 启动后端（`DATA_PROVIDER=eastmoney npm run start:server`，端口 4174）。
2. 每个交易日收盘后（建议 15:30 北京时间后）对新日期调用 `GET /api/market/emotion?date=YYYYMMDD`，按上面字段追加到 `days`（按 date 去重）；或重跑采集脚本生成 `history_export.json` 后复制：
   `cp market-emotion-dashboard/data/history_export.json data-dashboard/sentiment/data/history.json`
3. 历史回补更早日期：先以 `SINA_KLINE_DATALEN=<条数>` 预热日线缓存，再逐日调用接口。
4. 成交额统一为“亿元”；页面无需改动，刷新即生效（注意 CDN 缓存 history.json）。

数据源：新浪/腾讯（替代 Tushare），历史日个股成交额为 0，量能走指数成交额；算法 `market-emotion-eod-v3`。
