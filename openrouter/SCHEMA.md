# OpenRouter 周度数据 · schema

站内约定路径：`openrouter/data/openrouter.json`  
`schemaVersion`: **`openrouter-weekly-v2.1`**（相对 v2 增加 `gpuRentalIndex`；**原有** `kpis` / `token` / `revenue` / `providersLatest` 与 v2 附加截面口径不变）

只读数据契约（本目录不放 API key）。UI 由「数据追踪UI」负责 `index.html` / 顶栏 / 总览卡。

## 刷新

1. 在 `/workspace/openrouter_replicate` 拉取 `rankings-daily` + models catalog（见该目录 `scripts/`、`methodology_notes.md`）。
2. 运行 `python3 /workspace/openrouter_replicate/scripts/aggregate.py` 生成 `canvas_data_min.json` / CSV / `weekly_embed.json`（Token/Revenue 周序列）。
3. 将 Token/Revenue 结果写入本 JSON（或保留现有 `kpis`/`token`/`revenue`），再运行：
   `python3 /workspace/openrouter_replicate/scripts/enrich_dashboard.py`  
   拉取附加 Data API 截面并写回 `data/openrouter.json`（schema → v2）。
3b. GPU 租赁价格指数：源文件更新后运行
   `python3 /workspace/openrouter_replicate/scripts/sync_gpu_rental_index.py`（→ v2.1，仅增/刷 `gpuRentalIndex`）。
4. **刷新节奏（跟原数据）**：OpenRouter `rankings-daily` 按 **UTC 日**更新；有新完整日截面后，重跑 replicate 聚合并写回本 JSON（incomplete trailing week 滚动）。headline KPI 仅用完整周（恰好 7 个 UTC 日）。无新日数据则可不推。
5. 附加截面刷新建议：
   - `appsWeekly` / `contextMix` / `programmingShare`：对齐最新 **完整 Mon–Sun UTC 周**（与 `kpis.weekStart/weekEnd` 一致）。
   - `taskMix7d`：trailing **7d** 快照（采样；不一定对齐完整周）。
   - `sessionCost`：官方约 **周更**；窗口见 `meta.window_days` / `window_end_date`。
   - `catalogDerived`：随 `/models` catalog 快照更新。
   - `gpuRentalIndex`：镜像 `/workspace/silicon_gpu_index/gpu_rental_index_latest.json`（研究方法学委 / Silicon Data）；跑 `python3 /workspace/openrouter_replicate/scripts/sync_gpu_rental_index.py`。
6. 速率限制：Data API **30 rpm / 500 req/day/account**；enrich 脚本默认请求间隔 ~2.2s。
7. **禁止**把 `openrouter_api_key.txt` 或任何 Bearer token 写入 `data-dashboard/`。

## 溯源 / 许可

- 统一引用：`Source: OpenRouter … as of {meta.as_of}`（各截面 `citation` 字段已带）。
- Data API 聚合数据：**CC BY 4.0**；再发布时需署名 OpenRouter。
- 本 JSON `source.citation` / `source.license` / `source.endpoints` 列出所用 endpoint。

## 顶层字段

| 字段 | 类型 | 说明 | 空值 |
|------|------|------|------|
| `schemaVersion` | string | 固定 `openrouter-weekly-v2.1` | 否 |
| `asOf` | string | 数据截止展示时间，Asia/Shanghai 文本 | 否 |
| `updatedAt` | string | 本 JSON 生成/同步时间 | 否 |
| `asOfUtc` | string\|null | UTC ISO | 可 null |
| `source` | object | 溯源：OpenRouter 引用、endpoint 列表、收入公式摘要 | 否 |
| `providers` | string[] | 厂商图例顺序（11 家含 Other） | 否 |
| `kpis` | object | **最新完整周** headline（Token/Revenue） | 否 |
| `incompleteWeek` | object\|null | 不足 7 日的 trailing 周；不进 KPI | 可 |
| `token` | object | 完整周 token 序列（单位 T） | 否 |
| `revenue` | object | **仅完整周** 拟合流水序列（单位 $M） | 否 |
| `revenueIncompletePoint` | object\|null | 不完整周单点 | 可 null |
| `providersLatest` | object[] | 最新完整周按 token 降序的厂商拆分 | 否 |
| `meta` | object | 周界 / 完整周规则 / UI 提示 / additiveSections | 否 |
| `appsWeekly` | object\|null | App 排行（完整周） | 失败时可 null |
| `contextMix` | object\|null | 上下文长度桶份额（完整周） | 失败时可 null |
| `taskMix7d` | object\|null | 任务分类 7d 采样快照 | 失败时可 null |
| `programmingShare` | object\|null | programming 语言类型厂商份额 vs 全站 | 失败时可 null |
| `sessionCost` | object\|null | 已发布 harness 会话成本中位数 | 失败时可 null |
| `catalogDerived` | object\|null | `/models` 轻量派生指标 | 失败时可 null |
| `gpuRentalIndex` | object\|null | Silicon Data GPU 租赁价格指数表（外部；非 OpenRouter） | 无本地源时可 null |

