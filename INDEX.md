# INDEX — every `.py` file

_What each file does, why it exists, one real example, and what breaks if it is deleted.
Generated from the file headers + the actual import graph on 2026-10-31 (`D38`)._

## How to read this

| Tag | Meaning |
|---|---|
| **FATAL** | deleting it stops the app from starting (a module loaded at boot imports it) |
| **BREAKS A FEATURE** | the app starts, but one feature (or the AI steps) fails |
| **OPERATOR ONLY** | not loaded by the app; a script you run by hand |
| **TEST ONLY** | only the test suite uses it; the app is unaffected |
| **SAFE** | nothing in the repo imports it; check the note before deleting |

Reachability: **38 of 69 files** are loaded from the entrypoint (`run.py` → `msme/__main__.py` →
`msme.combined:app`, plus the uvicorn string `msme.combined:app`). The other 31 are tests, tools,
the host worker and the legacy app.

---

## 1. Entry and shared modules (12)

### `run.py` — entrypoint launcher
**Purpose:** starts the auto-poll scheduler and one uvicorn worker with `msme.combined:app` on :8899.
**Why needed:** it is the Docker `CMD` (`python run.py`) and the documented start command.
**Example:** `python run.py` → `curl -s localhost:8899/health`.
**If deleted:** Docker cannot start; `python -m msme` still works, but the standard command is gone. **FATAL (for Docker).**

### `msme/__main__.py` — `python -m msme`
**Purpose:** the same launcher as `run.py`, packaged so the app can run as a module.
**Why needed:** `run.py` imports it; `python -m msme` is the alternate start.
**Example:** `DASH_PORT=8897 python -m msme`.
**If deleted:** `run.py` fails to import and `python -m msme` is gone. **FATAL.**

### `msme/combined.py` — the one ASGI app
**Purpose:** wraps both sub-apps in the auth gate and dispatches each path to receive or filter.
**Why needed:** uvicorn loads it **by name** (`msme.combined:app`), so no file imports it.
**Example:** `curl -s localhost:8899/health` → `{"status":"ok",...}`; `curl -s localhost:8899/filter.html`.
**If deleted:** the server cannot load an app; everything is down. **FATAL.**

### `msme/config.py` — configuration
**Purpose:** env-overridable constants (ports, models, Gmail query, archive roots, prompts) and `load_prompt()`.
**Why needed:** 34 modules import it.
**Example:** `from msme import config; config.load_prompt("extract_prompt.txt", "v1")`.
**If deleted:** almost every import fails. **FATAL.**

### `msme/paths.py` — filesystem paths
**Purpose:** resolves `ROOT`, `STATIC`, `DOCS`, `PROMPTS`, `DATA`, `CREDS`, archives and repurpose folders from the package location, not the current directory.
**Why needed:** 15 modules; it is what makes the package safe to run from anywhere.
**Example:** `from msme import paths; (paths.DOCS / "jev-variants.json").exists()`.
**If deleted:** config/creds/filter/report/dashboard import errors. **FATAL.**

### `msme/db.py` — SQLite storage
**Purpose:** the schema and accessors for runs, checklist, pipeline traces, filter results, webhook queue, users, sessions, audit and filter-config versions.
**Why needed:** 16 modules; it is the source of truth for the checklist.
**Example:** `db.init_db(); db.list_checklist(limit=5)`.
**If deleted:** checklist, login, filter history and reports all die. **FATAL.**

### `msme/creds.py` — OAuth and API keys
**Purpose:** loads `creds/*.json`, builds Gmail/Sheets/Drive services, returns the DeepSeek key.
**Why needed:** every Google call and the AI steps.
**Example:** `creds.gmail().users().getProfile(userId="me").execute()`.
**If deleted:** the app may start, but no email is read or sent and no AI call runs. **FATAL (importers).**

### `msme/settings_store.py` — runtime settings
**Purpose:** reads/writes `data/settings.json` over the config defaults and masks secrets for pages.
**Why needed:** 16 modules; the Config page writes through it.
**Example:** `settings_store.get("ACCEPT_THRESHOLD")`; `settings_store.save({"ENABLE_AUTO": False})`.
**If deleted:** import errors across the app. **FATAL.**

