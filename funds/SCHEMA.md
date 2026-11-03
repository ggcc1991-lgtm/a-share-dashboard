# 基金数据 · schema

站内路径：

- 公募：`funds/data/mutual.json` · `schemaVersion`: **`funds-mutual-v1`**
- 私募：`funds/data/private.json` · `schemaVersion`: **`funds-private-v1`**

只读数据契约。UI：`funds/index.html`。顶栏「基金数据」下挂公募 / 私募（与 ETF 同款下拉）；私募 URL `funds/?view=private`；无页内 toggle、无首页总览卡。

## 刷新

| 类型 | 节奏 | 说明 |
|------|------|------|
| 公募 | **工作日 21:30**（Asia/Shanghai） | 有新 `asOf` 或字段变化再推；否则可不推 |
| 私募（策略指数） | **默认周五 21:30** | 当前为 Wind 私募/量化策略指数截面；无新 `asOf` / 无字段变化可不推；空列表可推 `funds: []` |

## 空列表约定

`funds: []`（或缺失）时：前端隐藏密表，展示「暂无数据」提示；KPI 仍可读（若有）。

## 顶层字段（公募 / 私募同构）

| 字段 | 类型 | 说明 |
|------|------|------|
| `schemaVersion` | string | `funds-mutual-v1` / `funds-private-v1` |
| `generatedAt` | string | ISO 生成时间（含时区） |
| `generatedAtDisplay` | string | 展示用北京时间文案 |
| `asOf` | string | 截面日 `YYYY-MM-DD` |
| `timezone` | string | 固定 `Asia/Shanghai` |
| `sample` | boolean? | `true` 时 UI 显示「样例」角标 |
| `note` | string? | 页脚一行说明 |
| `universe` | string? | 私募可为 `strategy_index`（Wind 策略指数）；有则 KPI/标题按「策略指数」展示 |
| `source` | object? | 可选溯源 |
| `kpis` | object[] | KPI 条（建议 3 个） |
| `funds` | object[] | 密表行；可空 |

### `kpis[]`

| 字段 | 说明 |
|------|------|
| `id` | 如 `watch_count` / `avg_ret_1y` / `avg_mdd_1y` |
| `label` | 展示名（策略指数场景可用「策略指数」等） |
| `value` | 数值 |
| `unit` | 如 `只` / `条` / `%` |
| `note` | 可选脚注 |

约定：`avg_ret_1y`、`avg_mdd_1y` 为百分数原值；回撤为负；UI 对回撤 KPI 使用 `var(--neg)`。

## `funds[]` · 公募

主列：`code`, `name`, `category`, `company`, `manager`, `nav`, `navDate`, `ret1m` / `ret3m` / `ret6m` / `ret1y` / `retYtd`, `mdd1y`, `aumYi`, `rank1y`, `asOf`。

可选：`thscode`, `fullName`, `ret1w`, `retSince`, `rankPeerSize`, `rankPeerPos`, `tags` 等。

## `funds[]` · 私募 / 策略指数

- 用 **`strategy`** 代替 `category`；可无 `rank1y`。
- 当前正式截面：`universe: "strategy_index"`，行 `kind: "strategy_index"`。
  - `nav`：**指数点位**（非基金单位净值）
  - `aumYi`：可为 `null`（UI 显示 —；策略指数表默认不展示规模列）
  - `company`：多为 `Wind策略指数`；`manager` 可空
- 其余收益 / 回撤字段与公募对齐。

## 数值口径

- 收益、回撤：百分数原值（`15.6` = 15.6%）；`mdd1y` 为负。
- `aumYi`：规模，单位 **亿元**（可 null）。
- 涨跌色：A 股习惯，正收益红 `var(--pos)`、负绿 `var(--neg)`；回撤列按负值着色。

## UI 消费

1. 默认 `/funds/` 加载 `mutual.json`；`/funds/?view=private` 加载 `private.json`（由 URL 决定，打开私募不闪公募）。
2. 若 `universe === "strategy_index"`（或行均为 `kind: strategy_index`）：副标「私募·策略指数」，密表用指数代码 + 点位列。
3. KPI 条读当前文件 `kpis`；密表读 `funds`。
4. 副标：`generatedAtDisplay` / `asOf`；`sample:true` 显示「样例」。
5. 页脚：`note` 一行。