`null` 约定：拉取失败或无数据时，对应附加截面可为 `null`；**不得**因此删除或改写 `kpis`/`token`/`revenue`。

---

## `kpis`（最新完整周）— 与 v1 相同

| 字段 | 单位 | 说明 |
|------|------|------|
| `weekStart` / `weekEnd` | YYYY-MM-DD | Mon–Sun UTC 完整周 |
| `tokens_T` | 万亿 token | 周合计 |
| `tokensWowPct` | % | vs 上一完整周 |
| `revenue_M` | 百万 USD | fitted |
| `revenueWowPct` | % | vs 上一完整周 |
| `openTokenSharePct` / `closedTokenSharePct` | % | 开源 / 闭源 token 份额 |
| `openRevenueSharePct` / `closedRevenueSharePct` | % | 开源 / 闭源收入份额 |

## `token` / `revenue` 序列 — 与 v1 相同

公共形状：`starts` / `labels` / `series` / `totals` / `wowPct` 或 `wow` / `openSharePct` / `closedSharePct` / `otherSharePct`。

- token：`tokens_trillions`（T）
- revenue：`USD_millions`（$M）；**完整周 only**

## `providersLatest[]` / `incompleteWeek` — 与 v1 相同

见既有字段；`incompleteWeek` 不进 headline。

## Token / Revenue 口径摘要

- Token：`rankings-daily` `total_tokens` 加总。
- Revenue：`tokens × (0.9×0.5×input + 0.1×output)`（$/token）；`:free`/stealth 等为 0；详见 replicate `methodology_notes.md`。

---

## `appsWeekly`

来源：`GET /api/v1/datasets/app-rankings`（`sort=popular|trending`，可选 `category=coding`）。窗口 = 最新完整周。

| 字段 | 说明 |
|------|------|
| `weekStart` / `weekEnd` | 与 `kpis` 对齐 |
| `popular[]` | 全站 popular Top（默认 25） |
| `coding[]` | `category=coding` popular |
| `trendingTop[]` | `sort=trending`（超额增长；可能少于 limit） |
| `trendingNote` | 可选一句话；无 trending 数据时可为 `null` |
| `citation` / `caveats` / `meta` | 溯源与限制 |

每行 app：`rank`, `app_id`, `app_name`, `total_tokens`, `total_tokens_T`, `total_requests`, `tok_per_req`（requests=0 → `null`）。

Caveats：仅公开 apps；隐藏/私有排除；跨 app token 因分词器不同仅近似；trending 可能 `<limit`。

---

## `contextMix`

来源：`GET /api/v1/datasets/rankings-daily?period=week&context_bucket={1K\|10K\|100K\|1M\|10M}`，同一完整周。

| 字段 | 说明 |
|------|------|
| `buckets[]` | 每桶：`bucket`, `tokens`, `tokens_T`, `sharePct`, `topModels` |
| `totalTokens` / `totalTokens_T` | 五桶合计 |
| `vsAllSiteTokensPct` | 相对 `kpis.tokens_T`；截断/覆盖差异下可 ≠100 |
| `metaByBucket` | 各桶 API `meta` |

Caveats：`context_bucket` 为 exact 数据集，**不可**与 `category` / `language_type` 组合；每桶为该桶内 top-50+`other`；五桶之和未必等于全站 headline。

---

## `taskMix7d`

来源：`GET /api/v1/classifications/task?window=7d`。

| 字段 | 说明 |
|------|------|
| `window` / `window_days` / `as_of` | 目前仅支持 `7d`；`as_of` 为窗口上沿（UTC 昨日口径） |
| `macroCategories[]` | Code / Data / Agent / General；含 `usageSharePct` / `tokenSharePct` |
| `classifications[]` | 细分 tag；含全局份额、类别内份额、`topModels`（截断） |

Caveats：**采样**数据；不暴露绝对量；分母为已分类流量（排除 unclassified）；**不一定**对齐 Mon–Sun 完整周。

