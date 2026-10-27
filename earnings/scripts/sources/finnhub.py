"""FINNHUB 适配器占位：设置环境变量 FINNHUB_API_KEY 后实现下列方法并在 sources.json 中启用。
参考端点: https://finnhub.io/api/v1/calendar/earnings , /stock/earnings , /stock/revenue-estimate"""
import os
from .base import Adapter as A, stamp
class Adapter(A):
    name="finnhub"
    def __init__(self):
        self.key=os.environ.get("FINNHUB_API_KEY"); self.available=bool(self.key)
    # def next_date(self,co): ...  返回 {"nextDate","dateStatus","_src":stamp("FINNHUB", url)}
    # def consensus(self,co): ...
    # def last_reported(self,co): ...
