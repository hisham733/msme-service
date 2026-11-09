# 7 — Cost page: tabs removed, 20-row database pagination

_2026-11-07 (S15) · built + tested + container rebuilt._

## 1. What changed

- `/ai-model.html` is now the **Cost** page only. The **Receive** and **Jev** tabs (and their
  JS/API calls on load) are removed.
- The per-email table is **server-paginated: 20 rows per page**
  (`/api/costs.json?page=1&page_size=20&q=…`). It returns `total`, `page`, `pages` and only the
  20 rows; **Prev / Next** move through the pages.
- Search is **server-side** (`q`) and resets to page 1; the browser never receives all 168 rows.
- The page is **admin-only** now (the Receive/Jev tabs were the editor-visible part). The editor
  page no longer links to it. `/by-email.html` and `/senders.html` remain aliases.
- The Receive/Jev data functions and `GET /api/models.json` remain in the code for future use.

## 2. Verification

| Check | Result |
|---|---|
| Full suite | **241 tests, OK** (8 skipped) |
| New pagination tests | 20 rows on page 1, 5 on page 2 (25 seeded), search, disjoint pages |
| Live API | `page=1` → **168 total, 9 pages, 20 rows**; `page=9` → **8 rows** |
| Live search | `q=Meltwater` → **1 row** (`1a162cc0b30af0e7`) |
| Routes | `/ai-model.html` **302**; `/api/costs.json` **401** without a session |
| Container | rebuilt; `/api/health` **200**, `{"webhook": true, "auto": false}` |

⭐ Decision — §2: **keep the page admin-only (A, recommended)** since it is now cost-only; or
**restore an editor-visible view (B)**, which would need a separate page (the Receive/Jev tabs are
gone).

## 3. Still open from the previous turn

The Google token is still `invalid_grant`: use **Config → Receive → Google account** to reconnect,
then enable the webhook and run the 241-email backfill.

✅ nothing to decide — the pagination and tab removal are done.

## Recap

| # | Item | State |
|---|---|---|
| 1 | Receive/Jev tabs removed | done |
| 2 | 20-row server pagination + Prev/Next | done |
| 3 | Server-side search | done |
| 4 | Page is admin-only | done |
| 5 | Tests + container | 241 pass; healthy |
| 6 | Gmail re-auth | **user step** |

## What I recommend next

**Carry on in this session** (low effort): complete the Google consent from the Config card, then
enable the webhook and run the backfill.
