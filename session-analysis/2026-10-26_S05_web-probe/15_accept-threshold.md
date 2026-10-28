# Accept threshold is editable

**Session:** 2026-10-26 · S05 · reply 15
**Status:** done.

## What changed

- `ACCEPT_THRESHOLD` is a saved setting (`data/settings.json`), default **60**, range **0–100**.
- `filter.accept_threshold()` reads it fresh for the next judgement; env/default 60 is fallback.
- Filter Config → Settings now has a number input + **Save** beside Accept threshold.
- Used live by `decide()`, the verdict’s `threshold`, `/config.json`, `/workflow.json` and the
  report runner.

## Behaviour

- Critical gates run first; if one fires, the threshold is irrelevant.
- No gate: weighted ≥ threshold → ACCEPT; below → REJECT.
- The existing 45–65 borderline band can still route to **EDITOR REVIEW**.

## Verified

- Live API: 60 → 65 → 60; `/workflow.json` followed.
- Full suite: **73 pass**; container rebuilt.

✅ nothing to decide
