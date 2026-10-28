# Receive Workflow Lab — interactive code walkthrough + `.py` map

**Session:** 2026-10-23_S03 · **Turn:** 5 · **IDs:** T-039
**Page:** `http://localhost:8899/workflow-lab.html` · **Image:** rebuilt 2026-10-23

---

## 1. What was built

- **New page** `static/workflow-lab.html` on :8899, linked from Checklist, Live flow and the other
  receive pages.
- **New backend** `workflow_lab.py` (APIRouter) behind the page.
- **8 stages** with real code, plain-English explanations, inputs, outputs and “what can go wrong”:
  Receive · Read & clean · Choose source · Fetch content · Extract article · Check media ·
  Decide readiness · Save.
- **Runnable examples** (simulated AI — instant, free, deterministic):
  `simple_release` (text-only, not ready) · `ready_release` (logo → ready) ·
  `no_article` (no release → not ready).
- **Replay latest real run** — the latest stored pipeline trace, read-only.
- **Per-stage runs** — edit the JSON input and run Normalize / Decide / Extract / Verify / Save.
- **PDF/DOCX upload** — the real media scan: text, image dimensions, logo vs photo.
- **Live email dry-run** (Phase 2) — real Gmail + real AI behind a warning modal; `dry_run=True`,
  so no archive, Sheet, reply or DB write.
- **Project code map** — every `.py` with role, purpose, importers and a verdict:
  `NEEDED — runtime` · `NEEDED — feature` · `NEEDED — support` · `TOOLING` ·
  `NOT RUNTIME — analysis / one-off / test`.
- The pipeline gained **opt-in** `dry_run`, `trace` and `process_model`; defaults keep the live
  receive path unchanged. `decide` / `extract` / `verify` accept an optional AI client so the lab
  never patches a global provider.

⭐ **Decision — §1:** ✅ nothing to decide — built as asked.

---

## 2. The `.py` verdicts a normal user can now read

**42 files** are shown, grouped:

| Verdict | Count | Examples |
|---|---:|---|
| **NEEDED — runtime** | 25 | `pipeline.py`, `normalize.py`, `decide.py`, `extract.py`, `verify.py`, `checklist.py`, `archive.py`, `gmail.py`, `db.py`, `filter.py` |
| **NEEDED — feature** (may be off) | 4 | `reply.py` (off in Docker), `scheduler.py` (auto off), `filter_llm.py` (assist off), `workflow_lab.py` |
| **NEEDED — support** | 1 | `connection_test.py` (Config page test) |
| **TOOLING — operator** | 1 | `run_all_emails.py` (bulk pass) |
| **TOOLING** | 1 | `tools/build_register_indexes.py` |
| **NOT RUNTIME — one-off** | 5 | `check_deepseek_key.py`, `export_creds.py`, `reauth_google.py`, `oauth_catch.py`, `tools/reorganize_archive.py` |
| **NOT RUNTIME — analysis** | 2 | `learn_jev_way.py`, `test_jev_weakness.py` |
| **NOT RUNTIME — test** | 3 | `tools/test_collect_select.py`, `test_report_versions.py`, `test_workflow_lab.py` |

The page shows the reason, the file role and who imports it, so “which is needed” is not a guess.
`.dockerignore` now includes `tools/` so the container can list the test/ops scripts too.

⭐ **Decision — §2:** ✅ nothing to decide.

---

## 3. Measured

| Check | Result |
|---|---|
| Page | `GET /workflow-lab.html` → **200**, title + code map present |
| Stages | `/api/workflow/stages` → **8**, all with code, inputs, outputs |
| Files | `/api/workflow/files` → **42** (25 core · 4 feature · 1 support · 1 ops · 1 tooling · 5 one-off · 2 analysis · 3 test) |
| Examples | simple → `readyToFilter=false` · ready → **true** (`hasLogo=true`) · no-article → `hasArticle=false` |
| Upload | 1,174 B DOCX → text + **2 images** (logo 80×77, photo 520×300) |
| Stage runs | Normalize / Verify returned their real output dicts |
| **No writes** | live DB unchanged after the runs: **208 checklist · 322 runs · 218 pipeline_results** |
| Tests | `tools.test_workflow_lab` **11 pass**; full tools suite **38 pass** |

⭐ **Decision — §3:** ✅ nothing to decide.

---

## 4. Safety and compatibility

- The lab calls `pipeline.process_model(..., dry_run=True)`; the archive, Sheet, reply and DB log
  are skipped. `archive_email` and `send_reply_for_row` are replaced by a preview / skipped marker.
- One lab run at a time; the code viewer only reads whitelisted functions.
- The live receive path is unchanged: `process_email` defaults to `dry_run=False, trace=None`.
- `flow.html` stays the live monitor; the new page is the explainer.

⭐ **Decision — §4:** ✅ nothing to decide.

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | `/workflow-lab.html` on :8899 | **built + live** |
| 2 | 8-stage code walkthrough | **done** |
| 3 | Simulated examples + real replay | **done** |
| 4 | Per-stage runs + PDF/DOCX upload | **done** |
| 5 | Live email dry-run | **built, behind warning** |
| 6 | `.py` purpose/needed map (42 files) | **done** |
| 7 | No writes / tests | **verified · 38 pass** |

## What I recommend next

Open **`http://localhost:8899/workflow-lab.html`**, run **Release with a logo (ready)** and walk the
8 stages — that is the clearest end-to-end picture. Then we can go back to the filter work. If you
want the live dry-run promoted to the main button (instead of the modal), say so; it costs AI tokens.
