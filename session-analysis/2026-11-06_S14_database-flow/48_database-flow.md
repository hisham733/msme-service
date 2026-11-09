# 48 — Database flow documented

_2026-11-06 (S14) · docs only · no code touched._

## 1. What changed

| File | Change |
|---|---|
| `docs/workflow/DATABASE-FLOW.md` (new, 147 lines) | end-to-end data flow, every table, the checklist contract, the N-6 link ids, safe read/backup commands, code map |
| `docs/INDEX.md` | workflow folder description + `DATABASE-FLOW.md` row (line 27) |

The doc covers:

- a mermaid flow: Gmail → queue → pipeline → `runs` / `pipeline_results` / `checklist` /
  `filter_results` → pages / repurpose export;
- all 12 tables with **who writes and who reads** them;
- the 14-column checklist contract plus the extra `replySent`, `replyTo`, `replyAt`, `messageId`,
  `rfc822MessageId` columns;
- the N-6 flow — two ids stored, the URL built on demand, old rows backfilled;
- run/filter status vocabulary;
- read-only `sqlite3` commands, the `-wal`/`-shm` warning, and a backup command;
- a file-by-file code map.

✅ nothing to decide — this is the requested doc.

## 2. Verification

| Check | Result |
|---|---|
| Live schema | read from `data/msme.sqlite3` (12 tables) |
| Row counts | checklist **241**, runs **355**, pipeline_results **251**, filter_results **24** |
| Checklist columns | 14 + `replySent`/`replyTo`/`replyAt`/`messageId`/`rfc822MessageId` confirmed |
| Code line refs | `_COLUMNS` db.py:41 · save ids db.py:247 · normalize.py:337 · pipeline.py:1373 · dashboard.py:859 · editor_data.py:209 |
| `docs/INDEX.md` | row present at line 27 |
| Code changed | **0** |

✅ nothing to decide — measured against the live DB.

## 3. What I recommend next

**Carry on in this session** (low effort): add the **N-7** (engine chunk rules) and **N-8/N-9** notes,
then stop for the 11-Nov call.
Reason: N-7 is engine-only and N-8/N-9 are operational, so they are short.

| # | Item | State |
|---|---|---|
| 1 | Database flow doc | done |
| 2 | N-1…N-6 specs | done |
| 3 | N-6 code + live build | done |
| 4 | Gmail token expired (`T-028`) | **open — user action** |
| 5 | N-7 / N-8 / N-9 | next |
