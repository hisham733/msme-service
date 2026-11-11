# COLLABORATION — MG and the partner on `msme-service`

*One page. Both sides edit it; append to the change log when the protocol changes. If a rule here conflicts with a decision in `decisions/`, the decision wins.*

## 1. One working copy

- `hisham733/msme-service` is the single source of truth.
- MG works in **`D:\msme-service`** (code). The data root is **`D:\msme project`**; DSH starts in the code root.
- The old `EmpiFlow/MSME_AI_News` is the **upstream record** only; it is not the runtime and is not deleted.

## 2. Branches

- `mg/<topic>` for MG, `hs/<topic>` for the partner. One topic per branch.
- Never work on `main`; never force-push.

## 3. Pull before push

```powershell
git switch main
git pull --rebase origin main
git switch <your-branch>
git rebase main
# re-run the suite
```

## 4. PR and merge

- Open a PR to `main`. CI must be green (`compileall` + ruff + unittest).
- **One review by the other person** — approve in the PR or explicitly in chat.
- Squash merge. The author merges after approval.
- **“Merge when ready”**: no fixed SLA — the author declares ready, the reviewer approves. If the other is unavailable, wait; no silent merges.

## 5. Conflicts

- The PR author resolves the conflict.
- Never resolve by deleting the other side.
- If both touched the same file, rebase and re-run the tests; if a contract changed, update the docs/tests in the same PR.

## 6. Database changes

- **Schema = code.** A schema change is a migration in `msme/db.py` (`CREATE TABLE IF NOT EXISTS` / `ALTER TABLE`) plus a test.
- The DB file is data; never commit it. Backfills are scripts, not committed DB files.
- The partner’s LLM gets the schema by pulling and starting the app (`init_db`); no manual DB file exchange.

## 7. Secrets and data

- Never commit `creds/`, `data/`, `all_emails/`, `repurpose_site/`, `emails/` or `.env`.
- The data root `D:\msme project` is mounted into the container; the SQLite file stays there for now.
- Remove the six archived client secrets from `creds/`; keep only the four live files.

## 8. Access

- The partner is the repo admin.
- MG pushes as **`caferpgit`** for now; `EmpiFlow` is not a collaborator. Switch the active `gh` account before a push, then switch back.
- Add `EmpiFlow` later if attribution matters; not a blocker.

## 9. Agent git policy

- `git commit*`: **allowed** locally.
- `git push*` and `git pull*`: **ask MG first** (`ask`, not `allow`).
- `opencode.json`: `git commit*: allow`, `git push*: ask`, `git pull*: ask`. If the shared profile keeps `deny`, use DSH/manual git locally.
- An agent never force-pushes and never commits `creds/`, `data/`, `all_emails/` or `.env`.

## 10. Tags and change log

- Tag a verified milestone: `handover-YYYYMMDD`.
- Append a row here when the protocol changes; do not rewrite the history.

| date | who | change |
|---|---|---|
| 2026-11-11 | MG | initial protocol: branches, PR, one review, merge-when-ready, DB migrations, agent git policy |
| 2026-11-11 | HS | P0-2 confirmed: `opencode.json` now `git commit*: allow`, `git push*: ask`, `git pull*: ask`; this file lives at the repo root |
