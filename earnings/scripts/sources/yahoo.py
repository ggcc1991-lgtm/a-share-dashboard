import math, datetime as dt
from .base import Adapter as A, TZ, stamp
def num(v):
    try: v=float(v); return None if math.isnan(v) else v
    except Exception: return None
def row(df,k,c):
    try: return num(df.loc[k,c])
    except Exception: return None
class Adapter(A):
    name="yahoo"
    def __init__(self):
        try: import yfinance as yf; self.yf=yf
        except Exception: self.available=False
        self.cache={}
    def t(self,co):
        s=co["yahoo"]
        if s not in self.cache:
            t=self.yf.Ticker(s)
            try: info=t.info
            except Exception: info={}
            self.cache[s]=(t,info)
        return self.cache[s]
    def src(self,co): return stamp("Yahoo Finance(yfinance)", f"https://finance.yahoo.com/quote/{co['yahoo']}/analysis")
    def next_date(self,co):
        t,info=self.t(co); ts=info.get("earningsTimestamp") or info.get("earningsTimestampStart")
        if not ts: return None
        est=info.get("isEarningsDateEstimate")
        return {"nextDate":dt.datetime.fromtimestamp(ts,TZ).isoformat(),"dateStatus":None if est is None else ("estimated" if est else "confirmed"),
                "currency":info.get("financialCurrency") or info.get("currency"),"_src":self.src(co)}
    def consensus(self,co):
        t,_=self.t(co)
        try:
            ee=t.earnings_estimate; re_=t.revenue_estimate
            return {"epsAvg":row(ee,"0q","avg"),"epsLow":row(ee,"0q","low"),"epsHigh":row(ee,"0q","high"),
              "epsAnalysts":row(ee,"0q","numberOfAnalysts"),"epsYearAgo":row(ee,"0q","yearAgoEps"),
              "revAvg":row(re_,"0q","avg"),"revLow":row(re_,"0q","low"),"revHigh":row(re_,"0q","high"),
              "revAnalysts":row(re_,"0q","numberOfAnalysts"),"revGrowth":row(re_,"0q","growth"),
              "currency":(re_.loc["0q","currency"] if "currency" in re_.columns else None),"_src":self.src(co)}
        except Exception: return None
    def last_reported(self,co):
        t,_=self.t(co); last=None
        try:
            eh=t.earnings_history.dropna(subset=["epsActual"]); q=eh.index[-1]; r=eh.iloc[-1]
            last={"quarterEnd":str(q)[:10],"epsActual":num(r.epsActual),"epsEstimate":num(r.epsEstimate),"epsSurprisePct":num(r.surprisePercent)}
        except Exception: pass
        try:
            qi=t.quarterly_income_stmt; cols=sorted(qi.columns,reverse=True); c0=cols[0]
            prev=[c for c in cols if abs((c0-c).days-365)<20]
            rev=row(qi,"Total Revenue",c0); ni=row(qi,"Net Income",c0); lr=last or {"quarterEnd":str(c0)[:10]}
            if str(c0)[:7]==lr["quarterEnd"][:7]:
                lr["revenue"]=rev; lr["netIncome"]=ni
                if prev:
                    pr=row(qi,"Total Revenue",prev[0]); pn=row(qi,"Net Income",prev[0])
                    lr["revenueYoY"]=(rev/pr-1) if rev and pr else None
                    lr["netIncomeYoY"]=(ni/pn-1) if ni and pn and pn>0 else None
            last=lr
        except Exception: pass
        try:
            ed=t.get_earnings_dates(limit=8); past=ed[ed["Reported EPS"].notna()]
            if len(past) and last: last["reportDate"]=past.index[0].tz_convert(TZ).isoformat()
        except Exception: pass
        if last: last["_src"]=self.src(co)
        return last
