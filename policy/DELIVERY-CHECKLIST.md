# 政策产业观察 · 交付对照 checklist

时间：Asia/Shanghai · 重建 `fetchedAt=2026-10-23T17:00:24+08:00`

## 成功标准

| 标准 | 状态 |
|------|------|
| 本地打开多窗实时（6h/24h/3d） | ✅ `realtime.byWindow` + UI 窗切换 |
| 增强表（layer/status/parent/三热度/三动量可排序） | ✅ 快照截面表 |
| 下钻抽屉（heat-series / companies / etfs / evidence） | ✅ 预取 28 包 |
| 数据与 API latest 一致 | ✅ `snapshotId=906027050724dd486f7b` · `asOf=2026-10-22` |

## 原站模块对齐

| # | 模块 | 状态 | 说明 |
|---|------|------|------|
| 1 | 实时动态 vs 日报快照双视图 | ✅ | `#viewToggle` |
| 2a | 实时：材料流 + 板块信号 | ✅ | 三 channel + 信号筛选 |
| 2b | 日报：指标条 + 热度总览 + 本次发布 | ✅ | coverage 六格 + brief |
| 3 | 材料：权威政策/媒体/即时关注 | ✅ | 日报 tab；关注汇自 realtime |
| 4 | 市场扫描：筛选 + 三榜 + 二维定位 + 明细 | ✅ | SVG 散点 policy×attention；三维略 |
| 5 | 快照截面：排名 + layer + 搜索 | ✅ | |
| 6 | 关联研究：公司 / ETF / 上市动态 | ✅ | securities/changes=1 |
| 7 | 页脚非荐股 | ✅ | |

## 缺口与约束落实

| 项 | 状态 |
|----|------|
| 多窗实时 6h/24h/3d | ✅ |
| 三类信号 view+layer+heat/momentum/evidence | ✅ |
| 板块总表可排序 + status/parent | ✅ |
| 异动完整 explanation + linked_sectors | ✅ 23/23 expl · 22 linked |
| 顶栏 meta | ✅ |
| 历史截面 ~15 只读 | ✅ 15 |
| 板块下钻预取 | ✅ 28 |
| 材料尽量全量 | ✅ policy 7 · media 154（API total） |
| schema v1.1 | ✅ |
| 三信号不可相加 | ✅ UI note + footer |
| ≤719px | ✅ media queries |
| 不改壳层 nav 以外 | ✅ |
| curl+UA | ✅ rebuild |
| 勿推 GitHub | ✅ 未推 |

## 路径

- 站内：`/workspace/data-dashboard/policy/{index.html,snapshot.json,README.md,SCHEMA.md}`
- 镜像：`/workspace/policy/{index.html,snapshot.json,rebuild_snapshot.py,SCHEMA.md,DELIVERY-CHECKLIST.md}`
- 原站截图：`/workspace/policy/ref-screens/`
- 产品参考：https://gendangzou.mobiusquant.ai/

## 截面数字

- asOf **2026-10-22** · snapshotId **906027050724dd486f7b**
- fetchedAt **2026-10-23T17:00:24+08:00**（Asia/Shanghai）
- sectors **78** · dynamics **23** · drilldown **28**
- heat Top20×3 · rt windows 6h/24h/3d · snapshots list 15
- securities changes **1** · coverage etfCount 1259 · companyRelations 19786 · taxonomyNodes 82

## 已知简化

- 三维空间定位：API 无现成坐标 → 仅二维散点 + UI 注明「三维略」
- 历史截面不可整包切换（仅列表钉住 latest）
- drilldown companies/etfs 仅首页（防 ETF 海量分页）
- 官网 /app /daily 营销页忽略