### `msme/auth.py` — login, roles, CSRF
**Purpose:** scrypt passwords, 7-day sessions, CSRF, the ASGI `AuthGate`, admin/editor rules, lockout, audit.
**Why needed:** `combined.py`, `dashboard.py`, `filter_service.py` import it; every request passes through it.
**Example:** `curl -s -c jar -H 'Content-Type: application/json' -d '{"username":"admin","password":"..."}' localhost:8899/api/auth/login`.
**If deleted:** the app cannot start; the auth boundary disappears. **FATAL.**

### `msme/connection_test.py` — Config-page connectivity checks
**Purpose:** tests Gmail, Sheets, Drive and the active LLM provider and returns `{ok, detail}`.
**Why needed:** the Config page's "Test connection" button; dashboard imports it at boot.
**Example:** `connection_test.test_all()`.
**If deleted:** import error at startup (dashboard imports it). **FATAL (import), feature = test button.**

### `msme/llm.py` — provider switch
**Purpose:** one `chat_json()` over DeepSeek or Gemini, tolerant JSON extraction, token tally.
**Why needed:** decide/extract/verify/reply/filter assist.
**Example:** `llm.LLMClient().chat_json("system", "user", max_tokens=2000)`.
**If deleted:** every AI step fails (imports in 9 modules). **FATAL.**

### `msme/deepseek.py` — DeepSeek client
**Purpose:** Chat Completions with `json_object`, retry policy and token usage tally.
**Why needed:** `llm.py` loads it for the default provider.
**Example:** `DeepSeekClient(model="deepseek-v4-flash").chat_json(...)`.
**If deleted:** DeepSeek calls fail (Gemini path still loads). **BREAKS A FEATURE.**

### Package markers (5)
`msme/__init__.py`, `msme/receive/__init__.py`, `msme/filtering/__init__.py`,
`msme/repurpose/__init__.py`, `msme/legacy/__init__.py` — empty package markers.
**If deleted:** Python may treat the folder as a namespace package, but packaging, CI and `pip install .`
become unreliable. **Not safe.**

---

## 2. Receive stage — `msme/receive/` (20)

### `dashboard.py` — receive pages + same-origin API
**Purpose:** serves `/`, `/checklist.html`, `/editor.html`, `/users.html`, `/account.html`, `/config.html`, the receive `/api/*` endpoints and the login routes.
**Why needed:** `combined.py` mounts it for every non-filter path.
**Example:** `curl -s localhost:8899/api/health`; `curl -s -b jar localhost:8899/api/emails`.
**If deleted:** the whole receive UI and API disappear. **FATAL.**

### `pipeline.py` — per-email orchestrator
**Purpose:** one email → normalize → decide → collect every source → extract → verify → checklist row → archive.
**Why needed:** every receive path (button, queue, webhook, scheduler, Lab dry-run) calls it.
**Example:** `pipeline.process_email(service, email_id, run_id=run_id)`.
**If deleted:** no email can be processed. **FATAL.**

### `gmail.py` — Gmail client
**Purpose:** list unread (forces `is:unread`), fetch a message, parse it, mark read, send replies, watch/history.
**Why needed:** receive, reply, webhook and the queue all use it.
**Example:** `gmail.list_unread(service, config.GMAIL_QUERY)`.
**If deleted:** no inbox access. **FATAL.**

### `normalize.py` — message → email model
**Purpose:** subject/from/date/body, attachments, links and remote body images into one model.
**Why needed:** `pipeline` and the Workflow Lab.
**Example:** `normalize.build_email_model(service, msg_id)`.
**If deleted:** the pipeline cannot read the email. **FATAL.**

### `checklist.py` — 14-column checklist row
**Purpose:** builds the row and saves it to SQLite; triggers the repurpose export for accepted rows.
**Why needed:** every run ends here.
**Example:** `checklist.save_checklist(row)`.
**If deleted:** runs finish but nothing is stored. **FATAL.**

### `archive.py` — local article archive
**Purpose:** writes `all_emails/<Subject>/article.md`, `images/`, `originals/`.
**Why needed:** the report, filter and repurpose read the archive.
**Example:** `archive.archive_email(model, article_text, "article.md", images)`.
**If deleted:** no article files, no report, no repurpose. **FATAL.**

### `archive_layout.py` — version grouping + dates
**Purpose:** groups `_1`, `_2` folder copies, picks one version per subject, parses received dates.
**Why needed:** the report manager and the ready list.
**Example:** `archive_layout.group_versions(paths.ARCHIVE)`.
**If deleted:** report/ready list import error. **FATAL.**

