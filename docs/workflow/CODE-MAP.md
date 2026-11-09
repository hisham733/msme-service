# Code map — `msme/`

_One app, one entrypoint. `run.py` (or `python -m msme`) starts `msme.combined:app` on :8899 (single uvicorn worker)._

## Layout

```
run.py                       # launcher: scheduler.start() + uvicorn msme.combined:app
msme/
  combined.py                # ASGI entrypoint: auth gate + receive/filter path dispatch
  paths.py                   # ROOT, STATIC, DOCS, PROMPTS, DATA, CREDS, archives (env-overridable)
  config.py                  # env defaults + prompt loading
  db.py                      # SQLite: runs, checklist, pipeline_results, filter_results, auth tables
  creds.py                   # Google OAuth services + DeepSeek key
  settings_store.py          # data/settings.json overrides
  auth.py                    # login, roles, CSRF, sessions, audit
  connection_test.py         # Config-page connectivity checks
  llm.py  deepseek.py        # provider switch + DeepSeek client
  receive/                   # Gmail -> article + media -> checklist row + archive
    dashboard.py             # pages + same-origin /api on :8899
    pipeline.py              # per-email orchestrator
    gmail.py normalize.py    # Gmail access + message -> email model
    decide.py extract.py verify.py   # the three AI steps
    checklist.py archive.py archive_layout.py
    drive_fetch.py onedrive_fetch.py box_fetch.py web_fetch.py
    receive_queue.py scheduler.py webhook_gmail.py reply.py
    editor_data.py workflow_lab.py
  filtering/                 # Jev: 3 hard gates + 11 weighted scores
    filter.py                # judge core (battery, routing)
    filter_service.py        # FastAPI sub-app: /filter, /lab, /report, /config
    filter_llm.py prefilter.py filter_log.py
  repurpose/                 # engine + bridge (D40)
    repurpose_export.py      # ACCEPT -> repurpose_inbox + repurpose_exports
    runner.py                # in-process worker (one article at a time)
    repurpose_worker.py      # manual CLI wrapper
    engine/                  # vendored pipeline + skills/ + dlw_shell/fonts/
  legacy/main.py             # old :8898 API, kept for reference and tests
tests/                       # unittest suite (191 tests)
tools/                       # ops + one-off developer scripts
static/ prompts/ docs/ data/ creds/ emails/ all_emails/   # runtime folders, resolved by paths.py
```

## Import rules

- Absolute package imports only: `from msme.receive import pipeline`, `from msme import config`.
- No flat imports (`import pipeline`) and no root compatibility shims (removed by `D38`).
- `msme/__init__.py` and every subpackage `__init__.py` stay empty; no import side effects.
- Feature modules never build a path from `__file__`; use `msme.paths`.

## Never move (code reads them by name — `D4`)

`docs/jev-variants.json` · `docs/archive-versions.json` · `docs/article-records.json` ·
`docs/artical.json` · `docs/negative-dataset.json` · `docs/email-dates.json` ·
`docs/sme-reject-6-10.json` · `docs/filter-variants-report-10.json` ·
`docs/filter-variant-separation.json` · `docs/published-index.json` · `docs/published-dataset.json` ·
`docs/gates-def-*.xlsx` · `docs/filter/original-gates.xlsx` · `docs/report-runs.jsonl`

## Commands

```bash
make test        # python3 -m unittest discover -s tests -p 'test_*.py' -v
make lint        # ruff check msme tests tools run.py
make compile     # python3 -m compileall -q msme run.py tools tests
make up          # docker compose up -d --build  -> http://localhost:8899
```
