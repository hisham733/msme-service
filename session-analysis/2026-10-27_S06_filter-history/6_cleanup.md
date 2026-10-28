# Cleanup — moved to `delet/`, organized reference docs

**Session:** 2026-10-27 · S06 · reply 6
**Status:** moved, not deleted. Review `delet/` before removing it.

## 1. New structure

- `delet/` — 878 MB of manual-review candidates, gitignored:
  - `caches/` — old `__pycache__`
  - `locks/` — office lock files
  - `duplicates/` — exact duplicate handoff file
  - `unused/` — `test-articles/`
  - `old-docs/` — old handoff, prompt-eval 0620/0630, old Drive 0751/v1
  - `old-reports/` — `Resolt/`
  - `old-experiments/` — `aggregation-tests/`
  - `old-ops/` — `run_all*`, `ReportManager.bas`
  - `legacy-emails/` — `emails/published articles/` (877 MB)
- `docs/reference/` — source guideline, meeting deck, `FILTER-RULES.pdf`,
  `email issues.odt`, `mg_prompt.md`, future MySQL schema.

## 2. Kept on purpose

- `emails/test filter emails/` — required by the filter test pages.
- `all_emails/` — live archive (2.4 GB); duplicate/no-article buckets are rollback copies.
- `data/`, `creds/`, `static/`, `prompts/`, `decisions/`, `todo/`, `session-analysis/`.
- Code-read docs stay flat: `jev-variants.json`, `article-records.json`,
  `archive-versions.json`, `artical.json`, `negative-dataset.json`, `gates-def-*.xlsx`,
  `published-index.json`, `report-runs.jsonl`.

## 3. Numbers

| Path | Size |
|---|---:|
| `emails/` (test filter + remaining legacy) | 694 MB |
| `delet/` (review only) | 878 MB |
| `all_emails/` (live) | 2.4 GB |
| `docs/reference/` | 2.9 MB |
| `repurpose_inbox/` | 23 MB |
| `repurpose_site/` | 20 MB |

Deleting `delet/` frees the 878 MB; no live data is in it.

## 4. Verified

- App health OK; checklist and engine dashboard return 200.
- Repurpose worker still running.
- Full suite: **81 pass**.
- Path docs updated (`README`, `docs/INDEX`, `docs/ARCHITECTURE`, `docs/WORKFLOW`,
  `docs/GUIDELINE-MAPPING`, `emails/INDEX`, `config.py`, `db.py`).

## 5. Still candidates, not moved

- `emails/` remaining 694 MB: `test filter emails/` (279 MB) is kept; the rest is old legacy
  subject material. Move/delete only after checking the filter test pages.
- `all_emails/_duplicates/` (328 MB) and `_no_article/` (15 MB) are rollback copies; do not
  delete without a backup.
- Filter-variant docs in `docs/` are intentionally kept (`D5`).

## What I recommend next

Review `delet/`, then make a backup/initial commit before deleting anything. After that,
`delet/` can be removed in one go; the remaining `emails/` decision can wait.

✅ nothing to decide now
