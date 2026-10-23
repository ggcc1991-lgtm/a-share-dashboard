# 政策产业观察 · `policy/`

站内路由 `/policy/`。UI 只读本目录 `./snapshot.json`（schema **`policy-industry-observe-v1.1`**）。

镜像：`/workspace/policy/`（`rebuild_snapshot.py` · `SCHEMA.md` · 同内容 `snapshot.json` / `index.html`）。

## 文件

| 路径 | 用途 |
|------|------|
| `snapshot.json` | 页面唯一数据源（钉死同一 `meta.snapshotId`） |
| `index.html` | Bloomberg 壳（#000 / #FFA028）：实时/日报双视图 + 扫描散点 + 下钻抽屉 |
| `README.md` | 本说明 |

## UI 对齐（原站 gendangzou 公开结构）

1. **双视图**：顶栏切换「实时动态」/「日报快照」
2. **实时**：6h / 24h / 3d 滚动窗 · 材料流（政策/媒体/即时关注）· 板块信号筛选
3. **日报**：指标条（快照/板块节点/公司关系/政策贡献/行情覆盖/资金样本）· brief 本次发布 · 板块热度总览（三信号 view + layer）
4. **材料**：权威政策 / 权威媒体 / 即时关注
5. **市场扫描**：全部/实时命中/新增信号/多源确认/负向压力 · 热度三榜 · **二维定位**（X=policy heat · Y=market attention · SVG 散点）· 板块明细
6. **快照截面**：layer + 搜索 + 可排序九列动量/热度
7. **关联研究**：预取公司 / ETF · `securities/changes` 上市动态
8. **历史截面**：近 ~15 条只读列表，钉住 latest
9. **下钻抽屉**：heat-series SVG · companies · etfs · evidence（未预取显示说明）
10. **页脚**：非荐股 · 三信号不可相加 · 不合进 /feed

## 字段要点

- **meta**：`snapshotId` · `asOf` · `fetchedAt`(Asia/Shanghai) · trade/status/taxonomy
- **coverage**：指标条 + `raw` API coverage
- **heat / sectors**：三信号独立；`layer=market_dynamic` 客户端过滤（部分 API 422）
- **dynamics**：完整 `explanation` + `linkedSectors`
- **realtime.byWindow**：`6h|24h|3d`
- **drilldown.byId**：预取包；companies/etfs **仅首页**（防 ETF 海量分页）
- **securities.changes**：上市动态

## 公开 API

- Base：`https://api.mobiusquant.ai/api/gendangzou`
- 钉截面：`GET /snapshots/latest` 后带同一 `snapshot_id`
- 热度 / 板块 / 异动 / 实时窗 / 材料 / snapshots 列表 / securities/changes / sector drilldown
- 重建：`python3 -u /workspace/policy/rebuild_snapshot.py`（curl + UA `GrokBot-policy/1.0`）

## 约束

- 三信号不可相加；结论在板块；非荐股；≤719px 可用；不改壳层 nav 以外栏目；勿推 GitHub。
