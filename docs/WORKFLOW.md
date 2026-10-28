# MSME Newsbot — Project Workflow

> **Interactive version:** open `http://localhost:8899/workflow-lab.html` for the live 9-stage
> walkthrough — real code, input/output, runnable examples and the full `.py` purpose map.

End-to-end flow of the press-release intake pipeline. Each email is processed
through the stages below; the AI model is **switched live from the Config page**
(`deepseek` or `gemini`), and every run is logged with the model + token usage.

---

## 1. High-level flow

```
Gmail Inbox
   │  (unread, in:inbox is:unread -category:promotions)
   ▼
Normalize ──────────▶ clean body for AI (strip cover/disclaimer/forwarders)
   │
   ▼
Decide Source (AI) ──▶ which attachment is the press release + link + images
   │
   ├─ attachment? ──▶ Load Attachments → Extract PDF/DOCX text
   ├─ drive link? ──▶ Drive Media Kit (recursive walk) → English release text
   │                  (fetched even when an attachment exists; short/branded &
   │                   tracker links are resolved to the real Drive folder first)
   └─ body only? ───▶ use cleaned email body
   │
   ▼
Extract & Clean PR (AI) ──▶ verbatim article + source + evidence
   │
   ▼
Logo Scan (deterministic) ──▶ embedded image in doc? (PDF /Subtype/Image, DOCX word/media)
   │
   ▼
Verify (AI) ──▶ headline, subject match, ready-to-filter, logo/image verdict
   │
   ▼
readyToFilter=true? ──▶ Filter (Jev) ──▶ ACCEPT / REJECT / EDITOR REVIEW
   │
   ▼
Checklist Row (14 cols) + filter_results ──▶ SQLite
   │
   ▼
Archive to PC ──▶ all_emails/<Subject>/{article.md, images/, originals/}
   │
   ▼
Dashboard ──▶ checklist.html · flow.html · logs.html · config.html
```

---

## 2. Pipeline stages (in order)

| # | Stage | Type | Module | What it does |
|---|-------|------|--------|--------------|
| 1 | **Gmail Inbox** | trigger | `gmail.py` | Lists unread emails matching the query |
| 2 | **Normalize** | code | `normalize.py` | Parses email → subject/from/date/body/attachments/links (incl. HTML `href`); builds `cleanBody`; resolves short/branded & tracker links to reveal hidden Drive folders (cap 8) |
| 3 | **Decide Source** | AI | `decide.py` | Chooses which attachment is the press release (English preferred), detects images + media-kit link |
| 4 | **Load Attachments** | code | `gmail.py` / `extract.py` | Downloads PDF/DOCX, extracts text (pypdf / python-docx) |
| 5 | **Drive Media Kit** | code | `drive_fetch.py` | Recursive folder walk (no AI); collects docs + images (images capped at the **15 largest**); detects embedded logo; picks the **English release** only. Merged with attachment media when both exist |
| 6 | **Extract & Clean PR** | AI | `extract.py` | Extracts the verbatim article + articleSource + evidence + logo/image flags |
| 7 | **Logo Scan** | deterministic | `extract.py` | `classify_doc_images()`: PDF `/Subtype /Image`, DOCX header/body `word/media/*` |
| 8 | **Verify** | AI | `verify.py` | Verdict: headline, subjectMatch (0–100), readyToFilter, hasLogo/hasImage |
| 9 | **Editorial Filter** | Jev | `filter.py` (in-process) | Runs only when readyToFilter=true; 3 hard gates + 11 weighted scores → **ACCEPT / REJECT / EDITOR REVIEW**; saved in `filter_results` |
| 10 | **Checklist Row** | code | `checklist.py` / `db.py` | Writes the 14-column row to SQLite |
| 11 | **Archive to PC** | code | `archive.py` | Saves article `.md`, `images/`, `originals/` to `emails/<Subject>/` |
| 12 | **Dashboard** | web | `dashboard.py` | Serves the 4 pages + `/api/*` endpoints |

---

## 3. AI model layer (switchable)

- **`llm.py`** — unified `LLMClient` exposing `chat_json(system, user, max_tokens)`.
- Provider chosen from settings: `LLM_PROVIDER = deepseek | gemini`.
- Every call creates a fresh client → **switching providers in the Config page takes effect on the next email immediately** (no restart).
- Token usage + model are captured per run.

| Provider | Model | Notes |
|----------|-------|-------|
| **deepseek** | `deepseek-flash` (V4.1-Flash) | `effort: low`; paid (~$0.0013/email) |
| **gemini** | `gemini-2.5-flash` | **free tier** (~1,500 req/day); ~34% fewer tokens |

`deepseek.py` handles the DeepSeek calls (with retry logic: no blind retry on
empty JSON, fails fast on 402/400). `connection_test.py` verifies whichever
provider is active.

---

## 4. Checklist columns (14)

```
subject, threadId, date, folderId, folderUrl, articleFile,
hasArticle, hasPic, hasLogo, hasLogoInArticle, hasImageInArticle,
subjectMatch, subjectScore, readyToFilter
```

