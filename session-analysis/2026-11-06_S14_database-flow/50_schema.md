# 50 — Full schema added to the database-flow doc

_2026-11-06 (S14) · docs only · no code touched._

## 1. What changed

`docs/workflow/DATABASE-FLOW.md` gained **§9 Full schema** — the exact `CREATE TABLE` SQL for all 12
tables plus the 2 indexes, with the migration columns marked.

- `checklist`: 14 contract columns + `replySent`/`replyTo`/`replyAt` + `messageId`/`rfc822MessageId`.
- `filter_results`: base columns + `battery`/`config_hash`/`article_hash`/`article_text`/`article_len`.
- The rest: `runs`, `pipeline_results`, `gmail_watch`, `webhook_events`, `webhook_messages`, `users`,
  `sessions`, `login_attempts`, `audit_log`, `filter_config_versions`.
- SQLite internals (`sqlite_sequence`, `sqlite_stat1`, `sqlite_stat4`) are omitted.

✅ nothing to decide — this is the requested schema.

## 2. Verification

| Check | Result |
|---|---|
| Source | live `data/msme.sqlite3` `.schema` (read-only) |
| Tables in the doc | 12 |
| Indexes | `idx_sessions_expires`, `idx_attempts_time` |
| Column order | `filter_results` aligned to the live order |
| Code changed | **0** |

✅ nothing to decide — measured.

## 3. What I recommend next

**Carry on** (low effort): finish the N-7/N-8/N-9 notes, then the 11-Nov call.
Reason: they are the last short rule items.

| # | Item | State |
|---|---|---|
| 1 | Tables + connections + full schema | done |
| 2 | N-6 live build | done |
| 3 | Gmail token (`T-028`) | **open — user action** |
| 4 | N-7 / N-8 / N-9 | next |
