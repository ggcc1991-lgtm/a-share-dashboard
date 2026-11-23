# 站点体验审计 2026-11-23（UI-2）

展示修复，没有改行情 JSON，没有改分数阈值，没有改投资建议。PR 未合并。

## 第二轮补齐（同一 PR）

上一轮留下的缺口在这一轮做完，并用浏览器动作核对，不是只看截图。

### 已补上的缺陷

- `/policy/` 在 375 和 390 宽的横向溢出是关闭的侧栏 `#drawer`。它 `position:fixed` 且比视口宽 2px，关着的时候仍算进 `scrollWidth`。关闭时宽度改为 0；打开时（点 `[data-sid]`）宽 375、溢出 0，正文能读到。375 和 390 的溢出都量到 **0**。
- `/etf/` 期货图初始化前把面板设成 `display:""`，样式表里的 `display:none` 又把它藏起来，图是 0×0。改为 `display:block` 后再 init。375 宽下 `chartFut` 为 327×194，有 tooltip、图例和 dataZoom。
- ETF / 抄底 / 信息流柱状图的 tooltip 原先不 `confine`，窄屏会画出画布。现在关在图内。信息流关键词和机会条补了 axis tooltip。
- 抄底 K 线、IM 贴水、融资余额，以及 OpenRouter 周图和 GPU 图，加了 `inside` dataZoom（不改数据，默认仍是 0–100 全区间）。ETF 和基金本来就有 inside + slider。
- `shell.js` 在 `echarts.init` 上包一层：`prefers-reduced-motion: reduce` 时 `animation: false` 且仪表盘 `valueAnimation: false`；tooltip 缺省 `confine: true`；容器用 ResizeObserver。用 Chrome 模拟 reduce 后，抄底 6 张图的 `animation` 都是 false。
- `legacy/index.html` 和 `bottom/full.html` 补了窄屏：`.grp .rd` 不再 `min-width:260px`，`overflow-x:clip`，按钮最小高度 44，备注不再被 3.2em 裁掉，减少动效，焦点环。嵌入的分数快照没有改。375 宽溢出 0，「由GC制作」还在，16 张图有宽度。

### 交互矩阵

Headless Chrome。图上的动作是 `dispatchAction`：`showTip`、`legendToggleSelect`、`dataZoom` 到 30–70 再回到 0–100。页签是真实 `click`。N/A 表示页面没有这种控件。

| 路由 | 宽 | 溢出 | tooltip | 图例开关 | dataZoom | 页签/点击 | 备注 |
|---|---|---|---|---|---|---|---|
| `/` | 1280、375 | 0 | SVG `title`，214 点 | N/A | N/A | 导航 ArrowDown 把 `aria-expanded` 设为 true | 说明含「近似重建」，tooltip `2026-11-23  红线 9/12` |
| `/etf/` | 1280、375 | 0 | 3 张图 showTip 成功，confine true | 成功后恢复 | 成功后回到 0–100 | 期货面板现在可见 | `chartFut` 不再是 0×0 |
| `/sentiment/` | 1280、375 | 0 | SVG `<title>` | N/A | N/A | 点 `[data-d]` 后格子带 `.sel`；1280 也能点到带「情绪」的格子 | 无 ECharts。手机藏长文案，短状态还在 |
| `/momentum/` | 1280、375 | 0 | N/A | N/A | N/A | 热力表，无图实例 | 未改排序逻辑 |
| `/feed/` | 1280、375 | 0 | 3 张图，含新的柱状 tooltip | 饼图图例可关 | N/A（分类条，不是时间轴） | 无页签 | |
| `/bottom/` | 1280、375 | 0 | K 线/贴水/融资/分组/进度 confine | 时间序列无多图例，记 N/A | 3 条时间序列 inside zoom 成功 | 仪表盘无 zoom，记 N/A | reduce 下 animation false |
| `/policy/` | 1280、375、390 | 0 | SVG spark 在抽屉里 | N/A | N/A | 点筛选按钮；点 `data-sid` 打开抽屉，宽等于视口 | |
| `/earnings/` | 1280、375 | 0 | N/A | N/A | N/A | 倒计时卡片，无 ECharts | 未改倒计时 |
| `/openrouter/` | 1280、375 | 0 | 3 张图 confine | 图例可关 | inside zoom 成功 | 点「拟合流水」后 `chartRevenue` 宽 350（375 视口） | 隐藏页签在点开前宽度为 0，属预期 |
| `/funds/` | 1280、375 | 0 | confine | 可关 | inside+slider 成功 | 第二个区块按钮可点 | 公募 |
| `/funds/?view=private` 与 `?tab=private` | 1280、375 | 0 | confine | 第一项常是 defaultOff，开关会把它打开，状态有变化 | 成功 | 标题含「周频截面，非盘中」和 asOf 2026-11-13 | 两个 query 都进私募 |
| `/legacy/`、`/bottom/full.html` | 375 | 0 | 15 张有 tooltip 且 confine；仪表盘无 tooltip，记 N/A | 迷你图无图例，记 N/A | K 线有 inside zoom | 无主导航页签 | 嵌入快照未改 |

