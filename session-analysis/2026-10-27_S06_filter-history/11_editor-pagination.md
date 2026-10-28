# Editor — 20 per page, newest edit first

**Session:** 2026-10-27 · S06 · reply 11

- `/editor.html` now loads **20 emails per page** from `/api/editor/articles`.
- Sort key is **last edit**, not received date:
  - checklist creation, latest filter result, latest run, or Repurpose run update.
- Cards show **Updated YYYY-MM-DD** so the order is clear.
- **Previous / Next** pager + “Page X of Y · N emails · newest edit first”.
- Search and tabs now request a new page from the server and reset to page 1.
- KPI counts remain whole-database counts.
- Live: **155 emails · 8 pages · 6 ready · 17 need attention**.
- No data/API schema change; editor page and API only.

✅ nothing to decide
