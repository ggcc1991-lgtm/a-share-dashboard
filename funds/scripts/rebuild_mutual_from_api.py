#!/usr/bin/env python3
"""Rebuild funds-mutual-v2 mutual.json from lxwfof /api/position/pub + /api/position/etf."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ABS_KEYS = ["A股总仓位", "港股", "总股票仓位"]
STYLE_KEYS = [
    "总股票仓位",
    "沪深300",
    "中证500",
    "中证1000",
    "中证2000",
    "万得微盘",
    "风格:红利",
    "风格:双创",
]
QUANT_STYLE = [
    "沪深300",
    "中证500",
    "中证1000",
    "中证2000",
    "万得微盘",
    "风格:红利",
    "风格:双创",
    "风格:微盘",
    "小微盘",
]
PART_MAP = [
    ("量化私募", "量化私募"),
    ("主动私募", "主观私募"),
    ("主动公募", "主动公募"),
    ("ETF", "ETF"),
]
QUANT_ORDER = [
    "300指增",
    "500指增",
    "1000指增",
    "2000指增",
    "A500指增",
    "双创指增",
    "800指增",
    "上证指增",
    "国证指增",
    "A50指增",
    "红利指增",
    "主动量化",
]
STYLE_GROUPS = ["价值", "白马成长", "均衡", "科技成长"]


def pick_series(src, keys):
    return {k: src[k] for k in keys if k in src}



TAB_LABEL = {"pub": "纯公募", "blend": "公募+私募", "all": "全部公募"}


def with_tab_label(tab):
    label = tab.get("label") or TAB_LABEL.get(tab["id"])
    if label:
        tab = dict(tab)
        tab["label"] = label
    return tab


def style_tab_from_styles4(tab_id, block):
    series = {"总股票仓位": block["total"]}
    series.update(block["series"])
    ordered = {k: series[k] for k in STYLE_KEYS if k in series}
    return with_tab_label({"id": tab_id, "dates": block["dates"], "series": ordered})


def style_tab_from_subjective(tab_id, subj):
    ordered = {k: subj["series"][k] for k in STYLE_KEYS if k in subj["series"]}
    return with_tab_label({"id": tab_id, "dates": subj["dates"], "series": ordered})


def quant_tab(tab_id, block):
    series = {"总仓位": block["total"]}
    for k in QUANT_STYLE:
        if k in block["series"]:
            series[k] = block["series"][k]
    return with_tab_label({"id": tab_id, "dates": block["dates"], "series": series})


def last_asof(dates):
    return dates[-1] if dates else None


def rebuild(pub_wrap, etf_wrap, mcp_asof: str, mcp_keys: list[str], now: datetime | None = None):
    assert pub_wrap.get("ok"), pub_wrap.get("error")
    assert etf_wrap.get("ok"), etf_wrap.get("error")
    pub = pub_wrap["data"]
    etf = etf_wrap["data"]
    now = now or datetime.now(ZoneInfo("Asia/Shanghai"))

    combo_api = pub["combo"]
    parts, scales = {}, {}
    for mk, ak in PART_MAP:
        parts[mk] = combo_api["parts"][ak]
        scales[mk] = combo_api["scales"][ak]
    combo = {
        "id": "combo",
        "anchor": "pos-combo",
        "title": "公私募全风格合计",
        "kind": "combo",
        "asOf": last_asof(combo_api["dates"]),
        "unit": "%",
        "defaultOff": ["A股总仓位"],
        "chips": ["主动私募", "量化私募", "主动公募", "ETF"],
        "chipDefault": ["主动私募", "量化私募", "主动公募", "ETF"],
        "dates": combo_api["dates"],
        "series": combo_api["series"],
        "parts": parts,
        "scales": scales,
    }
    if combo_api.get("note"):
        combo["note"] = combo_api["note"]

    pub_subj = pub["pub"]["subjective"]
    blend_subj = pub["blend"]["subjective"]
    pub_abs = {
        "id": "pub_abs",
        "anchor": "pos-pub-abs",
        "title": "主观公募绝对仓位",
        "kind": "tabs_abs",
        "asOf": last_asof(pub_subj["dates"]),
        "unit": "%",
        "hint": "持仓校准版（真实持仓锚定）",
        "lineKeys": ABS_KEYS,
        "tabs": [
            with_tab_label({"id": "pub", "dates": pub_subj["dates"], "series": pick_series(pub_subj["series"], ABS_KEYS)}),
            with_tab_label({"id": "blend", "dates": blend_subj["dates"], "series": pick_series(blend_subj["series"], ABS_KEYS)}),
        ],
        "accuracy": pub["accuracy"],
    }

    styles4 = pub["pub"]["styles4"]
    style_tabs = [
        style_tab_from_subjective("all", pub_subj),
        style_tab_from_subjective("blend", blend_subj),
    ]
    for g in STYLE_GROUPS:
        style_tabs.append(style_tab_from_styles4(g, styles4[g]))
    pub_style = {
        "id": "pub_style",
        "anchor": "pos-pub-style",
        "title": "主观公募风格拆分",
        "kind": "tabs_style",
        "asOf": last_asof(pub_subj["dates"]),
        "unit": "%",
        "hint": "持仓校准版（真实持仓锚定）",
        "defaultOff": ["总股票仓位"],
        "defaultTab": "all",
        "tabs": style_tabs,
        "accuracy": pub["accuracy"],
    }

    zhizeng = pub["pub"]["zhizeng"]
    quant_tabs, quant_asofs = [], []
    for tid in QUANT_ORDER:
        if tid in zhizeng:
            tab = quant_tab(tid, zhizeng[tid])
            quant_tabs.append(tab)
            quant_asofs.append(tab["dates"][-1])
    for tid in zhizeng:
        if tid not in QUANT_ORDER:
            tab = quant_tab(tid, zhizeng[tid])
            quant_tabs.append(tab)
            quant_asofs.append(tab["dates"][-1])
    pub_quant = {
        "id": "pub_quant",
        "anchor": "pos-pub-quant",
        "title": "量化公募风格拆分",
        "kind": "tabs_quant",
        "asOf": max(quant_asofs) if quant_asofs else pub.get("asof"),
        "unit": "%",
        "defaultOff": ["总仓位", "风格:微盘", "小微盘"],
        "defaultTab": "300指增",
        "tabs": quant_tabs,
        "accuracy": pub.get("accuracy_zz"),
        "zhizengCalibrated": bool(pub.get("zhizeng_calibrated")),
    }

    etf_sec = {
        "id": "etf",
        "anchor": "pos-etf",
        "title": "ETF持仓拆分",
        "kind": "single",
        "asOf": etf.get("asof") or last_asof(etf["dates"]),
        "unit": "%",
        "defaultOff": ["A股总仓位", "总股票仓位", "美股", "未拆分"],
        "dates": etf["dates"],
        "series": etf["series"],
        "note": etf.get("note")
        or "全市场股票型ETF（约1700只）按日频精确规模加权的持仓风格统计（指数成分穿透口径）；「其他」为宽基外的A股持仓情况，「未拆分」为指数成分缺失规模；每日凌晨自动更新",
    }
    if "scale" in etf:
        etf_sec["scale"] = etf["scale"]
    if "cnt" in etf:
        etf_sec["cnt"] = etf["cnt"]

    kpi_vals = {k: pub_subj["series"][k][-1] for k in ABS_KEYS}
    kpis = [
        {
            "id": "a_share_pos",
            "label": "主观公募·A股仓位",
            "value": kpi_vals["A股总仓位"],
            "unit": "%",
            "note": f"纯公募 asOf {pub_abs['asOf']}",
        },
        {"id": "hk_pos", "label": "主观公募·港股", "value": kpi_vals["港股"], "unit": "%", "note": "纯公募"},
        {
            "id": "total_equity",
            "label": "主观公募·总股票仓位",
            "value": kpi_vals["总股票仓位"],
            "unit": "%",
            "note": "A股+港股",
        },
    ]

    pub_asof = pub.get("asof") or pub_abs["asOf"]
    etf_asof = etf.get("asof") or etf_sec["asOf"]
    note = (
        f"主数据 /api/position/pub（asOf={pub_asof}），ETF 来自 /api/position/etf；"
        f"MCP dataset `position` 仅含私募侧（asOf={mcp_asof}），已另存 position-raw.json。"
        f"部分信息参考自lxwfof MCP。"
    )
    return {
        "schemaVersion": "funds-mutual-v2",
        "generatedAt": now.isoformat(timespec="seconds"),
        "generatedAtDisplay": now.strftime("%Y-%m-%d %H:%M") + "（北京时间）",
        "asOf": pub_abs["asOf"],
        "timezone": "Asia/Shanghai",
        "sample": False,
        "universe": "lxwfof_position_pub",
        "note": note,
        "kpis": kpis,
        "funds": [],
        "sections": [combo, pub_abs, pub_style, pub_quant, etf_sec],
        "source": {
            "page": "https://lxwfof.com/#/position",
            "mcp": {
                "namespace": "user-lxwfof MCP",
                "dataset": "position",
                "asOf": mcp_asof,
                "keys": mcp_keys,
                "coverage": "私募 subjective/styles4/zhizeng/text；无公募 combo/pub/blend/etf",
                "rawPath": "lxwfof-mutual-capture/position-raw.json",
            },
            "pubApi": {"path": "/api/position/pub", "asOf": pub_asof, "keys": list(pub.keys())},
            "etfApi": {"path": "/api/position/etf", "asOf": etf_asof},
            "gaps": [
                "MCP get_dataset(position) 不含公募四块与 ETF/产品自助",
                "产品自助 #pos-pattr 需 /api/position/ppos 逐产品，本版未收录",
                "pubpri_excess 为超额对比、非仓位，未并入 mutual.json",
            ],
            "compliance": "【部分信息参考自lxwfof MCP】",
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pub", required=True)
    ap.add_argument("--etf", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mcp-asof", default="2026-10-23")
    ap.add_argument("--mcp-summary", default="")
    args = ap.parse_args()
    mcp_keys = ["asof", "subjective", "styles4", "zhizeng", "text", "long_image", "styles4_calibrated"]
    mcp_asof = args.mcp_asof
    if args.mcp_summary and Path(args.mcp_summary).exists():
        s = json.loads(Path(args.mcp_summary).read_text(encoding="utf-8"))
        mcp_asof = s.get("asof") or mcp_asof
        mcp_keys = s.get("keys") or mcp_keys
    out = rebuild(
        json.loads(Path(args.pub).read_text(encoding="utf-8")),
        json.loads(Path(args.etf).read_text(encoding="utf-8")),
        mcp_asof,
        mcp_keys,
    )
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print("wrote", args.out, "asOf", out["asOf"], [(s["id"], s["asOf"]) for s in out["sections"]])


if __name__ == "__main__":
    main()
