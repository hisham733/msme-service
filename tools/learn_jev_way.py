#!/usr/bin/env python3
"""Learn the best `_jev_best_qu` wording per question from the test report.

Reads docs/article-records.json (per-article, ALL variants), computes separation
(mean YES% on rejects − on accepts) for every variant, and writes the best variant's
instruction + criteria into `<question>_jev_best_qu`. Writes docs/jev-way-learning.md.

Usage:  python3 learn_jev_best_qu.py
"""
import datetime
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")

D = json.load(open(os.path.join(DOCS, "article-records.json")))
V = json.load(open(os.path.join(DOCS, "jev-variants.json")))
G, S_ = D["gates"], D["scores"]
COLS = D["cols"]
ALLQ = G + S_

recs = [r for r in D["records"] if r.get("hasArticle") and r.get("results")]
REJ = [r for r in recs if r.get("outcome") == "REJECT"]
ACC = [r for r in recs if r.get("outcome") == "ACCEPT"]


def idFor(b, c):
    return b if c == "base" else b + "_" + c


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs)) if xs else None


def yes(r, vid):
    return r["results"].get(vid)


Q = V["questions"]
rows = []
for b in ALLQ:
    seps = {}
    for c in COLS:
        vid = idFor(b, c)
        rv = mean([yes(r, vid) for r in REJ])
        av = mean([yes(r, vid) for r in ACC])
        if rv is not None and av is not None:
            seps[c] = rv - av
    if not seps:
        continue
    best = max(seps, key=lambda k: seps[k])
    tops = seps[best]
    src = Q[idFor(b, best)]
    Q[idFor(b, "jev_best_qu")] = {"type": "noul", "instructions": src["instructions"], "criteria": src["criteria"]}
    conf = "strong" if tops >= 30 else ("weak" if tops >= 10 else "none")
    rows.append((b, best, tops, conf))

json.dump(V, open(os.path.join(DOCS, "jev-variants.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.load(open(os.path.join(DOCS, "jev-variants.json"), encoding="utf-8"))  # validate

L = ["# Learned `jev_best_qu` — best wording from the test report", "",
     f"_Generated {datetime.datetime.now():%Y-%m-%d %H:%M} · articles={len(recs)} rejects={len(REJ)} accepts={len(ACC)}_", "",
     "`separation = mean YES%(rejects) − mean YES%(accepts)` (higher = cleaner). "
     "`_jev_best_qu` is set to the best variant. Confidence: strong ≥30, weak ≥10, none otherwise.", "",
     "| question | _jev_best_qu learns from | separation | confidence |", "|---|---|---:|---|"]
for b, best, tops, conf in rows:
    L.append(f"| {b} | {idFor(b, best)} | {tops} | {conf} |")
open(os.path.join(DOCS, "jev-way-learning.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

print(f"learned jev_best_qu for {len(rows)} questions (articles={len(recs)}, rejects={len(REJ)})")
for b, best, tops, conf in rows:
    print(f"  {b:28} <- {idFor(b, best):28} sep {tops:>4} [{conf}]")