Resize：把视口从 1280 改到 900、从 375 改到更宽之后，ETF / 抄底 / 信息流图的 `getWidth()` 跟着变。OpenRouter 和基金里先量到的 100px 是尚未点开的隐藏画布，点开页签后收入图为 350。

控制台：上一轮 10 条路由在 390 宽没有 `exceptionThrown` 或 `console.error`。这一轮的 tooltip / zoom / 页签动作没有抛异常。

### 仍然没做

- 没有用手指在真机上捏合 dataZoom。桌面和 headless 用的是 `dispatchAction`，等价于组件收到缩放，不是触摸手势本身。
- 动量热力表和财报倒计时没有图例可点。
- 没有把每张图都改成同一套 slider 样式。时间序列能缩放；分类条不加一条无意义的缩放轴。

## 方法

- 基线：`main` @ `6fc7763`（PR 167 已合）。
- 本地 `python3 -m http.server`，Chrome headless。
- 每条主导航在 1280×900 和 390×844 各打开一次，记录正文长度、横向溢出、是否停在「加载中」、是否出现加载失败。
- 之后对改过的页面复查控制台异常、导航高度和关键文案。
- 没有逐个拖拽每张 ECharts 的 dataZoom。下表把「打开并读到主内容」和「交互未测」分开写。

## 路由

| 路径 | 1280 | 390 | 结果 |
|---|---|---|---|
| `/` | 溢出 0，9/12，折线 214 点 | 溢出 0，同样 214 点 | 已改说明与空值 |
| `/etf/` | 溢出 0，页内写明 23:00 更新 | 溢出 0 | 日合计本就跳过 null；展示格式收紧 |
| `/sentiment/` | 溢出 0，最新交易日 2026-11-23 | 溢出 0 | 未改逻辑。日历非交易日是「—」不是 0 |
| `/momentum/` | 溢出 0，交易日 2026-11-23 | 溢出 0 | 仅空字符串不再被格式化成 0 |
| `/feed/` | 溢出 0 | 溢出 0 | 时间改成上海生成时间 |
| `/bottom/` | 溢出 0，由GC制作仍在 | 溢出 0 | 口径说明；仪表盘不再从 0 数上去 |
| `/policy/` | 溢出 0，asOf 2026-11-22 | **溢出 2px**（改前改后都是 2） | 未改布局 |
| `/earnings/` | 溢出 0 | 溢出 0 | 倒计时是到点时钟，未改 |
| `/openrouter/` | 溢出 0 | 溢出 0 | 收入标明拟合 |
| `/funds/` | 溢出 0，生成 2026-11-19 21:34 | 溢出 0 | 空字符串格式 |
| `/funds/?view=private` | 溢出 0，asOf 2026-11-13 | 溢出 0 | 标明周频、非盘中 |
| `/legacy/`、`/bottom/full.html` | 未作为主导航打开 | 未测 | 归档页，本次不动 |

`prefers-reduced-motion` 的全局 `animation/transition: none` 原本就在 `theme.css`。这次没有在浏览器里强制打开该媒体查询做视觉对照。仪表盘数字动画则直接关掉，不依赖该媒体查询。

## 发现

严重度按「会让人把缺失或重建值当成实盘数字」来排。

### 已修

