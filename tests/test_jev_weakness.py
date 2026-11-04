#!/usr/bin/env python3
"""Test Jev's weak filters in NO-LLM mode.

Runs a battery of synthetic + real articles through the filter service (:8900)
with the LLM assist OFF (ENABLE_LLM_ASSIST=false), so Jev's calibrated routing
plus the deterministic `_route_ambiguity` are exercised directly. Each run is
logged to data/filter_verdicts.jsonl (the normal verdict log); nothing is deleted.

Usage:
    python test_jev_weakness.py                 # synthetic + real
    python test_jev_weakness.py --synthetic-only
    python test_jev_weakness.py --real-only
    python test_jev_weakness.py --limit 5

Output notes:
    - "AMBIGUOUS_<GATE>"  => a weak gate sat in [0.5, 0.85) on an ACCEPT -> EDITOR REVIEW
    - "BORDERLINE"        => weighted in [45, 65] -> EDITOR REVIEW
"""
import argparse
import glob
import json
import os
import sys
import urllib.request

BASE = os.environ.get("FILTER_URL", "http://127.0.0.1:8900/filter")
EMAILS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "emails")

WEAK_GATES = ("no_wider_value", "not_geographically_relevant", "defamatory", "political")

SYNTHETIC = [
    ("Acme appoints a manager (no_wider_value)", "no_wider_value / EDITOR REVIEW",
     "Acme Sdn Bhd is pleased to announce the appointment of Encik Rizal bin Hamid as its "
     "new regional sales manager, effective 1 November. He brings 15 years of experience in "
     "distribution and will lead the company's expansion in the northern region."),
    ("Company X wins Top Employer award (no_wider_value)", "no_wider_value / REJECT",
     "Company X Strategic Sdn Bhd was named a Top Employer 2026 by an independent body. The "
     "award recognises our internal HR practices and employee programmes. We thank our staff "
     "for their dedication."),
    ("US small-business tax overhaul (geo)", "not_geographically_relevant / EDITOR REVIEW",
     "WASHINGTON — In a landmark move, the United States Treasury announced a sweeping overhaul "
     "of small-business taxation, cutting income tax rates for firms with under 500 employees "
     "and introducing new quarterly filing rules. Federal officials said the changes take "
     "effect next tax year."),
    ("Viral defamation claim (defamatory)", "defamatory / EDITOR REVIEW",
     "A widely shared post claims that trusted baby formula brand Company X's milk formula is "
     "unsafe and was linked to illness in several infants. The post offers no evidence and "
     "cites unnamed 'internal documents'."),
    ("Vote out the worst government (political partisan)", "political / EDITOR REVIEW",
     "Vote them out! This is the worst government in Malaysian history; the current "
     "administration treats ordinary voters like fools and must be removed at the next "
     "election. Authorised by the party secretariat."),
    ("50% OFF our ERP (commercial)", "is_it_commercial_intent / REJECT",
     "50% OFF our cloud ERP this month only. Sign up now, limited slots, buy one year get one "
     "free. Prices start at RM99/month. Hurry, offer ends 31 October."),
    ("Join workshop on 3 Sep (not_current)", "not_current / check prefilter",
     "Join our free workshop on 3 September to learn about e-invoicing for your business. "
     "Places are limited. Register here to secure your seat."),
    ("MITI RM500m grant (accept control)", "ACCEPT",
     "KUALA LUMPUR, 22 October 2026 — The Ministry of Investment, Trade and Industry announced "
     "an RM500 million SME digitalisation grant. Eligible small and medium enterprises can "
     "access up to RM50,000 each for automation, AI and cloud adoption. Applications open on "
     "1 November through the ministry's portal."),
    ("Borderline scorer (borderline)", "BORDERLINE / EDITOR REVIEW",
     "Company Y, a vendor of office stationery, said it updated its website and mobile app to "
     "accept e-wallet payments. The upgrade, which took six months, was led by a newly "
     "appointed digital manager. The firm expects faster checkouts for its clients."),
]


def expected_for_real(folder):
    name = (folder or "").lower().replace("_", " ")
    if "celcomdigi" in name:
        return "not_sme_relevant / REJECT"
    if "pos malaysia" in name or "jumpstart" in name:
        return "is_it_commercial_intent / REJECT"
    if "smeam" in name or "budget 2027" in name:
        return "political-narrowed / ACCEPT"
    if "minimum wage" in name or "employers urge" in name:
        return "constructive / ACCEPT"
    if "aicpa" in name or "opinion" in name:
        return "ACCEPT (opinion)"
    if any(k in name for k in ("mihas", "matrade", "caexpo", "wagyu", "rmk13", "rehda")):
        return "ACCEPT"
    if "ey media" in name or "ey entrepreneur" in name:
        return "ACCEPT (check contact)"
    if "mdec" in name:
        return "ACCEPT"
    if "securities commission" in name or "sfc" in name:
        return "ACCEPT"
    if "tealive" in name:
        return "commercial / maybe REJECT"
    return "?"


