# 基金数据 · schema

站内路径：

- 公募：`funds/data/mutual.json` · `schemaVersion`: **`funds-mutual-v1`**
- 私募：`funds/data/private.json` · `schemaVersion`: **`funds-private-v1`**

只读数据契约。UI：`funds/index.html`。顶栏「基金数据」下挂公募 / 私募（与 ETF 同款下拉）；私募 URL `funds/?view=private`；无页内 toggle、无首页总览卡。

## 刷新

| 类型 | 节奏 | 说明 |
|------|------|------|
| 公募 | **工作日 21:30**（Asia/Shanghai） | 有新 `asOf` 或字段变化再推；否则可不推 |
| 私募（策略指数 · 三表） | **默认周五 21:30** | 绝对 / 超额 / 风格持仓；无新 `asOf` / 无字段变化可不推；空列表可推 `funds: []` 且 `tables` 可空 |

## 空列表约定

`funds: []`（或缺失）且无可用 `tables` 时：前端隐藏密表，展示「暂无数据」提示；KPI 仍可读（若有）。

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
| `funds` | object[] | **兼容**密表行；私募侧等同「绝对收益」表行（可空） |

## 私募扩展（`funds-private-v1`）

对应晨会「金融资本盘点」私募三块（Page `659ceb59-1707-46db-9cd6-19962110e905` / slide 30–32）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `tables` | object[] | **三张完整表**：`absolute` / `excess` / `style`；UI 私募页优先按此渲染 |
| `series` | object? | 完整时序（不截断）；图表/复核用，密表可不读 |

### `tables[]`

| 字段 | 说明 |
|------|------|
| `id` | `absolute` \| `excess` \| `style` |
| `title` | 绝对收益 / 超额收益 / 风格持仓 |
| `kind` | `performance`（业绩密表）或 `holdings_matrix`（风格截面） |
| `unit` | `index` 或 `%` |
| `base` / `baseDate` | 业绩表基期（通常 100 / `2020-12-31`） |
| `asOf` | 截面日 |
| `freq` | 如 `weekly` / `month_end_digitized` |
| `rowCount` | 行数（与 `rows.length` 一致，便于校验） |
| `note` | 表脚说明 |
| `columns` | `{key,label,align,format?}`；`format`=`num2`/`pct1` |
| `rows` | 完整行对象数组，**勿截断** |
| `styleKeys` | 仅 style 表：风格列键顺序 |

#### 表 1 · `absolute`（绝对收益）

- 行：10 策略（期权已剔除）
- 关键字段：`code`, `thscode`, `name`, `fullName`, `strategy`, `level`（点位）, `ret1m`/`ret3m`/`ret6m`/`ret1y`/`retYtd`/`retSince`, `mdd1y`, `asOf`
- 区间收益：周频回溯 **4 / 12 / 26 / 52** 周；YTD 相对上年 12-31 点位

#### 表 2 · `excess`（超额收益）

- 行：4 条（300/500/1000 指增 + 量选+小盘增强）
- 字段同业绩表，另加 `benchmark`（对标宽基代码）
- 口径：策略净值 ÷ 对应宽基自基日归一；量选对标中证1000

#### 表 3 · `style`（风格持仓）

- 行：5 页签（300/500/1000/2000/A500 指增）
- 列：`strategy` + `总仓位` + 9 风格线（`沪深300`…`小盘微`），单位 %
- 仍为晨会描点示意；完整风格时序在 `series.style` + `series.styleDates`

### `series`（可选但推荐完整写入）

| 字段 | 说明 |
|------|------|
| `dates` | 绝对/超额周频日期轴（完整） |
| `absolute` | `Record<策略, number[]>` 与 `dates` 等长 |
| `excess` | 同上，仅 4 策略 |
| `styleDates` | 风格月频/描点日期轴 |
| `style` | `Record<页签, Record<风格键, (number\|null)[]>>` |
| `codes` | Wind 代码映射 |
| `base` / `baseDate` / `lookbackWeeks` | 元信息 |

