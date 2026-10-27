"""港交所披露易：查找最近的『董事会会议召开日期 / Notice of Board Meeting』公告，解析会议日期作为已确认财报日期。
需要 pdftotext(poppler-utils)。仅当公告发布在最近一次业绩公告之后才采用。"""
import json, re, subprocess, tempfile, urllib.request, urllib.parse, datetime as dt
from .base import Adapter as A, stamp
UA={"User-Agent":"Mozilla/5.0"}
MON={m:i+1 for i,m in enumerate("january february march april may june july august september october november december".split())}
def get(u): return urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=40).read()
class Adapter(A):
    name="hkex"
    def stock_id(self,code):
        t=get(f"https://www1.hkexnews.hk/search/prefix.do?callback=cb&lang=EN&type=A&name={code}&market=SEHK").decode()
        for x in json.loads(t[t.index("(")+1:t.rindex(")")])["stockInfo"]:
            if x["code"]==code: return x["stockId"]
    def docs(self,code,days=120):
        sid=self.stock_id(code); now=dt.date.today()
        q=dict(sortDir=0,sortByOptions="DateTime",category=0,market="SEHK",stockId=sid,documentType=-1,fromDate=(now-dt.timedelta(days=days)).strftime("%Y%m%d"),
               toDate=now.strftime("%Y%m%d"),title="",searchType=0,t1code=-2,t2Gcode=-2,t2code=-2,rowRange=200,lang="E")
        r=json.loads(get("https://www1.hkexnews.hk/search/titleSearchServlet.do?"+urllib.parse.urlencode(q)))
        return json.loads(r["result"]) if r.get("result") not in (None,"null") else []
    def next_date(self,co):
        code=co.get("hk")
        if not code: return None
        try: ds=self.docs(code)
        except Exception: return None
        res=[d for d in ds if re.search(r"RESULTS",d["TITLE"],re.I) and "MEETING" not in d["TITLE"].upper()]
        last_res=res[0]["DATE_TIME"] if res else None
        for d in ds:
            if not re.search(r"BOARD MEETING",d["TITLE"],re.I): continue
            pub=dt.datetime.strptime(d["DATE_TIME"],"%d/%m/%Y %H:%M")
            if last_res and pub<=dt.datetime.strptime(last_res,"%d/%m/%Y %H:%M"): return None
            url="https://www1.hkexnews.hk"+d["FILE_LINK"]
            with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
                f.write(get(url)); f.flush()
                txt=subprocess.run(["pdftotext",f.name,"-"],capture_output=True,text=True).stdout
            txt=" ".join(txt.split())
            m=re.search(r"held on (?:\w+, )?(\d{1,2}) (\w+) (\d{4})",txt) or re.search(r"held on (\w+) (\d{1,2}), (\d{4})",txt)
            if not m: return None
            g=m.groups()
            day,mon,yr=(g[0],g[1],g[2]) if g[0].isdigit() else (g[1],g[0],g[2])
            if mon.lower() not in MON: return None
            return {"nextDate":f"{yr}-{MON[mon.lower()]:02d}-{int(day):02d}","dateStatus":"confirmed",
                    "_src":stamp(f"HKEXnews 董事会会议通告({pub:%Y-%m-%d})",url)}
        return None
