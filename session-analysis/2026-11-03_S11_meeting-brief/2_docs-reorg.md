# 2 — docs/ grouped by topic (D39)

**Deliverable:** `docs/` is now six topic folders plus the code-read files at the root.
Recorded in `decisions/D39.md`; `todo/✅ T-004.md` is closed.

## 1. New layout

```
docs/
  INDEX.md                     # rewritten: folders + the flat code-read list
  workflow/                    # ARCHITECTURE, WORKFLOW, WORKFLOW-RECEIVE-TO-PUBLISH,
                               # RECEIVE-WORKFLOW-7-EMAIL-EXAMPLES, RECEIVE-STAGES-EXPLAINED,
                               # MEDIA-SOURCE-DECISION, CODE-MAP
  filter/                      # FILTER-LOGIC, FILTER-REVIEW, FILTER-WORKFLOW, GATE-DEF-COMPARISON,
                               # GUIDELINE-MAPPING, JEV*, 1_JEV*, 2_JEV*, COMPARE-*, GATE-TEST-RESULTS,
                               # original-gates, test reports, experiments/
  filter/experiments/          # superseded variant runs, datasets, matrices, verdicts
  meetings/2026-09-21/         # kickoff transcript
  meetings/2026-10-29/         # meeting runbook
  meetings/2026-10-30/         # 30-Oct transcript, NEXT_MEETING.md, source.zip
  meetings/2026-11-09/         # MEETING-BRIEF-2026-11.md, MEETING-DECISIONS-2026-11.md
  operations/                  # production setup, token cost, not-ready, sender asks, weekly reports,
                               # repurpose integration, accepted links
  receive/                     # receive_feedback.md
  reference/                   # client source material + future-mysql
```

**Flat at `docs/` root (code reads/writes them by name — `D4`, `D39`):** `jev-variants.json`,
`archive-versions.json`, `article-records.json`, `artical.json`, `negative-dataset.json`,
`email-dates.json`, `sme-reject-6-10.json`, `filter-variants-report-10.json`,
`filter-variant-separation.json`, `published-index.json`, `published-dataset.json`,
`gates-def-*.xlsx`, `report-runs.jsonl`, `FILTER-REPORT-*`, `PROMPT-EVAL-*`, `DRIVE-FOLDER-4-*`,
`jev-way-learning.md`.

⭐ **Decision — §1:** ✅ nothing to decide; the layout is recorded in `D39`.

## 2. What was updated

- `docs/INDEX.md` rewritten with the folder map and the flat-file list.
- Every current doc/register link updated to the new paths (33 files touched).
- `README.md` docs row, `NOW.md` parked list, `decisions/D5.md` references.
- `D39` added, `T-004` closed, both register indexes regenerated.

## 3. Verification

- `python3 -m compileall -q msme run.py tools tests` — clean.
- **149 tests pass.**
- App started from the new tree on :8897: `/report/files` returned the 6 `gates-def*.xlsx`,
  `/lab/payload?file=jev-variants.json` `ok:true`, `/filters.json` 3 gates + 11 scores,
  `/api/workflow/files` 200.
- Link check over docs/registers: only two broken references, both inside the 30-Oct transcript
  pointing at partner files (`AGENDA.md`, the 30-Oct brief) that are not in this repo.

## 4. What I recommend next

Commit and push the reorg with the rest of the working tree (the profile denies `git commit`/`git push`
here). Thinking effort: **low**.
