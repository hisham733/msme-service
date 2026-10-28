# NOW — msme-service

*One NOW for this project, ≤ 40 lines · edit with Edit, never rewrite whole · updated 2026-10-28 (S07).*

## Direction

- Three-stage AI_News web service: **receive → filter → repurpose** (`run.py` starts one combined app on :8899).
- **Receive is built**: Gmail → normalize → decide/extract/verify → 14-col checklist (SQLite) →
  archive to `all_emails/` (live; legacy `emails/` kept for the test pages); dashboard pages on :8899.
- **Filter is built**: Jev runs inside receive when `readyToFilter=true`; 3 Critical Gates
  (Royalty/Religion/Race) + 11 weighted scores, editable from the Lab/Config pages; reports in `docs/` (old reports moved to `delet/old-reports/`).
- **Repurpose is built** on the external `MSME_AI_News` engine at **:8765**; `repurpose_export.py`
  exports latest ACCEPT articles automatically, `repurpose_worker.py` runs one at a time,
  site to `repurpose_site/` (D35).
- T2 workflow standard adopted 2026-10-21; website-runtime `.py` carry the FILE HEADER contract.
- **D6 built and live**: a single Drive file link is fetched; a view-only/refused file ends the run
  `needs_human`, never `success`, and its cover note is not archived.
- **D7**: remote HTML-body images count by dimensions (not 1 MB); **D20** fetches public
  article/speech pages.
- **D8**: vector logos drawn in a PDF `/Header` count as `hasLogoInArticle`; deterministic doc evidence
  overrides the text-only verify AI. A text-only wordmark is still not detected.
- **Batch built and live** (`picker-20261022`): D9–D16 (body/asset logos, subject + first paragraph,
  banners, release picker, Drive-image = media, OneDrive, Malay `siaran akhbar`). Live **220 checklist
  rows · 147 ready · 73 not ready** (the 153/135 snapshot is superseded; refresh NOT-READY before
  sending). MATRADE, EAP, World Bank, Jobstreet, i-City, Finnfund and Trainocate ready; Contributed
  Article needs an Atlas Copco photo. The 149-snapshot asks doc lists 11.
- **D14/T-024 deferred**: attached photos under 1 MB still have `hasPic=false`; APAC is ready via the
  OneDrive press-release logo/photo.
- **D17/D20 built**: Slides/Sheets → PDF, Drawings → PNG; public article/speech pages fetched.
- **D24 built** (image `collect-select-20261023`): collect every source first — all attachments, Drive/
  OneDrive/Box, web pages, body/asset images — then the extract AI selects the article from the candidate
  pool. Media is classified by dimensions, never a byte floor (Finnfund 250×87 logo). Cision release
  pages are fetched.
- **D25 built** (image `doc-limits-20261023`): 10 images per PDF/DOCX (25 examined), text first 30 PDF
  pages / 150k chars; no 10 MB hard ignore. Meltwater's 906-page PDF went from ~15 min to **115 s**;
  Workplace, Pink October and MRCA stay ready.
- **D26 built (2026-10-23)**: `all_emails/` sorted into `received-2026-10-15-and-above/` (40) and
  `received-2026-10-14-and-below/` (111); older versions in `_duplicates/` (47), no-article folders in
  `_no_article/` (12). The Report Manager reads `all_emails/`, shows one version per subject and has an
  **All / 15+ / 14- folder selector**; `docs/archive-versions.json` holds the keep map (151 entries).
- **Workflow Lab built (2026-10-23)**: `/workflow-lab.html` on :8899 — 8-stage receive walkthrough with
  real code, input/output, per-stage details, simulated examples, live dry-run, an **animated workflow
  diagram** (`#chart`) and the `.py` purpose map; no writes.
- **D27 live (2026-10-24)**: versioned receive prompt packs — **v1 is live** (`PROMPT_VERSION=v1`)
  for extract/verify/decide; v0 is the rollback. Two 6-email A/B runs: ready 6/6, flags 34/36 both;
  v1 tokens −9% / −12%; text sim 0.97–0.99. Live MRCA dry-run: ready, in-article logo/photo, 11.2k
  tokens. Cost $0.10; tests 44 pass.
- **Drive folder 4 (2026-10-24)**: 20 published articles from `all_emails`, only `readyToFilter=true`,
  each with `article.md` + `images/` + `originals/` + `link.md`; 1/2/3 untouched (`T-041`).
