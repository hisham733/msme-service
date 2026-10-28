# Filter History page + rubric snapshots

**Session:** 2026-10-27 · S06 · reply 1
**Status:** done.

## What was added

- Every new filter verdict now saves the **effective rubric**:
  - 3 gates: label, threshold, instruction, criteria
  - 11 scores: weight, instruction, criteria
  - accept threshold, LLM assist, Jev model
  - `config_hash`, `article_hash`, article text/length
- New page: **`/filter-history.html`**
  - articles with filter results on the left
  - every version on the right; newest first; older versions get a black **old** badge
  - click a version → exact gate/score definitions used
  - config diff against the newest version
  - **Re-run with current config** → new version on the **same checklist row**
- Links: Filter modal → **Filter history**; Config → Filter tab → **filter history**.

## Live proof

- Row **391** auto-filtered with a saved snapshot (6,416 chars, hash `8ebaed686025`).
- Re-run created filter result **3** on the **same checklist row 391**.
- History returns 3 versions: `3, 2` on row 391; `1` is legacy row 390 with no snapshot.
- Full suite: **78 pass**; page returns 200.

✅ nothing to decide
