# 3 — T-050 one repo, one process, one DB (planned, not built)

**Deliverable:** `todo/🟢 T-050.md` — the full migration plan, registered and indexed.
No code changed this turn.

## 1. Locked in the todo

1. **One repo**, **needed set only** — engine runtime + skills + tests + docs + the referenced
   decisions + AGENDA. MG’s client material, evidence, corpus, Jev, tools and registers are **not**
   merged.
2. **One process** — FastAPI + a daemon engine thread on :8899; no subprocess, no :8765.
3. **One DB** — `data/msme.sqlite3`; `run.json` stays as the folder contract and is mirrored.
4. **UI** — drop the engine dashboard; add `/repurpose.html` + `/api/repurpose/status`.
5. **Deps** — Pillow + PyMuPDF.

## 2. What the todo contains

- the exact copy list (what to take from `MSME_AI_News` and where it lands);
- the target layout (`msme/repurpose/engine/`, `tests/repurpose/`, `docs/repurpose/`);
- the three DB tables and the mirror rule;
- the path/config changes (`ENGINE_ROOT`, caches, harvest, fonts);
- phases P0–P4 with the proving run for each;
- the **cut-the-cord test** that must pass before `MSME_AI_News` is deleted;
- risks (upstream drift, deps size, fonts, ownership, long drafts).

⭐ **Decision — §1:** ✅ nothing to decide; the plan is recorded.

## 3. Still owed before P0

- Write `D40` (supersede `D35`).
- Record the upstream commit in `docs/repurpose/UPSTREAM.md`.
- Get MG’s **written OK** that his engine code moves here and his local folder is deleted.
- Confirm the engine tests’ client fixtures: the cold-run drafts are copied; the two client release
  folders stay absent, so those 4 tests will skip.

## 4. What I recommend next

Start at **P0** when you are ready: copy the needed set, write `D40`, and run the cut-the-cord test.
Thinking effort: **medium**; about 2 weeks for P0–P4.
