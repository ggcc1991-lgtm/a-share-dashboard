const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const P = require("../assets/present.js");

const root = path.join(__dirname, "..");

test("missing stays missing and zero stays zero", () => {
  for (const v of [null, undefined, "", "  ", NaN, Infinity, false]) {
    assert.equal(P.isMissing(v), true, String(v));
    assert.equal(P.formatNum(v, 2), "—");
    assert.equal(P.formatSigned(v, 1), "—");
    assert.equal(P.toFinite(v), null);
  }
  assert.equal(P.isMissing(0), false);
  assert.equal(P.formatNum(0, 2), "0");
  assert.equal(P.formatSigned(0, 1), "0");
  assert.equal(P.toFinite(0), 0);
  assert.equal(P.formatSigned(1.5, 1), "+1.5");
  assert.equal(P.formatSigned(-2, 0), "-2");
});

test("Shanghai formatting does not treat a fetch as an update", () => {
  assert.equal(P.formatShanghai("2026-11-23T15:28:48+08:00"), "2026-11-23 15:28");
  assert.equal(P.formatShanghai("2026-11-23T22:23:29.284012+08:00"), "2026-11-23 22:23");
  assert.equal(P.formatShanghai("2026-11-23 22:23:29"), "2026-11-23 22:23");
  assert.equal(P.formatShanghai("2026-11-23T07:28:48Z"), "2026-11-23 15:28");
  assert.equal(P.formatShanghai(""), "");
  assert.equal(P.formatShanghai(null), "");
});

test("flow sum skips nulls and does not invent a zero day", () => {
  const series = {
    a: { flow: [1, null, 0] },
    b: { flow: [null, null, 2] },
    c: { flow: ["", undefined, 0] },
  };
  assert.equal(P.sumNamedSeries(series, "flow", 0), 1);
  assert.equal(P.sumNamedSeries(series, "flow", 1), null);
  assert.equal(P.sumNamedSeries(series, "flow", 2), 2);
  assert.equal(P.sumNamedSeries(null, "flow", 0), null);
});

test("chart defaults confine tooltips and stop motion without touching series values", () => {
  const option = {
    animation: true,
    tooltip: { trigger: "axis" },
    series: [{ type: "line", data: [null, 0, 6, 9], detail: { valueAnimation: true } }],
  };
  P.applyChartDefaults(option, true);
  assert.equal(option.animation, false);
  assert.equal(option.series[0].animation, false);
  assert.equal(option.series[0].detail.valueAnimation, false);
  assert.equal(option.tooltip.confine, true);
  assert.deepEqual(option.series[0].data, [null, 0, 6, 9]);
  const keep = {
    animation: true,
    tooltip: { trigger: "item", confine: false },
    series: [{ type: "gauge", data: [9], detail: { valueAnimation: true } }],
  };
  P.applyChartDefaults(keep, false);
  assert.equal(keep.tooltip.confine, false);
  assert.equal(keep.animation, true);
  assert.equal(keep.series[0].detail.valueAnimation, true);
  assert.equal(keep.series[0].animation, undefined);
});

