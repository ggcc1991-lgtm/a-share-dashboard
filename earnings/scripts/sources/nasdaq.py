import json, re, urllib.request
from .base import Adapter as A, stamp
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124 Safari/537.36","Accept":"application/json"}
class Adapter(A):
    name="nasdaq"
    def next_date(self,co):
        s=co.get("nasdaq")
        if not s: return None
        try: txt=json.load(urllib.request.urlopen(urllib.request.Request(f"https://api.nasdaq.com/api/analyst/{s}/earnings-date",headers=UA),timeout=20))["data"].get("reportText")
        except Exception: return None
        m=re.search(r"(\d\d)/(\d\d)/(\d{4})",txt or "")
        if not m: return None
        return {"nextDate":f"{m[3]}-{m[1]}-{m[2]}","dateStatus":"estimated" if re.search(r"expected\*|estimated",txt,re.I) else "confirmed","nasdaqText":txt,
                "_src":stamp("Nasdaq/Zacks 算法预估" if re.search(r"expected\*|estimated",txt,re.I) else "Nasdaq/Zacks",f"https://www.nasdaq.com/market-activity/stocks/{s.lower()}/earnings")}
