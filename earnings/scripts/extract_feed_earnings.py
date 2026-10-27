#!/usr/bin/env python3
"""从 data-dashboard 信息流抽取机构提到的财报数字，合并进 earnings.json。

规则：只取 title+summary 中明确写出的数字；与面板交叉比对；
一致→note 标注「信息流·机构名·日期」；冲突→note 两边数值、不覆盖 overrides/已有一致预期；
不写入研报/条目 url（用户要求不挂链接）。可选 feedExtracts 供详情展示。
"""
from __future__ import annotations
import argparse, json, re, datetime as dt
from datetime import timezone, timedelta
from pathlib import Path

BJ = timezone(timedelta(hours=8))
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FEED = Path("/workspace/data-dashboard/data/feed.json")
DEFAULT_EARN = ROOT / "data" / "earnings.json"

COS = {
    "AAPL": ["苹果", "Apple", "AAPL"],
    "MSFT": ["微软", "Microsoft", "MSFT"],
    "GOOGL": ["谷歌", "Alphabet", "Google", "GOOGL", "GOOG"],
    "AMZN": ["亚马逊", "Amazon", "AMZN"],
    "META": ["Meta", "脸书", "Facebook", "META"],
    "NVDA": ["英伟达", "NVIDIA", "Nvidia", "NVDA"],
    "TSLA": ["特斯拉", "Tesla", "TSLA"],
    "TSM": ["台积电", "TSMC", "TSM"],
    "AMD": ["AMD"],
    "AVGO": ["博通", "Broadcom", "AVGO"],
    "0700.HK": ["腾讯", "Tencent", "0700"],
    "BABA": ["阿里巴巴", "阿里", "Alibaba", "BABA"],
    "BIDU": ["百度", "Baidu", "BIDU"],
    "JD": ["京东", "JD.com", "京东集团"],
    "3690.HK": ["美团", "Meituan", "3690"],
    "PDD": ["拼多多", "PDD", "Pinduoduo"],
    "1810.HK": ["小米", "Xiaomi", "1810"],
    "NTES": ["网易", "NetEase", "NTES"],
    "0981.HK": ["中芯", "SMIC", "中芯国际", "0981", "688981"],
    "1211.HK": ["比亚迪", "BYD", "1211", "002594"],
}
KW = re.compile(
    r"财报|业绩|earnings|EPS|营收|收入|净利润|指引|outlook|guidance|超预期|不及预期|"
    r"beat|miss|一致预期|分析师预期|consensus|GAAP|非GAAP|Non-GAAP|摊薄|每股收益|revenue|预告|快报",
    re.I,
)


def match_cos(text: str) -> list[str]:
    hits = []
    for sym, als in COS.items():
        for a in als:
            if re.match(r"^[A-Za-z0-9.]+$", a):
                if re.search(r"(?<![A-Za-z0-9])" + re.escape(a) + r"(?![A-Za-z0-9])", text, re.I):
                    hits.append(sym)
                    break
            elif a in text:
                hits.append(sym)
                break
    return hits