- **T-042 fixed (2026-10-24)**: queue queries enforce `is:unread`; single runs mark read; live
  Refresh returned **2 unread / 0 read** and the cache has 2 entries.
- **D28/T-043 built (2026-10-26)**: generic web article probe with `WEB_FETCH_MODE=off|known|probe`
  (default probe, editable known list); publisher logos never `hasLogo`; WebP. Event Me Now dry-run:
  `hasPic=true`, `readyToFilter=true` (1536×1024 WebP); probe/known true, off false; **81 tests pass**.
- **D29 (2026-10-26)**: SQLite is the sole checklist store; receive no longer appends to the Google
  Sheet; `/api/clear` clears SQLite only. The Sheet stays optional/manual.
- **D32 (2026-10-26)**: receive + filter are one pipeline on one port (:8899); `filter_results` is
  linked to the checklist row; `/config.html` combines both configs. Filter errors never fail receive.
- **D33 (2026-10-26)**: `ACCEPT_THRESHOLD` is editable (0–100, default 60) in the filter Config;
  the filter reads it fresh; critical gates still run first.
- **D34 (2026-10-27)**: each filter result saves the rubric snapshot (`battery`, `config_hash`,
  article text/hash); `/filter-history.html` shows versions and re-runs on the same checklist row.
- **T-044 closed (2026-10-26)**: published links stay in Google Drive; no checklist link column.
- **T-005/T-009 closed (2026-10-26, D30)**: no independent report-value check and no variant map;
  both are won't-do. The report figures remain unverified by this project.
- **T-008 closed (2026-10-26, D31)**: no receive-accuracy audit/fix; the old 52/55 figures stay
  the last measure and are unverified.
- **D35 (2026-10-27)**: Repurpose uses the external engine unchanged; dashboard :8765; auto-export +
  inbox worker; three accepted articles PASS/validated. `T-001` closed. User still owes `T-045`
  folder-4 link check.
- **D36 (2026-10-28)**: `/editor.html` end-user editor — every email, stage/rejection reason,
  local drafts, light desktop-first theme; publish button visible but disabled.
- **Webhook live (T-046, 2026-10-28)**: `/webhooks/gmail` 401 without a token; OIDC + dedupe +
  history → one queue shared with polling. Push proof: subscription `gmail-push-sub` in
  `sme-ai-510803` → endpoint 200, history 1 id, `source=webhook` processed. Watch on
  `projects/sme-ai-510803/topics/gmail-push` (renews ~6 days); SA
  `msme-webhook-push@sme-ai-510803`. 105 tests pass. Polling every 5 min is the fallback.
- **T-047 auth/audit** logged for later: local login, admin/editor roles, filter-config versions.

## What the user owes (one line each)

- **D3**: rotate (or confirm test-only) the six Google OAuth client secrets moved into `creds/`.
- **D3**: say whether to make the first git commit (repo is initialised, nothing committed).
- **T-011**: send MSIA's dayana.arif@msia.org.my the request to enable download on the Budget 2027 PDF.
- **T-022**: send the 11 asks in `docs/SENDER-ASKS-2026-10-22.md`; refresh the 149-snapshot list first.
- **T-038 resolved**: DeepSeek renewed (AUTH OK, balance $9.51); real v1 dry-runs succeeded.
- **T-028 done**: OAuth re-authed 2026-10-22; new receives work. Publish the consent screen to Production
  (or re-auth every 7 days) to avoid another expiry.
- **T-045**: check the 20 links in Drive folder 4 (`docs/DRIVE-FOLDER-4-20261024-0808.md`).
- **T-046 ops**: `docker update --restart unless-stopped wonderful_murdock`; rotate the tunnel
  token exposed in chat.

## Parked

- `docs/` reorganisation into outputs / gate-definitions / notes (`T-004`) — code paths read `docs/` flat.
- Duplicate FastAPI route sets in `main.py` and `dashboard.py` (`T-006`).
- Two archive stores, `emails/` (legacy, not read by the report) and `all_emails/` (live, date-sorted),
  `test-articles/` moved to `delet/unused/` for manual review (`T-007`).

## Map

- `README.md` (read first) · `decisions/INDEX.md` · `todo/INDEX.md` · replies in `session-analysis/`.
