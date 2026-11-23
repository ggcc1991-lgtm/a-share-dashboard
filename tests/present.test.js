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
  const keep = { tooltip: { trigger: "item", confine: false }, series: [{ type: "bar", data: [0] }] };
  P.applyChartDefaults(keep, false);
  assert.equal(keep.tooltip.confine, false);
  assert.equal(keep.animation, undefined);
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
