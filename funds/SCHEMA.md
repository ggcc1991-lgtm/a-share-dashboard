# 基金数据 · schema

站内路径：

- 公募：`funds/data/mutual.json` · `schemaVersion`: **`funds-mutual-v1`**
- 私募：`funds/data/private.json` · `schemaVersion`: **`funds-private-v1`**

只读数据契约。UI：`funds/index.html`（公募 / 私募标签切换；无首页总览卡）。

## 刷新

| 类型 | 节奏 | 说明 |
|------|------|------|
| 公募 | **工作日 21:30**（Asia/Shanghai） | 有新 `asOf` 或字段变化再推；否则可不推 |
| 私募 | **默认周五 21:30** | 披露频率低；无新截面可不推；空观察池可推 `funds: []` |

## 空列表约定

`funds: []`（或缺失）时：前端隐藏密表，展示「暂无数据」提示；KPI 仍可读（若有）。私募正式接入前可先手工维护观察池。

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
| `kpis` | object[] | KPI 条（建议 3 个） |
| `funds` | object[] | 观察池密表行；可空 |

### `kpis[]`

| 字段 | 说明 |
|------|------|
| `id` | 如 `watch_count` / `avg_ret_1y` / `avg_mdd_1y` |
| `label` | 展示名 |
| `value` | 数值 |
| `unit` | 如 `只` / `%` |
| `note` | 可选脚注 |

约定：`avg_ret_1y`、`avg_mdd_1y` 为百分数原值；回撤为负；UI 对回撤 KPI 使用 `var(--neg)`。

## `funds[]` · 公募

主列：`code`, `name`, `category`, `company`, `manager`, `nav`, `navDate`, `ret1m` / `ret3m` / `ret6m` / `ret1y` / `retYtd`, `mdd1y`, `aumYi`, `rank1y`, `asOf`。

可选：`thscode`, `fullName`, `ret1w`, `retSince`, `rankPeerSize`, `rankPeerPos`, `tags` 等。

## `funds[]` · 私募

用 **`strategy`** 代替 `category`；可无 `rank1y`。其余收益 / 净值 / 规模字段与公募对齐。

## 数值口径

- 收益、回撤：百分数原值（`15.6` = 15.6%）；`mdd1y` 为负。
- `aumYi`：规模，单位 **亿元**。
- 涨跌色：A 股习惯，正收益红 `var(--pos)`、负绿 `var(--neg)`；回撤列按负值着色。

## UI 消费

1. 默认加载 `mutual.json`；切「私募基金」加载 `private.json`。
2. KPI 条读当前文件 `kpis`；密表读 `funds`。
3. 副标：`generatedAtDisplay` / `asOf`；`sample:true` 显示「样例」。
4. 页脚：`note` 一行。
