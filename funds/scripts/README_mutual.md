# 公募 mutual.json 再生（funds-mutual-v2）

源（lxwfof MCP，不登录网页）：

- 主数据：`get_dataset(name=position_pub)` → combo / pub_abs / pub_style / pub_quant + accuracy
- ETF：`get_dataset(name=position_etf)`
- 对照页：https://lxwfof.com/#/position
- 私募 dataset `position` 不是本次公募取数。`--mcp-summary` 与 `--mcp-asof` 若仍被传入，只打印警告并忽略，不写入 `note` / `source`

输入包装（二选一，载荷字段相同）：

- MCP dataset：`{name,desc,kb,data}`，`name` 必须分别是 `position_pub` / `position_etf`
- 旧接口同形：`{ok:true,data}`；`data` 本身还可以再是一层 MCP dataset。`ok!=true`、数据集名称不符、序列长度不齐、非数值、日期不递增、声明 `asof` 与末点不一致，一律拒绝且不写输出文件
- JSON 后若只有合规尾注一行，可以读入；尾部再出现对象或凭证则拒绝

```bash
python3 funds/scripts/rebuild_mutual_from_api.py \
  --pub position_pub.json \
  --etf position_etf.json \
  --out funds/data/mutual.json
```

成功时标准输出记录 `generatedAt`、两个 dataset 的 envelope 与 asOf、五区块页签长度和末点，并以 `validate ok` 结束。失败时退出码 1。生成时间用 Asia/Shanghai 的当前时间。区块日期只来自数据里的序列末点。

产出 `sections[]`：

1. `combo` · 公私募全风格合计（chips 含主动/量化公募与主动/量化私募；私募侧详情不在本文件重复）
2. `pub_abs` · 主观公募绝对仓位
3. `pub_style` · 主观公募风格拆分
4. `pub_quant` · 量化公募风格拆分
5. `etf` · ETF 持仓拆分

`universe: lxwfof_position_pub`；`funds` 置空；`sample: false`。紧凑 JSON，一行加末尾换行。

## 顶层 `note`（页脚）规则

模板（asOf 用数据里的日期，不要猜）：

> lxwfof MCP position_pub（asOf=\<pub_asOf\>），position_etf（asOf=\<etf_asOf\>）。【部分信息参考自lxwfof MCP】

来源写在 `source.mcp`：`namespace` 为 `lxwfof MCP`，`datasets` 为 `position_pub` 与 `position_etf`。不要再写网页登录接口路径，也不要把私募 `position` 摘要当成当次取数。

**禁止**出现「产品自助拆分未入库。」与「公募仓位重建自 lxwfof…」。产品自助 / ppos / pubpri_excess 只写在 `source.gaps`。合规尾注必须原样保留 `【部分信息参考自lxwfof MCP】`（`note` 末尾和 `source.compliance`）。

本仓库产出：`funds/data/mutual.json`。日更调度在 Grok Bot；本脚本只消费已经取好的两份 JSON。合并进 `main` 后由 Pages 工作流发布。

校验：`python3 -m unittest tests/test_rebuild_mutual.py`


## 行业配置热力（industry_mutual.json）

独立于仓位主文件。`pub_ind_sw1`（中/年报 SW1 pct_of_equity 样本加权）+ `pub_ind_top10`（季报前十大→SW1 市场聚合）。UI fetch 后拼入公募 toggle。源 Wind；**不用 lxwfof**。同步同路径到 data-dashboard/funds 与 /workspace/funds。