### `receive_queue.py` — one-at-a-time queue
**Purpose:** accepts message ids from the webhook or polling, claims one row, runs the pipeline, marks read.
**Why needed:** `combined.py`, `scheduler.py` and the webhook.
**Example:** `receive_queue.enqueue_ids(["18f..."], source="webhook")`.
**If deleted:** webhook, polling and auto-receive stop. **FATAL.**

### `scheduler.py` — auto-poll loop
**Purpose:** when `ENABLE_AUTO=true`, polls Gmail every N minutes and enqueues unread mail.
**Why needed:** `msme/__main__.py` starts it at boot.
**Example:** `ENABLE_AUTO=true python run.py`.
**If deleted:** startup import error. **FATAL.**

### `webhook_gmail.py` — Gmail Push handler
**Purpose:** verifies the Pub/Sub OIDC token, decodes the push, dedupes it, enqueues the history.
**Why needed:** the public `/webhooks/gmail` route in `dashboard.py`.
**Example:** `curl -s -o /dev/null -w '%{http_code}' -X POST localhost:8899/webhooks/gmail` → `401`.
**If deleted:** startup import error (dashboard imports it). **FATAL.**

### `reply.py` — rejection reply email
**Purpose:** builds the reasons from the flags and sends the apology/reason email.
**Why needed:** the receive pipeline can call it; the Lab previews it.
**Example:** `reply.send_reply_for_row(service, model, row, force=True)`.
**If deleted:** startup import error (dashboard imports it). **FATAL.**

### `editor_data.py` — editor page data
**Purpose:** merges checklist + runs + stages + filter + repurpose into one item per email for `/editor.html`.
**Why needed:** the editor page.
**Example:** `editor_data.query_items(page=1, page_size=20)`.
**If deleted:** startup import error (dashboard imports it). **FATAL.**

### `workflow_lab.py` — Workflow Lab backend
**Purpose:** stages, real code excerpts, samples, dry-run sandbox and the `.py` purpose map.
**Why needed:** `/workflow-lab.html` and `/api/workflow/*`.
**Example:** `curl -s -b jar localhost:8899/api/workflow/files`.
**If deleted:** startup import error (dashboard imports it). **FATAL.**

### `decide.py` — AI step 1
**Purpose:** picks the press-release source and flags images/media-kit links.
**Why needed:** `pipeline` and the Lab.
**Example:** `decide.decide(model)`.
**If deleted:** startup import error (pipeline imports it). **FATAL.**

### `extract.py` — AI step 2 + text/image helpers
**Purpose:** selects the article from the candidate pool; extracts PDF/DOCX text and images; classifies logos/photos.
**Why needed:** pipeline, all four fetchers, filter service and the Lab.
**Example:** `extract.classify_doc_images(data, "release.docx")`.
**If deleted:** startup import error. **FATAL.**

### `verify.py` — AI step 3
**Purpose:** headline, subject match, `readyToFilter`, logo/image verdicts, deterministic finalise.
**Why needed:** `pipeline` and the Lab.
**Example:** `verify.verify(article, image_names, flags)`.
**If deleted:** startup import error. **FATAL.**

### `drive_fetch.py` — Google Drive media kit
**Purpose:** walks a Drive folder, downloads docs/images, fetches a single Drive file link.
**Why needed:** the pipeline's Drive source; `archive` reuses its downloader.
**Example:** `drive_fetch.fetch_media_kit("https://drive.google.com/drive/folders/...")`.
**If deleted:** startup import error (pipeline imports it). **FATAL.**

### `onedrive_fetch.py` — OneDrive public shares
**Purpose:** opens a public `1drv.ms` / `onedrive.live.com` share as a guest and downloads its files.
**Why needed:** the pipeline's OneDrive source.
**Example:** `onedrive_fetch.fetch_kit("https://1drv.ms/f/...")`.
**If deleted:** startup import error. **FATAL.**

### `box_fetch.py` — Box press kits
**Purpose:** parses a public Box folder and downloads its files (stdlib only).
**Why needed:** the pipeline's Box source.
**Example:** `box_fetch.fetch_press_kit("https://app.box.com/s/...")`.
**If deleted:** startup import error. **FATAL.**

### `web_fetch.py` — public article/speech pages
**Purpose:** in `WEB_FETCH_MODE=probe`, fetches public links and decides if a page is an article; extracts images.
**Why needed:** the pipeline's web source; SSRF guards and WebP handling.
**Example:** `web_fetch.fetch_article("https://www.pitchmystory.com/newswire/...")`.
**If deleted:** startup import error. **FATAL.**