**readyToFilter** = hasArticle AND (hasPic OR hasLogo OR hasImageInArticle) AND subjectScore > 60.

Filter verdicts are **not** extra checklist columns: `filter_results.checklist_id` links the
verdict to the row, and `db.list_checklist()` returns the latest summary for the UI.

---

## 5. Storage

| Store | Purpose | Path / ID |
|-------|---------|-----------|
| **SQLite** | checklist source of truth + run logs + `filter_results` | `data/msme.sqlite3` |
| **Google Sheet** `Checklist` tab | optional/manual; not synced by receive | `1T_XURPN4uuC8d7YqWbRFS-0QHLXW7-Y1UQ82rJPrQCo` |
| **Local PC archive** | article + images + originals | `emails/<Subject>/` |
| **MySQL schema** (prepared) | future switch | `docs/reference/future-mysql/schema_mysql.sql` |

---

## 6. API endpoints

### Dashboard app (`:8899` — same origin as the pages)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/health` | Service status + auto-poll flag |
| GET | `/api/emails` | List unread emails (cached 15s) |
| POST | `/api/run?email_id=` | Start processing one email (async → returns run_id) |
| GET | `/api/run-status?run_id=` | Poll run status (running / success / error) |
| POST | `/api/run-all` | Process all unread emails |
| GET | `/api/pipeline-results` | Per-run full stage detail + tokens + model |
| POST | `/api/clear` | Clear SQLite only |
| GET | `/api/download.csv` | Download checklist as CSV |
| GET | `/api/logs` | Run logs (status, model, error) |
| GET/PUT | `/api/config` | Read/save settings (provider, keys, sheet, auto) |
| POST | `/api/test-connection` | Test Gmail/Sheets/Drive/DeepSeek-or-Gemini |
| GET | `/checklist.json` / `/logs.json` | Dashboard data |

### Legacy receive paths

`combined.py` rewrites `/run`, `/run-all`, `/emails`, `/logs`, `/config` to their `/api/*`
equivalents on :8899; `:8898` is no longer exposed.

### Filter paths (same app, :8899)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/filter` | Judge one article → `{outcome: ACCEPT\|REJECT, weighted, gate, gates, scores, confidence}` |
| GET | `/health` | Combined liveness (`/api/health` is receive health) |
| GET | `/filters.json` | The 14-rule battery (6 gates + 8 scores) |
| GET | `/verdicts` | Recent verdicts (logged to `data/filter_verdicts.jsonl`) |

Runs **Jev** (`jev-latest`) via `POST api.typesafe.ai/v1/systemone`. The receive
pipeline calls this same judge in-process when an article is ready; the endpoints remain for
manual, lab and report use.

---

## 7. Dashboard pages

| Page | URL | Shows |
|------|-----|-------|
| **Checklist** | `/checklist.html` | KPI cards, email dropdown + Run/Refresh/Download/Clear, status column, 14-col table |
| **Workflow** | `/flow.html` | Animated pipeline diagram (incl. filter), live trace, recent runs with per-stage detail + tokens + model |
| **Receive logs** | `/receive-logs.html` | Receive run history with Status / Model / Subject / Error |
| **Filter logs** | `/logs.html` | Jev verdict/error trail |
| **Config** | `/config.html` | Combined receive settings + filter rule editor |

---

## 8. Trigger modes

- **Manual:** pick an email in the checklist dropdown → **Run** (async, shows Processing… → ✓ Completed).
- **Auto-poll:** set `ENABLE_AUTO=true` in Config + `SCHEDULE_MINUTES` → scheduler polls Gmail every N minutes (single worker).

---

## 9. Key modules reference

| File | Responsibility |
|------|----------------|
| `pipeline.py` | Orchestrates one email → checklist row (calls decide → extract → verify → archive) |
| `normalize.py` | Email parsing + `cleanBody` boilerplate strip |
| `gmail.py` | Gmail API: list/get/download/mark-read |
| `decide.py` / `extract.py` / `verify.py` | The 3 AI steps (system prompts from `prompts/`) |
| `drive_fetch.py` | Recursive Drive walk + English-release pick + logo scan |
| `archive.py` | Local PC save: article.md + images/ + originals/ |
| `checklist.py` | SQLite checklist write |
| `db.py` | SQLite: runs (with model), checklist, pipeline_results |
| `llm.py` | Unified provider client (deepseek/gemini) |
| `deepseek.py` | DeepSeek client + retry logic |
| `settings_store.py` | Persisted runtime settings |
| `scheduler.py` | Auto-poll (off unless enabled) |
| `combined.py` | One ASGI entrypoint: receive at root, filter paths on :8899 |
| `dashboard.py` / `main.py` | Receive app / legacy API (not started separately) |
| `filter.py` / `filter_service.py` | Jev 14-rule judge + filter routes (same :8899 app) |
| `run.py` | Entrypoint: one server + scheduler |