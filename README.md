# GC的数据监控中心（第一版）

统一深色主题的静态站：总览 + ETF + 信息聚合 + 抄底红线。

## 结构

```
/
  index.html               # 总览
  assets/theme.css         # 共用主题（扁平原文、4px 圆角、发丝边框）
  assets/bottom-skin.css   # 抄底页覆盖：压平旧面板圆角与霓虹阴影
  assets/shell.js          # 导航与格式化
  etf/index.html
  feed/index.html
  bottom/index.html
  data/
    etf.json               # 来自 etf 追踪 data.json
    feed.json              # 聚合订阅增量（当前为字段样例）
    bottom.json            # 抄底 latest 快照
```

## 主题令牌

- 背景 `#0a0a0b` / 表面 `#111113` / 卡片 `#121214` / 边框 `#2a2a2e`（1px hairline）
- 涨红 `#e85d5d` / 跌绿 `#3d9a6a` / 琥珀 `#d4a017` / 蓝灰 `#6b8cae`
- 字体 PingFang SC · 圆角 4px · 无霓虹光晕
- `/bottom/` 在共用主题之外再链 `assets/bottom-skin.css`

## 数据对接

| 模块 | 文件 | 说明 |
|------|------|------|
| ETF | `data/etf.json` | 字段保持 `etfs/dates/series/futures/baseline` |
| 信息流 | `data/feed.json` | `{ updated, items:[{source,sourceName,title,url,publishedAt,summary}] }` |
| 抄底 | `data/bottom.json` | `{ triggered_count, total, indicators[], generated_at }` |

本地预览：`python3 -m http.server 8080`（需 http，勿用 file://）

部署：整目录在 GitHub Pages 根目录。站内链接与资源都是相对路径，项目站点前缀 `/a-share-dashboard/` 下可直接使用。

## 本仓库

Pages 源：`main` 分支 `/`（与原先一致）。

| 页面 | 路径 |
|------|------|
| 总览 | `/` |
| ETF 追踪 | `/etf/` |
| 信息聚合 | `/feed/` |
| 抄底红线 | `/bottom/` |
| 原完整抄底面板 | `/legacy/` |

原先单独发布的抄底面板是仓库根目录的 `index.html`，与总览冲突，已原样挪到 `legacy/index.html`。`/bottom/` 的「原完整面板」指向该页。后续若仍有脚本把完整面板刷回根目录 `index.html`，会盖掉总览，应改为写入 `legacy/index.html`。
