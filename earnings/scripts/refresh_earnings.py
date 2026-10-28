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
 ("2330.TW","台积电(现股)","TW","2330.TW",None,None,None),("2454.TW","联发科","TW","2454.TW",None,None,None),("3711.TW","日月光投控","TW","3711.TW",None,None,None),
 ("005930.KS","三星电子","KR","005930.KS",None,None,None),("000660.KS","SK海力士","KR","000660.KS",None,None,None),
 ("SONY","索尼(ADR)","JP","SONY","SONY",None,None),("8035.T","东京电子","JP","8035.T",None,None,None),("9984.T","软银集团","JP","9984.T",None,None,None),
 ("ASML","ASML","EU","ASML","ASML",None,None),("SAP","SAP","EU","SAP","SAP",None,None),("ENR.DE","西门子能源","EU","ENR.DE",None,None,None),
 ("3008.TW","大立光","TW","3008.TW",None,None,None),("6488.TWO","环球晶圆","TW","6488.TWO",None,None,None),("2308.TW","台达电","TW","2308.TW",None,None,None),("3034.TW","联咏","TW","3034.TW",None,None,None),
 ("373220.KS","LG新能源","KR","373220.KS",None,None,None),("207940.KS","三星生物","KR","207940.KS",None,None,None),("035420.KS","NAVER","KR","035420.KS",None,None,None),
 ("6861.T","基恩士","JP","6861.T",None,None,None),("6857.T","爱德万测试","JP","6857.T",None,None,None),("6146.T","Disco","JP","6146.T",None,None,None),("6920.T","Lasertec","JP","6920.T",None,None,None),("4063.T","信越化学","JP","4063.T",None,None,None),("6981.T","村田制作所","JP","6981.T",None,None,None),
 ("IFX.DE","英飞凌","EU","IFX.DE",None,None,None),("STM","意法半导体","EU","STM","STM",None,None),("ASM.AS","ASM International","EU","ASM.AS",None,None,None),("BESI.AS","BE半导体","EU","BESI.AS",None,None,None),("ADYEN.AS","Adyen","EU","ADYEN.AS",None,None,None),("NVO","诺和诺德(ADR)","EU","NVO","NVO",None,None),
 ("AMAT","应用材料","US","AMAT","AMAT",None,None),("LRCX","拉姆研究","US","LRCX","LRCX",None,None),("KLAC","科磊","US","KLAC","KLAC",None,None),("ADI","亚德诺","US","ADI","ADI",None,None),
 ("VRT","维谛 Vertiv","US","VRT","VRT",None,None),("ETN","伊顿","US","ETN","ETN",None,None),("SU.PA","施耐德电气","EU","SU.PA",None,None,None),("SMCI","超微电脑","US","SMCI","SMCI",None,None),("DELL","戴尔","US","DELL","DELL",None,None),("ANET","Arista","US","ANET","ANET",None,None),("CSCO","思科","US","CSCO","CSCO",None,None),
 ("2382.TW","广达电脑","TW","2382.TW",None,None,None),("3231.TW","纬创","TW","3231.TW",None,None,None),("2317.TW","鸿海","TW","2317.TW",None,None,None),
 ("ARM","Arm","US","ARM","ARM",None,None),("MRVL","Marvell","US","MRVL","MRVL",None,None),("ALAB","Astera Labs","US","ALAB","ALAB",None,None),("CRDO","Credo","US","CRDO","CRDO",None,None),("COHR","Coherent","US","COHR","COHR",None,None),
 ("NOW","ServiceNow","US","NOW","NOW",None,None),("PLTR","Palantir","US","PLTR","PLTR",None,None),("SNOW","Snowflake","US","SNOW","SNOW",None,None),("CRWD","CrowdStrike","US","CRWD","CRWD",None,None),("DDOG","Datadog","US","DDOG","DDOG",None,None),("ADBE","Adobe","US","ADBE","ADBE",None,None),("CRM","Salesforce","US","CRM","CRM",None,None),("SHOP","Shopify","US","SHOP","SHOP",None,None),("MELI","MercadoLibre","US","MELI","MELI",None,None),
 # A股全产业链（Yahoo 沪市用 .SS；暂不挂 ashare 以免触 Tushare IP）
 ("002371.SZ","北方华创","CN","002371.SZ",None,None,None),("688012.SS","中微公司","CN","688012.SS",None,None,None),("688072.SS","拓荆科技","CN","688072.SS",None,None,None),("688120.SS","华海清科","CN","688120.SS",None,None,None),("688082.SS","盛美上海","CN","688082.SS",None,None,None),("688126.SS","沪硅产业","CN","688126.SS",None,None,None),("688019.SS","安集科技","CN","688019.SS",None,None,None),
 ("688256.SS","寒武纪","CN","688256.SS",None,None,None),("688041.SS","海光信息","CN","688041.SS",None,None,None),("603986.SS","兆易创新","CN","603986.SS",None,None,None),("603501.SS","韦尔股份","CN","603501.SS",None,None,None),("688008.SS","澜起科技","CN","688008.SS",None,None,None),
 ("600584.SS","长电科技","CN","600584.SS",None,None,None),("002463.SZ","沪电股份","CN","002463.SZ",None,None,None),("600183.SS","生益科技","CN","600183.SS",None,None,None),
 ("300308.SZ","中际旭创","CN","300308.SZ",None,None,None),("300502.SZ","新易盛","CN","300502.SZ",None,None,None),("300394.SZ","天孚通信","CN","300394.SZ",None,None,None),
 ("601138.SS","工业富联","CN","601138.SS",None,None,None),("000977.SZ","浪潮信息","CN","000977.SZ",None,None,None),("002837.SZ","英维克","CN","002837.SZ",None,None,None),
 ("688111.SS","金山办公","CN","688111.SS",None,None,None),("002230.SZ","科大讯飞","CN","002230.SZ",None,None,None),
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
            if x and x.get("nextDate") and (src=="overrides" or future(x.get("nextDate"))) and c["nextDate"] is None:  # 人工核对的 overrides 日期即使已过也保留
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
        ths_ad=ads.get("ths_src")
        if ths_ad and hasattr(ths_ad,"ashare_ytd"):
            try: y=ths_ad.ashare_ytd(co)
            except Exception as e: y=None; print(s,"ths ytd err",e)
            if y and not (c.get("lastReported") or {}).get("ashareYtd"):
                src=y.pop("_src",None)
                c["lastReported"]=c.get("lastReported") or {}
                c["lastReported"]["ashareYtd"]=y
                if src: c["sources"].setdefault("lastReported",[]).append(src)
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
        # 下游源整块失败时保留旧 consensus / lastReported（避免 Yahoo 抖动抹掉已有真值）
        oc0=old.get(s,{})
        if not c.get("consensus") and oc0.get("consensus"):
            c["consensus"]=oc0["consensus"]
        elif c.get("consensus") and oc0.get("consensus"):
            for fk in ("epsAvg","epsLow","epsHigh","epsAnalysts","epsYearAgo","revAvg","revLow","revHigh","revAnalysts","revGrowth","currency"):
                if c["consensus"].get(fk) is None and oc0["consensus"].get(fk) is not None:
                    c["consensus"][fk]=oc0["consensus"][fk]
            if oc0["consensus"].get("ashareAnnual") and not c["consensus"].get("ashareAnnual"):
                c["consensus"]["ashareAnnual"]=dict(oc0["consensus"]["ashareAnnual"], stale=True)
        if not c.get("lastReported") and oc0.get("lastReported"):
            c["lastReported"]=oc0["lastReported"]
        out.append(c); print(s,c["nextDate"],c["dateStatus"]); time.sleep(0.3)
    now=dt.datetime.now(TZ).isoformat(timespec="seconds")
    ts=ads.get("tushare_src")
    if ts:
        try: print("[tushare_src]", ts.status())
        except Exception as e: print("[tushare_src] status err", e)
    json.dump({"schema":"earnings-v2","updated":now,
      "consensusSource":"一致预期：A股年度 ashareAnnual 优先 Tushare report_rc / Wind 一致预期，季度仍 Yahoo；日期优先 overrides / Wind 预约披露 / Tushare disclosure_date / HKEXnews > Yahoo > Nasdaq/Zacks",
      "consensusAsOf":now[:10],"companies":out},open(a.out,"w"),ensure_ascii=False,indent=1)
