# Dashboard — superseded records removed

**Session:** 2026-10-22_S02 · **Turn:** 25 · **Image:** `msme-service:dashboard-dedupe-20261022`

- The dashboard now shows **only the latest checklist row per email/thread**.
- Older rows from re-runs (MATRADE 296/339, APAC duplicates, etc.) are **hidden from the dashboard**;
  they remain in SQLite/Google Sheet as history.
- KPIs now count unique emails: **149 total · 127 ready · 22 not ready**.
- The "Only not ready to filter" filter now shows the **latest** row only (MATRADE is ready; its old
  needs_human row is gone from the view).

Hard-refresh the page to load the new JS. No data was deleted.