---

## `programmingShare`

来源：`rankings-daily?period=week&language_type=programming`，对比同窗无 filter 的 `period=week`。

| 字段 | 说明 |
|------|------|
| `programmingTokens_T` / `allSiteTokens_T` | 周估计 |
| `programmingOfAllSitePct` | programming / all-site |
| `providersProgramming[]` | 厂商份额；含 `allSiteSharePct`、`shareDeltaPp` |
| `providersAllSite[]` | 同窗全站厂商份额 |
| `topModelsProgramming[]` | programming 顶模型 |

Caveats：`language_type` 为 **采样/上采样周粒度**；不可与 `context_bucket` 等 exact filter 组合；`period=day` 会 400；厂商映射同 replicate author 前缀；`allSite` 同窗 week 聚合可能与 `kpis.tokens_T` 略有差异。

---

## `sessionCost`

来源：`GET /api/v1/datasets/session-cost`（默认取 limit=200）。

| 字段 | 说明 |
|------|------|
| `coverage` | 返回 cell 数、app 数、`window_days` / `window_end_date`、覆盖说明 |
| `byTurnRange[]` | 按 `1-turn` / `2-9-turns` / … 汇总的 median-of-medians 等 |
| `byApp[]` | 按 app 汇总（截断 Top） |
| `sampleCells[]` | 原始 cell 样本（app/model/turn/median USD） |
| `meta` | API meta |

Caveats：**仅已发布 harness**；会话不跨 app 合并；隐私聚合中位数；**非**全站 ARPU；窗口常约 30d 且独立于 rankings 完整周；limit 可能截断长尾。

---

## `catalogDerived`

来源：本地 `models_catalog.json`（`GET /api/v1/models`）。

| 字段 | 说明 |
|------|------|
| `nModels` | catalog 模型数 |
| `freeSuffixCount` / `freeSuffixSharePct` | id 含 `:free` |
| `zeroPriceCount` | prompt+completion 均为 0 |
| `huggingFaceIdCount` / `huggingFaceIdSharePct` | 非空 `hugging_face_id` |
| `cachePricing` | 带 `input_cache_read/write` 的数量；`medianCacheReadToPromptRatio` |

Caveats：catalog **列表**指标，**非**流量加权；HF id ≠ 法律开源声明；`:free` 数量 ≠ free 流量份额。

---

## UI 消费建议

1. KPI 条读 `kpis.*`（Token/Revenue 不变）。
2. 堆积图 / WoW / 开闭源读 `token` 或 `revenue`；不要把 `incompleteWeek` 混进主序列。
3. 厂商表读 `providersLatest`。
4. 附加面板：`appsWeekly`（应用）、`contextMix`（上下文桶）、`taskMix7d`（任务结构）、`programmingShare`（编程流量厂商）、`sessionCost`（会话成本）、`catalogDerived`（供给面轻指标）、`gpuRentalIndex`（GPU 租赁 $/GPU-hr 表，外部 Silicon Data）。
5. 页脚 / tooltip：`asOf` + 各截面 `citation` + `source.revenueFormula` 短注。
6. 任一附加截面为 `null` 时隐藏对应面板，勿阻断主图。


## `gpuRentalIndex`（v2.1）

Silicon Data GPU 租赁价格指数。数据维护：**研究方法学委**。只读消费 `/workspace/silicon_gpu_index/gpu_rental_index_latest.json`，**不要**改 `series_30d.json`。

| 字段 | 说明 |
|------|------|
| `asOf` | 价格截面日 `YYYY-MM-DD` |
| `updatedAt` | 写入本 JSON 的 Asia/Shanghai 时间 |
| `unit` | `$/GPU-hr` |
| `source` | 固定 `Silicon Data` |
| `windowDays` | 30（公开滚动窗） |
| `refresh` | 源侧元数据（工作日、晚 UTC 常见） |
| `rows[]` | 表：`name` · `segment`(`neo`/`hs`) · `gpu` · `price` · `chg7dPct` · `asOf` |
| `history` | `{ dates[], series{name→number[]} }` 可选折线 |
| `citation` / `caveats` | 溯源与限制（脚本写入） |

刷新：源文件更新后跑 `openrouter_replicate/scripts/sync_gpu_rental_index.py`（`build_gpu_rental_index.py` 为同义别名）；无新日可不推。Caveats：OpenRouter **无**此指数；公开窗约 30 日；完整历史需 Pro/Bloomberg；勿改 `series_30d.json`。
