# docs/ — INDEX

_Hand-maintained. Code-read files stay flat (code reads `docs/<name>` directly — see `decisions/D4.md`). Old generated runs and experiments moved to `delet/` on 2026-10-27 for manual review._

## What the file prefixes mean

| Group | Files | What it is |
|---|---|---|
| `ARCHITECTURE.md` · `WORKFLOW.md` | 2 | historical architecture + the end-to-end receive pipeline reference (moved from root 2026-10-21; keep as written — `D5`) |
| `WORKFLOW-RECEIVE-TO-PUBLISH.md` | 1 | current receive → filter → repurpose → local-publish workflow, statuses and data map |
| `PRODUCTION-EMAIL-SETUP.md` | 1 | production Gmail switch: OAuth, settings, watch, test, rollback |
| `FILTER-LOGIC.md`, `FILTER-REVIEW.md` | 2 | historical rule descriptions kept as **test variants** — do not reconcile (`decisions/D5.md`); live truth is `/filters.json` |
| filter/Jev notes and comparisons (`.md`) | 25 | `AI-NEWS-WEEKLY-*`, `JEV*`, `GATE-DEF-COMPARISON`, `GUIDELINE-MAPPING`, `QUESTION-SPLIT`, `LEARNING-RUN`, `FILTER-WORKFLOW`, `COMPARE-*.md`, `best-*`, `jev-way-*`, `labelled-positives`, `filter-test-report-20`, `test-filter-report`, `SYSTEM-UPDATE-POSITIVE`, `ACCEPTED-10-LINKS`, `1_JEV_*`, `2_JEV_*`, `artical test filters`, `mg_prompt` |
| `INDEX.md` | 1 | this file |
| `NOT-READY-TO-FILTER-*.md` | 1 | verified list of emails still `readyToFilter=false` + reasons/actions |
| `SENDER-ASKS-*.md` | 1 | ready-to-send media/access requests for the remaining no-media rows |
| `gates-def-*.xlsx`, `original-gates.xlsx`, `gates def.gnumeric` | 10 | runnable **gate definitions** (one tab per question: instruction, TRUE/FALSE, threshold/weight) |
| `FILTER-REPORT-*.xlsx/.csv/.tsv` | 24 | **report outputs** (run timestamp in the name); `report-runs.jsonl` indexes them |
| `COMPARE-*.xlsx` | 4 | definition-vs-definition and AI-vs-editor comparisons |
| `*.json` | 39 | datasets and live state: `jev-variants.json` (Lab source of truth), `article-records.json`, `negative-dataset.json`, `email-dates.json`, `filter-frozen.json`, `archive-versions.json` (report keep map — `D26`) |
| `report-runs.jsonl` | 1 | append-only log of report runs (read by `/report/history`) |
| `PROMPT-EVAL-20261024-0700.md/.json` | 2 | latest receive prompt A/B (D27); older 0620/0630 runs are in `delet/old-docs/` |
| `DRIVE-FOLDER-4-20261024-0808.md/.json` + `DRIVE-FOLDER-4-SELECTION.json` | 3 | final Drive folder 4 manifests + selection (T-041); older 0751/v1 copies are in `delet/old-docs/` |
| `WEEKLY-REPORT-*.md` | 1 | weekly status report — done / issues / next (2026-10-24) |
| `GATE-TEST-RESULTS.xlsx` | 1 | gate-test evidence; the old PDF/VBA/bulk-run files are in `delet/old-ops/` or `docs/reference/` |
| `reference/` | folder | source guideline/deck, `FILTER-RULES.pdf`, `email issues.odt`, future MySQL schema — see `reference/INDEX.md` |

## Rules

- New report outputs land here (code writes them) — never edit `report-runs.jsonl` by hand.
- The Report Manager reads `all_emails/` (date buckets), one version per subject — `decisions/D26.md`.
- `jev-variants.json` is the **source of truth** for Jev wording (`filter.py:189`); edit via Jev Lab.
- Do not rename a file another doc references without updating the reference (`FILTER-WORKFLOW.md`,
  `JEV-WEAKNESSES.md` carry cross-links).
