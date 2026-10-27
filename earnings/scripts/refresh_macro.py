#!/usr/bin/env python3
"""Merge ForexFactory this-week calendar into earnings/data/calendar.json,
then fill CN macro actual/previous from Tushare cn_* (does not clear forecast).
Preserves importance / surprisePct; recomputes surprisePct when both actual & forecast are numeric.
Usage: python3 earnings/scripts/refresh_macro.py"""
from __future__ import annotations
import json, urllib.request, datetime as dt, pathlib, re, sys, math
P = pathlib.Path(__file__).resolve().parents[1] / "data" / "calendar.json"
BJ = dt.timezone(dt.timedelta(hours=8))
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

def parse_num(s):
    if s is None: return None
    if isinstance(s, (int, float)): return float(s)
    t = str(s).strip()
    if not t or t in ("暂无", "-", "—", "None"): return None
    # 3.55万亿 / 1.08万亿 / 198K / +2.9万 / 15.5% / 50.1
    m = re.search(r"([+-]?\d+(?:\.\d+)?)\s*万亿", t)
    if m: return float(m.group(1)) * 1e4  # 统一到「亿」方便比？实际 surprise 用同单位字符串解析更稳
    m = re.search(r"([+-]?\d+(?:\.\d+)?)\s*万(?!亿)", t)
    if m: return float(m.group(1))
    m = re.search(r"([+-]?\d+(?:\.\d+)?)\s*K", t, re.I)
    if m: return float(m.group(1))
    m = re.search(r"([+-]?\d+(?:\.\d+)?)", t.replace(",", ""))
    return float(m.group(1)) if m else None

def fmt_pct(v):
    if v is None or (isinstance(v, float) and math.isnan(v)): return None
    return f"{v:.1f}".rstrip("0").rstrip(".") + "%" if abs(v) < 1000 else str(v)

def surprise(actual_s, forecast_s):
    a, f = parse_num(actual_s), parse_num(forecast_s)
    if a is None or f is None or f == 0: return None
    return round((a - f) / abs(f) * 100, 1)

def verdict_from(actual_s, forecast_s, name=""):
    a, f = parse_num(actual_s), parse_num(forecast_s)
    if a is None or f is None: return None
    # 失业率等「越低越好」
    lower_better = bool(re.search(r"失业|claims|jobless", name, re.I))
    if abs(a - f) < 1e-9: return "符合预期"
    if lower_better:
        return "低于预期" if a < f else "高于预期"
    return "高于预期" if a > f else "低于预期"

# ---- 1) ForexFactory week ----
req = urllib.request.Request("https://nfs.faireconomy.media/ff_calendar_thisweek.json",
                            headers={"User-Agent": "Mozilla/5.0"})
try:
    ev = json.load(urllib.request.urlopen(req, timeout=30))
except Exception as e:
    print("FF fetch failed:", e); ev = []
d = json.load(open(P))
# preserve non-ff items; rebuild ff from feed
macro = [m for m in d["macro"] if not m["id"].startswith("ff-")]
keep = {"USD", "CNY"}
for e in ev:
    if e["country"] not in keep or e["impact"] not in ("High", "Medium"): continue
    t = dt.datetime.fromisoformat(e["date"]).astimezone(BJ)
    mid = "ff-%s-%s" % (e["country"], t.strftime("%Y%m%d%H%M")) + "-" + "".join(c for c in e["title"] if c.isalnum())[:20]
    # keep existing actual/verdict/importance/surprisePct if same id existed
    old = next((x for x in d["macro"] if x["id"] == mid), None)
    item = {"id": mid, "region": "US" if e["country"] == "USD" else "CN", "name": e["title"],
            "releaseAt": t.isoformat(),
            "status": "upcoming" if t > dt.datetime.now(BJ) else "pending",
            "actual": None, "forecast": e.get("forecast") or "暂无",
            "previous": e.get("previous") or "暂无", "verdict": None, "diff": None,
            "impact": e["impact"],
            "source": {"name": "ForexFactory 周历", "url": "https://www.forexfactory.com/calendar"},
            "importance": 3 if e["impact"] == "High" else 1}
    if old:
        for k in ("actual", "verdict", "diff", "surprisePct", "importance", "note", "status"):
            if old.get(k) is not None: item[k] = old[k]
        # if already released keep status
        if old.get("status") == "released": item["status"] = "released"
        if old.get("forecast") and old["forecast"] != "暂无": item["forecast"] = old["forecast"]
    macro.append(item)

# ---- 2) Tushare cn_* fill actual/previous ----
ts_status = {}
try:
    from sources import load
    ts = load("tushare_src")
except Exception as e:
    ts = None; print("tushare_src load failed:", e)

def month_of(item):
    # id cn-cpi-2026-09 / releaseAt
    m = re.search(r"(20\d{2})-?(\d{2})$", item["id"].replace("_", "-"))
    if m: return m.group(1) + m.group(2)
    if item.get("releaseAt"):
        d0 = dt.datetime.fromisoformat(item["releaseAt"])
        # CN data for month M usually released early next month → previous calendar month
        prev = (d0.replace(day=1) - dt.timedelta(days=1))
        return prev.strftime("%Y%m")
    return None

def quarter_of(item):
    m = re.search(r"(20\d{2})-q([1-4])", item["id"], re.I)
    if m: return m.group(1) + "Q" + m.group(2)
    return None

