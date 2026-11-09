# UPSTREAM — where the vendored repurpose engine came from

**Source:** `https://github.com/EmpiFlow/MSME_AI_News` (private)
**Commit:** `d7159ff7196510d97e4ca37c887a917ec94865bf` — `docs: filter kit and final handoff answer (reply 3)`, 2026-10-26 13:13 +0800
**Vendored:** 2026-11-06 (T-050, P0)

## What was copied (the needed set)

| Source | Destination |
|---|---|
| `pipeline/*.py` (except `dashboard.py`, `start_dashboard.cmd`) | `msme/repurpose/engine/` |
| `.claude/skills/msme-repurpose/`, `msme-image-select/` | `msme/repurpose/engine/skills/` |
| `DLW/assets/fonts/` | `msme/repurpose/engine/dlw_shell/fonts/` |
| `pipeline/GUIDE.md`, `IMAGE_GUIDE.md`, `VISION_MODEL.md`, `INDEX.md` | `docs/repurpose/` |
| `partner_handoff/INTEGRATION_CONTRACT.md`, `README.md`, `KNOWN_ISSUES.md`, `FILTER_KIT.md` | `docs/repurpose/` |
| `partner_handoff/demo_releases/`, `demo_releases_bad/` | `tests/repurpose/fixtures/` |
| `analysis/repurpose/cold-run/` | `tests/repurpose/fixtures/cold-run/` |
| `decisions/D-002`, `D-003`, `D-007`, `D-008`, `D-009`, `D-016` | `docs/repurpose/decisions/` |
| `meeting_notes/AGENDA.md` | `docs/meetings/2026-10-30/AGENDA.md` |
| `config.json` (reference only; converted in P1) | `docs/repurpose/upstream-config.json` |
| `pipeline/tests/` (staging; adapted in P1) | `docs/repurpose/upstream-tests/` |

## What was deliberately not copied

`Files_from_MSME/` (client material), `analysis/` evidence except the cold-run, `corpus/`,
`Jev/`, `tools/`, `roadmap/`, `.github/`, `.githooks/`, MG's `README/NOW/AGENTS/COLLABORATION`,
generated `DLW/articles|data|index`.

## Updating the vendored copy

This is a fork, not a submodule. To take an upstream change:

1. `git -C ../MSME_AI_News log --oneline d7159ff..HEAD` (or fetch the GitHub repo).
2. Diff the changed `pipeline/`, skills, docs or fonts against this copy.
3. Apply the change, run the cut-the-cord test (T-050 §P4), then update this file with the new
   commit and date.

## Local patch not in the upstream commit

`pipeline/build_site.py` was modified in the upstream working tree at copy time (last-publish
ordering: `"published": run.get("updated")` and sort by published/date). The vendored copy includes
it; the diff is saved as `UPSTREAM-PATCH-2026-11-06.diff`.

## Extra decisions copied for rationale

In addition to the six in the copy list above, these upstream decisions are kept so the engine
comments still resolve after the upstream folder is deleted: **D-004, D-006, D-010, D-012, D-013,
D-015, D-017, D-019, D-022, D-023**.

## Meeting sources copied with AGENDA.md

- `2026_sept_21_meeting_report.md` → `docs/meetings/2026-09-21/meeting-report.md`
- `2026-10-30_MSME_guideline-review.md` → `docs/meetings/2026-10-30/guideline-review.md`
