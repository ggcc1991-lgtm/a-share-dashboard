"""FMP 适配器占位：设置环境变量 FMP_API_KEY 后实现下列方法并在 sources.json 中启用。
参考端点: https://financialmodelingprep.com/api/v3/earning_calendar , /analyst-estimates/{sym}, /income-statement/{sym}?period=quarter"""
import os
from .base import Adapter as A, stamp
class Adapter(A):
    name="fmp"
    def __init__(self):
        self.key=os.environ.get("FMP_API_KEY"); self.available=bool(self.key)
    # def next_date(self,co): ...  返回 {"nextDate","dateStatus","_src":stamp("FMP", url)}
    # def consensus(self,co): ...
    # def last_reported(self,co): ...
