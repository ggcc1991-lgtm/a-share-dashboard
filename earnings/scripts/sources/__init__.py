"""数据源适配层。每个适配器实现 base.Adapter 的一个或多个方法，返回带 `_src` 的 dict（字段级来源）。
新增付费源：复制 fmp.py 模板，实现方法，在 ../sources.json 中把它放到对应字段优先级前面即可。"""
from importlib import import_module
def load(name): return import_module(f"sources.{name}").Adapter()
