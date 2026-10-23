(function () {
  const path = location.pathname.replace(/\/+$/, "") || "/";
  document.querySelectorAll(".nav a[data-match]").forEach((a) => {
    const m = a.getAttribute("data-match");
    if (m === "/" && (path.endsWith("/data-dashboard") || path.endsWith("index.html") || /\/data-dashboard\/?$/.test(path) || path === "" || path === "/")) {
      // handled below
    }
    const href = a.getAttribute("href");
    try {
      const u = new URL(href, location.href);
      const p = u.pathname.replace(/\/+$/, "") || "/";
      if (p === path || (m !== "/" && path.endsWith(m))) a.classList.add("active");
      if (m === "/" && /(?:^|\/)(index\.html)?$/.test(path.split("/").pop() || "") && !path.includes("/etf") && !path.includes("/feed") && !path.includes("/bottom")) {
        a.classList.add("active");
      }
    } catch (_) {}
  });
})();

window.DashTheme = {
  echartsDark: {
    backgroundColor: "transparent",
    textStyle: { color: "#8b9bb4" },
    title: { textStyle: { color: "#e6edf7" } },
    legend: { textStyle: { color: "#8b9bb4" } },
    categoryAxis: {
      axisLine: { lineStyle: { color: "#243044" } },
      axisLabel: { color: "#8b9bb4" },
      splitLine: { lineStyle: { color: "#1a2332" } },
    },
    valueAxis: {
      axisLine: { lineStyle: { color: "#243044" } },
      axisLabel: { color: "#8b9bb4" },
      splitLine: { lineStyle: { color: "#1a2332" } },
    },
  },
  colors: ["#3dd6c6", "#4c8dff", "#f5a623", "#ff3b4a", "#a78bfa", "#34d399"],
};

window.DashFmt = {
  num(v, d = 2) {
    if (v == null || Number.isNaN(+v)) return "—";
    return (+v).toLocaleString("zh-CN", { maximumFractionDigits: d, minimumFractionDigits: 0 });
  },
  signed(v, d = 2) {
    if (v == null || Number.isNaN(+v)) return "—";
    const n = +v;
    const s = n > 0 ? "+" : "";
    return s + n.toLocaleString("zh-CN", { maximumFractionDigits: d });
  },
  time(iso) {
    if (!iso) return "";
    try {
      const d = new Date(iso);
      return d.toLocaleString("zh-CN", { hour12: false, timeZone: "Asia/Shanghai" });
    } catch {
      return iso;
    }
  },
};


(function motion() {
  const header = document.querySelector(".app-header");
  if (header) {
    const onScroll = () => header.classList.toggle("is-scrolled", window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }
  // re-trigger entrance for nodes injected after load
  const io = ("IntersectionObserver" in window)
    ? new IntersectionObserver((entries) => {
        entries.forEach((en) => {
          if (en.isIntersecting) {
            en.target.classList.add("dash-inview");
            io.unobserve(en.target);
          }
        });
      }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 })
    : null;
  const watch = (root) => {
    if (!io) return;
    root.querySelectorAll(".card, .panel, .feed-item, .chart, .holder, .headline-list a").forEach((el) => io.observe(el));
  };
  watch(document);
  const mo = new MutationObserver((muts) => {
    muts.forEach((m) => m.addedNodes.forEach((n) => {
      if (n.nodeType === 1) watch(n);
    }));
  });
  mo.observe(document.body, { childList: true, subtree: true });
})();
