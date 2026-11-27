"""公募 mutual.json 重建：MCP dataset 与旧 API 包装、五区块、坏数据拒绝。"""
from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "rebuild_mutual_from_api",
    ROOT / "funds/scripts/rebuild_mutual_from_api.py",
)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

NOW = datetime(2026, 11, 24, 0, 30, tzinfo=ZoneInfo("Asia/Shanghai"))
PUB_DATES = ["2024-01-05", "2024-01-12"]
BLEND_DATES = ["2024-01-05", "2024-01-12"]
STYLE_DATES = ["2024-01-08", "2024-01-15"]
QUANT_DATES = ["2024-01-09", "2024-01-16"]
COMBO_DATES = ["2024-01-03", "2024-01-10"]
ETF_DATES = ["2024-01-02", "2024-01-17"]
EXTRA_DATES = ["2024-02-01", "2024-02-08"]

# 本轮 position_pub / position_etf 落盘后的末点与长度。序列本身仍以文件内 dates 为准。
PUBLISHED = {
    "combo": {"asOf": "2026-11-13", "n": 359, "start": "2020-01-03"},
    "pub": {"asOf": "2026-11-17", "n": 1920, "start": "2015-01-09"},
    "blend": {"asOf": "2026-11-13", "n": 329, "start": "2020-01-03"},
    "style_group": {"asOf": "2026-11-13", "n": 652, "start": "2015-01-05"},
    "quant": {
        "300指增": (608, "2015-01-09"),
        "500指增": (608, "2015-01-09"),
        "1000指增": (423, "2018-08-17"),
        "2000指增": (115, "2024-09-06"),
        "A500指增": (71, "2025-07-11"),
        "双创指增": (413, "2018-11-02"),
        "800指增": (154, "2023-12-01"),
        "上证指增": (308, "2020-11-20"),
        "国证指增": (161, "2023-10-13"),
        "A50指增": (110, "2024-10-11"),
        "红利指增": (335, "2020-05-15"),
        "主动量化": (608, "2015-01-09"),
    },
    "quant_asOf": "2026-11-20",
    "etf": {"asOf": "2026-11-20", "n": 2399, "start": "2017-01-03"},
    "kpis": {"a_share_pos": 79.65, "hk_pos": 10.48, "total_equity": 90.13},
}


def _nums(n, base):
    return [round(base + i * 0.25, 2) for i in range(n)]


def _series(n, keys, base=10.0):
    return {key: _nums(n, base + offset) for offset, key in enumerate(keys)}


def _block(dates, keys, total=False, base=10.0):
    block = {"dates": list(dates), "series": _series(len(dates), keys, base)}
    if total:
        block["total"] = _nums(len(dates), 80)
    return block


def _pub_payload(extra_quant=False, part_api_key="主观私募"):
    subj_keys = list(dict.fromkeys(mod.ABS_KEYS + mod.STYLE_KEYS))
    style_lines = [key for key in mod.STYLE_KEYS if key != "总股票仓位"]
    part_keys = ["沪深300", "A股总仓位", "港股"]
    parts, scales = {}, {"dates": list(COMBO_DATES)}
    for key in ("量化私募", "主观私募", "主动公募", "ETF"):
        stored = part_api_key if key == "主观私募" else key
        parts[stored] = _series(len(COMBO_DATES), part_keys, 20)
        scales[stored] = _nums(len(COMBO_DATES), 1000)
    zhizeng = {
        name: _block(QUANT_DATES, mod.QUANT_STYLE, total=True, base=30)
        for name in mod.QUANT_ORDER
    }
    if extra_quant:
        zhizeng["测试指增"] = _block(EXTRA_DATES, mod.QUANT_STYLE, total=True, base=40)
    return {
        "asof": PUB_DATES[-1],
        "pub": {
            "subjective": _block(PUB_DATES, subj_keys, base=50),
            "styles4": {name: _block(STYLE_DATES, style_lines, total=True) for name in mod.STYLE_GROUPS},
            "zhizeng": zhizeng,
        },
        "blend": {"subjective": _block(BLEND_DATES, subj_keys, base=60)},
        "combo": {
            "dates": list(COMBO_DATES),
            "series": _series(len(COMBO_DATES), part_keys, 30),
            "parts": parts,
            "scales": scales,
            "note": "规模加权",
        },
        "accuracy": {"text": "持仓校准版", "asof": PUB_DATES[-1]},
        "accuracy_zz": {"text": "指增准确度", "asof": QUANT_DATES[-1]},
        "zhizeng_calibrated": True,
    }


