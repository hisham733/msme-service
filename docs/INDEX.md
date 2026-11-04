# docs/ — INDEX

_Docs are grouped by topic. Files the **code reads or writes by name stay flat at `docs/` root** —
moving them would break the Report Manager, the Lab or verdict logging (`D4`, `D39`)._

## Folders

| Folder | What it holds |
|---|---|
| `workflow/` | how the service works: architecture, end-to-end workflow, the seven email examples, the stage-by-stage comparison, source routing, code map |
| `filter/` | Jev rules, gate definitions and comparisons; `filter/experiments/` keeps the superseded variant runs |
| `meetings/` | `2026-09-21/`, `2026-10-29/`, `2026-10-30/` (call + sources), `2026-11-09/` (next-call brief and decision list) |
| `operations/` | runbooks and reports: production email setup, token cost, not-ready list, sender asks, weekly reports, repurpose integration |
| `receive/` | receive-stage feedback and measurements |
| `reference/` | client source material (guideline, deck, `FILTER-RULES.pdf`, email issues) + `future-mysql/` |

### `workflow/`

| File | What it is |
|---|---|
| `ARCHITECTURE.md` · `WORKFLOW.md` | historical architecture + end-to-end receive reference — keep as written (`D5`) |
| `WORKFLOW-RECEIVE-TO-PUBLISH.md` | current receive → filter → repurpose → local-publish workflow |
| `RECEIVE-WORKFLOW-7-EMAIL-EXAMPLES.md` | seven real emails, full stage-by-stage walkthroughs |
| `RECEIVE-STAGES-EXPLAINED.md` | the eleven receive stages, compared across the seven emails |
| `MEDIA-SOURCE-DECISION.md` | who picks the source/fetcher: link guard, URL routing, decide-suggestion detail |
| `CODE-MAP.md` | the `msme/` package layout and import rules (`D38`) |

### `filter/`

| File | What it is |
|---|---|
| `FILTER-LOGIC.md` · `FILTER-REVIEW.md` | historical rule descriptions kept as **test variants** — do not reconcile (`D5`) |
| `FILTER-WORKFLOW.md` | the filter pipeline and battery reference |
| `GATE-DEF-COMPARISON.md` · `GUIDELINE-MAPPING.md` | gate-definition comparisons and the guideline mapping |
| `JEV.md` · `JEV-WEAKNESSES.md` · `1_JEV_*` · `2_JEV_*` | Jev input/output reference and weakness notes |
| `QUESTION-SPLIT.md` · `LEARNING-RUN.md` · `SYSTEM-UPDATE-POSITIVE.md` · `best-*` · `jev-way-*` | wording experiments and learnings |
| `COMPARE-*.md` · `filter-test-report-20.md` · `test-filter-report.md` · `GATE-TEST-RESULTS.xlsx` | comparison/test evidence |
| `original-gates.xlsx` | original gate variant — keep (`D5`) |
| `experiments/` | superseded JSON/MD variant runs (datasets, matrices, verdicts) |

### `meetings/`

| Folder | What it holds |
|---|---|
| `2026-09-21/` | kickoff transcript |
| `2026-10-29/` | the MSME meeting runbook |
| `2026-10-30/` | the guideline-review transcript, `NEXT_MEETING.md`, and the source zip |
| `2026-11-09/` | `MEETING-BRIEF-2026-11.md` (30-Oct outcomes + next call) and `MEETING-DECISIONS-2026-11.md` (open decisions) |

### `operations/`

`PRODUCTION-EMAIL-SETUP.md` · `PROCESS-TOKEN-COST.md` · `NOT-READY-TO-FILTER-2026-10-22.md` ·
`SENDER-ASKS-2026-10-22.md` · `WEEKLY-REPORT-2026-10-24.md` · `AI-NEWS-WEEKLY-5-13-OCT.md` ·
`REPURPOSE-INTEGRATION-2026-10-27.md` · `ACCEPTED-10-LINKS.md/.json` · `HANDOVER-2026-11.md`.

### `receive/`

`receive_feedback.md` — the 20-folder receive/image feedback batch.

## Flat files at `docs/` root — code reads or writes these by name

**Do not move or rename them** (`D4`, `D39`).

| File | Read/written by |
|---|---|
| `jev-variants.json` | `msme/filtering/filter.py` (Lab source of truth), `filter_service.py` (Lab save/learn) |
| `archive-versions.json` | `filter_service.py` (report keep map) |
| `article-records.json` | `filter_service.py` (`/testfilter/learn`) |
| `artical.json` | `filter_service.py` (Lab default payload) |
| `negative-dataset.json` · `email-dates.json` · `sme-reject-6-10.json` | `archive_layout.build_date_map` (report dates/negatives) |
| `filter-variants-report-10.json` · `filter-variant-separation.json` | `static/testfilter.html` via `/lab/payload` |
| `published-index.json` · `published-dataset.json` | `tools/drive_folder4.py` |
| `gates-def-*.xlsx` (6) | `filter_service.py` `/report/files` + report runs |
| `report-runs.jsonl` | `filter_service.py` report history |
| `FILTER-REPORT-*.xlsx/.csv/.tsv` | written by `filter_service.py`; downloaded by the Report Manager |
| `PROMPT-EVAL-*.md/.json` | written by `tools/prompt_eval.py` |
| `DRIVE-FOLDER-4-*.md/.json` | written by `tools/drive_folder4.py` |
| `jev-way-learning.md` | written by `tools/learn_jev_way.py` |
| `INDEX.md` | this file |

## Rules

- New report outputs land at `docs/` root (the code writes them there) — never move them into a folder.
- `jev-variants.json` is the **source of truth** for Jev wording; edit it through the Jev Lab.
- The Report Manager reads `all_emails/` (date buckets), one version per subject — `decisions/D26.md`.
- Keep `FILTER-LOGIC.md`, `FILTER-REVIEW.md`, `gates-def-*` and `original-gates.xlsx` as variants —
  never reconcile them to the live battery (`decisions/D5.md`).
- This grouping is recorded in `decisions/D39.md`; `todo/T-004.md` is closed.
