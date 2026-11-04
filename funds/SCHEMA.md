# 基金数据 · schema

站内路径：

- 公募：`funds/data/mutual.json` · `schemaVersion`: **`funds-mutual-v2`**
- 私募：`funds/data/private.json` · `schemaVersion`: **`funds-private-v1`**

只读数据契约。UI：`funds/index.html`。顶栏「基金数据」下挂公募 / 私募（与 ETF 同款下拉）；私募 URL `funds/?view=private`；公募默认 `funds/`（`view=mutual`）。无页内公私 toggle、无首页总览卡。

## 刷新

| 类型 | 节奏 | 说明 |
|------|------|------|
| 公募（仓位多图） | **工作日 21:30**（Asia/Shanghai） | 有新 `asOf` 或字段变化再推；否则可不推 |
| 私募（策略指数 · 三表） | **默认周五 21:30** | 绝对 / 超额 / 风格持仓；无新 `asOf` / 无字段变化可不推；空列表可推 `funds: []` 且 `tables` 可空 |

## 空列表约定

- **公募 v2**：以 `sections[]` 为主；`funds: []` 仅兼容旧观察池，**不再作为主 UX**。
- **私募**：`funds: []`（或缺失）且无可用 `tables` 时：前端隐藏密表，展示「暂无数据」；KPI 仍可读（若有）。

## 顶层字段（公募 / 私募共用元信息）

| 字段 | 类型 | 说明 |
|------|------|------|
| `schemaVersion` | string | `funds-mutual-v2` / `funds-private-v1` |
| `generatedAt` | string | ISO 生成时间（含时区） |
| `generatedAtDisplay` | string | 展示用北京时间文案 |
| `asOf` | string | 截面日 `YYYY-MM-DD`（公募主 asOf 取主观公募绝对仓位末点） |
| `timezone` | string | 固定 `Asia/Shanghai` |
| `sample` | boolean? | `true` 时 UI 显示「样例」角标 |
| `note` | string? | 页脚一行说明 |
| `universe` | string? | 公募仓位可为 `lxwfof_position_pub`；私募可为 `strategy_index` |
| `source` | object? | 溯源（MCP / API path / gaps） |
| `kpis` | object[] | KPI 条 |
| `funds` | object[] | **兼容**密表行；公募 v2 保持 `[]` |

---

## 公募 · `funds-mutual-v2`（lxwfof 公私募持仓统计 · 公募侧）

对应站点 `https://lxwfof.com/#/position` 公募相关锚点。主 UX 为 **多段 ECharts 折线**（仿私募 `series` 渲染），**不再**以观察池 `funds[]` 表为主。

### 顶层扩展

| 字段 | 类型 | 说明 |
|------|------|------|
| `sections` | object[] | **有序区块**：combo / pub_abs / pub_style / pub_quant /（可选）etf |
| `funds` | `[]` | 旧观察池已清空；保留键以免旧客户端报错 |

### `sections[]` 共用字段

| 字段 | 说明 |
|------|------|
| `id` | `combo` \| `pub_abs` \| `pub_style` \| `pub_quant` \| `etf` |
| `anchor` | 与源站一致：`pos-combo` / `pos-pub-abs` / `pos-pub-style` / `pos-pub-quant` / `pos-etf` |
| `title` | 展示标题 |
| `kind` | `combo` \| `tabs_abs` \| `tabs_style` \| `tabs_quant` \| `single` |
| `asOf` | 本区块末点日期 |
| `unit` | 通常 `%` |
| `defaultOff` | 默认图例隐藏的线名 |
| `hint` / `note` / `accuracy` | 可选说明；`accuracy` 含 `text`/`r2_*`/`n_funds` |

#### 1. `combo` · 公私募全风格合计（`kind: combo`）

| 字段 | 说明 |
|------|------|
| `chips` | 成分名：`主动私募`/`量化私募`/`主动公募`/`ETF`（API `主观私募` 已映射为 `主动私募`） |
| `dates` | 公共日期轴 |
| `series` | 全成分规模加权后的风格线（含 `A股总仓位` 等；默认 off） |
| `parts` | `Record<成分, Record<线名, number[]>>` 供前端按选中 chips × `scales` 重加权 |
| `scales` | `Record<成分, number[]>` 亿元规模（与 dates 等长） |

前端：chips 多选（至少 1）；全选用预计算 `series`，子集用 `Σ(scale×value)/Σ(scale)` 重算。

