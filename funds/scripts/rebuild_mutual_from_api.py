#!/usr/bin/env python3
"""Rebuild funds-mutual-v2 mutual.json from lxwfof MCP position_pub + position_etf.

Accepts an MCP dataset envelope ``{name,desc,kb,data}`` or the legacy
``{ok:true,data}`` wrapper around the same payload. The written source is
always lxwfof MCP ``position_pub`` / ``position_etf``. A stale private
``position`` summary is not treated as this fetch.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
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
TAB_LABEL = {"pub": "纯公募", "blend": "公募+私募", "all": "全部公募"}
SECTION_ORDER = ["combo", "pub_abs", "pub_style", "pub_quant", "etf"]
SECTION_KIND = {
    "combo": "combo",
    "pub_abs": "tabs_abs",
    "pub_style": "tabs_style",
    "pub_quant": "tabs_quant",
    "etf": "single",
}
COMPLIANCE = "【部分信息参考自lxwfof MCP】"
NAMESPACE = "lxwfof MCP"
DATASETS = ["position_pub", "position_etf"]
FORBIDDEN = ("产品自助拆分未入库。", "公募仓位重建自 lxwfof")
NOTE_DENY = (
    "/api/position/pub",
    "/api/position/etf",
    "网页登录",
    "position-raw.json",
    "仅含私募",
    "dataset `position`",
)
GAPS = [
    "产品自助 #pos-pattr 需逐产品 ppos，本版未收录",
    "pubpri_excess 为超额对比、非仓位，未并入 mutual.json",
]
SENSITIVE_KEYS = {
    "authorization",
    "token",
    "access_token",
    "refresh_token",
    "id_token",
    "password",
    "secret",
    "api_key",
    "apikey",
    "cookie",
    "set_cookie",
}
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_COMPLIANCE_MARK = "部分信息参考自lxwfof MCP"


class RebuildError(ValueError):
    """Input or invariant failure. main() prints it and exits 1."""


def pick_series(src, keys):
    return {k: src[k] for k in keys if k in src}


def with_tab_label(tab):
    label = tab.get("label") or TAB_LABEL.get(tab["id"]) or tab["id"]
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


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _sensitive_key(key):
    norm = str(key).replace("-", "_").strip().lower()
    return norm in SENSITIVE_KEYS or norm.endswith("_token") or norm.endswith("_secret")


def reject_sensitive(obj, role, depth=0):
    if depth > 8:
        return
    if isinstance(obj, dict):
        for key, value in obj.items():
            if _sensitive_key(key):
                raise RebuildError(f"{role}: 输入含敏感字段 {key}，拒绝写入")
            if isinstance(value, (dict, list)):
                reject_sensitive(value, role, depth + 1)
    elif isinstance(obj, list) and obj and isinstance(obj[0], (dict, list)):
        for value in obj:
            if isinstance(value, (dict, list)):
                reject_sensitive(value, role, depth + 1)


def require_dates(dates, role):
    if not isinstance(dates, list) or not dates:
        raise RebuildError(f"{role}: dates 为空")
    prev = None
    for i, day in enumerate(dates):
        if not isinstance(day, str) or not _DATE.fullmatch(day):
            raise RebuildError(f"{role}: dates[{i}] 不是 YYYY-MM-DD")
        try:
            datetime.strptime(day, "%Y-%m-%d")
        except ValueError as exc:
            raise RebuildError(f"{role}: dates[{i}] 不是有效日期 {day}") from exc
        if prev is not None and day <= prev:
            raise RebuildError(f"{role}: dates 未严格递增 {prev} -> {day}")
        prev = day
    return dates


def _require_values(values, n, role):
    if not isinstance(values, list) or len(values) != n:
        got = len(values) if isinstance(values, list) else type(values).__name__
        raise RebuildError(f"{role}: 长度 {got} != {n}")
    for i, value in enumerate(values):
        if value is None:
            continue
        if not _is_number(value):
            raise RebuildError(f"{role}[{i}] 不是数值")
    return values


def require_series(series, n, role, required):
    if not isinstance(series, dict) or not series:
        raise RebuildError(f"{role}: series 缺失")
    missing = [key for key in required if key not in series]
    if missing:
        raise RebuildError(f"{role}: 缺少序列 {missing}")
    for key, values in series.items():
        _require_values(values, n, f"{role} 序列「{key}」")
    return series


def lookup_component(mapping, api_key, display_key, role):
    if not isinstance(mapping, dict):
        raise RebuildError(f"{role}: 不是对象")
    if api_key in mapping:
        return mapping[api_key]
    if display_key != api_key and display_key in mapping:
        return mapping[display_key]
    raise RebuildError(f"{role}: 缺少成分 {api_key}")


def looks_like_private_position(data):
    if not isinstance(data, dict):
        return False
    has_private = any(key in data for key in ("subjective", "styles4", "zhizeng", "text"))
    has_public = any(key in data for key in ("pub", "blend", "combo"))
    return has_private and not has_public


def is_mcp_envelope(obj):
    return (
        isinstance(obj, dict)
        and isinstance(obj.get("name"), str)
        and obj.get("name") != ""
        and "data" in obj
        and ("desc" in obj or "kb" in obj)
    )


def _as_object(data, role):
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError as exc:
            raise RebuildError(f"{role}: data 不是 JSON 对象") from exc
    if not isinstance(data, dict):
        raise RebuildError(f"{role}: data 不是对象")
    return data


def _from_mcp(wrap, role, expected_dataset):
    name = wrap.get("name")
    if name != expected_dataset:
        raise RebuildError(f"{role}: MCP dataset 名称为 {name!r}，需要 {expected_dataset!r}")
    data = _as_object(wrap.get("data"), role)
    if expected_dataset == "position_pub" and looks_like_private_position(data):
        raise RebuildError(f"{role}: dataset 内容是私募 position，不能当作 position_pub")
    return data, {
        "envelope": "mcp_dataset",
        "dataset": expected_dataset,
        "provider": NAMESPACE,
        "namespace": NAMESPACE,
    }


def unwrap_input(wrap, *, role, expected_dataset):
    """Return ``(payload, meta)`` from an MCP dataset or a legacy API wrapper."""
    if not isinstance(wrap, dict):
        raise RebuildError(f"{role}: 需要 JSON 对象")
    reject_sensitive(wrap, role)
    if is_mcp_envelope(wrap):
        return _from_mcp(wrap, role, expected_dataset)
    if "ok" in wrap:
        if wrap.get("ok") is not True:
            err = wrap.get("error") or wrap.get("message") or wrap.get("ok")
            raise RebuildError(f"{role}: 旧 API 包装失败: {err}")
        data = wrap.get("data")
        if is_mcp_envelope(data):
            payload, meta = _from_mcp(data, role, expected_dataset)
            meta = dict(meta)
            meta["outerEnvelope"] = "legacy_api"
            return payload, meta
        data = _as_object(data, role)
        if expected_dataset == "position_pub" and looks_like_private_position(data):
            raise RebuildError(f"{role}: 这是私募 position 摘要，不能当作 position_pub")
        return data, {
            "envelope": "legacy_api",
            "dataset": expected_dataset,
            "provider": NAMESPACE,
            "namespace": NAMESPACE,
        }
    raise RebuildError(
        f"{role}: 无法识别。接受 MCP dataset {{name,desc,kb,data}} 或旧 API {{ok:true,data}}"
    )


def _header_asof(payload, last, role):
    header = payload.get("asof")
    if header is None:
        return last
    if not isinstance(header, str) or not _DATE.fullmatch(header):
        raise RebuildError(f"{role}: asof 不是 YYYY-MM-DD")
    if header != last:
        raise RebuildError(f"{role}: asof {header} 与序列末点 {last} 不一致")
    return header


def validate_pub_payload(pub):
    if not isinstance(pub, dict):
        raise RebuildError("position_pub: data 不是对象")
    if looks_like_private_position(pub):
        raise RebuildError("position_pub: 输入是私募 position，没有公募 pub/combo")
    for key in ("pub", "blend", "combo"):
        if not isinstance(pub.get(key), dict):
            raise RebuildError(f"position_pub: 缺少 {key}")
    subjective_keys = list(dict.fromkeys(ABS_KEYS + STYLE_KEYS))
    for role, block in (
        ("position_pub pub.subjective", pub["pub"].get("subjective")),
        ("position_pub blend.subjective", pub["blend"].get("subjective")),
    ):
        if not isinstance(block, dict):
            raise RebuildError(f"{role} 缺失")
        dates = require_dates(block.get("dates"), role)
        require_series(block.get("series"), len(dates), role, subjective_keys)
    styles4 = pub["pub"].get("styles4")
    if not isinstance(styles4, dict):
        raise RebuildError("position_pub: pub.styles4 缺失")
    style_lines = [key for key in STYLE_KEYS if key != "总股票仓位"]
    for name in STYLE_GROUPS:
        block = styles4.get(name)
        role = f"position_pub styles4.{name}"
        if not isinstance(block, dict):
            raise RebuildError(f"{role} 缺失")
        dates = require_dates(block.get("dates"), role)
        require_series(block.get("series"), len(dates), role, style_lines)
        _require_values(block.get("total"), len(dates), f"{role} total")
    zhizeng = pub["pub"].get("zhizeng")
    if not isinstance(zhizeng, dict) or not zhizeng:
        raise RebuildError("position_pub: pub.zhizeng 为空")
    missing_tabs = [name for name in QUANT_ORDER if name not in zhizeng]
    if missing_tabs:
        raise RebuildError(f"position_pub: zhizeng 缺少页签 {missing_tabs}")
    for name, block in zhizeng.items():
        role = f"position_pub zhizeng.{name}"
        if not isinstance(block, dict):
            raise RebuildError(f"{role} 不是对象")
        dates = require_dates(block.get("dates"), role)
        require_series(block.get("series"), len(dates), role, QUANT_STYLE)
        _require_values(block.get("total"), len(dates), f"{role} total")
    if not isinstance(pub.get("accuracy"), dict) or not pub["accuracy"].get("text"):
        raise RebuildError("position_pub: accuracy.text 缺失")
    if pub.get("accuracy_zz") is not None and not isinstance(pub.get("accuracy_zz"), dict):
        raise RebuildError("position_pub: accuracy_zz 不是对象")
    combo = pub["combo"]
    role = "position_pub combo"
    dates = require_dates(combo.get("dates"), role)
    require_series(combo.get("series"), len(dates), role, ["A股总仓位"])
    parts = combo.get("parts")
    scales = combo.get("scales")
    for display_key, api_key in PART_MAP:
        part = lookup_component(parts, api_key, display_key, f"{role} parts")
        require_series(part, len(dates), f"{role} parts.{display_key}", [])
        scale = lookup_component(scales, api_key, display_key, f"{role} scales")
        _require_values(scale, len(dates), f"{role} scales.{display_key}")
    if isinstance(scales, dict) and "dates" in scales and list(scales["dates"]) != list(dates):
        raise RebuildError(f"{role}: scales.dates 与 dates 不一致")
    _header_asof(pub, pub["pub"]["subjective"]["dates"][-1], "position_pub")


def validate_etf_payload(etf):
    if not isinstance(etf, dict):
        raise RebuildError("position_etf: data 不是对象")
    if looks_like_private_position(etf):
        raise RebuildError("position_etf: 输入不是 ETF 持仓")
    dates = require_dates(etf.get("dates"), "position_etf")
    require_series(etf.get("series"), len(dates), "position_etf", ["A股总仓位", "总股票仓位"])
    for key in ("scale", "cnt"):
        if key in etf:
            _require_values(etf[key], len(dates), f"position_etf {key}")
    _header_asof(etf, dates[-1], "position_etf")


def _dataset_record(meta, as_of, keys):
    record = {
        "dataset": meta["dataset"],
        "asOf": as_of,
        "envelope": meta["envelope"],
        "keys": keys,
    }
    if meta.get("outerEnvelope"):
        record["outerEnvelope"] = meta["outerEnvelope"]
    return record


def build_note(pub_asof, etf_asof):
    return (
        f"lxwfof MCP position_pub（asOf={pub_asof}），"
        f"position_etf（asOf={etf_asof}）。"
        f"{COMPLIANCE}"
    )


def rebuild(pub_wrap, etf_wrap, now: datetime | None = None):
    pub, pub_meta = unwrap_input(pub_wrap, role="position_pub", expected_dataset="position_pub")
    etf, etf_meta = unwrap_input(etf_wrap, role="position_etf", expected_dataset="position_etf")
    validate_pub_payload(pub)
    validate_etf_payload(etf)
    now = now or datetime.now(ZoneInfo("Asia/Shanghai"))
    if now.tzinfo is None or now.utcoffset() is None:
        raise RebuildError("generatedAt 需要带时区的 Asia/Shanghai 时间")

    combo_api = pub["combo"]
    parts, scales = {}, {}
    for display_key, api_key in PART_MAP:
        parts[display_key] = lookup_component(combo_api["parts"], api_key, display_key, "combo parts")
        scales[display_key] = lookup_component(combo_api["scales"], api_key, display_key, "combo scales")
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
    for group in STYLE_GROUPS:
        style_tabs.append(style_tab_from_styles4(group, styles4[group]))
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
    seen = set()
    for tid in list(QUANT_ORDER) + [tid for tid in zhizeng if tid not in QUANT_ORDER]:
        if tid in zhizeng and tid not in seen:
            tab = quant_tab(tid, zhizeng[tid])
            quant_tabs.append(tab)
            quant_asofs.append(tab["dates"][-1])
            seen.add(tid)
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

    kpi_vals = {key: pub_subj["series"][key][-1] for key in ABS_KEYS}
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

    pub_asof = _header_asof(pub, pub_abs["asOf"], "position_pub")
    etf_asof = _header_asof(etf, etf_sec["asOf"], "position_etf")
    doc = {
        "schemaVersion": "funds-mutual-v2",
        "generatedAt": now.isoformat(timespec="seconds"),
        "generatedAtDisplay": now.strftime("%Y-%m-%d %H:%M") + "（北京时间）",
        "asOf": pub_abs["asOf"],
        "timezone": "Asia/Shanghai",
        "sample": False,
        "universe": "lxwfof_position_pub",
        "note": build_note(pub_asof, etf_asof),
        "kpis": kpis,
        "funds": [],
        "sections": [combo, pub_abs, pub_style, pub_quant, etf_sec],
        "source": {
            "page": "https://lxwfof.com/#/position",
            "mcp": {
                "namespace": NAMESPACE,
                "datasets": list(DATASETS),
                "position_pub": _dataset_record(pub_meta, pub_asof, list(pub.keys())),
                "position_etf": _dataset_record(etf_meta, etf_asof, list(etf.keys())),
            },
            "gaps": list(GAPS),
            "compliance": COMPLIANCE,
        },
    }
    validate_document(doc)
    return doc


def _series_ok(series, n, role):
    if not isinstance(series, dict) or not series:
        raise RebuildError(f"{role}: series 缺失")
    for key, values in series.items():
        _require_values(values, n, f"{role} 序列「{key}」")


def validate_document(doc):
    if not isinstance(doc, dict):
        raise RebuildError("输出不是对象")
    if doc.get("schemaVersion") != "funds-mutual-v2":
        raise RebuildError("schemaVersion 不是 funds-mutual-v2")
    if doc.get("sample") is not False:
        raise RebuildError("sample 必须为 false")
    if doc.get("timezone") != "Asia/Shanghai":
        raise RebuildError("timezone 必须为 Asia/Shanghai")
    if doc.get("funds") != []:
        raise RebuildError("funds 必须为 []")
    generated = datetime.fromisoformat(doc.get("generatedAt") or "")
    if generated.utcoffset() is None or generated.utcoffset().total_seconds() != 8 * 3600:
        raise RebuildError("generatedAt 必须是 Asia/Shanghai（+08:00）")
    display = generated.strftime("%Y-%m-%d %H:%M") + "（北京时间）"
    if doc.get("generatedAtDisplay") != display:
        raise RebuildError("generatedAtDisplay 与 generatedAt 不一致")
    note = doc.get("note") or ""
    if COMPLIANCE not in note:
        raise RebuildError("note 缺少合规尾注")
    if not note.startswith("lxwfof MCP position_pub（asOf="):
        raise RebuildError("note 未标明 lxwfof MCP position_pub")
    if "position_etf（asOf=" not in note:
        raise RebuildError("note 未标明 position_etf")
    for bad in FORBIDDEN + NOTE_DENY:
        if bad in note:
            raise RebuildError(f"note 含禁止文案: {bad}")
    raw = json.dumps(doc, ensure_ascii=False)
    for bad in FORBIDDEN:
        if bad in raw:
            raise RebuildError(f"输出含禁止文案: {bad}")
    source = doc.get("source")
    if not isinstance(source, dict):
        raise RebuildError("source 缺失")
    if "pubApi" in source or "etfApi" in source:
        raise RebuildError("source 仍声称网页登录 API")
    if source.get("compliance") != COMPLIANCE:
        raise RebuildError("source.compliance 不是原样合规尾注")
    mcp = source.get("mcp")
    if not isinstance(mcp, dict) or mcp.get("namespace") != NAMESPACE:
        raise RebuildError("source.mcp.namespace 不是 lxwfof MCP")
    if mcp.get("datasets") != DATASETS:
        raise RebuildError("source.mcp.datasets 不是 position_pub / position_etf")
    if mcp.get("dataset") == "position" or "position-raw.json" in raw:
        raise RebuildError("私募 position 摘要被写成了本次取数")
    for name, as_key in (("position_pub", "position_pub"), ("position_etf", "position_etf")):
        block = mcp.get(as_key)
        if not isinstance(block, dict) or block.get("dataset") != name:
            raise RebuildError(f"source.mcp.{as_key} 缺失")
        if block.get("envelope") not in ("mcp_dataset", "legacy_api"):
            raise RebuildError(f"source.mcp.{as_key}.envelope 无法识别")
        if block.get("asOf") != _asof_in_note(note, name):
            raise RebuildError(f"{name} 的 source asOf 与 note 不一致")
    gaps = source.get("gaps")
    if not isinstance(gaps, list) or gaps != GAPS:
        raise RebuildError("source.gaps 与约定缺口不一致")
    if "产品自助" not in " ".join(gaps):
        raise RebuildError("产品自助缺口应只写在 source.gaps")
    sections = doc.get("sections")
    if not isinstance(sections, list) or [s.get("id") for s in sections] != SECTION_ORDER:
        raise RebuildError("sections 必须依次为 combo / pub_abs / pub_style / pub_quant / etf")
    by_id = {s["id"]: s for s in sections}
    for sid, kind in SECTION_KIND.items():
        if by_id[sid].get("kind") != kind:
            raise RebuildError(f"{sid} kind 不是 {kind}")
        if by_id[sid].get("unit") != "%":
            raise RebuildError(f"{sid} unit 不是 %")
    _check_combo(by_id["combo"])
    _check_tabs(by_id["pub_abs"], ["pub", "blend"], "pub_abs")
    _check_tabs(by_id["pub_style"], ["all", "blend", *STYLE_GROUPS], "pub_style")
    _check_tabs(by_id["pub_quant"], list(QUANT_ORDER), "pub_quant", allow_extra=True)
    _check_single(by_id["etf"])
    if by_id["pub_abs"]["asOf"] != by_id["pub_abs"]["tabs"][0]["dates"][-1]:
        raise RebuildError("pub_abs asOf 不是纯公募末点")
    if by_id["pub_style"]["asOf"] != by_id["pub_style"]["tabs"][0]["dates"][-1]:
        raise RebuildError("pub_style asOf 不是全部公募末点")
    quant_ends = [tab["dates"][-1] for tab in by_id["pub_quant"]["tabs"]]
    if by_id["pub_quant"]["asOf"] != max(quant_ends):
        raise RebuildError("pub_quant asOf 不是各页签末点的最大值")
    if doc.get("asOf") != by_id["pub_abs"]["asOf"]:
        raise RebuildError("顶层 asOf 不是主观公募绝对仓位末点")
    pub_tab = by_id["pub_abs"]["tabs"][0]
    expected = {
        "a_share_pos": pub_tab["series"]["A股总仓位"][-1],
        "hk_pos": pub_tab["series"]["港股"][-1],
        "total_equity": pub_tab["series"]["总股票仓位"][-1],
    }
    kpis = doc.get("kpis")
    if not isinstance(kpis, list) or [k.get("id") for k in kpis] != list(expected):
        raise RebuildError("kpis 缺失")
    for kpi in kpis:
        if kpi.get("value") != expected[kpi["id"]]:
            raise RebuildError(f"kpi {kpi['id']} 不是序列末点")
        if kpi.get("unit") != "%":
            raise RebuildError(f"kpi {kpi['id']} 单位不是 %")


def _asof_in_note(note, dataset):
    token = f"{dataset}（asOf="
    start = note.find(token)
    if start < 0:
        raise RebuildError(f"note 缺少 {dataset}")
    start += len(token)
    end = note.find("）", start)
    if end < 0:
        raise RebuildError(f"note 中 {dataset} 的 asOf 不完整")
    return note[start:end]


def _check_tab_label(tab, role):
    label = tab.get("label")
    expected = TAB_LABEL.get(tab.get("id"), tab.get("id"))
    if label != expected or not label:
        raise RebuildError(f"{role}: 页签 {tab.get('id')} 的中文标签不是 {expected!r}")


def _check_tabs(section, ids, role, allow_extra=False):
    tabs = section.get("tabs")
    got = [tab.get("id") for tab in tabs] if isinstance(tabs, list) else None
    ok = got is not None and (got[: len(ids)] == ids if allow_extra else got == ids)
    if not ok:
        raise RebuildError(f"{role}: 页签顺序不是 {ids}")
    for tab in tabs:
        _check_tab_label(tab, role)
        dates = require_dates(tab.get("dates"), f"{role}.{tab['id']}")
        _series_ok(tab.get("series"), len(dates), f"{role}.{tab['id']}")
        if tab["id"] == "pub":
            missing = [key for key in ABS_KEYS if key not in tab["series"]]
            if missing:
                raise RebuildError(f"{role}.pub 缺少 {missing}")
        if role == "pub_style":
            missing = [key for key in STYLE_KEYS if key not in tab["series"]]
            if missing:
                raise RebuildError(f"{role}.{tab['id']} 缺少 {missing}")
        if role == "pub_quant":
            missing = [key for key in ["总仓位", *QUANT_STYLE] if key not in tab["series"]]
            if missing:
                raise RebuildError(f"{role}.{tab['id']} 缺少 {missing}")


def _check_combo(section):
    dates = require_dates(section.get("dates"), "combo")
    _series_ok(section.get("series"), len(dates), "combo")
    if section.get("asOf") != dates[-1]:
        raise RebuildError("combo asOf 不是 dates 末点")
    if section.get("chips") != ["主动私募", "量化私募", "主动公募", "ETF"]:
        raise RebuildError("combo chips 不是中文四档")
    for chip in section["chips"]:
        _series_ok(section.get("parts", {}).get(chip), len(dates), f"combo.parts.{chip}")
        _require_values(section.get("scales", {}).get(chip), len(dates), f"combo.scales.{chip}")


def _check_single(section):
    dates = require_dates(section.get("dates"), "etf")
    _series_ok(section.get("series"), len(dates), "etf")
    if section.get("asOf") != dates[-1]:
        raise RebuildError("etf asOf 不是 dates 末点")
    for key in ("scale", "cnt"):
        if key in section:
            _require_values(section[key], len(dates), f"etf {key}")


def load_json(path: Path):
    text = Path(path).read_text(encoding="utf-8").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        try:
            obj, end = decoder.raw_decode(text)
        except json.JSONDecodeError as exc:
            raise RebuildError(f"{path}: JSON 无法解析: {exc}") from exc
        rest = text[end:].strip()
        if not rest:
            return obj
        if "{" in rest or _sensitive_key(rest) or "bearer " in rest.lower() or "authorization" in rest.lower():
            raise RebuildError(f"{path}: JSON 之后有无法识别的内容")
        if _COMPLIANCE_MARK not in rest:
            raise RebuildError(f"{path}: JSON 之后有无法识别的尾部")
        return obj


def dump_compact(doc) -> str:
    return json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n"


def report(path, doc) -> str:
    mcp = doc["source"]["mcp"]
    lines = [
        f"wrote {path}",
        f"generatedAt {doc['generatedAt']} {doc['generatedAtDisplay']}",
        f"source {mcp['namespace']} datasets={','.join(mcp['datasets'])}",
    ]
    for name in DATASETS:
        meta = mcp[name]
        lines.append(f"  {name} envelope={meta['envelope']} asOf={meta['asOf']}")
    for section in doc["sections"]:
        if "tabs" in section:
            tabs = ",".join(
                f"{tab['id']}/{tab['label']}:{len(tab['dates'])}@{tab['dates'][-1]}"
                for tab in section["tabs"]
            )
            lines.append(f"section {section['id']} asOf={section['asOf']} tabs {tabs}")
        else:
            dates = section["dates"]
            lines.append(
                f"section {section['id']} asOf={section['asOf']} "
                f"dates={len(dates)} {dates[0]}..{dates[-1]} series={len(section['series'])}"
            )
    lines.append("validate ok")
    text = "\n".join(lines)
    print(text)
    return text


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="用 lxwfof MCP position_pub / position_etf 重建 funds/data/mutual.json"
    )
    parser.add_argument("--pub", required=True, help="position_pub JSON：MCP {name,desc,kb,data} 或旧 {ok:true,data}")
    parser.add_argument("--etf", required=True, help="position_etf JSON：MCP {name,desc,kb,data} 或旧 {ok:true,data}")
    parser.add_argument("--out", required=True, help="输出 mutual.json 路径")
    parser.add_argument("--mcp-asof", default=None, help="已忽略。私募 position 的 asOf 不写入本次公募文件")
    parser.add_argument("--mcp-summary", default=None, help="已忽略。私募 position 摘要不作为本次公募取数")
    args = parser.parse_args(argv)
    ignored = [flag for flag, value in (("--mcp-asof", args.mcp_asof), ("--mcp-summary", args.mcp_summary)) if value]
    if ignored:
        print(
            "warning: 忽略 "
            + " / ".join(ignored)
            + "；私募 position 摘要不作为本次公募取数，未写入 mutual.json",
            file=sys.stderr,
        )
    try:
        doc = rebuild(load_json(args.pub), load_json(args.etf))
    except RebuildError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    out = Path(args.out)
    if not out.parent.exists():
        print(f"error: 输出目录不存在: {out.parent}", file=sys.stderr)
        return 1
    out.write_text(dump_compact(doc), encoding="utf-8")
    report(out, doc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
