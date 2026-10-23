# GC的数据监控中心（第一版）

Bloomberg 终端风格的静态站：总览 + ETF + 信息流 + 抄底红线 + 政策产业。

## 结构

```
/
  index.html               # 总览
  assets/theme.css         # 共用主题（纯黑底、橙色 chrome、直角、密表）
  assets/bottom-skin.css   # 抄底页覆盖：纯黑底、直角、去掉霓虹阴影
  assets/shell.js          # 导航、格式化、数字滚动
  etf/index.html
  feed/index.html
  bottom/index.html
  policy/index.html        # 政策产业观察 v1 密排桌面
  policy/snapshot.json     # schema policy-industry-observe-v1（/policy/ 唯一数据源）
  policy/README.md
  data/
    etf.json               # 来自 etf 追踪 data.json
    feed.json              # 聚合订阅增量（当前为字段样例）
    bottom.json            # 抄底 latest 快照
```

## 主题令牌

- 背景 `--bg: #000000` / 表面 `#0a0a0a` / 边框 `#2b2b2b`
- 终端 chrome `--bb` / `--accent` / `--cy`：`#ffa028`（只用于导航、分区标题、按钮，不表示涨跌）
- 涨红 `--pos: #ef5350` / 跌绿 `--neg: #26a69a`（A股语义，不改成西方绿涨）
- 直角 `--r: 0` · 密表 · 总览为三列（抄底红线 7/12 头 + 12 行指标 / 最新要闻 / 政策产业 + ETF）加顶部行情条
- `/bottom/` 在共用主题之外再链 `assets/bottom-skin.css`

## 数据对接

| 模块 | 文件 | 说明 |
|------|------|------|
| ETF | `data/etf.json` | 字段保持 `etfs/dates/series/futures/baseline` |
| 信息流 | `data/feed.json` | `{ updated, items:[{source,sourceName,title,url,publishedAt,summary}] }` |
| 抄底 | `data/bottom.json` | `{ triggered_count, total, indicators[], generated_at }` |
| 政策产业 | `policy/snapshot.json` | schema `policy-industry-observe-v1`。`/policy/` 只读该文件。总览第三列只用 `brief` 做短预告，不读 `data/policy.json` |

本地预览：`python3 -m http.server 8080`（需 http，勿用 file://）

部署：整目录在 GitHub Pages 根目录。站内链接与资源都是相对路径，项目站点前缀 `/a-share-dashboard/` 下可直接使用。

## 本仓库

Pages 源：`main` 分支 `/`（与原先一致）。

| 页面 | 路径 |
|------|------|
| 总览 | `/`（导航：总览 / ETF / 信息流 / 抄底 / 政策产业） |
| ETF | `/etf/` |
| 信息流 | `/feed/` |
| 抄底 | `/bottom/` |
| 政策产业 | `/policy/` |
| 原完整抄底面板 | `/legacy/` |

原先单独发布的抄底面板是仓库根目录的 `index.html`，与总览冲突，已原样挪到 `legacy/index.html`。`/bottom/` 的「原完整面板」指向该页。后续若仍有脚本把完整面板刷回根目录 `index.html`，会盖掉总览，应改为写入 `legacy/index.html`。