---

## 3. Filter stage — `msme/filtering/` (5)

### `filter.py` — Jev judge core
**Purpose:** asks Jev one battery (3 hard gates + 11 weighted scores) in one request, then routes to ACCEPT / EDITOR REVIEW / REJECT.
**Why needed:** receive (when `readyToFilter=true`), the filter page, the Lab, reports and history.
**Example:** `filter.judge(article)` → `{"outcome":"ACCEPT","weighted":78,...}`.
**If deleted:** startup import error (dashboard and pipeline import it). **FATAL.**

### `filter_service.py` — filter sub-app
**Purpose:** serves `/filter.html`, `/verdicts.html`, `/lab.html`, `/testfilter.html`, `/reportmanager.html`, `/config.json`, `/filters.json`, `/report/*` and writes report files into `docs/`.
**Why needed:** `combined.py` dispatches filter paths to it.
**Example:** `curl -s -b jar localhost:8899/filters.json`.
**If deleted:** startup import error (combined imports it); no filter UI/report. **FATAL.**

### `filter_llm.py` — DeepSeek assist for Jev
**Purpose:** optional preprocess (clean/translate/extract) and a second opinion on one weak gate or a borderline score.
**Why needed:** `filter.py` and `filter_service.py` import it lazily; switchable with `ENABLE_LLM_ASSIST`.
**Example:** `ENABLE_LLM_ASSIST=true` then `filter_llm.preprocess(article)`.
**If deleted:** the app starts and Jev still judges; you lose the optional assist (the import is guarded). **BREAKS A FEATURE.**

### `filter_log.py` — verdict/error trail
**Purpose:** appends every verdict to `data/filter_verdicts.jsonl` and failures to `filter_errors.jsonl`.
**Why needed:** the verdicts/logs pages, the report and history.
**Example:** `filter_log.log_verdict(article, verdict, source="manual")`.
**If deleted:** startup import error (filter_service imports it). **FATAL.**

### `prefilter.py` — deterministic pre-checks
**Purpose:** date staleness, contacts, sponsored/advertorial signals before/around the AI.
**Why needed:** `filter.py` imports it lazily and falls back to no pre-checks when it is missing.
**Example:** `prefilter.run(article)`.
**If deleted:** the app starts and Jev still judges; deterministic pre-checks silently become empty. **BREAKS A FEATURE.**

---

## 4. Repurpose stage — `msme/repurpose/` (2)

### `repurpose_export.py` — export to the external engine
**Purpose:** picks the latest ACCEPT per article and copies `article.md` + images into `repurpose_inbox/`.
**Why needed:** `checklist.py` calls it for accepted rows; `python -m msme.repurpose.repurpose_export --apply` is the manual run.
**Example:** `python3 -m msme.repurpose.repurpose_export --apply`.
**If deleted:** accepted articles stop reaching the engine (the rest of the app still runs). **BREAKS A FEATURE.**

### `repurpose_worker.py` — host worker
**Purpose:** watches `repurpose_inbox/` and runs the external `MSME_AI_News` engine one article at a time.
**Why needed:** only when the engine runs on this host; it is not imported by the app.
**Example:** `REPURPOSE_ENGINE_ROOT=../MSME_AI_News python3 -m msme.repurpose.repurpose_worker`.
**If deleted:** nothing in the app changes; you lose the worker command. **OPERATOR ONLY.**

---

## 5. Legacy — `msme/legacy/` (1)

### `main.py` — old `:8898` receive API
**Purpose:** the pre-combined receive API (run one/all, emails, logs, config, test connection).
**Why needed:** **not started** by `run.py`; kept for reference and `tests/test_gmail_unread.py`.
**Example:** `uvicorn msme.legacy.main:app --port 8898` (not used in production).
**If deleted:** the legacy reference disappears and `tests/test_gmail_unread.py` fails. **TEST ONLY (for the live app).**

---

## 6. Tests — `tests/` (14)

Deleting any test does not affect the running app; it removes the proof for that area and lowers the
CI count (currently **149 tests**).

