# msme-service — project index

> AI_News intake: receive press releases from Gmail → judge them with Jev → repurpose the accepted
> ones. Owner: Hisham. **Read this file first** — the map for humans and LLM sessions.
> Structure standard set 2026-10-21 (T2).

## 1. Where everything is

| Path | What it holds |
|---|---|
| `README.md` | this map |
| `INDEX.md` | every `.py` file: purpose, example and what breaks if deleted |
| `NOW.md` | standing state (≤ 40 lines) |
| `AGENTS.md` | machine rules for a session opened here |
| `opencode.json` | always-loaded instruction files + permission profile |
| `.claude/rules/msme-service.md` | project rules injected every session |
| `decisions/` | one OKF file per decision + generated `INDEX.md` |
| `todo/` | one OKF file per open item + generated `INDEX.md` |
| `session-analysis/` | one folder per working day; the numbered reply per turn |
| `msme/` | the service package — receive, filtering (Jev), repurpose, legacy — see `docs/workflow/CODE-MAP.md` (`D38`) |
| `run.py` | the one entrypoint: scheduler + `msme.combined:app` on :8899 |
| `tests/` | unittest suite (297 tests) |
| `tools/` | ops + one-off developer scripts, `build_register_indexes.py` |
| `msme/repurpose/` | ACCEPT → inbox export, the in-process engine runner and the vendored engine (D40) |
| `pyproject.toml` · `Makefile` · `.github/workflows/ci.yml` | ruff config, dev commands, CI |
| `static/` | every web page, served by one combined app on :8899 — see `static/INDEX.md` |
| `docs/` | topic folders — `workflow/`, `filter/` (+ `experiments/`), `meetings/`, `operations/`, `receive/`, `reference/` — plus the code-read files at the root; see `docs/INDEX.md` (`D39`) |
| `docs/reference/` | source guidelines, meeting deck, `FILTER-RULES.pdf`, email issues, future MySQL schema |
| `delet/` | manual-review deletion candidates (ignored by git) |
| `data/` | runtime state: SQLite, settings, verdict/error logs (`git`-ignored) |
| `prompts/` | DeepSeek system prompts for decide/extract/verify |
| `docs/reference/future-mysql/` | prepared MySQL schema (not used) |
| `creds/` | OAuth client/credential JSON — **secrets, never committed** |
| `emails/` | legacy archive / test articles — **not** read by the Report Manager |
| `all_emails/` | **live receive archive**, sorted by received date (see `all_emails/INDEX.md`, `D26`) |
| `delet/old-reports/` | old archived filter reports — manual review |
| `repurpose_inbox/` · `repurpose_site/` | engine input / built site — gitignored |

## 2. Hard rules

1. **Verify before asserting** — run the service/test and quote the result; a mechanism not run is a guess.
2. **Registers are the single home** for decisions and open work; a reply reasons, never stores.
   After editing register items run `python3 tools/build_register_indexes.py`.
3. **Build and test together** — name the run that proves a change, or say why none.
4. **Never commit `creds/`, `data/` or the email archives**; no secret in a page, log or reply.
5. Repurpose runs **in-process** (`msme/repurpose/engine/`, `D40`): one worker thread, one article at a time; no separate engine or :8765.

## 3. Commands (run from this folder)

```bash
python3 tools/build_register_indexes.py         # regenerate decisions/ + todo/ INDEX.md
python3 -m compileall -q msme run.py tools tests   # syntax check after edits
python3 -m unittest discover -s tests -p 'test_*.py' -v   # 297 tests
python run.py                                   # start one combined app (or: docker compose up -d --build)
curl -s localhost:8899/health
python3 -m msme.repurpose.repurpose_export --apply   # manual export (auto when ENABLE_AUTO_REPURPOSE)
python3 -m msme.repurpose.repurpose_worker --once    # manual run (the app starts the worker itself)
curl -s localhost:8899/repurpose.html                # repurpose queue/status
curl -s localhost:8899/workflow-lab.html     # interactive receive walkthrough
```

## 4. Login (T-047)

- Local accounts only: `/login`. Roles: **admin** (everything) and **editor** (`/editor.html` + filter config).
- 7-day session cookie (`HttpOnly`, `Secure`, `SameSite=Lax`) + CSRF on every non-GET; the webhook stays public (Pub/Sub OIDC).
- First admin comes from `AUTH_BOOTSTRAP_USERNAME` / `AUTH_BOOTSTRAP_PASSWORD` in `.env` **only while the users table is empty**. Sign in, change the password on `/account.html`, then remove those two lines from `.env`.
- `COOKIE_SECURE=false` only for direct `http://localhost` access; the tunnel is HTTPS.
- Admin pages: `/users.html` (create/disable/reset roles, audit log) and the filter-config version history/restore.

## 5. Session rules

- Reply per turn: `session-analysis/<YYYY-MM-DD>_S<nn>_<subject>/<n>_<subject>.md`; chat = summary only.
- `S<nn>` = the project's working-day number — one folder per calendar day; extra sessions the same day
  add `2_…`, `3_…` files inside that day's folder.
- A new session reads, in order: this README → `NOW.md` → `todo/INDEX.md` → today's reply.
- Long detail lives in satellites (`docs/*.md`, `static/INDEX.md`) and is linked, never inlined here.
