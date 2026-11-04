# 1 — D38 · T-048 · package reorg (`msme/`)

**Date:** 2026-10-31 (S10) · **Scope:** structure only, no behaviour change · **Decision:** D38

## 1. What changed

The service is now one package with stage subpackages, and the repository root holds only `run.py`.

| Before | After |
|---|---|
| 45 `.py` in the root | `run.py` only |
| flat `import pipeline` everywhere | `from msme.receive import pipeline` |
| paths from `dirname(__file__)` (~30 sites) | `msme/paths.py` (ROOT, STATIC, DOCS, PROMPTS, DATA, CREDS, archives) |
| `tools/test_*.py` | `tests/` (13 modules) |
| 7 one-off scripts in the root | `tools/` |
| no lint/CI | `pyproject.toml` + ruff, `Makefile`, `.github/workflows/ci.yml` |

```
run.py                         # launcher -> msme.combined:app
msme/
  combined.py  config.py  paths.py  db.py  creds.py  settings_store.py
  auth.py  connection_test.py  llm.py  deepseek.py
  receive/     20 modules + decide/extract/verify + the four media fetchers
  filtering/   filter.py, filter_service.py, filter_llm.py, filter_log.py, prefilter.py
  repurpose/   repurpose_export.py, repurpose_worker.py
  legacy/      main.py
tests/  tools/  static/  prompts/  docs/  data/  creds/  all_emails/ …
```

209 import lines were rewritten; no compatibility shims remain. `docs/CODE-MAP.md` is the new one-page map.
`D38` records the rule; it narrows only the "root `*.py`" wording — `D4` (docs stay flat) and `D5` (never reconcile/delete filter variants) are untouched.

⭐ **Decision — §1:** ✅ nothing to decide.

## 2. Proving runs (all run this session)

| Check | Result |
|---|---|
| `python3 -m compileall -q msme run.py tools tests` | clean |
| `python3 -m unittest discover -s tests -p 'test_*.py'` | **149 tests, OK** |
| `ruff check msme tests tools run.py` (0.17.3) | **All checks passed** |
| `python3 -m msme` on :8897 | `/health` → `{"status":"ok","auto":false,...}` |
| Docker image `msme-service:pkg-reorg-20261031` | built; container `/health` 200 |
| `/login` · `/filters.json` without session | 200 · **401** |
| login `admin / <bootstrap>` → `/filters.json` | 200 · **3 gates + 11 scores** |
| `/report/files` | 6 `gates-def*.xlsx` listed |
| `/lab/payload?file=jev-variants.json` | `ok:true` |
| `/api/workflow/files` | 54 files, paths `msme/…`, importer graph correct |
| `/editor.html`, `/workflow-lab.html` | 200 |

The **live container was not restarted** — it still runs the previous image. Nothing changes for users until a rebuild.

⭐ **Decision — §2:** ✅ nothing to decide.

## 3. What stays exactly the same

- One entrypoint, one port: `python run.py` → `msme.combined:app` on :8899 (single worker).
- Docker `CMD` unchanged; compose mounts unchanged (`creds/`, `data/`, `docs/`, `all_emails/`…).
- Every URL, API path, DB schema and prompt file is unchanged.
- `docs/` stays flat; the 12 code-read files were not moved (`D4`).
- All filenames kept (your call), so headers, registers and old replies stay readable.

⭐ **Decision — §3:** ✅ nothing to decide.

## 4. Security finding raised now (off the main direction, but it is a secret)

`tools/export_creds.py` contains an **n8n encryption key literal** (`KEY = b"Ny1…"`). It was already in the baseline commit and is now in `tools/`. It is a real credential, not a test value.

- **Operational meaning:** anyone with the repo can decrypt an exported n8n credential blob if they also get one.
- **Example:** the file was used once to move n8n tokens into `creds/*.json`; it is not needed for the service to run.
- **Effect of not deciding:** the key stays in git history (even if the line is removed later) and in every clone, including the partner's.
- **Options:** (A) move it to an env var now and rotate the n8n encryption key; (B) leave it and accept the risk because the n8n instance is being retired.
- **Recommendation:** **A** — it is a 10-minute change and the partner clone is the moment it stops being private.
- **Blocks the build?** No. **Needed by:** before the handover push.

⭐ **Decision — §4:** A or B?

## 5. What remains for the handover

1. **You:** commit the working tree and push `main` — the profile denies `git commit` / `git push`.
2. **Docs reorg (`D39`, not yet written):** ~55 superseded experiment files → `delet/old-docs/`; `docs/reference/` client files → the bundle only; rewrite `docs/INDEX.md`; fix five register links; keep the code-read files flat.
3. **Bundle:** `creds/{gmail,drive,sheets,deepseek}.json`, `TYPESAFE_API_KEY`, sanitised `data/` snapshot (clear `sessions`, `login_attempts`, `audit_log`; keep `users`/`checklist`/`filter_results`), the client source files.
4. **Partner runbook** (`T-048`): clone → folders → `.env` (`COOKIE_SECURE=false`, `ENABLE_AUTO=false`, `REPLY_ENABLED=false`, `ENABLE_WEBHOOK=false`) → `docker compose up -d --build` → `admin/admin`; keep polling off on the shared mailbox.

⭐ **Decision — §5:** continue with the docs reorg + bundle in this session, or stop here and do it next session?

## 6. Parked this turn

- 8 unused local variables (`F841`) found by ruff — real smells (e.g. `pipeline.py` `web_logo_names` is built but never counted). Parked: they need a behaviour review, not a lint fix.
- `docs/REPURPOSE-INTEGRATION-2026-10-27.md` and `WORKFLOW-RECEIVE-TO-PUBLISH.md` still name `repurpose_export.py` without the `msme/repurpose/` prefix — cosmetic, folded into the docs reorg.

## 7. Recap

| Item | State |
|---|---|
| Package layout (`D38`) | **built and proven** |
| Tests / lint / compile | 149 pass · ruff clean · compile clean |
| Docker image | built, health/login/endpoints verified, not deployed |
| Live container | untouched (old image still serving) |
| Commit / push | **owed by you** |
| Docs reorg + bundle | pending (D39, T-048) |
| n8n key literal | raised, awaiting A/B |

## 8. What I recommend next

**Carry on in this session** with §4 (n8n key → env, rotate) and then the docs reorg + bundle — the context of the reorg is already loaded, so a new session would pay to rebuild it. Thinking effort: **medium** (mostly mechanical moves plus one security change). If you prefer a clean boundary, compact first and start a new session with:

> "Read NOW.md, docs/CODE-MAP.md and decisions/D38.md. Do the docs reorg (D39) and build the partner handover bundle per todo/T-048.md."
