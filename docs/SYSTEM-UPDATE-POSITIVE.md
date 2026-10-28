# System update — positive polarity + 3-variant layout

**Date:** 2026-10-12 · Frozen: **`0060ff3b1265b698`** · Polarity: **positive (high YES = good)**

## 1. What changed

### 1.1 Polarity flipped to POSITIVE (scores **and** gates)
Every question now asks the **GOOD** condition, so **a high YES = good** (the direct phrasing the
Jev doc recommends — no “is it free of …” inversion of the target). Example:

| before (negative / defect) | after (positive / good) |
|---|---|
| `nsr_consumer`: “Is this **NOT** about a business (consumer/lifestyle)?” | “Is this about a business or the business ecosystem…?” |
| `no_substance`: “…thin announcement with almost nothing…” | “Is there substantial material here to build a story from?” |
| `royalty` gate: “Does this **disparage** the royal institution?” | “Is the article **free of** disparagement of the royal institution?” |

**Gates keep the “free of \<defect\>” form** (not “does it treat X respectfully?”) so a **neutral**
article scores **high** (good) instead of looking defective — e.g. an article that never
mentions religion now scores `religion good ≈ 0.98`, not `0.24`.

### 1.2 Engine changes (`filter.py`)
- **Scores:** `weighted = Σ noul × weight` (good = the YES value). ACCEPT when `weighted ≥ 60`.
- **Gates:** fire REJECT when the good is **absent**: `(1 − noul) ≥ threshold`
  (i.e. good ≤ 15% for the 0.85 threshold).
- `judge()` returns gate values as the **defect probability** (fires ≥ thr) and score values as
  **good% = noul**. `assist()` / `_route_ambiguity()` use `defect = 1 − noul` for the ambiguity band.
- UI (Records/Reports) updated: all columns show **GOOD% (YES)**; a gate that fires shows a **low**
  good%. Config page label updated.

### 1.3 Variants reduced to THREE per question
Everything else (`_2,_3,_4,_g1.._g8,_jev_best_qu`) removed. Now:
1. **`<q>`** — base (the live wording)
2. **`<q>_1`** — paraphrase (alternate positive wording)
3. **`<q>_jev_learn`** — the learned wording (winner from the site articles)

### 1.4 Criteria trimmed
TRUE/FALSE criteria removed (empty) where the instruction alone is clear; kept (short) only where the
boundary is subtle — `nsr_single_company`, `is_it_commercial_intent`, `disc_content`,
`unsubst_claims`.

## 2. Learning (jev_learn)
Re-ran on the labelled set — **100 published positives + 20 editor “Not relevant” negatives** —
with the corrected orientation (accepts should score **high**). Candidates per question = base +
paraphrase; the higher-AUC wording was written to `<q>_jev_learn` (**15 of 23 changed**).
Artifacts: `docs/jev-learn-rerun2.json`, `docs/jev-learn-rerun2-matrix.json`.

> Caveats: gates (`royalty/religion/race`) still have no sensitivity positives → near-random AUC;
> `contact` remains inverted (published pages omit press contacts).

## 3. Verification (live `:8899/filter`)
| article | outcome | weighted | gates |
|---|---|--:|---|
| Pos Malaysia — SME Jumpstart Workshop | ACCEPT | 76% | none |
| Karaoke Manekineko — 20 Outlets | EDITOR REVIEW | 59% | none (borderline) |

Gates on both: `royalty 0.01`, `religion 0.02`, `race 0.02` (defect ≈ 0 → good).

## 4. Notes
- Lab file rebuilt (`docs/jev-variants.json`): 23 questions × 3 variants + context = 70 entries.
- Live = base. `jev_learn` is a **testing variant** (not promoted) — promote if you want it live.
- Records/Reports data was cleared for your manual run.
- `filter_settings.json` is `{}` (Lab file is the source of truth).
