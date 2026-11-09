# 6 — AI Model page, Config tabs, reconnect, webhook switch, cost

_2026-11-07 (S15) · built + tested + container rebuilt._

## 1. What was built

| # | Item | Result |
|---|---|---|
| `T-051` | By-sender page → **AI Model** | `static/ai-model.html`; **Receive** tab (email id + AI model + sender + subject + last run + status + runs + ready + open) and **Jev** tab (email id + Jev model + outcome + weighted + gate + confidence + subject + filtered + ready + open). `/by-email.html` and `/senders.html` remain aliases |
| `T-052` | Google reconnect from Config | **Receive → Google account**: *Open Google consent* → paste the failed `127.0.0.1:8080/?code=…` URL → *Finish reconnect*; rewrites `creds/{gmail,drive,sheets}.json` and renews the watch |
| `T-053` | Gmail webhook on/off | **Receive → Gmail push webhook**: live status, topic, watch expiry, Enable/Disable; the flag is runtime and the watch is created/stopped immediately; OFF makes `/webhooks/gmail` answer `200 disabled` |
| `T-054` | Repurpose config | **Config Repurpose** tab: auto-repurpose, model, temperature, retry limit, poll seconds; read-only in-process/paths + queue link |
| `T-055` | Cost receive → publish | **Cost** tab (admin only): total spend, chain spend, avg/email, avg/published, stage split, budget bar with “≈ N emails left”, 14-day sparkline, most expensive email, tokens, per-email table; engine usage is now recorded |

`/config.html` now has four tabs: **Receive · Filter · Repurpose · Cost**. Routes added:
`/ai-model.html`, `GET/POST /api/webhook`, `GET/POST /api/google/reauth`,
`GET /api/models.json`, `GET /api/costs.json`.

## 2. Verification

| Check | Result |
|---|---|
| `compileall` | OK |
| Full suite | **239 tests, OK** (8 skipped) |
| New tests | `test_cost` (9), `test_ai_model_dashboard` (7), `test_google_oauth` (6), `test_repurpose_usage` (8), 4 new webhook toggle tests |
| Container | rebuilt, `/api/health` **200**, `{"webhook": true, "auto": false}` |
| Routes | `/ai-model.html`, `/by-email.html`, `/config.html` = **302** without a session; `/api/costs.json` = **401** |
| Live data | Receive **168 emails / 355 runs**; Jev **22 results** (18 ACCEPT, 4 EDITOR REVIEW) |

⭐ Decision — §2: **re-authenticate now from the new Config card (A, recommended)** so I can prove
the reconnect, enable the Gmail watch and run the 241-email backfill; or **leave it (B)** and the
Cost/Jev data stays as it is and no new mail is received.

## 3. The cost numbers (live dB, 2026-11-07)

| Metric | Value |
|---|---:|
| All-runs spend (250 receive + 24 Jev) | **≈ $2.06** |
| Chain spend (latest per email, 168) | **≈ $1.40** |
| Avg per email | **≈ $0.00833** |
| Most expensive email | Meltwater `1a162cc0b30af0e7` **≈ $0.0319** |
| Repurpose | **not measured yet** — 0 runs; usage is recorded from the next run |

Rates are the measured defaults (`DeepSeek $0.65/1M total`, `Jev $0.042/1M input`) and are editable
on **Config → Cost**. A run without usage shows “not measured”, never a silent $0.

```mermaid
flowchart LR
    R[receive run<br/>pipeline_results.tokens] --> C{one email id}
    F[Jev verdict<br/>filter_results.verdict.usage] --> C
    P[repurpose run<br/>repurpose_runs.usage_json] --> C
    C --> D[msme/cost.py<br/>prices] --> A[/api/costs.json<br/>Cost tab]
```

⭐ Decision — §3: **keep `creds/` writable by the container (A, recommended)** — required for the
in-app reconnect button; or **revert to read-only (B)** and reconnect only with the terminal tool.

## 4. What is still the user’s step

1. Config → **Receive** → *Google account* → **Open Google consent**; sign in as
   `ainews.msme@gmail.com`, approve Gmail/Drive/Sheets; copy the failed `127.0.0.1:8080/?code=…`
   URL, paste it, **Finish reconnect**.
2. Then **Gmail push webhook → Enable** (the watch is created immediately).
3. Then run `python3 tools/backfill_emails.py --apply` — the **Receive** tab fills the sender column.

✅ nothing to decide — the historical engine cost stays “not measured”; every new repurpose run is priced.

## Recap

| # | Item | State |
|---|---|---|
| 1 | AI Model page (Receive + Jev) | built |
| 2 | Google reconnect card | built; live consent is yours |
| 3 | Webhook on/off | built; watch needs a valid token |
| 4 | Repurpose + Cost Config tabs | built |
| 5 | Cost cards + budget bar | built; $2.06 all runs / $1.40 chain |
| 6 | Tests + container | 239 pass; healthy |

## What I recommend next

**Carry on in this session** (low effort): use the Config card to reconnect, then enable the
webhook and run the backfill; no new session is needed.