filled = []
if ts and ts.available:
    # cache series
    caches = {}
    def series(api, **kw):
        key = (api, tuple(sorted(kw.items())))
        if key not in caches:
            caches[key] = ts.macro_series(api, **kw)
        return caches[key]

    for item in macro:
        if item.get("region") != "CN": continue
        iid, name = item["id"], item.get("name") or ""
        # 已有 actual 则跳过（不覆盖；也避免无谓消耗 Tushare 配额/触发 IP 粘性）
        if item.get("actual") not in (None, "", "暂无") and item.get("previous") not in (None, "", "暂无"):
            continue
        actual = None; previous = None; api = None; field = None; row_month = None

        if iid.startswith("cn-cpi-") and "PPI" not in name:
            api, field = "cn_cpi", "nt_yoy"; row_month = month_of(item)
            df = series(api, start_m="202501", end_m="202612")
        elif iid.startswith("cn-ppi-") or ("CPI / PPI" in name and iid.startswith("cn-cpi-")):
            # combined CPI/PPI row: skip auto or only fill note; leave as-is for combined
            if "CPI / PPI" in name: continue
            api, field = "cn_ppi", "ppi_yoy"; row_month = month_of(item)
            df = series(api, start_m="202501", end_m="202612")
        elif re.search(r"cn-pmi-\d", iid) and "非制造" not in name:
            api, field = "cn_pmi", "pmi010000"; row_month = month_of(item)
            df = series(api, start_m="202501", end_m="202612")
        elif "nmpmi" in iid or "非制造" in name:
            api, field = "cn_pmi", "pmi020100"; row_month = month_of(item)
            df = series(api, start_m="202501", end_m="202612")
        elif iid.startswith("cn-m2-"):
            api, field = "cn_m", "m2_yoy"; row_month = month_of(item)
            df = series(api, start_m="202501", end_m="202612")
        elif iid.startswith("cn-gdp-"):
            api, field = "cn_gdp", "gdp_yoy"
            df = series(api, start_q="2024Q1", end_q="2026Q4")
            row_month = None
        else:
            continue

        if df is None or getattr(df, "empty", True): continue
        # locate row
        row = None; prev_row = None
        if api == "cn_gdp":
            q = quarter_of(item)
            if not q or "quarter" not in df.columns: continue
            # quarter values like 2026Q3
            hit = df[df["quarter"].astype(str).str.upper() == q.upper()]
            if len(hit):
                row = hit.iloc[0]
                # previous quarter
                try:
                    y = int(q[:4]); n = int(q[-1])
                    pq = f"{y-1}Q4" if n == 1 else f"{y}Q{n-1}"
                    ph = df[df["quarter"].astype(str).str.upper() == pq]
                    if len(ph): prev_row = ph.iloc[0]
                except Exception: pass
        else:
            if not row_month or "month" not in df.columns: continue
            hit = df[df["month"].astype(str).str.replace("-", "").str[:6] == row_month]
            if len(hit):
                row = hit.iloc[0]
                # previous month
                y, m = int(row_month[:4]), int(row_month[4:])
                pm = f"{y-1}12" if m == 1 else f"{y}{m-1:02d}"
                ph = df[df["month"].astype(str).str.replace("-", "").str[:6] == pm]
                if len(ph): prev_row = ph.iloc[0]

        if row is None or field not in row.index: continue
        val = row.get(field)
        if val != val or val is None: continue
        # PMI is index level; others are yoy %
        if api == "cn_pmi":
            actual_s = f"{float(val):.1f}".rstrip("0").rstrip(".")
            prev_s = (f"{float(prev_row.get(field)):.1f}".rstrip("0").rstrip(".") if prev_row is not None and prev_row.get(field) == prev_row.get(field) else None)
        else:
            actual_s = fmt_pct(float(val))
            prev_s = fmt_pct(float(prev_row.get(field))) if prev_row is not None and prev_row.get(field) == prev_row.get(field) else None

        # only fill empty actual; never clear forecast
        changed = False
        if item.get("actual") in (None, "", "暂无"):
            item["actual"] = actual_s; changed = True
        if prev_s and item.get("previous") in (None, "", "暂无"):
            item["previous"] = prev_s; changed = True
        if item.get("actual") not in (None, "", "暂无") and item.get("status") in ("pending", "upcoming"):
            # if releaseAt passed → released
            try:
                if item.get("releaseAt") and dt.datetime.fromisoformat(item["releaseAt"]) <= dt.datetime.now(BJ):
                    item["status"] = "released"; changed = True
            except Exception: pass
        # surprise / verdict / diff — only if missing
        if item.get("surprisePct") is None:
            sp = surprise(item.get("actual"), item.get("forecast"))
            if sp is not None: item["surprisePct"] = sp; changed = True
        if not item.get("verdict"):
            v = verdict_from(item.get("actual"), item.get("forecast"), name)
            if v: item["verdict"] = v; changed = True
        if not item.get("diff"):
            a, f = parse_num(item.get("actual")), parse_num(item.get("forecast"))
            if a is not None and f is not None:
                item["diff"] = f"{a-f:+.1f}" + ("pp" if (item.get("forecast") or "").endswith("%") or (item.get("actual") or "").endswith("%") else "")
                changed = True
        # annotate source without wiping existing forecast source name entirely — append note
        src = item.get("source") or {}
        item["source"] = {"name": (src.get("name") or "") + (" / Tushare " + api if "Tushare" not in (src.get("name") or "") else ""),
                          "url": src.get("url") or "https://tushare.pro/document/2"}
        if changed: filled.append(iid)

    try: ts_status = ts.status()
    except Exception: pass
else:
    print("tushare unavailable, skip macro fill")

d["macro"] = macro
d["updated"] = dt.datetime.now(BJ).isoformat(timespec="seconds")
json.dump(d, open(P, "w"), ensure_ascii=False, indent=1)
print("macro items", len(macro), "tushare_filled", filled, "ts_status", ts_status)
