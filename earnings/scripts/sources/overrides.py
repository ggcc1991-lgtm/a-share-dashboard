"""人工核对的公告/IR 数据（data/overrides.json），每条自带 source/asOf。"""
import json, os
from .base import Adapter as A
P=os.path.join(os.path.dirname(__file__),"..","..","data","overrides.json")
class Adapter(A):
    name="overrides"
    def __init__(self):
        try: self.d=json.load(open(P))["companies"]
        except Exception: self.d={}
    def next_date(self,co):
        o=self.d.get(co["symbol"],{})
        if "nextDate" in o: return {"nextDate":o["nextDate"],"dateStatus":o.get("dateStatus"),"_src":o.get("dateSource")}
    def consensus(self,co):
        o=self.d.get(co["symbol"],{}).get("consensus")
        return dict(o) if o else None
    def last_reported(self,co):
        o=self.d.get(co["symbol"],{}).get("lastReported")
        if not o: return None
        o=dict(o); o["_src"]=o.pop("source",None); return o
