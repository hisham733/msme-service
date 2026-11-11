# PARTNER ACTION BRIEF — install, data gaps, schema and collaboration

**From:** MG · **To:** the partner's LLM · **Date:** 2026-11-11
**Repo:** `hisham733/msme-service` · **Head:** `8d4b1cb` (parent `5b4eea1`)
**MG's roots:** code `D:\msme-service` · data `D:\msme project` · upstream reference `C:\Users\mgowy\OneDrive\Desktop\CAF MG files\MG Projects\Malaysia SME`

This is the one file to act on. It covers (A) what MG is installing, (B) what the old data root does and does not contain, (C) the two P0s, (D) the collaboration protocol, and (E) what to reply with.

---

## A. What MG is installing

- **One service**: `msme-service` on `:8899`; the engine is vendored at `msme/repurpose/engine/` and runs **in-process** (`REPURPOSE_INPROCESS=true`); no `:8765`, no host worker.
- **Code root**: `D:\msme-service` (clone of `8d4b1cb`). **Data root**: `D:\msme project` (the old bundle), bind-mounted into the container:
  `creds`, `data`, `all_emails`, `repurpose_inbox`, `repurpose_site`.
- **Safe flags** locally: `ENABLE_AUTO=false`, `ENABLE_WEBHOOK=false`, `REPLY_ENABLED=false`, `restart: unless-stopped`, `COOKIE_SECURE=false` for localhost.
- **MG will**: build, `/health`, run the suite, reset the local admin password, backfill the 17 exports, verify the 17 folders + one draft, and **not** run receive against the shared mailbox yet.

**No new archive/creds bundle is needed for files.** The gaps are credentials and rows — see B.

---

## B. The old data root — what is sufficient, what is not

| Item | State | Action |
|---|---|---|
| `all_emails/` 2.85 GB | present | none |
| `creds/{gmail,drive,sheets,deepseek}.json` | present | confirm freshness (Gmail) |
| `data/settings.json` | present; `ENABLE_AUTO=false` | confirm keys |
| `data/msme.sqlite3` 241/24 | present; `init_db` migrates the missing `checklist`/`filter_results` columns and creates `repurpose_*` | none for schema |
| `repurpose_exports`/`runs`/`events` | **empty** | backfill the 17 exports |
| `repurpose_inbox` 17 folders | present, all processed | none |
| `repurpose_site` | built | re-verify after install |
| Admin password | **unknown** (`users` has `admin`, `MG123`, `user1`) | **MG resets locally**; no need to send it |
| Gmail OAuth | may be expired (testing consent ~7 days) | **confirm or send fresh `creds/gmail.json`** |
| 6 archived client secrets in `creds/` | present | **remove/rotate**; do not rely on them |
| `emails/` 694 MB | absent | optional; not needed |

**B1. Backfill the repurpose rows.** The 17 exports exist in `data/repurpose_export.json` and each folder's `run.json`, but `repurpose_exports`/`repurpose_runs`/`repurpose_events` are empty. Confirm the mapping (`folder`, `checklist_id`, `filter_result_id`, `status`, `usage_json`, `run_json`, timestamps) or send the backfill SQL/script. MG can run it locally.

**B2. Gmail token.** Confirm `creds/gmail.json` still works. If not, send a fresh `creds/{gmail,drive,sheets}.json` or the re-auth steps. Receive is blocked without it; the dashboard/filter/repurpose on existing data are not.

**B3. Keys.** Confirm the TypeSafe key (old `.env`) and the DeepSeek/Gemini keys (`data/settings.json`) are valid and whose spend they are. Never send them in chat; use the password manager.

---

## C. The two P0s

### P0-1 — email-id / stage tables (T-040)

The DB is **folder-keyed**, not article-keyed. A dashboard cannot reliably join by a folder name that can change. The email id already exists as `checklist.id`; use it as the canonical key (no parallel UUID), add `article_hash` for duplicate emails, and add the missing tables/columns:

```sql
-- canonical email/article key
ALTER TABLE checklist ADD COLUMN article_hash TEXT;      -- if not present
-- stage runs: one row per stage execution
CREATE TABLE IF NOT EXISTS stage_runs (
  run_id TEXT PRIMARY KEY,
  article_id TEXT,                -- checklist.id (or a UUID that maps to it)
  stage TEXT,                     -- receive | filter | repurpose | publish
  service TEXT,
  status TEXT, started_at TEXT, ended_at TEXT,
  error_code TEXT, error_text TEXT
);
-- append-only event log: the dashboard's source
CREATE TABLE IF NOT EXISTS article_events (
  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
  article_id TEXT, stage TEXT, status TEXT,
  reason_code TEXT, reason_text TEXT, notes TEXT,
  actor TEXT, created_at TEXT, payload_json TEXT
);
-- per-rule validation results (the "why fail")
CREATE TABLE IF NOT EXISTS validation_results (
  result_id INTEGER PRIMARY KEY AUTOINCREMENT,
  article_id TEXT, run_id TEXT,
  rule_code TEXT, level TEXT, ok INTEGER, detail TEXT
);
-- image selection provenance
CREATE TABLE IF NOT EXISTS images (
  image_id INTEGER PRIMARY KEY AUTOINCREMENT,
  article_id TEXT, path TEXT, role TEXT,
  rung TEXT, selected INTEGER, reason TEXT
);
-- add article_id to the existing repurpose tables
ALTER TABLE repurpose_runs ADD COLUMN article_id TEXT;
ALTER TABLE repurpose_events ADD COLUMN article_id TEXT;
```

