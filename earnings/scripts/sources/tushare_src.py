"""Tushare Pro 适配器（A 股 + 国内宏观）。
仅在 co['ashare'] 有值时拉财报字段；港股/美股不调用（api_scope_denied）。
失败走 /workspace/tushare/fallback.py 粘性降级，不抛异常、不阻塞刷新。"""
from __future__ import annotations
import datetime as dt, math, os, sys, statistics
from .base import Adapter as A, TZ, stamp

_TS_ROOT = "/workspace/tushare"
if _TS_ROOT not in sys.path:
    sys.path.insert(0, _TS_ROOT)

def _fb():
    try:
        import fallback as fb  # type: ignore
        return fb
    except Exception as e:
        print("[tushare_src] fallback import failed:", e, flush=True)
        return None

def _num(v):
    try:
        if v is None: return None
        v = float(v)
        return None if math.isnan(v) else v
    except Exception:
        return None

def _ymd(s):
    if not s: return None
    s = str(s).replace("-", "")[:8]
    if len(s) < 8: return None
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}"

def _iso_date(s):
    d = _ymd(s)
    return d  # date-only; refresh treats date-only as end-of-day BJ

class Adapter(A):
    name = "tushare_src"

    def __init__(self):
        self.fb = _fb()
        self.available = self.fb is not None
        self._api_ok = {}   # api -> True/False/None
        self._api_err = {}

    def src(self, api, extra=""):
        return stamp(f"Tushare {api}{extra}", "https://tushare.pro/document/2")

    def call(self, api, **kw):
        if not self.available or self.fb is None: return None
        if self.fb.is_sticky_failed():
            self._api_err[api] = self.fb.last_error() or "sticky fail"
            self._api_ok[api] = False
            return None
        df = self.fb.call(api, **kw)
        if df is None:
            self._api_ok[api] = False
            self._api_err[api] = self.fb.last_error() or "None"
            return None
        self._api_ok[api] = True
        return df

    def status(self):
        return {"ok": {k: v for k, v in self._api_ok.items()}, "err": dict(self._api_err),
                "sticky": bool(self.fb and self.fb.is_sticky_failed()),
                "last": (self.fb.last_error() if self.fb else "")}

    # ---- earnings ----
    def next_date(self, co):
        code = co.get("ashare")
        if not code: return None
        today = dt.date.today()
        # end_date 过滤报告期；取未来计划披露日
        df = self.call("disclosure_date", ts_code=code, start_date=f"{today.year}0101", end_date=f"{today.year+1}1231")
        if df is None or getattr(df, "empty", True): return None
        best = None
        for _, r in df.iterrows():
            for col, status in (("actual_date", "confirmed"), ("pre_date", "confirmed")):
                d = _ymd(r.get(col))
                if not d: continue
                dd = dt.date.fromisoformat(d)
                if dd < today: continue
                if best is None or dd < best[0]:
                    best = (dd, status, r.get("end_date"))
        if not best: return None
        return {"nextDate": best[0].isoformat(), "dateStatus": best[1],
                "currency": "CNY",
                "_src": self.src("disclosure_date", f" {code}")}

    def last_reported(self, co):
        code = co.get("ashare")
        if not code: return None
        # 1) 单季合并利润表
        out = self._from_income(code)
        # 2) 快报补空 / 更新更近报告期
        ex = self._from_express(code)
        if ex:
            if not out or (ex.get("quarterEnd") or "") > (out.get("quarterEnd") or ""):
                out = ex
            else:
                for k, v in ex.items():
                    if k == "_src": continue
                    if out.get(k) is None and v is not None: out[k] = v
        # 3) 财务指标补 EPS
        fi = self._from_fina(code, (out or {}).get("quarterEnd"))
        if fi and out:
            for k, v in fi.items():
                if k == "_src": continue
                if out.get(k) is None and v is not None: out[k] = v
        # 4) 业绩预告 → guidance 备注（不作为实际数）
        fc = self._from_forecast(code)
        if fc and out:
            out.setdefault("note", fc)
        elif fc:
            out = {"note": fc, "quarterEnd": None, "_src": self.src("forecast", f" {code}")}
        return out

    PERIODS = ("20260930", "20260630")  # 只取 2026 最新报告期；旧报告期不写入

    def _from_income(self, code):
        for per in self.PERIODS:
            df = self.call("income", ts_code=code, period=per, report_type="1")
            if df is None: return None  # 失败 → 交给下游，不再重试
            if getattr(df, "empty", True): continue
            df = df.sort_values("f_ann_date", ascending=False)
            r = df.iloc[0]
            rev = _num(r.get("total_revenue")) or _num(r.get("revenue"))
            ni = _num(r.get("n_income_attr_p"))
            eps = _num(r.get("diluted_eps")) or _num(r.get("basic_eps"))
            out = {"quarterEnd": _ymd(r.get("end_date")), "reportDate": _ymd(r.get("f_ann_date") or r.get("ann_date")),
                   "revenue": rev, "netIncome": ni, "epsActual": eps, "epsGaap": eps,
                   "epsGaapBasis": "A股合并报表累计口径摊薄 EPS（Tushare income report_type=1，年初至报告期末）",
                   "netIncomeBasis": "归母净利润（累计）", "currency": "CNY",
                   "_src": self.src("income", f" {code} {per}")}
            fi = self.call("fina_indicator", ts_code=code, period=per)
            if fi is not None and not getattr(fi, "empty", True):
                f = fi.iloc[0]
                tr = _num(f.get("tr_yoy")); np_ = _num(f.get("netprofit_yoy"))
                if tr is not None: out["revenueYoY"] = tr / 100
                if np_ is not None: out["netIncomeYoY"] = np_ / 100
            return out
        return None

    def _from_express(self, code):
        df = self.call("express", ts_code=code, start_date="20250101", end_date="20261231")
        if df is None or getattr(df, "empty", True): return None
        df = df.sort_values("end_date", ascending=False)
        r = df.iloc[0]
        rev = _num(r.get("revenue")); ni = _num(r.get("n_income")); eps = _num(r.get("diluted_eps"))
        yoy_s = _num(r.get("yoy_sales")); yoy_n = _num(r.get("yoy_dedu_np"))
        out = {"quarterEnd": _ymd(r.get("end_date")), "reportDate": _ymd(r.get("ann_date")),
               "revenue": rev, "netIncome": ni, "epsActual": eps, "epsGaap": eps,
               "epsGaapBasis": "A股业绩快报摊薄 EPS（Tushare express）",
               "revenueYoY": (yoy_s / 100.0) if yoy_s is not None else None,
               "netIncomeYoY": (yoy_n / 100.0) if yoy_n is not None else None,
               "note": "来源：业绩快报（未经审计）",
               "currency": "CNY",
               "_src": self.src("express", f" {code}")}
        return out

    def _from_fina(self, code, qe):
        df = self.call("fina_indicator", ts_code=code, start_date="20240101", end_date="20261231")
        if df is None or getattr(df, "empty", True): return None
        df = df.sort_values("end_date", ascending=False)
        if qe:
            key = qe.replace("-", "")
            hit = df[df["end_date"].astype(str).str.replace("-", "").str[:8] == key]
            r = hit.iloc[0] if len(hit) else df.iloc[0]
        else:
            r = df.iloc[0]
        eps = _num(r.get("dt_eps")) or _num(r.get("eps"))
        return {"epsActual": eps, "epsGaap": eps,
                "epsGaapBasis": "A股财务指标 EPS（Tushare fina_indicator）",
                "_src": self.src("fina_indicator", f" {code}")}

    def _from_forecast(self, code):
        df = self.call("forecast", ts_code=code, start_date="20250101", end_date="20261231")
        if df is None or getattr(df, "empty", True): return None
        df = df.sort_values("ann_date", ascending=False)
        r = df.iloc[0]
        parts = [f"业绩预告({_ymd(r.get('end_date'))})", str(r.get("type") or "")]
        if r.get("p_change_min") == r.get("p_change_min") and r.get("p_change_min") is not None:
            parts.append(f"净利变动 {r.get('p_change_min')}%~{r.get('p_change_max')}%")
        if r.get("summary"): parts.append(str(r.get("summary"))[:120])
        return "；".join(p for p in parts if p)

    def consensus(self, co):
        """report_rc → 当年年度盈利预测汇总，写入 consensus.ashareAnnual（不碰季度 eps*/rev* 字段）。
        report_rc 单位：np/op_rt 为万元；quarter 形如 2026Q4 表示年度预测。同一机构取最新一篇。"""
        code = co.get("ashare")
        if not code: return None
        today = dt.date.today()
        start = (today - dt.timedelta(days=90)).strftime("%Y%m%d")
        df = self.call("report_rc", ts_code=code, start_date=start, end_date=today.strftime("%Y%m%d"))
        if df is None or getattr(df, "empty", True): return None
        target = f"{today.year}Q4"
        sub = df[df["quarter"].astype(str).str.upper() == target]
        if getattr(sub, "empty", True): return None
        sub = sub.sort_values("report_date", ascending=False).drop_duplicates("org_name")
        def agg(col, mul=1.0):
            v = [_num(x) for x in sub[col].tolist()] if col in sub.columns else []
            v = [x * mul for x in v if x is not None]
            if not v: return None
            return {"avg": round(statistics.mean(v), 4), "high": max(v), "low": min(v), "n": len(v)}
        eps = agg("eps"); np_ = agg("np", 1e4); rev = agg("op_rt", 1e4)
        if not eps and not np_: return None
        asof = _ymd(sub["report_date"].astype(str).max())
        return {"ashareAnnual": {"fiscalYear": today.year, "basis": "年度预测（非季度）",
                                 "eps": eps, "netProfit": np_, "revenue": rev,
                                 "orgs": int(sub["org_name"].nunique()), "window": f"{_ymd(start)}~{today.isoformat()}",
                                 "source": f"Tushare report_rc {code}", "asOf": asof, "unit": "CNY（np/op_rt 万元×1e4）"},
                "_src": self.src("report_rc", f" {code} {target}")}

    # ---- macro helpers (used by refresh_macro) ----
    def macro_series(self, api, **kw):
        df = self.call(api, **kw)
        if df is None or getattr(df, "empty", True): return None
        return df
