/**
 * Shared presentation helpers. Display only: never invents market values.
 * Missing / blank stays missing. A real 0 stays 0.
 */
(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.DashPresent = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function isMissing(v) {
    if (v == null) return true;
    if (typeof v === "boolean") return true;
    if (typeof v === "string" && v.trim() === "") return true;
    if (typeof v === "number" && !Number.isFinite(v)) return true;
    return false;
  }

  function toFinite(v) {
    if (isMissing(v)) return null;
    var n = typeof v === "number" ? v : Number(String(v).trim());
    return Number.isFinite(n) ? n : null;
  }

  function formatNum(v, digits) {
    var n = toFinite(v);
    if (n == null) return "—";
    var d = digits == null ? 2 : digits;
    return n.toLocaleString("zh-CN", { maximumFractionDigits: d, minimumFractionDigits: 0 });
  }

  function formatSigned(v, digits) {
    var n = toFinite(v);
    if (n == null) return "—";
    var d = digits == null ? 2 : digits;
    var s = n > 0 ? "+" : "";
    return s + n.toLocaleString("zh-CN", { maximumFractionDigits: d, minimumFractionDigits: 0 });
  }

  /** Accepts ISO, "YYYY-MM-DD HH:mm", +08, and extra fractional digits. */
  function parseInstant(iso) {
    if (iso == null || iso === "") return null;
    var s = String(iso).trim();
    s = s.replace(/(\.\d{3})\d+/, "$1");
    s = s.replace(/([+-]\d{2})$/, "$1:00");
    var hasZone = /[zZ]$|[+-]\d{2}:\d{2}$/.test(s);
    if (!hasZone && /^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}/.test(s)) s += "+08:00";
    if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}/.test(s)) s = s.replace(" ", "T");
    var d = new Date(s);
    return Number.isNaN(d.getTime()) ? null : d;
  }

  function formatShanghai(iso) {
    var d = parseInstant(iso);
    if (!d) {
      var m = String(iso || "").match(/^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})/);
      return m ? m[1] + " " + m[2] : (iso == null || iso === "" ? "" : String(iso));
    }
    try {
      var parts = new Intl.DateTimeFormat("en-CA", {
        timeZone: "Asia/Shanghai",
        year: "numeric", month: "2-digit", day: "2-digit",
        hour: "2-digit", minute: "2-digit", hour12: false,
      }).formatToParts(d);
      var g = function (t) { return (parts.find(function (x) { return x.type === t; }) || {}).value || ""; };
      var hh = g("hour") === "24" ? "00" : g("hour");
      return g("year") + "-" + g("month") + "-" + g("day") + " " + hh + ":" + g("minute");
    } catch (_) {
      return String(iso);
    }
  }

  /**
   * Sum one named array across series at an index.
   * Null / blank slots are skipped. If every slot is missing, the result is null, not 0.
   */
  function sumNamedSeries(seriesMap, key, index) {
    if (!seriesMap || typeof seriesMap !== "object") return null;
    var s = 0;
    var any = false;
    var rows = Object.keys(seriesMap);
    for (var i = 0; i < rows.length; i++) {
      var row = seriesMap[rows[i]];
      var arr = row && row[key];
      if (!arr) continue;
      var n = toFinite(arr[index]);
      if (n == null) continue;
      s += n;
      any = true;
    }
    return any ? s : null;
  }

  /**
   * Short caveats already present on the snapshot. Does not change thresholds.
   */
  function bottomCaveats(bottom) {
    if (!bottom || !Array.isArray(bottom.indicators)) return [];
    var asOf = bottom.as_of ? String(bottom.as_of) : "";
    var out = [];
    for (var i = 0; i < bottom.indicators.length; i++) {
      var ind = bottom.indicators[i];
      if (!ind) continue;
      var meta = ind.meta || {};
      var name = ind.name || ind.id || "指标";
      if (meta.proxy === true || meta.kind === "atm_iv_proxy") {
        out.push(name + " 为平值期权隐含波动率代理，不是官方 QVIX");
      }
      if (ind.id === "margin_balance" && meta.date && asOf && String(meta.date) !== asOf) {
        out.push(name + " 数据日 " + meta.date + "，截面 " + asOf + "（发布值，未外推）");
      }
    }
    return out;
  }

  /**
   * Chart option defaults. Does not change series data.
   * Reduced motion turns animation off. Tooltips stay inside the plot.
   */
  function applyChartDefaults(option, reduce) {
    if (!option || typeof option !== "object" || Array.isArray(option)) return option;
    if (reduce) {
      option.animation = false;
      option.animationDuration = 0;
      var series = option.series;
      if (series && !Array.isArray(series)) series = [series];
      if (Array.isArray(series)) {
        for (var i = 0; i < series.length; i++) {
          var s = series[i];
          if (!s || typeof s !== "object") continue;
          s.animation = false;
          if (s.detail && typeof s.detail === "object") s.detail.valueAnimation = false;
        }
      }
    }
    var tip = option.tooltip;
    if (tip && typeof tip === "object" && !Array.isArray(tip) && tip.confine == null) tip.confine = true;
    return option;
  }

  return {
    isMissing: isMissing,
    toFinite: toFinite,
    formatNum: formatNum,
    formatSigned: formatSigned,
    parseInstant: parseInstant,
    formatShanghai: formatShanghai,
    sumNamedSeries: sumNamedSeries,
    bottomCaveats: bottomCaveats,
    applyChartDefaults: applyChartDefaults,
  };
});
