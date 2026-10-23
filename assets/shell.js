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
      if (m === "/" && /(?:^|\/)(index\.html)?$/.test(path.split("/").pop() || "") && !path.includes("/etf") && !path.includes("/feed") && !path.includes("/bottom") && !path.includes("/policy")) {
        a.classList.add("active");
      }
    } catch (_) {}
  });
})();

window.DashTheme = {
  echartsDark: {
    backgroundColor: "transparent",
    textStyle: { color: "#a0a0a0" },
    title: { textStyle: { color: "#e8e8e8" } },
    legend: { textStyle: { color: "#a0a0a0" } },
    categoryAxis: {
      axisLine: { lineStyle: { color: "#2b2b2b" } },
      axisLabel: { color: "#a0a0a0" },
      splitLine: { lineStyle: { color: "#1a1a1a" } },
    },
    valueAxis: {
      axisLine: { lineStyle: { color: "#2b2b2b" } },
      axisLabel: { color: "#a0a0a0" },
      splitLine: { lineStyle: { color: "#1a1a1a" } },
    },
  },
  // A股涨红跌绿 + 琥珀强调
  colors: ["#ffa028", "#ef5350", "#26a69a", "#ffb74d", "#64b5f6", "#a0a0a0"],
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
  if (!header) return;
  const onScroll = () => header.classList.toggle("is-scrolled", window.scrollY > 4);
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });
})();


window.DashMotion = {
  countTo(el, target, { duration = 700, decimals = 0, prefix = "", suffix = "" } = {}) {
    if (!el || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      if (el) el.textContent = prefix + target + suffix;
      return;
    }
    const start = performance.now();
    const from = 0;
    const to = Number(target);
    if (!Number.isFinite(to)) { el.textContent = prefix + target + suffix; return; }
    el.classList.add("is-counting");
    const tick = (now) => {
      const p = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      const v = from + (to - from) * eased;
      el.textContent = prefix + v.toLocaleString("zh-CN", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      }) + suffix;
      if (p < 1) requestAnimationFrame(tick);
      else el.classList.remove("is-counting");
    };
    requestAnimationFrame(tick);
  },
};


/* == page transitions fallback ==
   View Transitions handle MPA nav when supported; this covers the rest.
*/
(function pageTransitions() {
  const reduceMq = window.matchMedia("(prefers-reduced-motion: reduce)");
  const supportsVT = "startViewTransition" in document;
  const html = document.documentElement;
  const DURATION_MS = 180;

  function preferMotion() {
    return !reduceMq.matches;
  }

  function clearPageClasses() {
    html.classList.remove("bb-page-enter", "bb-page-leave");
  }

  window.addEventListener("pageshow", clearPageClasses);

  // Enter: brief fade-in when VT is unavailable
  if (preferMotion() && !supportsVT) {
    html.classList.add("bb-page-enter");
    const done = () => html.classList.remove("bb-page-enter");
    const onEnd = (e) => {
      if (e.target !== html) return;
      html.removeEventListener("animationend", onEnd);
      done();
    };
    html.addEventListener("animationend", onEnd);
    setTimeout(done, DURATION_MS + 80);
  }

  // Leave: intercept same-origin in-site links when VT unavailable
  if (supportsVT) return;

  document.addEventListener(
    "click",
    (e) => {
      if (!preferMotion()) return;
      if (e.defaultPrevented || e.button !== 0) return;
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;

      const a = e.target.closest && e.target.closest("a[href]");
      if (!a) return;
      if (a.target === "_blank" || a.hasAttribute("download")) return;

      const raw = a.getAttribute("href");
      if (!raw || raw.startsWith("javascript:")) return;
      // hash-only / in-page
      if (raw.charAt(0) === "#") return;

      let url;
      try {
        url = new URL(raw, location.href);
      } catch (_) {
        return;
      }
      if (url.origin !== location.origin) return;
      if (
        url.pathname === location.pathname &&
        url.search === location.search &&
        url.hash !== ""
      ) {
        return;
      }
      if (url.href === location.href) return;

      e.preventDefault();
      if (html.classList.contains("bb-page-leave")) return;
      html.classList.add("bb-page-leave");

      let navigated = false;
      const go = () => {
        if (navigated) return;
        navigated = true;
        location.href = url.href;
      };
      const timer = setTimeout(go, DURATION_MS);
      const onEnd = (ev) => {
        if (ev.target !== html) return;
        html.removeEventListener("animationend", onEnd);
        clearTimeout(timer);
        go();
      };
      html.addEventListener("animationend", onEnd);
    },
    true
  );
})();
