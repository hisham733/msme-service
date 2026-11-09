# 7 — workflow docs updated for one engine (D40)

**Deliverable:** every current workflow/meeting/rule doc now describes the in-process engine; the
upstream engine docs are marked historical; the referenced upstream decisions are preserved.
No app code changed.

## 1. Current docs updated

| File | Change |
|---|---|
| `docs/workflow/WORKFLOW-RECEIVE-TO-PUBLISH.md` | §5 “Open DLW / :8765” → **`/repurpose.html`**; §6 adds `repurpose_exports` / `repurpose_runs` / `repurpose_events` |
| `docs/meetings/2026-11-09/MEETING-DECISIONS-2026-11.md` | external-engine row → in-process `D40`; `M-4` and `AG-01…AG-08` rows → vendored engine/skills |
| `docs/new-rules/N-3`, `N-4`, `N-5` | “external engine (`MSME_AI_News`)” → vendored engine; `D-004`/`D-006` paths → `docs/repurpose/decisions/` |
| `todo/🟢 T-049.md` | engine track → vendored engine `D40`; `related` += `D40` |
| `docs/operations/PROCESS-TOKEN-COST.md` | “external engine” → “vendored engine (in-process since D40)” |
| `docs/meetings/2026-11-09/MEETING-BRIEF-2026-11.md` | N-5/N-7/AG rows → “vendored engine” |
| `docs/INDEX.md` | `repurpose/` row now says “vendored upstream engine docs; runs in-process (`D40`)” |
| `decisions/D35.md` | top note: **Superseded by `D40` (2026-11-06)** |
| `docs/repurpose/UPSTREAM.md` | adds the 10 extra decisions, the local `build_site.py` patch and the two meeting sources |

## 2. Upstream docs marked, not rewritten

A top note on `GUIDE`, `INTEGRATION_CONTRACT`, `HANDOFF-README`, `PIPELINE-INDEX`, `IMAGE_GUIDE`,
`VISION_MODEL`: this is the upstream document; in this repo the engine is vendored and runs
in-process; `python -m pipeline.*`, `config.local.json` and `:8765` no longer apply; use
`python -m msme.repurpose.engine.*` and `/repurpose.html`.

## 3. Preserved before the folder is deleted

- **16 upstream decisions** in `docs/repurpose/decisions/` (the six original + D-004, D-006, D-010,
  D-012, D-013, D-015, D-017, D-019, D-022, D-023).
- The **uncommitted upstream `build_site.py` fix** saved as
  `docs/repurpose/UPSTREAM-PATCH-2026-11-06.diff` (the vendored copy already includes it).
- The two meeting sources linked from `AGENDA.md`: `docs/meetings/2026-09-21/meeting-report.md`,
  `docs/meetings/2026-10-30/guideline-review.md`.

## 4. Verification

- **Link check: 0 broken links** across `docs/`, `decisions/`, `todo/`, `README`, `NOW`, `INDEX`.
- `python3 -m compileall -q msme run.py tools tests` — clean.
- **191 tests pass** (8 skipped).
- Register indexes regenerated (`decisions=40`, `todo=50`).

## 5. Still owed

- MG’s written OK before deleting `../MSME_AI_News`.
- One real ACCEPT end-to-end with the live DeepSeek key.
- Rebuild/redeploy the live app image so it no longer runs the old external path.

⭐ **Decision — §1:** ✅ nothing to decide; the docs now match the one-engine build.
