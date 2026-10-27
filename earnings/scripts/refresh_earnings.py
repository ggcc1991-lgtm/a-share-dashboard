#!/usr/bin/env python3
"""刷新 earnings/data/earnings.json。数据源由 sources.json 配置的适配器链提供（字段级合并，记录每个字段块的来源）。
用法: python refresh_earnings.py [--out ../data/earnings.json] [--only SYM,SYM]
取不到的字段为 null（页面显示“暂无”），绝不填充推测值。"""
import json, os, sys, time, argparse, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
from sources import load
from sources.base import TZ
COS = [ # symbol, 名称, 地区, yahoo, nasdaq, hk 代码, ashare(Tushare)
 ("AAPL","苹果","US","AAPL","AAPL",None,None),("MSFT","微软","US","MSFT","MSFT",None,None),("GOOGL","谷歌(Alphabet)","US","GOOGL","GOOGL",None,None),
 ("AMZN","亚马逊","US","AMZN","AMZN",None,None),("META","Meta","US","META","META",None,None),("NVDA","英伟达","US","NVDA","NVDA",None,None),
 ("TSLA","特斯拉","US","TSLA","TSLA",None,None),("TSM","台积电(ADR)","TW","TSM","TSM",None,None),("AMD","AMD","US","AMD","AMD",None,None),
 ("AVGO","博通","US","AVGO","AVGO",None,None),("0700.HK","腾讯控股","CN","0700.HK",None,"00700",None),("BABA","阿里巴巴(ADR)","CN","BABA","BABA","09988",None),
 ("BIDU","百度(ADR)","CN","BIDU","BIDU","09888",None),("JD","京东(ADR)","CN","JD","JD","09618",None),("3690.HK","美团","CN","3690.HK",None,"03690",None),
 ("PDD","拼多多","CN","PDD","PDD",None,None),("1810.HK","小米集团","CN","1810.HK",None,"01810",None),("NTES","网易(ADR)","CN","NTES","NTES","09999",None),
 ("0981.HK","中芯国际","CN","0981.HK",None,"00981","688981.SH"),("1211.HK","比亚迪股份","CN","1211.HK",None,"01211","002594.SZ"),
]
def merge(dst,src):
    for k,v in (src or {}).items():
        if k=="_src": continue
        if k not in dst: dst[k]=v  # 高优先级源显式给出的 null 不被覆盖
def future(d):
    if not d: return False
    return dt.datetime.fromisoformat(d if "T" in d else d+"T23:59:00+08:00")>=dt.datetime.now(TZ)
if __name__=="__main__":
    here=os.path.dirname(os.path.abspath(__file__))
    ap=argparse.ArgumentParser(); ap.add_argument("--out",default=os.path.join(here,"..","data","earnings.json")); ap.add_argument("--only"); a=ap.parse_args()
    cfg=json.load(open(os.path.join(here,"sources.json")))
    ads={}
    for n in {x for k in ("next_date","consensus","last_reported") for x in cfg[k]}:
        try:
            ad=load(n)
            if ad.available: ads[n]=ad
        except Exception as e: print("skip source",n,e)
    old={}
    if os.path.exists(a.out):
        try: old={c["symbol"]:c for c in json.load(open(a.out))["companies"]}
        except Exception: pass
    only=set(a.only.split(",")) if a.only else None
    out=[]
    for s,n,r,y,nq,hk,ashare in COS:
        if only and s not in only: out.append(old.get(s,{"symbol":s,"name":n,"region":r})); continue
        co={"symbol":s,"name":n,"region":r,"yahoo":y,"nasdaq":nq,"hk":hk,"ashare":ashare}
        c={"symbol":s,"name":n,"region":r,"currency":None,"nextDate":None,"dateStatus":"unknown","sources":{}}
        for src in cfg["next_date"]:   # 第一个给出“未来日期”的源胜出
            ad=ads.get(src)
            if not ad: continue
            try: x=ad.next_date(co)
            except Exception as e: x=None; print(s,src,"err",e)
            if x and x.get("currency") and not c["currency"]: c["currency"]=x["currency"]
            if x and x.get("nasdaqText"): c["nasdaqText"]=x["nasdaqText"]
            if x and future(x.get("nextDate")) and c["nextDate"] is None:
                c["nextDate"]=x["nextDate"]; c["dateStatus"]=x.get("dateStatus") or "unknown"; c["sources"]["nextDate"]=x.get("_src")
        for key,meth in (("consensus","consensus"),("lastReported","last_reported")):
            blk={}; used=[]
            for src in cfg[meth]:
                ad=ads.get(src)
                if not ad: continue
                try: x=getattr(ad,meth)(co)
                except Exception as e: x=None; print(s,src,"err",e)
                if x:
                    if key=="lastReported" and blk.get("quarterEnd") and x.get("quarterEnd") and x["quarterEnd"]!=blk["quarterEnd"]: continue  # 不同季度不混合
                    merge(blk,x); used.append(x.get("_src"))
            c[key]=blk or None; c["sources"][key]=[u for u in used if u]
        ts_ad=ads.get("tushare_src")
        if ts_ad and co.get("ashare"):
            try: y=ts_ad.last_reported(co)
            except Exception as e: y=None; print(s,"tushare last err",e)
            cur=(c.get("lastReported") or {}).get("quarterEnd") or ""
            if y and (y.get("quarterEnd") or "")>cur[:10]:
                src=y.pop("_src",None); c.setdefault("lastReported",{}) ; c["lastReported"] = c["lastReported"] or {}
                c["lastReported"]["ashareYtd"]=y
                if src: c["sources"].setdefault("lastReported",[]).append(src)
            elif y: print(s,"tushare last",y.get("quarterEnd"),"not newer than",cur,"→ skip")
        ov=ads.get("overrides")
        if ov:
            o=ov.d.get(s,{})
            for k in ("currency","guidance","note"):
                if o.get(k): c[k]=o[k]
            if o.get("lastReported",{}).get("guidance"): c["guidance"]=o["lastReported"]["guidance"]
        oc=(old.get(s,{}).get("consensus") or {})
        if oc.get("ashareAnnual") and not (c.get("consensus") or {}).get("ashareAnnual"):
            c["consensus"]=c.get("consensus") or {}; c["consensus"]["ashareAnnual"]=dict(oc["ashareAnnual"], stale=True)
        ol=(old.get(s,{}).get("lastReported") or {})
        if ol.get("ashareYtd") and c.get("lastReported") and not c["lastReported"].get("ashareYtd") and ol["ashareYtd"].get("quarterEnd","")>(c["lastReported"].get("quarterEnd") or ""):
            c["lastReported"]["ashareYtd"]=ol["ashareYtd"]
        for k in ("guidance","note","manual","feedExtracts"):  # 旧文件人工/信息流摘录保留
            if k in old.get(s,{}) and not c.get(k): c[k]=old[s][k]
        out.append(c); print(s,c["nextDate"],c["dateStatus"]); time.sleep(0.3)
    now=dt.datetime.now(TZ).isoformat(timespec="seconds")
    ts=ads.get("tushare_src")
    if ts:
        try: print("[tushare_src]", ts.status())
        except Exception as e: print("[tushare_src] status err", e)
    json.dump({"schema":"earnings-v2","updated":now,
      "consensusSource":"一致预期：A股优先 Tushare report_rc，其余 Yahoo（港股 .HK）；日期优先 overrides/HKEXnews/Tushare disclosure_date > Yahoo > Nasdaq/Zacks",
      "consensusAsOf":now[:10],"companies":out},open(a.out,"w"),ensure_ascii=False,indent=1)
