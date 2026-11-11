# PARTNER REPLY — answers to the action brief

**From:** HS (the partner) · **To:** MG's LLM · **Date:** 2026-11-11
**Repo:** `hisham733/msme-service` · **Branch:** `hs/partner-handoff-2026-11-11` · **Parent head:** `8d4b1cb`
**Read with:** `COLLABORATION.md` (now at the repo root) and `docs/MG_Partner/PARTNER-ACTION-BRIEF (1).md`.

All answers below were verified on our side today, not guessed.

---

## A. Install — confirmed

- One service on `:8899`, engine vendored and in-process (`REPURPOSE_INPROCESS=true`); no `:8765`.
- Safe flags for local: `ENABLE_AUTO=false`, `ENABLE_WEBHOOK=false`, `REPLY_ENABLED=false`,
  `restart: unless-stopped`, `COOKIE_SECURE=false` for localhost.
- **No objection** to resetting the local admin password. Do not send it.

## B. Data root, backfill, token, keys

### B1. Backfill — script provided (`tools/backfill_repurpose.py`)

- Reads `data/repurpose_export.json` + each `repurpose_inbox/<folder>/run.json`; rebuilds
  `repurpose_exports`, `repurpose_runs`, `repurpose_events`, and the P0-1 `validation_results` /
  `images`; sets `article_id = checklist.id`.
- **Idempotent** (derived rows replaced; one backfill event per folder). Dry-run by default:
  `python3 tools/backfill_repurpose.py` → `--apply`.
- On our side it rebuilt **20 folders** (not 17 — the script counts what is actually there):
  `repurpose_exports` 20/21, `repurpose_runs` 20, `repurpose_events` 27, `validation_results` 407,
  `images` 19. All **20** manifest `checklist_id`s exist in our `checklist`.
- On MG's bundle with 17 folders, the same script will write 17 (it does not hardcode the count).

### B2. Gmail token — **valid** (verified just now)

- `users.getProfile` → **`ainews.msme@gmail.com`**, 250 messages. No need to resend `creds/gmail.json`
  right now.
- Risk: the OAuth consent is in **testing** (~7-day refresh expiry). Publish the consent screen to
  Production, or re-auth every 7 days, to avoid a silent expiry (`T-028`).

### B3. Keys — confirm ownership, never send values

- **DeepSeek:** AUTH OK, balance **$8.33** (verified today). Amounts are estimates from stored tokens at
  the editable rates (`D42`).
- **TypeSafe (Jev)** and **Gemini:** configured in `data/settings.json`; values are not in this file or
  chat. Confirm they are MG's accounts (who pays) via the password manager.

## C. The two P0s — both confirmed and built

### P0-1 — article-keyed schema — **done** (`msme/db.py`, `D46`)

- Canonical key = **`checklist.id`** (`article_id`); no parallel UUID.
- New tables: **`stage_runs`**, **`article_events`**, **`validation_results`**, **`images`**.
- New columns: **`checklist.article_hash`**, **`repurpose_runs.article_id`**, **`repurpose_events.article_id`**.
- **`PRAGMA busy_timeout = 5000`** in `_connect()`.
- Writers: `db.add_stage_run`, `db.add_article_event`, `db.add_validation_results`, `db.add_image`.
- Acceptance join: **`db.article_timeline(article_id)`** → receive → filter → repurpose → validation (+ events).
- Migration is code (`init_db` + `ALTER TABLE`) + tests (`tests/test_partner_p0.py`); the DB file is never
  committed. Backfill script as in B1.

### P0-2 — agent git policy — **done** (`opencode.json`)

- `git commit*: allow`, `git push*: ask`, `git pull*: ask`. Recorded in `COLLABORATION.md` §9 + change log.
- An agent never force-pushes and never commits `creds/`, `data/`, `all_emails/`, `.env`.

## D. `COLLABORATION.md`

- Added at the **repo root** (reviewed; your draft with a change-log row for P0-2). Please review and
  merge on `main` via the PR.

## E. D-032 / D-033 / D-040 — confirmed

- **D-032:** `MSME_AI_News` stays the upstream record; not the runtime; **do not delete**.
- **D-033:** SQLite for this phase; Postgres deferred; `busy_timeout` set.
- **D-040:** one repo, one process, one DB; engine vendored and in-process.

## F. Reply checklist

- [x] Admin: **no objection** to MG resetting the local password (do not send it).
- [x] Backfill: **script provided** (`tools/backfill_repurpose.py`), idempotent, counts actual folders.
- [x] Gmail: **token valid** (`ainews.msme@gmail.com`); no resend needed now.
- [x] Keys: DeepSeek OK ($8.33); TypeSafe/Gemini configured — confirm ownership (no values in chat).
- [x] P0-1: **confirmed and implemented** (tables, `article_id`, `article_hash`, `busy_timeout`, timeline join, backfill, tests).
- [x] P0-2: **confirmed** (`opencode.json` = commit allow / push+pull ask).
- [x] `COLLABORATION.md`: added at the root; review + merge.
- [x] D-032 / D-033 / D-040: confirmed.
- [ ] **Remove/rotate the six archived client secrets** in `creds/` (HS action): `ai_sme.json`,
  `ai_sme_last.json`, `client_secret_2_936991497155-…json`, `client_secret_new.json`, `last.json`,
  `mse_ai_app.json`. Keep `deepseek.json`, `gmail.json`, `drive.json`, `sheets.json`.

## Counts and notes

- Test suite: **297 pass** (README/NOW updated from the stale 191/271).
- The branch carries the newer work on top of `8d4b1cb` (N-3 report link, N-4 capture, table-driven
  export, cost live-balance, N-7 docs, P0-1, backfill, COLLABORATION) — merge it before installing so MG
  gets the current code.
- **Security:** never send a password, OAuth token or API key in chat; the data root is client material.
