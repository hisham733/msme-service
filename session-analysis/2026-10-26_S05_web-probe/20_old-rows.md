# Old receive versions are visible in black

**Session:** 2026-10-26 · S05 · reply 20
**Status:** done for re-receive rows.

## 1. Change

- The checklist now renders **all** rows, not only the newest per thread.
- The newest row keeps its normal status (`received`, `receive issue`, `error`).
- Older rows for the same thread show a **black “old”** badge.
- Current versions sort first; old versions follow, newest first inside each group.
- Added filter option **Only old versions**.
- KPIs still count only the newest row per thread.
- The Receive modal labels an old row **old version**.

## 2. What we did so far

- T-043/D28: generic web image probe, 3-state `WEB_FETCH_MODE`, WebP.
- D29: SQLite is the sole checklist store; Sheet sync removed.
- T-044/T-005/T-009/T-008: closed as won’t do.
- D32: receive + filter now run in one pipeline on one port `:8899`; filter results are
  separate and linked (`filter_results.checklist_id`).
- D33: ACCEPT threshold is editable 0–100 (default 60).
- Config: one Config tab with **Config Receive** / **Config Filter**; nav simplified.
- Checklist: compact table, clickable Receive modal, filter gate/score modal, score colours.
- Current: **73 tests pass**, 220 checklist rows, 1 filter result.

## 3. Not built yet

- The **Re-run filter** action and saved gate/weight snapshots are planned (D34), not implemented.
  Re-receiving the same email already adds a new row and marks the old one black.

✅ nothing to decide
