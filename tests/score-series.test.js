const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { selectYtdScorePoints, normalizeScorePoints, describeScoreSeries, YTD_START } = require("../assets/score-series.js");

const root = path.join(__dirname, "..");

function readJSON(rel) {
  return JSON.parse(fs.readFileSync(path.join(root, rel), "utf8"));
}

/** Independent of selectYtdScorePoints: same published-point rules, for contract checks. */
function expectedPairs(series) {
  if (!Array.isArray(series)) return [];
  const last = new Map();
  const seen = [];
  for (const x of series) {
    if (!x || x.d == null || x.v == null || Number.isNaN(+x.v) || String(x.d) < YTD_START) continue;
    const d = String(x.d);
    if (!last.has(d)) seen.push(d);
    last.set(d, +x.v);
  }
  seen.sort();
  return seen.map((d) => [d, last.get(d)]);
}

function pairs(points) {
  return points.map((p) => [p.d, p.v]);
}

test("current data contract: plot published YTD scores, do not flatten to the live count", () => {
  const scoreHist = readJSON("data/score_history.json");
  const history = readJSON("data/history.json");

  assert.equal(scoreHist.from, "2026-01-01");
  assert.equal(history.from, "2026-01-01");
  assert.equal(typeof scoreHist.generated_at, "string");
  assert.ok(Array.isArray(scoreHist.points) && scoreHist.points.length >= 2);
  assert.ok(String(scoreHist.points[0].d) <= "2026-01-31");
  assert.ok(String(scoreHist.points.at(-1).d) >= "2026-01-01");

  for (const key of ["csi1000_kline", "im_basis", "margin_balance"]) {
    assert.ok(Array.isArray(history[key]) && history[key].length > 0, key);
    assert.ok(String(history[key][0].d) >= "2026-01-01", key);
  }

  const beforeScore = JSON.stringify(scoreHist);
  const beforeHist = JSON.stringify(history);
  const picked = selectYtdScorePoints(scoreHist, history);
  assert.equal(JSON.stringify(scoreHist), beforeScore);
  assert.equal(JSON.stringify(history), beforeHist);

  const sh = expectedPairs(scoreHist.points);
  const hs = expectedPairs(history.score);
  const got = pairs(picked.points);
  const matchSh = JSON.stringify(got) === JSON.stringify(sh);
  const matchHs = JSON.stringify(got) === JSON.stringify(hs);
  assert.ok(matchSh || matchHs, "plotted series must be an unmodified published series");
  assert.equal(picked.source, matchSh ? "score_history.points" : "history.score");
  assert.ok(got.length >= 2);
  assert.ok(got[0][0] >= YTD_START);
  assert.ok(got[0][0] <= "2026-01-31");
  assert.ok(new Set(got.map((p) => p[1])).size > 1, "do not replace history with a flat present score");
  assert.ok(got.some((p) => p[1] !== got.at(-1)[1]));
});

test("homepage wires the spark to score_history and does not paint bottom.json", () => {
  const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
  assert.match(html, /assets\/score-series\.js/);
  assert.match(html, /selectYtdScorePoints/);
  assert.match(html, /data\/score_history\.json/);
  assert.match(html, /data\/history\.json/);
  const start = html.indexOf("async function initScoreSpark");
  const end = html.indexOf("(async () => {", start);
  assert.ok(start > 0 && end > start);
  const spark = html.slice(start, end);
  assert.doesNotMatch(spark, /triggered_count/);
  assert.doesNotMatch(spark, /bottom\.json/);
  assert.match(html, /今年以来信号变化/);
  assert.doesNotMatch(html, /scoreSparkNote/);
  assert.doesNotMatch(html, /describeScoreSeries/);
  assert.match(fs.readFileSync(path.join(root, "bottom/index.html"), "utf8"), /由GC制作/);
});

test("uses score_history.points when history.score is missing", () => {
  const picked = selectYtdScorePoints(
    { points: [{ d: "2026-01-05", v: 0 }, { d: "2026-11-23", v: 9, live: true }] },
    { from: "2026-01-01" }
  );
  assert.equal(picked.source, "score_history.points");
  assert.deepEqual(pairs(picked.points), [["2026-01-05", 0], ["2026-11-23", 9]]);
  assert.equal(picked.points.at(-1).live, true);
});

test("falls back to history.score when score_history is missing or empty", () => {
  const archived = { score: [{ d: "2026-01-05", v: 0 }, { d: "2026-06-01", v: 4 }] };
  for (const scoreHist of [null, undefined, {}, { points: [] }, { points: null }, { points: {} }]) {
    const picked = selectYtdScorePoints(scoreHist, archived);
    assert.equal(picked.source, "history.score");
    assert.deepEqual(pairs(picked.points), [["2026-01-05", 0], ["2026-06-01", 4]]);
  }
});