| File | Proves | Delete impact |
|---|---|---|
| `test_auth.py` | scrypt, sessions, roles, CSRF, lockout, audit, config versions | auth changes become unproven |
| `test_webhook.py` | OIDC rejection, payloads, history, queue | webhook changes unproven |
| `test_workflow_lab.py` | stages, code map, write-free sandbox | Lab changes unproven |
| `test_gmail_unread.py` | `is:unread` enforcement, mark-read, legacy `main` | Gmail-query changes unproven |
| `test_prompt_eval.py` | v0/v1 prompt resolution + replay harness | prompt-pack changes unproven |
| `test_collect_select.py` | D24 collect-then-select, media dimensions | receive-selection changes unproven |
| `test_report_versions.py` | one version per subject, received dates | report changes unproven |
| `test_filter_history.py` | filter-result linkage + rubric snapshot | history changes unproven |
| `test_filter_storage.py` | filter storage, log, one-port routing | routing changes unproven |
| `test_checklist_sqlite.py` | checklist persistence | checklist changes unproven |
| `test_accept_threshold.py` | editable ACCEPT threshold | threshold changes unproven |
| `test_editor_labels.py` | plain-language editor labels | editor wording unproven |
| `test_web_probe.py` | web modes, SSRF, WebP, article fetch | web-fetch changes unproven |
| `test_jev_weakness.py` | manual Jev weakness runner (not a unittest class) | the manual runner is lost; the 149 count is unchanged |

---

## 7. Tools — `tools/` (10)

None of these are imported by the app.

| File | What it does | Example | If deleted |
|---|---|---|---|
| `build_register_indexes.py` | regenerates `decisions/INDEX.md` + `todo/INDEX.md` | `python3 tools/build_register_indexes.py` | the documented register workflow breaks (rules tell every session to run it) |
| `reauth_google.py` | mints `creds/{gmail,drive,sheets}.json` from an OAuth client | `python3 tools/reauth_google.py url` | you cannot re-authorise Google when the token expires |
| `oauth_catch.py` | same as above but with a local redirect server on :8080 | `python3 tools/oauth_catch.py` | the container-based re-auth path is lost |
| `check_deepseek_key.py` | checks the DeepSeek key and lists models | `python3 tools/check_deepseek_key.py` | lose a one-off key check |
| `export_creds.py` | decrypts n8n credentials into `creds/*.json` (contains an n8n key literal — see `T-048`) | `N8N_DB=/data/database.sqlite python3 tools/export_creds.py` | lose the n8n migration path; **also remove the key literal** |
| `prompt_eval.py` | A/B the receive prompts on archived emails | `python3 tools/prompt_eval.py --help` | `tests/test_prompt_eval.py` fails; no prompt A/B |
| `run_all_emails.py` | re-runs every cached email through receive + filter | `python3 tools/run_all_emails.py` | lose the bulk reprocess command |
| `reorganize_archive.py` | sorts `all_emails/` into date buckets (D26, already ran) | `python3 tools/reorganize_archive.py --apply` | you cannot re-sort a future archive |
| `drive_folder4.py` | publishes 20 articles to Drive `Email_Articles/4` (T-041) | `python3 tools/drive_folder4.py --select` | lose that one-off Drive publisher |
| `learn_jev_way.py` | learns the best wording per question from `docs/article-records.json` | `python3 tools/learn_jev_way.py` | lose the offline wording learner (the Lab can still edit wording) |

---

## 8. Delete guide (my assessment — you decide)

| Tier | Files | Consequence |
|---|---|---|
| **Never** | everything marked **FATAL** above (34 runtime files + 5 `__init__.py`) | the app stops starting |
| **Keep while the feature lives** | `repurpose_export.py`, `repurpose_worker.py`, `msme/legacy/main.py` | repurpose stops, or the legacy API/tests stop |
| **Keep for the partner** | `tests/` (14), `tools/reauth_google.py`, `tools/oauth_catch.py`, `tools/build_register_indexes.py`, `tools/prompt_eval.py` | you lose proof, re-auth, the register workflow or the prompt harness |
| **Likely one-off, safe to retire** | `tools/export_creds.py`, `tools/check_deepseek_key.py`, `tools/drive_folder4.py`, `tools/learn_jev_way.py`, `tools/reorganize_archive.py`, `tools/run_all_emails.py`, `tests/test_jev_weakness.py` | nothing in the app changes; you lose that manual utility (and `export_creds.py` carries a secret that should be rotated anyway) |

Tell me which ones you still need and I will confirm the exact consequence of each deletion before
anything is removed.