#### 2. `pub_abs` · 主观公募绝对仓位（`kind: tabs_abs`）

| 字段 | 说明 |
|------|------|
| `lineKeys` | 固定 `A股总仓位` / `港股` / `总股票仓位`（无美股） |
| `tabs[]` | `pub`=纯公募、`blend`=公募+私募；每项含 `dates`+`series` |

#### 3. `pub_style` · 主观公募风格拆分（`kind: tabs_style`）

| 字段 | 说明 |
|------|------|
| `defaultOff` | 通常含 `总股票仓位` |
| `tabs[]` | `all` 全部公募 / `blend` 公募+私募 / `价值`/`白马成长`/`均衡`/`科技成长` |
| 线名 | `总股票仓位` + 七风格（沪深300…风格:双创）；四组页签的总仓位来自源 `total` |

#### 4. `pub_quant` · 量化公募风格拆分（`kind: tabs_quant`）

| 字段 | 说明 |
|------|------|
| `defaultTab` | 默认 `300指增` |
| `defaultOff` | `总仓位` + `风格:微盘` + `小微盘` |
| `tabs[]` | `300/500/1000/2000/A500/双创/800/上证/国证/A50/红利指增` + `主动量化` |
| 线名 | `总仓位` + 九风格（含微盘/小微盘） |

#### 5. `etf` · ETF持仓拆分（`kind: single`，可选）

| 字段 | 说明 |
|------|------|
| `dates` / `series` | 全历史日频；`defaultOff` 含 A股总仓位/总股票仓位/美股/未拆分 |
| `note` | 源站口径说明 |

### 数据来源与缺口

- **MCP** `user-lxwfof MCP` → `get_dataset(name=position)`：仅有私募侧 `subjective`/`styles4`/`zhizeng`/`text`（页头 asOf 约私募周频），**不含**公募四块 / ETF / 产品自助。
- **公募主数据**：同源站点 `/api/position/pub`（`pub`/`blend`/`combo`/`accuracy*`）；ETF：`/api/position/etf`。
- **未收录**：`#pos-pattr` 产品自助（需 `/api/position/ppos`）；`pubpri_excess` 属超额对比、不进本文件。
- 合规：回答中须保留 MCP 返回末尾提示语（如「部分信息参考自lxwfof MCP」）。

### 公募 UI 消费（`view=mutual`）

1. 读 `sections[]` 按序渲染多张图；KPI 读 `kpis`。
2. 每区独立 tabs/chips + 区间（全样本/近3年/近1年/2024至今）；默认可视窗口可从 2023-01-01 起（历史更早时）。
3. ECharts：本地 `../assets/echarts.min.js` + `DashTheme.echartsDark`；仓位线用中性/固定名色，**不做涨跌红绿**。
4. `funds[]` 空时不渲染观察池密表；无 `sections` 时才回退旧 `funds` 表。

### 旧版 `funds-mutual-v1`（已废弃主路径）

曾以 `funds[]` 观察池密表为主。v2 起保留空 `funds` 键，契约以 `sections` 为准。

---

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
| `id` | 如 `watch_count` / `avg_ret_1y` / `avg_mdd_1y` / `a_share_pos` |
| `label` | 展示名 |
| `value` | 数值 |
| `unit` | 如 `只` / `条` / `%` |
| `note` | 可选脚注 |

约定：`avg_ret_1y`、`avg_mdd_1y` 为百分数原值；回撤为负；UI 对回撤 KPI 使用 `var(--neg)`。仓位类 KPI 不做涨跌色。

## `funds[]` · 公募（兼容层，v2 通常为空）

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
- 仓位 / 风格持仓：百分点原值（`64` = 64%），不做涨跌色。
- `aumYi`：规模，单位 **亿元**（可 null）。
- 涨跌色：A 股习惯，正收益红 `var(--pos)`、负绿 `var(--neg)`；回撤列按负值着色。

## UI 消费（总览）

1. 默认 `/funds/` 加载 `mutual.json`；`/funds/?view=private` 加载 `private.json`。
2. **公募**：有非空 `sections` → 多段仓位图；否则回退 `funds` 密表。
3. **私募**：若 `tables` 含三表，页内分段 +（若有）`series` 折线；否则回退 `funds`。
4. 副标：`generatedAtDisplay` / `asOf`；`sample:true` 显示「样例」。
5. 页脚：`note` 一行；各 section/表可用自身 `note`/`accuracy.text`。