test("empty and error inputs stay empty", () => {
  for (const args of [
    [null, null],
    [undefined, undefined],
    [{}, {}],
    [{ points: [] }, { score: [] }],
    [{ points: "nope" }, { score: "nope" }],
    [new Error("HTTP 404"), { score: null }],
  ]) {
    const picked = selectYtdScorePoints(args[0], args[1]);
    assert.deepEqual(picked, { points: [], source: null });
  }
});

test("drops invalid points and dates before 2026-01-01 without inventing replacements", () => {
  const picked = selectYtdScorePoints({
    points: [
      null,
      { d: "2025-12-31", v: 9 },
      { d: "2026-01-05", v: null },
      { d: "2026-01-06" },
      { d: "2026-01-07", v: "nope" },
      { d: "2026-01-08", v: 0 },
      { v: 3 },
      { d: "2026-01-09", v: 1 },
    ],
  }, null);
  assert.deepEqual(pairs(picked.points), [["2026-01-08", 0], ["2026-01-09", 1]]);
});

test("does not fill gaps or extend the series with the latest score", () => {
  const picked = selectYtdScorePoints({
    points: [
      { d: "2026-01-05", v: 0 },
      { d: "2026-01-06", v: 2 },
      { d: "2026-11-23", v: 9, live: true },
    ],
  }, {});
  assert.equal(picked.points.length, 3);
  assert.deepEqual(pairs(picked.points), [
    ["2026-01-05", 0],
    ["2026-01-06", 2],
    ["2026-11-23", 9],
  ]);
});

test("a present-only score_history does not hide an earlier history.score archive", () => {
  const picked = selectYtdScorePoints(
    { points: [{ d: "2026-11-23", v: 9, live: true }] },
    { score: [{ d: "2026-01-05", v: 0 }, { d: "2026-06-01", v: 4 }, { d: "2026-11-20", v: 6 }] }
  );
  assert.equal(picked.source, "history.score");
  assert.deepEqual(pairs(picked.points), [
    ["2026-01-05", 0],
    ["2026-06-01", 4],
    ["2026-11-20", 6],
  ]);
});

test("same start keeps the longer published series and its own values", () => {
  const picked = selectYtdScorePoints(
    { points: [{ d: "2026-01-05", v: 0 }, { d: "2026-11-20", v: 6 }, { d: "2026-11-23", v: 9, live: true }] },
    { score: [{ d: "2026-01-05", v: 0 }, { d: "2026-11-20", v: 9 }] }
  );
  assert.equal(picked.source, "score_history.points");
  assert.equal(picked.points.find((p) => p.d === "2026-11-20").v, 6);
  assert.equal(picked.points.at(-1).v, 9);
});

test("same start with a shorter score_history keeps the longer history.score", () => {
  const picked = selectYtdScorePoints(
    { points: [{ d: "2026-01-05", v: 9 }] },
    { score: [{ d: "2026-01-05", v: 0 }, { d: "2026-04-01", v: 2 }, { d: "2026-11-20", v: 6 }] }
  );
  assert.equal(picked.source, "history.score");
  assert.deepEqual(pairs(picked.points), [
    ["2026-01-05", 0],
    ["2026-04-01", 2],
    ["2026-11-20", 6],
  ]);
});

test("describeScoreSeries names the reconstruction and the live point without rewriting values", () => {
  const scoreHist = readJSON("data/score_history.json");
  const text = describeScoreSeries(scoreHist, "score_history.points");
  assert.match(text, /近似重建/);
  assert.match(text, /标为实值的日期 2026-11-23 9/);
  assert.match(text, /不用该实值回填/);
  assert.match(text, /score_history\.points/);
  assert.equal(text.includes("2026-11-20 9"), false);
  const picked = selectYtdScorePoints(scoreHist, readJSON("data/history.json"));
  assert.equal(picked.points.find((p) => p.d === "2026-11-20").v, 6);
  assert.equal(picked.points.at(-1).live, true);
});

test("duplicate dates keep the later published value and sort chronologically", () => {
  const points = normalizeScorePoints([
    { d: "2026-03-02", v: 4 },
    { d: "2026-01-05", v: 1 },
    { d: "2026-01-05", v: 0 },
    { d: "2026-03-02", v: 5, live: true },
  ]);
  assert.deepEqual(pairs(points), [["2026-01-05", 0], ["2026-03-02", 5]]);
  assert.equal(points[1].live, true);
});