### `kpis[]`

| 字段 | 说明 |
|------|------|
| `id` | 如 `watch_count` / `avg_ret_1y` / `avg_mdd_1y` |
| `label` | 展示名（策略指数场景可用「绝对收益策略」等） |
| `value` | 数值 |
| `unit` | 如 `只` / `条` / `%` |
| `note` | 可选脚注 |

约定：`avg_ret_1y`、`avg_mdd_1y` 为百分数原值；回撤为负；UI 对回撤 KPI 使用 `var(--neg)`。

## `funds[]` · 公募

主列：`code`, `name`, `category`, `company`, `manager`, `nav`, `navDate`, `ret1m` / `ret3m` / `ret6m` / `ret1y` / `retYtd`, `mdd1y`, `aumYi`, `rank1y`, `asOf`。

可选：`thscode`, `fullName`, `ret1w`, `retSince`, `rankPeerSize`, `rankPeerPos`, `tags` 等。

## `funds[]` · 私募 / 策略指数（兼容层）

- 用 **`strategy`** 代替 `category`；可无 `rank1y`。
- 当前正式截面：`universe: "strategy_index"`，行 `kind: "strategy_index"`。
  - `nav`：**指数点位**（非基金单位净值）；与 `tables[absolute].rows[].level` 同源
  - `aumYi`：可为 `null`（UI 显示 —；策略指数表默认不展示规模列）
  - `company`：多为 `Wind策略指数`；`manager` 可空
- 有 `tables` 时：UI 渲染三表；`funds` 仍保留供旧客户端 / 绝对收益兜底。
- 其余收益 / 回撤字段与公募对齐。

## 数值口径

- 收益、回撤：百分数原值（`15.6` = 15.6%）；`mdd1y` 为负。
- `aumYi`：规模，单位 **亿元**（可 null）。
- 涨跌色：A 股习惯，正收益红 `var(--pos)`、负绿 `var(--neg)`；回撤列按负值着色。
- 风格持仓：百分点原值（`64` = 64%），不做涨跌色。

## UI 消费

1. 默认 `/funds/` 加载 `mutual.json`；`/funds/?view=private` 加载 `private.json`（由 URL 决定，打开私募不闪公募）。
2. 若 `universe === "strategy_index"`（或行均为 `kind: strategy_index`）：副标「私募·策略指数」。
3. **私募优先**：若 `tables` 含 `absolute`/`excess`/`style`，用页内分段切换三张完整密表；KPI 条读 `kpis`。
4. **私募折线（仅 `view=private`）**：若存在非空 `series`，在 KPI 与密表之间（`tableSeg` 下方）渲染 ECharts 折线（本地 `../assets/echarts.min.js` + `DashTheme.echartsDark`）；公募不显示图。
   - 与 `?table=` / 页内分段联动：`absolute` → `series.dates` × `series.absolute`；`excess` → `series.dates` × `series.excess`；`style` → `series.styleDates` × `series.style[页签]`。
   - 风格页签默认 `300指增`（无则取第一个 key）：`300指增` / `500指增` / `1000指增` / `2000指增` / `A500指增`；切换只重画风格图，不改 table 分段。
   - 区间切换（按 dates / styleDates 过滤，终点取序列末点 / asOf）：全样本 / 近3年 / 近1年 / 2024至今。
   - 图例可点击显隐（默认全显）。业绩图用策略固定色（如 `300指增=#2F5BFF`）；风格持仓用中性色板，**不做涨跌红绿**。
   - 点数过多时四周抽样（保留终点）以减轻卡顿；`setOption` 复用实例，监听 `resize`。
   - 无 `series` 或对应段为空：隐藏图，不报错。密表仍只读 `tables`。
5. 若无 `tables`：回退单表渲染 `funds`（旧行为）。
6. 副标：`generatedAtDisplay` / `asOf`；`sample:true` 显示「样例」。
7. 页脚：`note` 一行；各表可用自身 `note`。
