# msme-service — project index

> AI_News intake: receive press releases from Gmail → judge them with Jev → repurpose the accepted
> ones. Owner: Hisham. **Read this file first** — the map for humans and LLM sessions.
> Structure standard set 2026-10-21 (T2).

## 1. Where everything is

| Path | What it holds |
|---|---|
| `README.md` | this map |
| `NOW.md` | standing state (≤ 40 lines) |
| `AGENTS.md` | machine rules for a session opened here |
| `opencode.json` | always-loaded instruction files + permission profile |
| `.claude/rules/msme-service.md` | project rules injected every session |
| `decisions/` | one OKF file per decision + generated `INDEX.md` |
| `todo/` | one OKF file per open item + generated `INDEX.md` |
| `session-analysis/` | one folder per working day; the numbered reply per turn |
| `tools/` | `build_register_indexes.py` — regenerates both register INDEX files |
| `static/` | every web page, served by one combined app on :8899 — see `static/INDEX.md` |
| `docs/` | reports, gate definitions, Jev notes, `WORKFLOW-RECEIVE-TO-PUBLISH.md`, `PRODUCTION-EMAIL-SETUP.md` — see `docs/INDEX.md` |
| `docs/reference/` | source guidelines, meeting deck, `FILTER-RULES.pdf`, email issues, future MySQL schema |
| `delet/` | manual-review deletion candidates (ignored by git) |
| `data/` | runtime state: SQLite, settings, verdict/error logs (`git`-ignored) |
| `prompts/` | DeepSeek system prompts for decide/extract/verify |
| `docs/reference/future-mysql/` | prepared MySQL schema (not used) |
| `creds/` | OAuth client/credential JSON — **secrets, never committed** |
| `emails/` | legacy archive / test articles — **not** read by the Report Manager |
| `all_emails/` | **live receive archive**, sorted by received date (see `all_emails/INDEX.md`, `D26`) |
| `delet/old-reports/` | old archived filter reports — manual review |
| `*.py` (root) | the service — one combined app in `run.py`: receive + filter on :8899 |
| `repurpose_export.py` | auto-exports latest ACCEPT articles to `repurpose_inbox/` (D35) |
| `repurpose_worker.py` | host worker: runs the engine for new inbox folders, one at a time |
| `repurpose_inbox/` · `repurpose_site/` | external engine input / built site — gitignored |

## 2. Hard rules

1. **Verify before asserting** — run the service/test and quote the result; a mechanism not run is a guess.
2. **Registers are the single home** for decisions and open work; a reply reasons, never stores.
   After editing register items run `python3 tools/build_register_indexes.py`.
3. **Build and test together** — name the run that proves a change, or say why none.
4. **Never commit `creds/`, `data/` or the email archives**; no secret in a page, log or reply.
5. Repurpose is **not built** — do not describe it as working (see `todo/T-001`).

## 3. Commands (run from this folder)

```bash
python3 tools/build_register_indexes.py         # regenerate decisions/ + todo/ INDEX.md
python3 -m compileall -q *.py                   # syntax check after edits
python run.py                                   # start one combined app (or: docker compose up -d --build)
curl -s localhost:8899/health
python3 repurpose_export.py --apply          # manual export (auto when ENABLE_AUTO_REPURPOSE)
python3 repurpose_worker.py                  # host worker: run new inbox folders
(cd ../MSME_AI_News && python3 -m pipeline.run check)   # engine key check
(cd ../MSME_AI_News && python3 -m pipeline.dashboard)   # engine dashboard :8765
curl -s localhost:8899/workflow-lab.html     # interactive receive walkthrough
```

## 4. Session rules

- Reply per turn: `session-analysis/<YYYY-MM-DD>_S<nn>_<subject>/<n>_<subject>.md`; chat = summary only.
- `S<nn>` = the project's working-day number — one folder per calendar day; extra sessions the same day
  add `2_…`, `3_…` files inside that day's folder.
- A new session reads, in order: this README → `NOW.md` → `todo/INDEX.md` → today's reply.
- Long detail lives in satellites (`docs/*.md`, `static/INDEX.md`) and is linked, never inlined here.