def _etf_payload():
    keys = ["沪深300", "A股总仓位", "总股票仓位", "美股", "未拆分"]
    return {
        "asof": ETF_DATES[-1],
        "dates": list(ETF_DATES),
        "series": _series(len(ETF_DATES), keys, 70),
        "scale": _nums(len(ETF_DATES), 30000),
        "cnt": [100, 101],
        "note": "ETF 穿透",
    }


def _mcp(name, payload):
    return {"name": name, "desc": "dataset", "kb": 1, "data": payload}


def _legacy(payload):
    return {"ok": True, "data": payload}


def _rebuild(pub_wrap, etf_wrap=None):
    return mod.rebuild(pub_wrap, etf_wrap if etf_wrap is not None else _mcp("position_etf", _etf_payload()), NOW)


class RebuildMutualTests(unittest.TestCase):
    def test_mcp_envelope_builds_five_sections_and_labels_source(self):
        doc = _rebuild(_mcp("position_pub", _pub_payload(extra_quant=True)))
        self.assertEqual([s["id"] for s in doc["sections"]], mod.SECTION_ORDER)
        self.assertFalse(doc["sample"])
        self.assertEqual(doc["funds"], [])
        self.assertEqual(doc["asOf"], PUB_DATES[-1])
        self.assertEqual(
            doc["note"],
            "lxwfof MCP position_pub（asOf=2024-01-12），"
            "position_etf（asOf=2024-01-17）。"
            "【部分信息参考自lxwfof MCP】",
        )
        self.assertEqual(doc["source"]["compliance"], "【部分信息参考自lxwfof MCP】")
        self.assertEqual(doc["source"]["mcp"]["namespace"], "lxwfof MCP")
        self.assertEqual(doc["source"]["mcp"]["datasets"], ["position_pub", "position_etf"])
        self.assertEqual(doc["source"]["mcp"]["position_pub"]["envelope"], "mcp_dataset")
        self.assertEqual(doc["source"]["mcp"]["position_etf"]["envelope"], "mcp_dataset")
        self.assertNotIn("pubApi", doc["source"])
        self.assertNotIn("etfApi", doc["source"])
        for bad in ("产品自助拆分未入库。", "公募仓位重建自 lxwfof", "/api/position/", "网页登录", "仅含私募"):
            self.assertNotIn(bad, json.dumps(doc, ensure_ascii=False))
        self.assertTrue(any("产品自助" in gap for gap in doc["source"]["gaps"]))

        by_id = {s["id"]: s for s in doc["sections"]}
        self.assertEqual(by_id["combo"]["asOf"], COMBO_DATES[-1])
        self.assertEqual(len(by_id["combo"]["dates"]), len(COMBO_DATES))
        self.assertEqual(by_id["pub_abs"]["asOf"], PUB_DATES[-1])
        self.assertEqual(by_id["pub_style"]["asOf"], PUB_DATES[-1])
        self.assertEqual(by_id["pub_quant"]["asOf"], EXTRA_DATES[-1])
        self.assertEqual(by_id["etf"]["asOf"], ETF_DATES[-1])
        self.assertEqual(
            [(t["id"], t["label"], len(t["dates"]), t["dates"][-1]) for t in by_id["pub_abs"]["tabs"]],
            [("pub", "纯公募", 2, PUB_DATES[-1]), ("blend", "公募+私募", 2, BLEND_DATES[-1])],
        )
        style_ids = ["all", "blend", *mod.STYLE_GROUPS]
        self.assertEqual([t["id"] for t in by_id["pub_style"]["tabs"]], style_ids)
        self.assertEqual(by_id["pub_style"]["tabs"][0]["label"], "全部公募")
        self.assertEqual(by_id["pub_style"]["tabs"][2]["label"], "价值")
        quant_ids = [*mod.QUANT_ORDER, "测试指增"]
        self.assertEqual([t["id"] for t in by_id["pub_quant"]["tabs"]], quant_ids)
        self.assertEqual(by_id["pub_quant"]["tabs"][-1]["label"], "测试指增")
        for section in doc["sections"]:
            if "tabs" in section:
                for tab in section["tabs"]:
                    n = len(tab["dates"])
                    for key, values in tab["series"].items():
                        self.assertEqual(len(values), n, f"{section['id']}.{tab['id']}.{key}")
                    self.assertTrue(tab["label"])
            else:
                n = len(section["dates"])
                for key, values in section["series"].items():
                    self.assertEqual(len(values), n, f"{section['id']}.{key}")
        self.assertEqual(doc["kpis"][0]["value"], by_id["pub_abs"]["tabs"][0]["series"]["A股总仓位"][-1])
        self.assertEqual(doc["generatedAt"], "2026-11-24T00:30:00+08:00")
        self.assertEqual(doc["generatedAtDisplay"], "2026-11-24 00:30（北京时间）")

    def test_legacy_api_wrapper_matches_mcp_sections(self):
        payload = _pub_payload()
        etf = _etf_payload()
        mcp_doc = _rebuild(_mcp("position_pub", payload), _mcp("position_etf", etf))
        legacy_doc = _rebuild(_legacy(payload), _legacy(etf))
        nested_doc = _rebuild(
            {"ok": True, "data": _mcp("position_pub", payload)},
            {"ok": True, "data": _mcp("position_etf", etf)},
        )
        self.assertEqual(mcp_doc["sections"], legacy_doc["sections"])
        self.assertEqual(mcp_doc["sections"], nested_doc["sections"])
        self.assertEqual(mcp_doc["note"], legacy_doc["note"])
        self.assertEqual(legacy_doc["source"]["mcp"]["position_pub"]["envelope"], "legacy_api")
        self.assertEqual(nested_doc["source"]["mcp"]["position_pub"]["envelope"], "mcp_dataset")
        self.assertEqual(nested_doc["source"]["mcp"]["position_pub"]["outerEnvelope"], "legacy_api")
        self.assertNotIn("/api/position/pub", legacy_doc["note"])
        self.assertNotIn("网页登录", json.dumps(legacy_doc, ensure_ascii=False))

    def test_display_key_alias_for_subjective_private_bucket(self):
        doc = _rebuild(_legacy(_pub_payload(part_api_key="主动私募")))
        combo = doc["sections"][0]
        self.assertIn("主动私募", combo["parts"])
        self.assertNotIn("主观私募", combo["parts"])
        self.assertEqual(len(combo["scales"]["主动私募"]), len(combo["dates"]))

    def test_stale_private_summary_is_not_this_fetch(self):
        pub = _mcp("position_pub", _pub_payload())
        etf = _mcp("position_etf", _etf_payload())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pub_path = root / "pub.json"
            etf_path = root / "etf.json"
            stale = root / "position-summary.json"
            out = root / "mutual.json"
            pub_path.write_text(json.dumps(pub, ensure_ascii=False), encoding="utf-8")
            etf_path.write_text(json.dumps(etf, ensure_ascii=False) + "\n【部分信息参考自lxwfof MCP】\n", encoding="utf-8")
            stale.write_text(json.dumps({"asof": "1999-01-01", "keys": ["text", "subjective"]}), encoding="utf-8")
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = mod.main([
                    "--pub", str(pub_path),
                    "--etf", str(etf_path),
                    "--out", str(out),
                    "--mcp-summary", str(stale),
                    "--mcp-asof", "1999-01-01",
                ])
            self.assertEqual(code, 0)
            text = out.read_text(encoding="utf-8")
            self.assertNotIn("1999-01-01", text)
            self.assertNotIn("position-raw.json", text)
            self.assertNotIn("仅含私募", text)
            self.assertIn("【部分信息参考自lxwfof MCP】", text)
            self.assertTrue(text.endswith("\n"))
            self.assertEqual(text.count("\n"), 1)
            self.assertIn("忽略", stderr.getvalue())
            self.assertIn("validate ok", stdout.getvalue())
            self.assertIn("position_pub envelope=mcp_dataset asOf=2024-01-12", stdout.getvalue())
            self.assertIn("position_etf envelope=mcp_dataset asOf=2024-01-17", stdout.getvalue())

    def test_bad_inputs_are_rejected_and_not_written(self):
        good_pub = _mcp("position_pub", _pub_payload())
        good_etf = _mcp("position_etf", _etf_payload())
        cases = {
            "ok-false": ({"ok": False, "error": "denied"}, good_etf),
            "wrong-dataset": (_mcp("position", {"asof": "2024-01-12", "subjective": {}, "text": ""}), good_etf),
            "private-legacy": (_legacy({"asof": "2024-01-12", "subjective": {"dates": PUB_DATES}, "zhizeng": {}}), good_etf),
            "etf-name-on-pub": (_mcp("position_etf", _etf_payload()), good_etf),
            "not-object": (["nope"], good_etf),
            "secret": ({**good_pub, "Authorization": "Bearer SUPERSECRET"}, good_etf),
        }
        short = _pub_payload()
        short["pub"]["subjective"]["series"]["A股总仓位"] = [1.0]
        cases["length"] = (_mcp("position_pub", short), good_etf)
        dirty = _pub_payload()
        dirty["pub"]["subjective"]["series"]["港股"] = ["10.48", 10.0]
        cases["text-number"] = (_mcp("position_pub", dirty), good_etf)
        unordered = _pub_payload()
        unordered["pub"]["subjective"]["dates"] = ["2024-01-12", "2024-01-05"]
        unordered["asof"] = "2024-01-05"
        cases["unordered"] = (_mcp("position_pub", unordered), good_etf)
        mismatch = _pub_payload()
        mismatch["asof"] = "2024-01-01"
        cases["asof-mismatch"] = (_mcp("position_pub", mismatch), good_etf)
        missing_part = _pub_payload()
        del missing_part["combo"]["parts"]["主观私募"]
        del missing_part["combo"]["scales"]["主观私募"]
        cases["missing-part"] = (_mcp("position_pub", missing_part), good_etf)
        bad_etf = _etf_payload()
        bad_etf["series"]["A股总仓位"] = [None, "bad"]
        cases["bad-etf"] = (good_pub, _mcp("position_etf", bad_etf))

        for name, (pub_wrap, etf_wrap) in cases.items():
            with self.subTest(name=name):
                with self.assertRaises(mod.RebuildError) as caught:
                    mod.rebuild(pub_wrap, etf_wrap, NOW)
                self.assertNotIn("SUPERSECRET", str(caught.exception))

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pub_path = root / "pub.json"
            etf_path = root / "etf.json"
            out = root / "mutual.json"
            pub_path.write_text(json.dumps({"ok": False, "error": "denied"}), encoding="utf-8")
            etf_path.write_text(json.dumps(good_etf), encoding="utf-8")
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                code = mod.main(["--pub", str(pub_path), "--etf", str(etf_path), "--out", str(out)])
            self.assertEqual(code, 1)
            self.assertFalse(out.exists())
            self.assertIn("旧 API 包装失败", stderr.getvalue())

    def test_trailing_compliance_line_parses_and_garbage_tail_does_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pub.json"
            path.write_text(json.dumps(_mcp("position_pub", _pub_payload())) + "\n【部分信息参考自lxwfof MCP】\n", encoding="utf-8")
            loaded = mod.load_json(path)
            self.assertEqual(loaded["name"], "position_pub")
            path.write_text(json.dumps({"ok": True, "data": {}}) + "\n{\"token\":\"SECRET\"}\n", encoding="utf-8")
            with self.assertRaises(mod.RebuildError):
                mod.load_json(path)

    def test_ui_keeps_chinese_tabs_and_two_decimals(self):
        html = (ROOT / "funds/index.html").read_text(encoding="utf-8")
        self.assertIn('const TAB_LABEL = { pub: "纯公募", blend: "公募+私募", all: "全部公募" };', html)
        self.assertIn("function fmtNum(v, d = 2)", html)
        self.assertIn('mutual: { file: "data/mutual.json"', html)

    def test_published_mutual_json(self):
        path = ROOT / "funds/data/mutual.json"
        raw = path.read_text(encoding="utf-8")
        self.assertTrue(raw.endswith("\n"))
        self.assertEqual(raw.count("\n"), 1)
        doc = json.loads(raw)
        mod.validate_document(doc)
        self.assertEqual(
            doc["note"],
            "lxwfof MCP position_pub（asOf=2026-11-17），"
            "position_etf（asOf=2026-11-20）。"
            "【部分信息参考自lxwfof MCP】",
        )
        self.assertEqual(doc["source"]["compliance"], "【部分信息参考自lxwfof MCP】")
        self.assertEqual(doc["source"]["mcp"]["position_pub"]["envelope"], "mcp_dataset")
        self.assertEqual(doc["source"]["mcp"]["position_etf"]["envelope"], "mcp_dataset")
        self.assertNotEqual(doc["generatedAt"], "2026-11-19T21:34:11+08:00")
        self.assertGreater(doc["generatedAt"], "2026-11-23T00:00:00+08:00")
        self.assertRegex(doc["generatedAt"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+08:00$")
        by_id = {s["id"]: s for s in doc["sections"]}
        combo = by_id["combo"]
        self.assertEqual(combo["asOf"], PUBLISHED["combo"]["asOf"])
        self.assertEqual(combo["dates"][0], PUBLISHED["combo"]["start"])
        self.assertEqual(len(combo["dates"]), PUBLISHED["combo"]["n"])
        self.assertEqual(combo["dates"][-1], combo["asOf"])
        pub_tabs = {t["id"]: t for t in by_id["pub_abs"]["tabs"]}
        self.assertEqual(pub_tabs["pub"]["label"], "纯公募")
        self.assertEqual(len(pub_tabs["pub"]["dates"]), PUBLISHED["pub"]["n"])
        self.assertEqual(pub_tabs["pub"]["dates"][0], PUBLISHED["pub"]["start"])
        self.assertEqual(pub_tabs["pub"]["dates"][-1], PUBLISHED["pub"]["asOf"])
        self.assertEqual(len(pub_tabs["blend"]["dates"]), PUBLISHED["blend"]["n"])
        self.assertEqual(pub_tabs["blend"]["dates"][-1], PUBLISHED["blend"]["asOf"])
        self.assertEqual(by_id["pub_abs"]["asOf"], PUBLISHED["pub"]["asOf"])
        style_tabs = {t["id"]: t for t in by_id["pub_style"]["tabs"]}
        self.assertEqual(style_tabs["all"]["label"], "全部公募")
        self.assertEqual(len(style_tabs["all"]["dates"]), PUBLISHED["pub"]["n"])
        self.assertEqual(style_tabs["blend"]["label"], "公募+私募")
        for name in mod.STYLE_GROUPS:
            tab = style_tabs[name]
            self.assertEqual(tab["label"], name)
            self.assertEqual(len(tab["dates"]), PUBLISHED["style_group"]["n"])
            self.assertEqual(tab["dates"][0], PUBLISHED["style_group"]["start"])
            self.assertEqual(tab["dates"][-1], PUBLISHED["style_group"]["asOf"])
        self.assertEqual(by_id["pub_style"]["asOf"], PUBLISHED["pub"]["asOf"])
        quant_tabs = {t["id"]: t for t in by_id["pub_quant"]["tabs"]}
        self.assertEqual(list(quant_tabs), list(mod.QUANT_ORDER))
        for name, (n, start) in PUBLISHED["quant"].items():
            tab = quant_tabs[name]
            self.assertEqual(tab["label"], name)
            self.assertEqual(len(tab["dates"]), n)
            self.assertEqual(tab["dates"][0], start)
            self.assertEqual(tab["dates"][-1], PUBLISHED["quant_asOf"])
            for key, values in tab["series"].items():
                self.assertEqual(len(values), n, name + "." + key)
        self.assertEqual(by_id["pub_quant"]["asOf"], PUBLISHED["quant_asOf"])
        etf = by_id["etf"]
        self.assertEqual(etf["asOf"], PUBLISHED["etf"]["asOf"])
        self.assertEqual(etf["dates"][0], PUBLISHED["etf"]["start"])
        self.assertEqual(len(etf["dates"]), PUBLISHED["etf"]["n"])
        self.assertEqual(len(etf["scale"]), PUBLISHED["etf"]["n"])
        self.assertEqual(len(etf["cnt"]), PUBLISHED["etf"]["n"])
        for kpi in doc["kpis"]:
            self.assertEqual(kpi["value"], PUBLISHED["kpis"][kpi["id"]])
        self.assertGreater(len(combo["dates"]), 100)
        self.assertGreater(len(etf["dates"]), 1000)
        self.assertFalse(doc["sample"])


if __name__ == "__main__":
    unittest.main()