def extract_fields(text: str) -> dict:
    fields: dict = {}
    m = re.search(r"总营收共识约?\s*([\d]+(?:\.[\d]+)?)\s*亿\s*美元（\+?\s*([\d]+(?:\.[\d]+)?)%\s*）", text)
    if m:
        fields["revConsensusUsd"] = round(float(m.group(1)) * 1e8)
        fields["revConsensusYoY"] = float(m.group(2)) / 100
        fields["revConsensusText"] = f"约{m.group(1)}亿美元（+{m.group(2)}%）"
    m = re.search(r"云收入(?:最新)?一致预期约?\s*([\d]+(?:\.[\d]+)?)\s*亿\s*美元（\+?\s*([\d]+(?:\.[\d]+)?)%\s*）", text)
    if m:
        fields["cloudRevConsensusUsd"] = round(float(m.group(1)) * 1e8)
        fields["cloudRevConsensusYoY"] = float(m.group(2)) / 100
        fields["cloudRevConsensusText"] = f"约{m.group(1)}亿美元（+{m.group(2)}%）"
    m = re.search(r"搜索约\+?\s*([\d]+(?:\.[\d]+)?)%", text)
    if m:
        fields["searchYoY"] = float(m.group(1)) / 100
    m = re.search(r"YouTube广告约\+?\s*([\d]+(?:\.[\d]+)?)%", text)
    if m:
        fields["youtubeAdsYoY"] = float(m.group(1)) / 100
    m = re.search(r"(?:实际|公布|报出)[^。]{0,20}EPS[^\d]{0,6}([\d\.]+)", text, re.I)
    if m:
        fields["epsActual"] = float(m.group(1))
    m = re.search(r"(?:预期|估计|共识)[^。]{0,20}EPS[^\d]{0,6}([\d\.]+)", text, re.I)
    if m:
        fields["epsEstimate"] = float(m.group(1))
    return fields


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feed", type=Path, default=DEFAULT_FEED)
    ap.add_argument("--earn", type=Path, default=DEFAULT_EARN)
    ap.add_argument("--days", type=int, default=14, help="只看近 N 天；条目很少时脚本会自动用全部")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    raw = json.load(open(a.feed))
    items = raw["items"] if isinstance(raw, dict) else raw
    if len(items) <= 120:
        window = items  # 全部
        print(f"[feed] {len(items)} items → use all")
    else:
        cut = dt.datetime.now(BJ) - dt.timedelta(days=a.days)
        window = []
        for it in items:
            try:
                t = dt.datetime.fromisoformat(it["publishedAt"].replace("Z", "+00:00"))
            except Exception:
                continue
            if t.astimezone(BJ) >= cut:
                window.append(it)
        print(f"[feed] {len(items)} total, {len(window)} in last {a.days}d")

    matched, skips = [], []
    for it in window:
        text = (it.get("title") or "") + "\n" + (it.get("summary") or "")
        if not KW.search(text):
            continue
        syms = match_cos(text)
        if not syms:
            continue
        fields = extract_fields(text)
        excerpt = None
        for part in re.split(r"[。\n]", text):
            if re.search(r"共识|一致预期|EPS|营收|指引", part):
                excerpt = part.strip()[:180]
                break
        if not fields:
            skips.append(
                {
                    "symbols": syms,
                    "sourceName": it.get("sourceName"),
                    "title": (it.get("title") or "")[:80],
                    "reason": "company+earnings keywords but no explicit numbers",
                }
            )
            continue
        for sym in syms:
            matched.append(
                {
                    "symbol": sym,
                    "sourceName": it.get("sourceName"),
                    "publishedAt": it.get("publishedAt"),
                    "fields": fields,
                    "excerpt": excerpt,
                }
            )

    earn = json.load(open(a.earn))
    by = {c["symbol"]: c for c in earn["companies"]}
    written, conflicts = [], []
    for ex in matched:
        c = by.get(ex["symbol"])
        if not c:
            continue
        tag = f"信息流·{ex['sourceName']}·{(ex['publishedAt'] or '')[:10]}"
        fe = {
            "sourceName": ex["sourceName"],
            "publishedAt": ex["publishedAt"],
            "fields": ex["fields"],
            "excerpt": ex["excerpt"],
        }
        notes_bits = []
        f = ex["fields"]
        if "revConsensusUsd" in f and c.get("consensus") and c["consensus"].get("revAvg"):
            panel = c["consensus"]["revAvg"]
            feed_v = f["revConsensusUsd"]
            rel = abs(panel - feed_v) / max(abs(panel), 1)
            if rel < 0.02:
                notes_bits.append(
                    f"{tag}：Q3总营收共识{f.get('revConsensusText','')}，与面板Yahoo一致预期约{panel/1e8:.0f}亿美元基本一致"
                )
                fe["agreeWith"] = ["consensus.revAvg"]
            else:
                conflicts.append({"symbol": ex["symbol"], "field": "revAvg", "panel": panel, "feed": feed_v, "tag": tag})
                notes_bits.append(
                    f"{tag}：信息流总营收共识{f.get('revConsensusText')}；面板Yahoo revAvg={panel/1e8:.2f}亿美元——冲突，保留面板值不覆盖"
                )
                fe["conflictWith"] = ["consensus.revAvg"]
        elif "revConsensusUsd" in f:
            if not c.get("consensus") or c["consensus"].get("revAvg") is None:
                c.setdefault("consensus", {})["revAvg"] = f["revConsensusUsd"]
                if "revConsensusYoY" in f:
                    c["consensus"]["revGrowth"] = f["revConsensusYoY"]
                written.append(f"{ex['symbol']}.consensus.revAvg")
                notes_bits.append(f"{tag}：写入总营收共识{f.get('revConsensusText')}（面板原无）")
            else:
                notes_bits.append(f"{tag}：摘录总营收共识{f.get('revConsensusText')}")

        segs = []
        if "cloudRevConsensusText" in f:
            segs.append(f"云收入一致预期{f['cloudRevConsensusText']}")
        if "searchYoY" in f:
            segs.append(f"搜索约+{f['searchYoY']*100:.0f}%")
        if "youtubeAdsYoY" in f:
            segs.append(f"YouTube广告约+{f['youtubeAdsYoY']*100:.0f}%")
        if segs:
            notes_bits.append("另摘" + "、".join(segs))
            written.append(f"{ex['symbol']}.note segments")

        existing = [x for x in (c.get("feedExtracts") or []) if (x.get("sourceName"), x.get("publishedAt")) != (ex["sourceName"], ex["publishedAt"])]
        existing.append(fe)
        c["feedExtracts"] = existing
        written.append(f"{ex['symbol']}.feedExtracts")

        new_note = "；".join(notes_bits)
        old = c.get("note") or ""
        parts = [p for p in re.split(r"；", old) if p.strip() and tag not in p]
        parts.append(new_note)
        c["note"] = "；".join(parts)
        written.append(f"{ex['symbol']}.note")

    earn["updated"] = dt.datetime.now(BJ).isoformat(timespec="seconds")
    report = {"extracts": len(matched), "written": written, "conflicts": conflicts, "skips": skips}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not a.dry_run:
        json.dump(earn, open(a.earn, "w"), ensure_ascii=False, indent=1)
        print("[ok] wrote", a.earn)


if __name__ == "__main__":
    main()
