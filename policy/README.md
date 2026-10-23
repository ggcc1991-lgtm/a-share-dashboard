# 政策产业观察 · `policy/`

站内路由 `/policy/`。UI 只读本目录 `./snapshot.json`（schema `policy-industry-observe-v1`）。

## 文件

| 路径 | 用途 |
|------|------|
| `snapshot.json` | 页面唯一数据源（钉死同一 `meta.snapshotId`） |
| `index.html` | Bloomberg 终端风密排：brief / 三类热度 / 板块表 / 异动 / 实时24h / 材料 |
| `README.md` | 本说明（给 github助手） |

镜像副本（非站内路径）：`/workspace/policy/snapshot.json` + `SCHEMA.md`。

## 字段要点

- **meta**：`snapshotId` · `asOf` · `fetchedAt`（Asia/Shanghai）· `timezone` · `route=/policy/` · `navLabel=政策产业观察`
- **brief.highlights**：结构化对象 `{title,text,...}`，页面渲染为 `title — text`；勿当纯字符串
- **heat**：`policy` / `marketAttention` / `marketTrading` 各 Top≈20，**不可相加**
- **sectors**：全量板块；`heat.policy|marketAttention|marketTrading` 为标量（来自 `/sectors` 的 `policy_heat` / `market_attention` / `market_trading`，缺省时按 `sector_id` 与 `/sector-heat?view=` 合并）
- **dynamics**：`/sector-dynamics` 异动（`type=anomaly_type`，`score=anomaly_score`）
- **realtime**：默认 `window=24h`（滚动窗，不随日报快照清空）
- **materials.policy / materials.media**：`title` `url` `publishedAt`（`material_date` 或 `first_seen_at`）`summary` `tags` `industry` `channel` `source`
- **feedCompatible.items**：可选同形瘦列表；**默认不合进 /feed**

## 公开 API

- Base：`https://api.mobiusquant.ai/api/gendangzou`（无鉴权可读）
- 钉截面：先 `GET /snapshots/latest`，后续带同一 `snapshot_id`
- 热度：`GET /sector-heat?view=policy|market_attention|market_trading`
- 板块：`GET /sectors?snapshot_id=`
- 异动：`GET /sector-dynamics?snapshot_id=`
- 实时：`GET /realtime?window=24h`
- 材料：`GET /policy-materials` · `GET /media-materials`（按日滚动，数量以 API `pagination.total` 为准）

## 重建注意

- 三信号独立展示，禁止合成总分。
- `layer=market_dynamic` 在部分过滤接口会 422，站内用客户端 tab 过滤。
- 政策材料当日总量可能 <15（API 实有多少写多少）；媒体通常更多。
- 页脚约定：公开 API 截面 · 结论在板块 · 非荐股 · 不合进 /feed。
