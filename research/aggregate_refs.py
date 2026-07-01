#!/usr/bin/env python3
"""Aggregate research/refs-*.json into the site dataset:
  site/src/data/references.json  (deduped, normalized array)
  site/src/data/references-stats.json (facet counts)
"""
import json, os, glob, re
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "..", "site", "src", "data")
os.makedirs(OUT_DIR, exist_ok=True)

TOPIC_LABEL = {
    "palantir": "Palantir 起源",
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "google": "Google Cloud",
    "otherlabs": "其他 AI 公司",
    "china": "国内生态",
    "media": "媒体报道",
    "vc": "VC 与分析",
    "github": "开源项目",
    "community": "社区 / 播客",
    "cases": "落地案例",
    "china2": "国内长尾",
    "firstperson": "亲历者视角",
}
KNOWN_TYPES = {
    "official-jd", "company-blog", "media", "vc-analysis", "github",
    "x-thread", "youtube", "podcast", "forum", "cn-article", "academic",
    "levels", "other",
}


def norm_url(u: str) -> str:
    u = (u or "").strip()
    if not u:
        return ""
    p = urlparse(u)
    host = (p.netloc or "").lower().replace("www.", "")
    path = (p.path or "").rstrip("/")
    return f"{host}{path}".lower()


def domain_of(u: str) -> str:
    try:
        return (urlparse(u).netloc or "").lower().replace("www.", "")
    except Exception:
        return ""


records = {}
raw_total = 0
for fp in sorted(glob.glob(os.path.join(HERE, "refs-*.json"))):
    topic = re.sub(r"^refs-|\.json$", "", os.path.basename(fp))
    try:
        data = json.load(open(fp, encoding="utf-8"))
    except Exception as e:
        print("skip", fp, e)
        continue
    for it in data:
        raw_total += 1
        url = (it.get("url") or "").strip()
        if not url or not url.startswith("http"):
            continue
        key = norm_url(url)
        typ = it.get("type") or "other"
        if typ not in KNOWN_TYPES:
            typ = "other"
        company = it.get("company")
        if isinstance(company, str):
            company = company.strip() or None
        lang = it.get("lang") if it.get("lang") in ("en", "zh") else "en"
        year = it.get("year")
        if isinstance(year, (int, float)):
            year = str(int(year))
        if isinstance(year, str):
            year = year.strip() or None
        verified = bool(it.get("verified"))
        rec = {
            "title": (it.get("title") or "").strip(),
            "url": url,
            "domain": domain_of(url),
            "type": typ,
            "company": company,
            "lang": lang,
            "year": year,
            "note": (it.get("note") or "").strip(),
            "verified": verified,
            "topic": topic,
        }
        if key in records:
            ex = records[key]
            # prefer verified; prefer richer note; keep earliest topic but record both
            if verified and not ex["verified"]:
                ex["verified"] = True
            if len(rec["note"]) > len(ex["note"]):
                ex["note"] = rec["note"]
            if not ex["company"] and company:
                ex["company"] = company
            if not ex["year"] and year:
                ex["year"] = year
            ex.setdefault("topics", [ex["topic"]])
            if topic not in ex["topics"]:
                ex["topics"].append(topic)
        else:
            rec["topics"] = [topic]
            records[key] = rec

items = list(records.values())
# stable id + sort: verified first, then by topic then title
for i, r in enumerate(items):
    r["id"] = i
items.sort(key=lambda r: (not r["verified"], r["topic"], r["title"]))
for i, r in enumerate(items):
    r["id"] = i

# ---- stats ----
def count(field):
    out = {}
    for r in items:
        v = r.get(field)
        if isinstance(v, list):
            for x in v:
                out[x] = out.get(x, 0) + 1
        else:
            k = v if v else "(空)"
            out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))

stats = {
    "total": len(items),
    "raw_total": raw_total,
    "verified": sum(1 for r in items if r["verified"]),
    "by_topic": count("topics"),
    "by_type": count("type"),
    "by_lang": count("lang"),
    "by_company": count("company"),
    "topic_labels": TOPIC_LABEL,
}

json.dump(items, open(os.path.join(OUT_DIR, "references.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=0)
json.dump(stats, open(os.path.join(OUT_DIR, "references-stats.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

print(f"raw={raw_total}  deduped={len(items)}  verified={stats['verified']}")
print("by_topic:", stats["by_topic"])
print("by_type:", stats["by_type"])
print("by_lang:", stats["by_lang"])
print("top companies:", list(stats["by_company"].items())[:14])
