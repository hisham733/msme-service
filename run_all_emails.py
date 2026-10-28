#!/usr/bin/env python3
"""Run the FULL pipeline over all inbox emails, then filter every archived article.

1. For each cached email that does NOT already have a successful receive run,
   POST /api/run and poll until it finishes (records ai_error/error too).
2. After the receive pass, list the filter's archived articles and judge each
   one through :8900/filter (regenerates the cleared verdict log).

Sequential (Gmail + DeepSeek rate-limit friendly). Progress printed to stdout.
"""
import json
import os
import sys
import time
import urllib.request

API = "http://127.0.0.1:8899"
FILTER = "http://127.0.0.1:8900/filter"
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "msme.sqlite3")


def _req(url, data=None, method=None, timeout=60):
    body = json.dumps(data).encode() if data is not None else None
    m = method or ("POST" if data is not None else "GET")
    req = urllib.request.Request(url, data=body, method=m,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def already_run(email_id):
    import sqlite3
    try:
        c = sqlite3.connect(DB)
        row = c.execute(
            "select status from runs where email_id=? order by rowid desc limit 1",
            (email_id,)).fetchone()
        c.close()
        return bool(row and row[0] == "success")
    except Exception:
        return False


def run_receive(email_id, subject):
    try:
        d = _req(f"{API}/api/run?email_id={email_id}", method="POST")
    except Exception as e:
        return "error", f"run-start: {e}"
    run_id = d.get("run_id", "")
    deadline = time.time() + 360
    while time.time() < deadline:
        time.sleep(3)
        try:
            s = _req(f"{API}/api/run-status?run_id={run_id}")
        except Exception as e:
            return "error", f"poll: {e}"
        st = s.get("status")
        if st != "running":
            return st, s.get("error", "")
    return "timeout", subject[:60]


def filter_article(art):
    try:
        path = (art.get("path") or "").replace("/app/", "")
        body = open(path, encoding="utf-8").read()
    except Exception as e:
        return {"error": f"read {art.get('path')}: {e}"}
    return _req(FILTER, {
        "subject": art.get("subject", ""),
        "from": "",
        "date": art.get("date", ""),
        "bodyText": body,
    }, timeout=300)


def main():
    print("== step 1: emails ==")
    emails = _req(f"{API}/api/emails?force=0").get("emails", [])
    print(f"cached emails: {len(emails)}")
    stats = {"success": 0, "ai_error": 0, "error": 0, "skip(existing)": 0}
    for i, e in enumerate(emails, 1):
        eid, subj = e.get("id", ""), e.get("subject", "")
        if already_run(eid):
            stats["skip(existing)"] += 1
            print(f"[{i}/{len(emails)}] SKIP (already processed) {subj[:50]}")
            continue
        status, err = run_receive(eid, subj)
        stats[status] = stats.get(status, 0) + 1
        print(f"[{i}/{len(emails)}] {eid} -> {status} | {subj[:50]}" + (f" | err={err[:90]}" if err else ""))

    print("\n== step 2: filter archived ==")
    try:
        arts = _req("http://127.0.0.1:8900/archived").get("articles", [])
    except Exception as e:
        print("archived list failed:", e)
        arts = []
    print(f"archived articles to judge: {len(arts)}")
    fstats = {}
    for a in arts:
        r = filter_article(a)
        out = r.get("outcome", "ERROR")
        fstats[out] = fstats.get(out, 0) + 1
        print(f"FILTER {out:<15} w={r.get('weighted')} gate={r.get('gate')} | {a.get('subject','')[:55]}" +
              (f" err={r.get('error')}" if r.get("error") else ""))

    print("\n== DONE ==")
    print("receive:", json.dumps(stats))
    print("filter :", json.dumps(fstats))


if __name__ == "__main__":
    main()