def judge(subject, body):
    payload = json.dumps({"subject": subject, "from": "", "date": "", "bodyText": body}).encode()
    req = urllib.request.Request(BASE, data=payload, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=300)
        return json.loads(r.read())
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def fmt_gates(gates):
    if not gates:
        return ""
    band = {k: v for k, v in gates.items() if WEAK_GATES and k in WEAK_GATES and 0.5 <= float(v) < 0.85}
    shown = ", ".join(f"{k}={v}" for k, v in sorted(gates.items())) if not band else \
            f"AMB[{', '.join(f'{k}={v}' for k, v in band.items())}] " + \
            ", ".join(f"{k}={v}" for k, v in sorted(gates.items()) if k not in band)
    return shown


def run_cases(cases):
    rows = []
    flags = []
    for idx, (name, expected, body) in enumerate(cases, 1):
        print(f"[{idx}] {name}")
        v = judge(name[:200], body)
        if v.get("error"):
            print("      ERROR:", v["error"])
            rows.append({"idx": idx, "case": name, "expected": expected, "actual": "ERROR",
                         "weighted": "", "gate": "", "error": v["error"]})
            continue
        outcome = v.get("outcome"); gate = v.get("gate"); weighted = v.get("weighted")
        reasons = v.get("reasons") or []
        det = v.get("deterministic") or {}
        stale = "?" if det.get("stale") is None else det.get("stale", {}).get("is_stale")
        contact = "?" if det.get("contacts") is None else det.get("contacts", {}).get("has_contact")
        note = " · ".join(filter(None, [
            f"stale={stale}",
            f"contact={contact}",
            f"route={v.get('assist')}" if v.get("assist") else "",
        ]))
        print(f"      expected: {expected}")
        print(f"      ACTUAL  : OUTCOME={outcome} weighted={weighted} gate={gate} reasons={reasons}")
        print(f"      gates   : {fmt_gates(v.get('gates'))}")
        if note:
            print(f"      note    : {note}")
        # contradiction flag
        exp = expected.upper()
        flip = False
        if "REJECT" in exp and outcome != "REJECT": flip = True
        if "EDITOR REVIEW" in exp and outcome != "EDITOR REVIEW": flip = True
        if exp.strip() == "ACCEPT" and outcome != "ACCEPT": flip = True
        if flip:
            flags.append((name, expected, outcome, weighted, gate))
        rows.append({"idx": idx, "case": name, "expected": expected, "actual": outcome,
                     "weighted": weighted, "gate": gate, "reasons": reasons})
    return rows, flags


def collect_real(limit=None):
    cases = []
    seen = set()
    for md in sorted(glob.glob(os.path.join(EMAILS_DIR, "*", "*.md"))):
        folder = os.path.basename(os.path.dirname(md))
        if folder in seen:
            continue
        seen.add(folder)
        try:
            body = open(md, encoding="utf-8").read()
        except Exception:
            continue
        cases.append((folder, expected_for_real(folder), body))
        if limit and len(cases) >= limit:
            break
    return cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--synthetic-only", action="store_true")
    ap.add_argument("--real-only", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    cases = []
    if not args.real_only:
        cases += [(c[0], c[1], c[2]) for c in SYNTHETIC]
    if not args.synthetic_only:
        cases += [(c[0], c[1], c[2]) for c in collect_real(args.limit)]

    if not cases:
        print("no cases")
        sys.exit(1)

    print(f"\n=== running {len(cases)} cases through {BASE} (LLM assist OFF) ===\n")
    rows, flags = run_cases(cases)

    print("\n=== summary ===")
    for r in rows:
        print(f"[{r['idx']:>2}] {r['actual']:>14} | w={str(r['weighted']):>4} | {r['case'][:55]}")
    if flags:
        print("\n=== unexpected results (worth a look) ===")
        for name, expected, actual, w, gate in flags:
            print(f"  {name[:55]:<55} | expected {expected:<32} | got {actual} (w={w}, gate={gate})")
    else:
        print("  (no contradictions against the expected tags)")


if __name__ == "__main__":
    main()
