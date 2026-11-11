# 1 — Partner handoff pack (P0-1 / P0-2 / backfill) — built, staged, push pending

_2026-11-11 (S16) · full pack approved (push first, branch + PR)._

## 1. What was built

| Part | Result |
|---|---|
| **P0-1 schema** | `stage_runs`, `article_events`, `validation_results`, `images`; `checklist.article_hash`; `article_id` on `repurpose_runs`/`repurpose_events`; `PRAGMA busy_timeout=5000`; `db.article_timeline(article_id)` acceptance join; writers (`add_stage_run`/`add_article_event`/`add_validation_results`/`add_image`) — `D46` |
| **Backfill** | `tools/backfill_repurpose.py` (dry-run/`--apply`, idempotent): reads `data/repurpose_export.json` + each `run.json` → exports/runs/events/validation/images, `article_id = checklist.id` |
| **P0-2** | `opencode.json` → `git commit*: allow`, `git push*: ask`, `git pull*: ask` |
| **Collaboration** | `COLLABORATION.md` at the repo root (+ P0-2 change-log row) |
| **Reply** | `docs/MG_Partner/PARTNER-REPLY-2026-11-11.md` (answers A–F) |
| **Docs** | `DATABASE-FLOW.md` + schema graph regenerated; README/NOW counts → 297 |

## 2. Verified

- **297 tests pass** (8 skipped) · `compileall` OK.
- Backfill applied to the live DB: 20 folders → `repurpose_exports` 20/21, `runs` 20, `events` 27,
  `article_events` 20, `validation_results` **407**, `images` 19; all 20 manifest `checklist_id`s exist.
  `article_timeline(414)` → filter ACCEPT, repurpose validated, 23 validations, 1 event.
- **Gmail token valid** (`ainews.msme@gmail.com`, 250 messages); **DeepSeek $8.33**.
- **Branch** `hs/partner-handoff-2026-11-11`, **54 files staged**, nothing committed yet.

## 3. Blocker — commit still denied

`opencode.json` was changed (P0-2) but the running profile has not reloaded it: `git commit*` is still
`deny`, so the commit cannot run in this session. The work is staged and the branch is checked out.
Either restart the session (then commit is `allow`, push is `ask`), or run manually:

```
git commit -m "partner handoff: P0-1 article-keyed schema, backfill, P0-2 git policy, COLLABORATION"
git push -u origin hs/partner-handoff-2026-11-11
gh pr create --base main --head hs/partner-handoff-2026-11-11 \
  --title "Partner handoff: P0-1 schema, backfill, P0-2, COLLABORATION" \
  --body "Answers in docs/MG_Partner/PARTNER-REPLY-2026-11-11.md"
```

⚠ nothing to decide on the pack itself; the only open step is the commit/push (permission reload or
manual).

## Recap

| # | Item | State |
|---|---|---|
| 1 | P0-1 schema + timeline join | done |
| 2 | Backfill tool + applied (20 folders, 407 validation) | done |
| 3 | P0-2 opencode permissions | done (needs restart) |
| 4 | COLLABORATION.md + PARTNER-REPLY | done |
| 5 | Tests / compile | 297 pass |
| 6 | Branch + staged | 54 files, uncommitted |
