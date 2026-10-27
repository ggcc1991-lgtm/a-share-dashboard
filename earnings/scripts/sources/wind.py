"""WIND 适配器占位：设置环境变量 WIND_API_KEY 后实现下列方法并在 sources.json 中启用。
参考端点: WindPy: w.wsd/w.wss 业绩预告、一致预期(WIND一致预期 EPS/营收) — 需本地 Wind 终端"""
import os
from .base import Adapter as A, stamp
class Adapter(A):
    name="wind"
    def __init__(self):
        self.key=os.environ.get("WIND_API_KEY"); self.available=bool(self.key)
    # def next_date(self,co): ...  返回 {"nextDate","dateStatus","_src":stamp("WIND", url)}
    # def consensus(self,co): ...
    # def last_reported(self,co): ...