test("bottom signal copy uses four count tiers and does not rank win rate", () => {
  const cases = [
    [0, "信号较少", "信号较少（0/12项触发）"],
    [5, "信号较少", "信号较少（5/12项触发）"],
    [6, "信号增多", "信号增多（6/12项触发）"],
    [8, "信号增多", "信号增多（8/12项触发）"],
    [9, "信号较强", "信号较强（9/12项触发）"],
    [10, "信号高度集中", "信号高度集中（10/12项触发）"],
    [12, "信号高度集中", "信号高度集中（12/12项触发）"],
  ];
  for (const [n, tier, text] of cases) {
    const s = P.bottomSignal(n, 12);
    assert.equal(s.count, n);
    assert.equal(s.total, 12);
    assert.equal(s.tier, tier);
    assert.equal(s.text, text);
  }
  assert.deepEqual(P.bottomSignal(null, 12), { count: null, total: 12, tier: "", text: "—" });
  assert.equal(P.bottomSignal(undefined).text, "—");
  assert.match(P.bottomSignalNote(), /0–5 信号较少/);
  assert.match(P.bottomSignalNote(), /不表示胜率更高/);
  assert.equal(P.neutralSignalNote("作者的具体点位如有可手动覆盖"), "具体点位如有可手动覆盖");
  assert.equal(P.neutralSignalNote("可能与原作者口径不同"), "口径见各指标备注");
  assert.equal(P.neutralSignalNote("空仓阈值2.45万亿"), "空仓阈值2.45万亿");

  const bottom = JSON.parse(fs.readFileSync(path.join(root, "data/bottom.json"), "utf8"));
  assert.equal(bottom.triggered_count, 9);
  assert.equal(bottom.total, 12);
  assert.equal(bottom.as_of, "2026-11-23");
  assert.equal(bottom.verdict.score, 9);
  assert.equal(bottom.verdict.band.headline, "信号较强（9/12项触发）");
  assert.equal(bottom.verdict.band.label, "信号较强");
  assert.equal(bottom.verdict.band.color, "#4c8dff");
  assert.equal(bottom.verdict.band.next, 10);
  assert.equal(bottom.verdict.band.gap_next, 1);
  assert.equal(P.bottomSignal(bottom.triggered_count, bottom.total).text, bottom.verdict.band.headline);
  assert.deepEqual(bottom.strategy.bands.map((b) => [b.min, b.max, b.label]), [
    [0, 5, "信号较少"],
    [6, 8, "信号增多"],
    [9, 9, "信号较强"],
    [10, 12, "信号高度集中"],
  ]);
  const vix = bottom.indicators.find((i) => i.id === "csi1000_vix");
  assert.equal(vix.value, 41.16);
  assert.equal(vix.threshold, 35);
  assert.equal(vix.status, "triggered");
  const margin = bottom.indicators.find((i) => i.id === "margin_balance");
  assert.equal(margin.value, 2.271);
  assert.equal(margin.status, "triggered");
  assert.match(margin.note, /空仓阈值2\.45万亿/);
  const tech = bottom.indicators.find((i) => i.id === "tech_six");
  assert.equal(tech.status, "triggered");
  assert.equal(tech.value, "4/4 回撤≥25%");
  assert.match(tech.note, /12037\.597/);
  assert.doesNotMatch(tech.note, /作者/);
  assert.equal(bottom.indicators.filter((i) => i.status === "triggered").length, 9);
  const voice = JSON.stringify({
    strategy: bottom.strategy,
    band: bottom.verdict.band,
    advice: bottom.verdict.advice,
    risks: bottom.verdict.risks,
    basis: bottom.verdict.basis,
    notes: bottom.verdict.notes,
    summary: bottom.verdict.summary,
  });
  for (const bad of ["作者", "胜率越高", "胜率提高", "高度警戒", "持仓耐心", "空仓可", "出手", "分批", "观望", "抄底区"]) {
    assert.equal(voice.includes(bad), false, bad);
  }

  const home = fs.readFileSync(path.join(root, "index.html"), "utf8");
  const page = fs.readFileSync(path.join(root, "bottom/index.html"), "utf8");
  assert.match(home, /DashPresent\.bottomSignal/);
  assert.match(page, /DashPresent\.bottomSignal/);
  for (const phrase of ["信号较少", "信号增多", "信号较强", "信号高度集中", "项触发"]) {
    assert.match(home, new RegExp(phrase));
  }
  const bandSrc = home.slice(home.indexOf("function band"), home.indexOf("function fmtIndVal"));
  assert.match(bandSrc, /n >= 10 \? "信号高度集中"/);
  assert.match(bandSrc, /n >= 9 \? "信号较强"/);
  assert.match(bandSrc, /n >= 6 \? "信号增多"/);
  assert.match(bandSrc, /: "信号较少"/);
  assert.doesNotMatch(bandSrc, /verdict\?\.band|高度警戒|持仓耐心|空仓可|作者|观望/);
  assert.match(page, /由GC制作/);
  assert.match(page, /2026-01-01/);
  for (const bad of ["高度警戒抄底区", "持仓耐心等", "空仓可考虑", "作者出手", "作者区", "作者偏好"]) {
    assert.equal(home.includes(bad), false, bad);
    assert.equal(page.includes(bad), false, bad);
  }
  assert.doesNotMatch(page, /<h4>空仓<\/h4>|<h4>持仓<\/h4>/);

  for (const rel of ["bottom/full.html", "legacy/index.html"]) {
    const html = fs.readFileSync(path.join(root, rel), "utf8");
    const head = html.slice(0, html.indexOf("const LATEST"));
    const tail = html.slice(html.lastIndexOf("function signalPhrase"));
    assert.match(head, /0–5 信号较少/);
    assert.match(head, /10–12 信号高度集中/);
    assert.match(head, /由GC制作/);
    assert.match(head, /不表示胜率更高/);
    assert.match(tail, /function band\(n\)\{return \[signalPhrase\(n\)/);
    assert.match(tail, /signalPhrase\(V\.score\)/);
    assert.doesNotMatch(tail, /\$\{esc\(B\.label\)\}|V\.advice|操作建议（规则化|高度警戒抄底区|持仓耐心等|空仓可考虑/);
  }
});

test("bottom caveats come from the snapshot and do not change the score", () => {
  const bottom = JSON.parse(fs.readFileSync(path.join(root, "data/bottom.json"), "utf8"));
  const lines = P.bottomCaveats(bottom);
  assert.ok(lines.some((t) => t.includes("代理") && t.includes("QVIX")));
  assert.ok(lines.some((t) => t.includes("融资余额") && t.includes("2026-11-05") && t.includes(bottom.as_of)));
  assert.equal(bottom.triggered_count, 9);
  assert.equal(P.bottomCaveats(null).length, 0);
  assert.equal(P.bottomCaveats({ indicators: [{ id: "margin_balance", name: "融资余额", meta: { date: "2026-11-23" } }], as_of: "2026-11-23" }).length, 0);
});
