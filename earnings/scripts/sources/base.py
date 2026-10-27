import datetime as dt
TZ = dt.timezone(dt.timedelta(hours=8))
def stamp(name, url=None): return {"name": name, "url": url, "asOf": dt.datetime.now(TZ).isoformat(timespec="seconds")}
class Adapter:
    """接口约定（全部可选，未实现返回 None）：
    next_date(co)  -> {"nextDate","dateStatus","_src"}
    consensus(co)  -> {"epsAvg","epsLow","epsHigh","epsAnalysts","revAvg",...,"currency","_src"}
    last_reported(co) -> {"quarterEnd","reportDate","revenue","netIncome","revenueYoY","netIncomeYoY","epsActual","epsEstimate","epsSurprisePct",...,"_src"}
    co = {"symbol","name","region","nasdaq","hk","yahoo"}"""
    name = "base"
    available = True
    def next_date(self, co): return None
    def consensus(self, co): return None
    def last_reported(self, co): return None
