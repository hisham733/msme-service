> Preserved from the project-root `README.md` at the 2026-10-21 T2 setup. It is a historical
> architecture reference, not the project map — the map is `README.md` at the root.

# MSME Newsbot — Python Service

Replaces the n8n archive workflow with a standalone Python (FastAPI) service.

## Architecture

```
msme-service/
├── combined.py       # one ASGI entrypoint on :8899; routes receive + filter paths
├── main.py           # legacy receive API (not started by run.py)
├── dashboard.py      # receive app (static pages + /api/*)
├── run.py            # entrypoint: one server + scheduler (single worker)
├── scheduler.py      # auto-poll Gmail (OFF until ENABLE_AUTO=true)
├── pipeline.py       # orchestrates one email -> checklist row
├── decide.py         # DeepSeek: which attachment is the press release
├── extract.py        # DeepSeek: extract article text + PDF/DOCX text + logo scan
├── drive_fetch.py    # recursive Drive folder walk (docs + images + logo)
├── verify.py         # DeepSeek: headline, subject match, ready-to-filter
├── filter.py         # Jev: 14-rule editorial judge (gates + weighted score)
├── filter_service.py # Jev filter routes (/filter, /verdicts) behind combined.py
├── deepseek.py       # shared DeepSeek client (json_object + retry)
├── gmail.py          # Gmail list/get/download/mark-read
├── normalize.py      # email -> model (subject/from/body/attachments/links)
├── checklist.py      # write the 14-column row to SQLite
├── db.py             # SQLite storage (MySQL schema prepared in docs/reference/future-mysql/)
├── creds.py          # load exported OAuth tokens
├── export_creds.py   # one-time: decrypt n8n tokens into creds/*.json
├── prompts/          # DeepSeek prompts (ported from n8n)
├── static/           # dashboard HTML
├── docs/reference/future-mysql/schema_mysql.sql  # future MySQL switch
├── Dockerfile
└── docker-compose.yml
```

## Run

```bash
# 1. Export credentials from n8n (once)
docker run --rm -v n8n_n8n_data:/data -v "$PWD":/wf -w /wf \
  python:3.12-alpine sh -c "pip install cryptography -q && python3 export_creds.py"

# 2. Build + run
docker compose up -d --build
```

- **One app**: http://localhost:8899  (checklist, filter, logs, lab, report)
- **Health**: GET `:8899/health` (receive health at `/api/health`)
- **Filter API**: POST `:8899/filter`; verdicts at `:8899/verdicts`
- Legacy receive paths (`/run`, `/run-all`, `/emails`, `/logs`, `/config`) are rewritten to `/api/*`.

## Filter stage (inside receive)

The same pipeline calls **Jev** (TypeSafe System One) when `readyToFilter=true`.
The verdict is stored in `filter_results` and linked to the checklist row; the filter
routes remain available for manual/lab/report use on :8899.

- 6 hard gates (noul): not_sme_relevant, no_wider_value, is_it_commercial_intent
  (**guideline-aligned: hard-sell only**), not_geographically_relevant — each has its
  own threshold (default 0.85, editable) → REJECT; defamatory + political → **EDITOR REVIEW**
- 8 scored criteria (noul, phrased negatively): no_substance, not_identifiable,
  unattributed_claims, not_current, no_editorial_value, contact,
  category_fit, not_sme_voice — %-weights summing to 100 (editable); ≥ 60 → ACCEPT
- 1 context question (noul): is_negative_or_attacking (polarity, for editors)
- Outcomes: **ACCEPT / EDITOR REVIEW / REJECT** (+ HOLD on the receive side). Optional
  DeepSeek assist: preprocess (clean/translate/extract) + second opinion on weak gates and borderline weighted

```bash
curl -X POST localhost:8899/filter -H 'Content-Type: application/json' -d '{
  "subject": "Fwd: [PRESS RELEASE] ...",
  "from": "Editor MSME <editor@malaysiasme.com.my>",
  "date": "Wed, 30 Sep 2026",
  "bodyText": "KUALA LUMPUR, 29 Sep 2026 - ..."
}'
# -> {"outcome":"ACCEPT","weighted":78,"gate":null,"gates":{...},"scores":{...}}
```

Verdicts are logged to `data/filter_verdicts.jsonl` (GET /verdicts). The receive
pipeline calls Jev automatically for ready articles; the filter API remains available for
manual, lab and report use.

## Manual vs auto

- **Manual now**: POST `/api/run?email_id=<gmail-id>` on :8899 (or paste the id into the dashboard button).
- **Auto later**: set `ENABLE_AUTO=true` and `SCHEDULE_MINUTES=5` in docker-compose.yml.
  - Must run **one uvicorn worker** (already the case) so the scheduler doesn't double-fire.

## Checklist columns (14)

`subject, threadId, date, folderId, folderUrl, articleFile, hasArticle, hasPic,
hasLogo, hasLogoInArticle, hasImageInArticle, subjectMatch, subjectScore, readyToFilter`

Source of truth: **SQLite** `data/msme.sqlite3`; the checklist row is written there only.
Filter verdicts live in `filter_results`, linked by `checklist_id`; the 14-column checklist
contract is unchanged. The Google Sheet is optional/manual and is not synced. MySQL schema
is prepared in `docs/reference/future-mysql/schema_mysql.sql` for a future switch (`DB_ENGINE=mysql` + `MYSQL_DSN`).

## Credentials

Exported from the n8n DB into `creds/*.json` (not committed). Google OAuth tokens
auto-refresh via `google-auth`. DeepSeek key is in `creds/deepseek.json`.