# D29 — SQLite is the sole checklist store

**Session:** 2026-10-26 · S05 · reply 3
**Status:** done. Google Sheet sync removed; T-044 is now SQLite-only.

## 1. What changed

- `checklist.py`: `save_checklist()` writes to **SQLite only**; `append_to_sheet()` is removed
  and the module no longer imports `creds`/`config`.
- `dashboard.py`: `POST /api/clear` clears **SQLite only**; it no longer clears the Sheet.
- Config page: the Sheet card is marked **optional** and says receive does not sync it.
- Flow page / Workflow Lab / `ARCHITECTURE.md` / `WORKFLOW.md` / `NOW.md` / `data/INDEX.md`
  now name SQLite as the checklist source of truth.
- The Sheet itself is untouched: still header-only, 14 columns.

✅ nothing to decide — §1

## 2. Why

- Sheet: 14-column header, **0 data rows**; SQLite: **210 checklist rows**.
- The Sheet is editable again (`canEdit=true`, owner `ainews.msme@gmail.com`), but it was
  already non-fatal: a Sheet failure never stopped the run.
- Removing the append removes one network call and one duplicate source of truth per run.
- Decision record: `decisions/D29.md`.

✅ nothing to decide — §2

## 3. Verified

- `checklist` has no `append_to_sheet`, no `creds`, 14 columns.
- New `tools/test_checklist_sqlite.py`: **3 pass** — SQLite-only save, no Sheet path, row order.
- Full suite: **62 pass**.
- Rebuilt container; `:8898/health` OK; Config page and Flow page serve the SQLite wording;
  `/checklist.json` still returns **210 rows**.

✅ nothing to decide — §3

## 4. Next — T-044 dry-run

T-044 no longer needs a Sheet choice. Next is the **read-only mapping dry-run**:

1. Read Drive folders 1–4 and each `link.md`.
2. Match to checklist rows by `articleFile` first, then normalized subject.
3. Report exact, fuzzy/ambiguous and unmatched rows, plus duplicate subjects.
4. Write a manifest only; no DB update yet.

The write scope (latest row per article vs all duplicate rows) can be chosen after the
dry-run shows the real counts.

✅ nothing to decide — §4

## Recap

| Item | State |
|---|---|
| Checklist write | SQLite only |
| Sheet sync | removed |
| `/api/clear` | SQLite only |
| Sheet file | optional/manual, header only |
| Tests | 62 pass |
| T-044 | dry-run next |

## What I recommend next

Continue in this session with the **T-044 dry-run** (medium effort); it makes no writes and gives
the exact match/duplicate counts before deciding what to update.
