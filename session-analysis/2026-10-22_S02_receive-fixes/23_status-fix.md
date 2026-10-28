# MATRADE "needs human" was a dashboard status bug

**Session:** 2026-10-22_S02 · **Turn:** 23 · **Image:** `msme-service:dashboard-status-20261022`
**ID:** T-030

## 1. Why it showed needs human

The row was **ready** (`hasArticle/hasPic/hasLogo/... = yes`, subject 100). The status label came from
`/api/logs`:

- `/api/logs` returns runs **newest first**;
- the dashboard assigned every run to the same email key, so the **oldest** run (`needs_human`) overwrote
  the newest `success`.

So the old failed attempt's status was painted on the new row.

## 2. Fixed

- keep the **first (newest)** run per email in the status map;
- only the **latest checklist row** per email shows the current status;
- older duplicate rows (MATRADE had 296 old + 339/340 new) show **superseded** (grey), not needs human;
- `/checklist.json` now carries `id` + `created_at` to identify the latest row.

Deployed: `msme-service:dashboard-status-20261022`. Refresh the dashboard (hard reload) to load the new JS.

## 3. Current MATRADE rows

| Row | Article | Ready | Status |
|---|:--:|:--:|---|
| 340 (latest) | ✅ | ✅ | completed |
| 339 | ✅ | ✅ | superseded |
| 296 (first failed attempt) | ❌ | ❌ | superseded |

No decision needed. The pipeline was correct; only the label was wrong.
