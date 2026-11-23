/**
 * Homepage「今年以来信号变化」series.
 *
 * The publisher writes daily red-line counts to data/score_history.json `points`.
 * data/history.json `score` is the legacy copy and may be absent.
 * Only those published points are plotted: gaps stay empty, and the live
 * bottom.json count is never copied onto missing days.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.ScoreSeries = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  var YTD_START = "2026-01-01";
  var EMPTY_LABEL = "待抄底写入 score_history.points";

  function isScorePoint(x) {
    return !!(x && x.d != null && x.v != null && !Number.isNaN(+x.v) && String(x.d) >= YTD_START);
  }

  function normalizeScorePoints(series) {
    if (!Array.isArray(series)) return [];
    var lastByDate = Object.create(null);
    var seen = [];
    for (var i = 0; i < series.length; i++) {
      var x = series[i];
      if (!isScorePoint(x)) continue;
      var d = String(x.d);
      if (!Object.prototype.hasOwnProperty.call(lastByDate, d)) seen.push(d);
      var point = { d: d, v: +x.v };
      if (x.live === true) point.live = true;
      lastByDate[d] = point;
    }
    seen.sort();
    var out = [];
    for (var j = 0; j < seen.length; j++) out.push(lastByDate[seen[j]]);
    return out;
  }

  /**
   * Prefer the published series that still reaches back to the earliest date.
   * When both start together, keep the longer one; ties go to score_history
   * because that file is the one the publisher still refreshes.
   */
  function selectYtdScorePoints(scoreHistory, history) {
    var fromScore = normalizeScorePoints(scoreHistory && scoreHistory.points);
    var fromHist = normalizeScorePoints(history && history.score);
    if (!fromScore.length && !fromHist.length) return { points: [], source: null };
    if (!fromHist.length) return { points: fromScore, source: "score_history.points" };
    if (!fromScore.length) return { points: fromHist, source: "history.score" };
    if (fromHist[0].d < fromScore[0].d) return { points: fromHist, source: "history.score" };
    if (fromScore[0].d < fromHist[0].d || fromScore.length >= fromHist.length) {
      return { points: fromScore, source: "score_history.points" };
    }
    return { points: fromHist, source: "history.score" };
  }

  return {
    YTD_START: YTD_START,
    EMPTY_LABEL: EMPTY_LABEL,
    normalizeScorePoints: normalizeScorePoints,
    selectYtdScorePoints: selectYtdScorePoints,
  };
});
