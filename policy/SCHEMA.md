# policy-industry-observe-v1.1

路径：站内 `data-dashboard/policy/snapshot.json`（路由 `/policy/`）；镜像 `/workspace/policy/snapshot.json`。

## 顶层
- `schema` 固定 `policy-industry-observe-v1.1`
- `meta` — `snapshotId` / `asOf` / `fetchedAt`(Asia/Shanghai) / `marketTradeDate` / `marketStatus` / `taxonomyVersion` / `publishedAt` / `dataStatus` / `quality`
- `brief` — 日报头条 + 结构化 `highlights[{title,text,...}]`
- `coverage` — 指标条：`sectorCount` / `anomalyCount` / `etfCount` / `companyRelations` / `taxonomyNodes` + `raw`（API coverage）
- `heat` — `policy` / `marketAttention` / `marketTrading` 各 Top≈20；**三信号不可相加**
- `sectors[]` — 全量；含 `layer` / `status` / `parent` / `heat{}` / `momentum{}`（标量）
- `dynamics[]` — 异动；含完整 `explanation` + `linkedSectors[]`
- `realtime` — `defaultWindow=24h`；`byWindow.{6h,24h,3d}` 各含 `window/summary/sectors/materials`；顶层兼容 24h 字段
- `materials` — `policy` / `media` 全量分页 + `policyTotal` / `mediaTotal`；即时关注从 realtime materials `channel=market_attention` 汇聚
- `snapshots` — 近约 15 条只读列表；`pinnedId` 钉住 latest（不假切换历史整包）
- `securities` — `security.lifecycle`：`/securities/changes` → `changes[]`（上市动态）
- `drilldown` — 预取热度 Top + 异动涉及板块；`byId[sectorId]` 含 detail / companies / etfs / evidence / heatSeries
- `feedCompatible.items` — 可选同形瘦列表；**默认不合进 /feed**

## 材料条
`title` `url` `publishedAt` `summary` `tags[]` `industry` `channel`(`policy|media|market_attention`) `source`

## UI 模块（对齐原站公开结构）
1. 实时动态 vs 日报快照双视图
2. 实时：材料流 + 板块信号；日报：指标条 + 板块热度总览 + 本次发布
3. 材料：权威政策 / 权威媒体 / 即时关注
4. 市场扫描：筛选 + 热度三榜 + 二维定位（policy × marketAttention 散点）+ 板块明细
5. 快照截面：layer + 搜索 + 可排序总表
6. 关联研究：公司 / ETF / 上市动态
7. 页脚非荐股声明
