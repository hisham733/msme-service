#!/usr/bin/env python3
"""N-7 sample measurement — measure the latest live MALAYSIA SME posts against the rule.

Read-only: fetches the WordPress REST API, computes per-article structure (H2, paragraphs,
words/paragraph, images, feature flag, chart candidates) and writes a JSON cache.

Usage:
    python3 tools/n7_measure.py            # fetch up to 100 and write /tmp/opencode/n7_metrics.json
    python3 tools/n7_measure.py --posts 50 # custom count

Proves: python3 -m compileall -q tools/n7_measure.py
"""
import argparse
import html as htmlmod
import json
import re
import statistics
import urllib.request

BASE = "https://www.malaysiasme.com.my/wp-json/wp/v2/posts"
UA = "Mozilla/5.0 (research; N-7 sample measurement)"
CACHE = "/tmp/opencode/n7_metrics.json"
CHART_RE = re.compile(r"chart|graph|infographic|figure|image0\d|data\s*source", re.I)


def _plain(t):
    return " ".join(htmlmod.unescape(re.sub(r"<[^>]+>", " ", t or "")).split())


def _fetch(posts):
    out, page = [], 1
    while page <= 2 and len(out) < posts:
        url = (f"{BASE}?per_page=100&page={page}&_embed=1"
               f"&_fields=id,date,title,content,featured_media,link")
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        batch = json.loads(urllib.request.urlopen(req, timeout=40).read().decode())
        if not batch:
            break
        out += batch
        if len(batch) < 100:
            break
        page += 1
    return out[:posts]


def _metrics(p):
    content = (p.get("content") or {}).get("rendered") or ""
    heads = [(m.start(), _plain(m.group(1)))
             for m in re.finditer(r"<h2[^>]*>(.*?)</h2>", content, re.S | re.I)]
    paras = [(_plain(m.group(1)), m.start())
             for m in re.finditer(r"<p[^>]*>(.*?)</p>", content, re.S | re.I)]
    paras = [(t, pos) for t, pos in paras if len(t.split()) >= 8]
    words = [len(t.split()) for t, _ in paras]
    imgs = re.findall(r"<img\b[^>]*>", content, re.I)
    img_srcs = []
    for tag in imgs:
        m = re.search(r'src="([^"]+)"', tag, re.I) or re.search(r"data-src=\"([^\"]+)\"", tag, re.I)
        alt = re.search(r'alt="([^"]*)"', tag, re.I)
        img_srcs.append({"src": (m.group(1) if m else ""), "alt": (alt.group(1) if alt else "")})
    featured = 0
    emb = (p.get("_embedded") or {}).get("wp:featuredmedia") or []
    if p.get("featured_media") and emb:
        featured = 1
    total_words = sum(words)
    is_feature = (len(paras) >= 17) or (total_words >= 1200)
    text = _plain(content)
    chart_hits = sorted({s.lower() for s in CHART_RE.findall(text)})
    chart_imgs = [i for i in img_srcs if CHART_RE.search(i["src"] + " " + i["alt"])]
    # paragraphs per heading (assign each paragraph to the preceding H2)
    sections, cur = [], "Opening"
    counters = {}
    for t, pos in paras:
        prev = [h for h in heads if h[0] < pos]
        cur = prev[-1][1] if prev else "Opening"
        counters[cur] = counters.get(cur, 0) + 1
    return {
        "id": p.get("id"), "date": (p.get("date") or "")[:10],
        "title": _plain((p.get("title") or {}).get("rendered") or ""),
        "url": p.get("link") or "",
        "h2": len(heads), "headings": [h[1] for h in heads],
        "n_paras": len(paras),
        "median_words": round(statistics.median(words), 1) if words else 0,
        "total_words": total_words,
        "in_body_imgs": len(imgs), "featured": featured,
        "total_imgs": featured + len(imgs),
        "feature": is_feature,
        "sections": counters,
        "img_srcs": img_srcs[:12],
        "chart_words": chart_hits,
        "chart_imgs": chart_imgs[:8],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--posts", type=int, default=100)
    a = ap.parse_args()
    posts = _fetch(a.posts)
    rows = [_metrics(p) for p in posts]
    json.dump(rows, open(CACHE, "w"), ensure_ascii=False, indent=1)
    rel = [r for r in rows if not r["feature"]]
    print(f"posts={len(rows)} releases={len(rel)} features={len(rows)-len(rel)} -> {CACHE}")
    print("median paras (releases):", statistics.median([r["n_paras"] for r in rel]))
    print("median words/para:", statistics.median([r["median_words"] for r in rows]) if rows else 0)
    print("charts flagged:", sum(1 for r in rows if r["chart_words"] or r["chart_imgs"]))


if __name__ == "__main__":
    main()
