import re
#!/usr/bin/env python3
"""刷新 earnings/data/earnings.json —— 数据源：Yahoo Finance(yfinance) + Nasdaq/Zacks 财报日期接口。
用法: python refresh_earnings.py [--out ../data/earnings.json]
仅写入接口返回的真实数据；取不到的字段为 null（页面显示“暂无”）。"""
import json, sys, datetime as dt, time, math, urllib.request, argparse, os
import yfinance as yf
TZ = dt.timezone(dt.timedelta(hours=8))
COS = [
 ("AAPL","苹果","US","AAPL"),("MSFT","微软","US","MSFT"),("GOOGL","谷歌(Alphabet)","US","GOOGL"),
 ("AMZN","亚马逊","US","AMZN"),("META","Meta","US","META"),("NVDA","英伟达","US","NVDA"),
 ("TSLA","特斯拉","US","TSLA"),("TSM","台积电(ADR)","TW","TSM"),("AMD","AMD","US","AMD"),
 ("AVGO","博通","US","AVGO"),("0700.HK","腾讯控股","CN",None),("BABA","阿里巴巴(ADR)","CN","BABA"),
 ("BIDU","百度(ADR)","CN","BIDU"),("JD","京东(ADR)","CN","JD"),("3690.HK","美团","CN",None),
 ("PDD","拼多多","CN","PDD"),("1810.HK","小米集团","CN",None),("NTES","网易(ADR)","CN","NTES"),
 ("0981.HK","中芯国际","CN",None),("1211.HK","比亚迪股份","CN",None),
]
UA = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124 Safari/537.36","Accept":"application/json"}
def nasdaq(sym):
    try:
        r = urllib.request.urlopen(urllib.request.Request(f"https://api.nasdaq.com/api/analyst/{sym}/earnings-date", headers=UA), timeout=20)
        d = json.load(r)["data"]; return d.get("reportText")
    except Exception as e: return None
def num(v):
    try:
        v=float(v); return None if math.isnan(v) else v
    except Exception: return None
def row(df, key, col):
    try: return num(df.loc[key, col])
    except Exception: return None
def get(sym, name, region, nq):
    t = yf.Ticker(sym); o = {"symbol":sym,"name":name,"region":region}
    info = {}
    try: info = t.info
    except Exception: pass
    o["currency"] = info.get("financialCurrency") or info.get("currency")
    ts = info.get("earningsTimestamp") or info.get("earningsTimestampStart")
    if ts: o["nextDate"] = dt.datetime.fromtimestamp(ts, TZ).isoformat()
    else:
        try: o["nextDate"] = str(t.calendar.get("Earnings Date")[0])
        except Exception: o["nextDate"] = None
    est = info.get("isEarningsDateEstimate")
    o["dateStatus"] = None if est is None else ("estimated" if est else "confirmed")
    o["nasdaqText"] = nasdaq(nq) if nq else None
    if o["nasdaqText"] and "expected*" in o["nasdaqText"] and o["dateStatus"] is None: o["dateStatus"]="estimated"
    cons = {}
    try:
        ee=t.earnings_estimate; re_=t.revenue_estimate
        cons = {"epsAvg":row(ee,"0q","avg"),"epsLow":row(ee,"0q","low"),"epsHigh":row(ee,"0q","high"),
                "epsAnalysts":row(ee,"0q","numberOfAnalysts"),"epsYearAgo":row(ee,"0q","yearAgoEps"),
                "revAvg":row(re_,"0q","avg"),"revLow":row(re_,"0q","low"),"revHigh":row(re_,"0q","high"),
                "revAnalysts":row(re_,"0q","numberOfAnalysts"),"revGrowth":row(re_,"0q","growth"),
                "currency": (re_.loc["0q","currency"] if "currency" in re_.columns else None)}
    except Exception: pass
    o["consensus"]=cons
    # 最近已发布季度：EPS 实际 vs 预期（Yahoo earnings_history）+ 利润表
    last = None
    try:
        eh = t.earnings_history.dropna(subset=["epsActual"])
        q = eh.index[-1]; r = eh.iloc[-1]
        last = {"quarterEnd":str(q)[:10],"epsActual":num(r.epsActual),"epsEstimate":num(r.epsEstimate),"epsSurprisePct":num(r.surprisePercent)}
    except Exception: pass
    try:
        qi = t.quarterly_income_stmt
        cols = sorted(qi.columns, reverse=True); c0 = cols[0]
        prev = [c for c in cols if abs((c0 - c).days - 365) < 20]
        rev = row(qi,"Total Revenue",c0); ni = row(qi,"Net Income",c0)
        lr = last or {"quarterEnd":str(c0)[:10]}
        if str(c0)[:10][:7] == lr["quarterEnd"][:7]:
            lr["revenue"]=rev; lr["netIncome"]=ni
            if prev:
                pr=row(qi,"Total Revenue",prev[0]); pn=row(qi,"Net Income",prev[0])
                lr["revenueYoY"]= (rev/pr-1) if rev and pr else None
                lr["netIncomeYoY"]= (ni/pn-1) if ni and pn and pn>0 else None
        last = lr
    except Exception: pass
    try:
        ed = t.get_earnings_dates(limit=8)
        past = ed[ed["Reported EPS"].notna()]
        if len(past) and last: last["reportDate"]=past.index[0].tz_convert(TZ).isoformat()
    except Exception: pass
    o["lastReported"]=last
    return o
if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--out",default=os.path.join(os.path.dirname(__file__),"..","data","earnings.json")); a=ap.parse_args()
    old={}
    if os.path.exists(a.out):
        try: old={c["symbol"]:c for c in json.load(open(a.out))["companies"]}
        except Exception: pass
    out=[]
    for s,n,r,nq in COS:
        try: c=get(s,n,r,nq)
        except Exception as e: c={"symbol":s,"name":n,"region":r,"error":str(e)}
        # 保留人工补充字段（指引、备注、手工核对的实际数）
        for k in ("guidance","note","manual"):
            if k in old.get(s,{}): c[k]=old[s][k]
        nd=c.get("nextDate")
        if nd and dt.datetime.fromisoformat(nd if "T" in nd else nd+"T23:59:00+08:00")<dt.datetime.now(TZ):
            m=re.search(r"(\d\d)/(\d\d)/(\d{4})",c.get("nasdaqText") or "")
            if m: c["nextDate"]=f"{m[3]}-{m[1]}-{m[2]}"; c["dateStatus"]="estimated"; c["dateSource"]="Nasdaq/Zacks 算法预估"
            else: c["nextDate"]=None; c["dateStatus"]="unknown"
        if s=="3690.HK" and (c.get("lastReported") or {}).get("reportDate","")[:4]<"2026": c["lastReported"]=None
        out.append(c); print(s, c.get("nextDate"), c.get("dateStatus")); time.sleep(0.5)
    now=dt.datetime.now(TZ).isoformat(timespec="seconds")
    json.dump({"schema":"earnings-v1","updated":now,"consensusSource":"Yahoo Finance 分析师一致预期（底层为 LSEG/Refinitiv 等汇总）；美股日期另参 Nasdaq/Zacks","consensusAsOf":now[:10],"companies":out},open(a.out,"w"),ensure_ascii=False,indent=1)