1. **总览抄底折线把重建值和实值画成同一种线，也不说明。** 高。`score_history.note` 写明历史日由 history/extra_history 近似重建，不含缩量放量、加息、PCR；只有末日用 `bottom.json`。发布序列里 2026-11-20 = **6**，而该字段被删之前、当日收盘实值曾记为 **9**。图仍画发布值 6，不回填 9。现在图下写出这条 note，并单独标出 `live: true` 的 2026-11-23 = 9。来源 `score_history.points`。PR 167 的 214 点折线还在，tooltip 仍是 `2026-11-23  红线 9/12`。
2. **总览 ETF 流入把缺失当成 0。** 高。`index.html` 用 `flow?.[i] ?? 0` 相加。`/etf/` 已经是「有值才加，全缺则 null」。总览改成同一规则：全缺得到 null，显示「—」；真 0 仍是 0。
3. **`bottom.json` 加载失败时总览会画出 0/12。** 中。`triggered_count ?? 0`。失败时该卡改为「抄底数据未加载，其他栏目不受影响」，顶栏信号为「—」。文件里的 0 仍显示 0。
4. **汇金观察份额和为 0 时显示「—」。** 中。`holderSum ? format : "—"` 把合法 0 当成空。改为 `== null` 才显示「—」。缺失份额不再用 `|| 0` 加进去。
5. **空字符串被格式化成 0。** 中。`DashFmt`、ETF、动量、基金、OpenRouter 的数字格式在 `""` 上得到 0，因为 `+"" === 0`。空字符串、空白、NaN、Infinity、布尔值现在是「—」；数字 0 仍是 0。
6. **信息流页眉把原始 ISO 当更新时间。** 中。`2026-11-23T22:23:29.284012+08:00` 原样出现。现为「生成 2026-11-23 22:23」。这是文件里的 `updated`，不是本次 fetch 的时刻。无时区的日期时间按 Asia/Shanghai 理解，再格式化到上海。
7. **OpenRouter 收入只写英文 fitted。** 中。KPI 改为「拟合估计 · 非实际收入 · 完整周」。开源/闭源收入份额标「拟合」。不完整周仍不进主图（原逻辑保留）。GPU 历史里的 null 继续 `connectNulls: false`；若序列里有 null，表注写「历史空值保持缺失，不补 0」。
8. **抄底口径藏在长 note 里。** 中。VIX `meta.proxy === true` 时写明是平值期权隐含波动率代理，不是官方 QVIX。融资余额 `meta.date` 为 2026-11-05，截面 `as_of` 为 2026-11-23，页上写「数据日 …，未外推」。阈值没动。`/bottom/` 的「由GC制作」还在。
9. **仪表盘从 0 数到 9。** 中。`valueAnimation: true` 会在动画中途显示 0/12。已关闭。`DashMotion.countTo` 不再从 0 计数，橙色闪动关键帧已删。
10. **顶栏时钟容易被看成数据更新时间。** 低。前面加了「现在」。抄底页脚改为「截面 … · 生成 …」，生成时间是 `generated_at` 的上海时间，不是 fetch 时间。
11. **私募 asOf 2026-11-13，没有说明这不是盘中。** 低。标题加「周频截面，非盘中」，与 schema 的周频约定一致，没有把 asOf 改成今天。
12. **焦点与窄屏点击。** 低。`:focus-visible` 为 2px 琥珀描边。≤719px 导航高 44px（复查实测 44）。次要字色 `--mu-2` `#8f8f8f`、`--mu-3` `#8a8a8a`，仍是黑底琥珀壳。
13. **信息流分析条把缺失数值写成 0。** 低。`+x.value || 0` 改为缺失则 null。计数（某来源 0 条）仍是 0，那是条数不是行情。

### 查过、未改

- 情绪：`sentiment/data/history.json` 126 个交易日，20260521–20261123，`exportedAt` 2026-11-23T07:31:00Z。页头「最新交易日 2026-11-23」与末日一致。非交易日格是「情绪 —」，不是 0。
- ETF 页日合计本来就跳过 null。页头「数据更新」用的是 JSON 的 `updated`。
- 动量 0 只是不加涨跌色，数字仍格式化出来。
- 财报页「未来 7 日」倒计时是到公告时点的时钟，文案写了「实时倒计时」。不是把缺失财务数写成 0。
- OpenRouter 不完整周与完整周 KPI 本来就是分开的。
- 各主图已有 `resize` 监听：总览 spark、ETF、基金、OpenRouter、信息流、抄底。没有再包一层。

### 未做（第一轮；第二轮已补的见文首）

- 财报筛选芯片在桌面仍有一批高度小于 32px 的控件。没有把所有芯片改成 44px，避免打乱密表。手机上的主导航已经是 44px。
- 基金折线 `connectNulls: true` 会跨过空点连线，但不会把空点画成 0。这次没有改这个既有画法。

## 测试

`node --test tests/present.test.js tests/score-series.test.js`

17 项，17 通过，0 失败。原有 16 项都在。新增：`applyChartDefaults` 在减少动效时关掉 animation / valueAnimation、给 tooltip 加 confine，且不改 series 数据（null 和 0 都留着）。其余仍覆盖空值与 0、上海时间、流入缺失不为 0、抄底口径、YTD 发布值（2026-11-20 为 6，2026-11-23 为 9 且 `live`）。

## 本地测量（不是生产 CDN）

Headless Chrome，`127.0.0.1:8080`。

- 10 条主导航在 390 宽、`mobile: true` 下没有 `exceptionThrown`，也没有 `console.error`。
- 这些页面的 `.nav` 高度都是 44。
- 总览文档 `domContentLoadedEventEnd` 约 54–85ms，`transferSize` 约 20KB（只是文档请求，本地服务器）。基金私募约 38–60ms，信息流约 103–106ms。这些数字会随缓存变成 0 传输，不能当成生产性能。

## 风险

- 说明文字直接引用发布 note，句子偏长。它是口径，不是新的分数。
- 无时区的时间字符串按上海墙钟解析。带 `Z` 或 `+08:00` 的仍按瞬时时间再换到上海。
- 政策页关闭时的 2px 溢出已在第二轮去掉。打开抽屉时宽等于视口。
- 本分支已并入当时的 `main`（ETF / 财报 JSON 由其他发布写入）。后续合并不要用旧快照覆盖这些文件。
