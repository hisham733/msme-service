# 11 — Two emails through receive → filter → publish

_2026-11-07 (S15) · live run · 2 emails, exactly as asked._

## 1. The run

| Email | ID | Result |
|---|---|---|
| **AFFIN SME BizChat 2026 — Johor SMEs** | `1a1b3c9d218c4cc9` | ready · Jev **ACCEPT 86** · engine **validated** · **published** |
| **MATRADE at FoodExpo Qazaqstan 2026** | `1a1b3c878952cccf` | ready · Jev **ACCEPT 91** · engine **validated** · **published** |

- Checklist rows **414** and **415**; filter results **25/26**; both `repurpose_exports` rows exist.
- Engine: 1 validator retry each, then `status: validated`.
- Unread dropped **33 → 31** (the two are marked read).
- Site output:
  - `repurpose_site/articles/affin-sme-bizchat-2026-brings-2027-outlook-to-more-than-200-johor-smes.html`
  - `repurpose_site/articles/matrade-debuts-at-foodexpo-qazaqstan-2026-opening-central-asian-export.html`
  - both are at the top of `repurpose_site/data/articles.js` (17 articles total), so they show on the demo index.

## 2. The blocker found and fixed

The first engine attempt **validated the draft but could not publish**:

```
[Errno 30] Read-only file system: '/app/repurpose_site/assets/fonts'
```

`docker-compose.yml` mounted `./repurpose_site:/app/repurpose_site:ro`. The engine must write
`articles/`, `assets/fonts/`, `images/`, `data/articles.js` and `index.html`. The mount is now
**writable**; the two folders were re-run and published.

⭐ Decision — §2: **keep `repurpose_site` writable (A, recommended)** — publish cannot work
read-only; or **move the site output to a separate writable volume (B)** if you want the
`repurpose_site/` checkout itself protected.

## 3. Cost (live, after the run)

| Item | AFFIN | MATRADE |
|---|---:|---:|
| Receive | $0.005556 | $0.005278 |
| Filter (Jev) | $0.000086 | $0.000086 |
| Repurpose (46,404 / 44,409 tokens) | **$0.030163** | **$0.028866** |
| **Chain total** | **$0.035804** | **$0.034229** |

- All runs: **$2.1285** (receive $2.0670 · filter $0.0024 · repurpose $0.0590)
- Latest chain: **$1.4696** over 170 emails · published **2** · avg/published **$0.0295**
- `repurpose_runs.usage_json` is populated for both; the Cost page shows the publish amounts.

**Honesty note:** the first AFFIN attempt (before the mount fix) failed at the build step, so its
draft/validate tokens were not persisted. The shown repurpose cost is the successful re-run only;
the real spend is slightly higher than the dashboard shows for AFFIN.

## 4. What is still open

- 31 unread remain (not run, by request).
- `emails` backfill still not run (`emails` = 0); it does not affect this cost page.
- `COST_BUDGET_USD` is still unset; the rates are the measured defaults.
- The Gmail watch is active until **2026-11-14 03:11 UTC**; new mail will push.

✅ nothing to decide — the two-email workflow reached publish.

## Recap

| # | Item | State |
|---|---|---|
| 1 | AFFIN receive → filter → publish | **done** |
| 2 | MATRADE receive → filter → publish | **done** |
| 3 | `repurpose_site` read-only blocker | **fixed** (mount writable) |
| 4 | Repurpose usage/cost recorded | **done** ($0.030 / $0.029) |
| 5 | Two articles visible on the demo index | **done** |
| 6 | 31 unread / backfill / budget | not run |

## What I recommend next

**Carry on in this session** (low effort): set `COST_BUDGET_USD` on Config → Cost, then decide
whether to process the remaining 31 unread or leave them for the publisher.