- Every change is a **migration in `msme/db.py`** (`CREATE TABLE IF NOT EXISTS` / `ALTER TABLE`) plus a test; never a hand-edited DB file.
- Backfill `article_id` from `checklist.id`; backfill the 17 exports; add `busy_timeout` to `_connect`.
- Acceptance: one SQL join returns receive → filter → repurpose → validation for one `article_id`.

### P0-2 — `opencode.json` commit/push permission

Current: `"git commit*": "deny"`, `"git push*": "deny"`. MG's rule:

- `git commit*`: **allow** (local commits at any time)
- `git push*`: **ask**
- `git pull*`: **ask**

Change the two entries and add `git pull*`, or confirm that MG uses DSH/manual git and the shared profile stays `deny`. Record the choice in `COLLABORATION.md`.

---

## D. Collaboration protocol — `COLLABORATION.md`

A ready draft is `partner_handoff/COLLABORATION-SERVICE.md` on MG's side. Please:

1. Review it; copy it to the service root as **`COLLABORATION.md`**.
2. Merge it to `main` (a PR is preferred; a direct doc commit is acceptable if you prefer).
3. Follow it; append to its change log when the protocol changes.

The rules in one line:

- Branches `mg/<topic>` / `hs/<topic>`; PR to `main`; CI green; **one review**; squash merge.
- **Merge when ready** — the author declares ready, the reviewer approves in the PR or chat; no fixed SLA; no silent merges; wait if the other is unavailable.
- Pull `--rebase` before push; never force-push `main`.
- The PR author resolves conflicts; never delete the other side.
- **Schema changes are code migrations** (`msme/db.py` + test); the DB file is data, never committed; backfills are scripts.
- Never commit `creds/`, `data/`, `all_emails/`, `repurpose_site/`, `.env`.
- Tag `handover-YYYYMMDD` after a verified merge.
- MG pushes as **`caferpgit`** for now; `EmpiFlow` is not a collaborator. No functional blocker; attribution only.

---

## E. What stays

- **D-032**: the old `MSME_AI_News` / `C:\...\Malaysia SME` is the **upstream record**; not the runtime; **do not delete**. The new code root is `D:\msme-service`; the data root is `D:\msme project`.
- **D-033**: **SQLite** for this phase; Postgres deferred. The DB lives on the bind mount for now; `busy_timeout`; a named volume only if locking.
- **D-040**: one repo, one process, one DB. The engine is vendored and in-process; no `:8765`, no host worker.

---

## F. What to reply with — checklist

- [ ] Admin: no objection to MG resetting the local password (or send the current one via the password manager).
- [ ] Backfill: confirm the 17-export mapping, or send the SQL/script.
- [ ] Gmail: token still valid, or send fresh `creds/{gmail,drive,sheets}.json`.
- [ ] Keys: confirm TypeSafe/DeepSeek/Gemini ownership and validity (no values in chat).
- [ ] P0-1: confirm the `article_id`/stage/validation/image migration plan (or propose an alternative that keeps one join key).
- [ ] P0-2: confirm `opencode.json` becomes commit allow / push-pull ask, or that MG uses DSH/manual git.
- [ ] `COLLABORATION.md`: review, add to `main`, confirm the branch/PR/merge rule.
- [ ] Confirm `MSME_AI_News` stays the upstream record (D-032), SQLite (D-033), one service (D-040).
- [ ] Remove/rotate the six archived client secrets in `creds/`.

**Security:** never send a password, OAuth token or API key in chat. Use the password manager or an encrypted channel. The data root is client material; do not forward it.

---

## G. MG's install sequence (for context, not action)

1. Clone `8d4b1cb` → `D:\msme-service` (done).
2. Add `docker-compose.data.yml` (five data mounts) + `.env` (TypeSafe, safe flags) — done, no secrets printed.
3. Build, `/health`, `/login`, `/repurpose.html`, `/api/repurpose/status`.
4. Run the suite; record the count (README 191 / NOW 271 / 239 source methods — reconcile).
5. Reset the local admin password; backfill the 17 exports; verify the 17 folders + one draft.
6. Start a new DSH session **in `D:\msme-service`** for the workflow setup and coding.
7. First PRs: `mg/collaboration`, `mg/safe-compose`, `mg/article-event-schema`, `mg/mailbox-safety`, `mg/docs-truth`.
