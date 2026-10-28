# Data-Driven Wording Re-Learning — Run Report

**Date:** 2026-10-12
**Goal:** stop guessing ground truth; use the *published site* as authoritative
positives and the *editor’s “Not relevant”* replies as negatives, auto-generate new
wordings per question, and learn the best wording for each gate/score (weights fixed).

**Result:** promoted learned wordings for 9 of 14 scores; end-to-end reject-F1 on the
labelled set went **0.30 → 0.68 in-sample**, **0.34 → 0.53 (5-fold CV)**.
Frozen version **`b278cecfd96d0ffa`**.

---

## 1. Data collection

### Positives — published site posts (`docs/published-dataset.json`)
- Source: `https://www.malaysiasme.com.my/wp-sitemap.xml` → `post-sitemap.xml` +
  `post-sitemap2.xml` (1,553 posts total).
- Kept the **100 most-recent news-style** posts (excluded posts whose categories are
  only Opinion / Columns / Pillars / Awards).
- Date range: **2026-09-12 → 2026-10-09**.
- Per post captured: url, title, date, **categories**, bodyText.
- Also wrote `docs/published-index.json` (url/title/date/categories) — reusable for
  **duplicate detection**.
- Top categories in the sample: Technology 43, business 26, SME 24, International Trade 23,
  Industry Collaboration 22, Investment 20, Government 16.

> Why this matters: the site **publishes single-company launches** (Event Me Now, FCM Travel,
> Mercedes, OCBC…). So “single-company launch” ≠ “not SME-relevant” — it’s a positive.

### Negatives — editor “Not relevant” (`docs/negative-dataset.json`)
- Searched Gmail (`"not relevant"`): **20 threads** (the 19 known + ICAEW Budget 2027).
- Extracted the forwarded article body from each (stripped editor note/signature/disclaimer).
- Label = `reject`.

### Labelled set (`docs/labelled-dataset.json`)
- **100 positives (accept)** + **20 negatives (reject)** = 120.

---

## 2. Auto-generated wordings (`docs/jev-variants.json`)
- For each of the 18 questions, DeepSeek (`deepseek-flash`) produced **8 new wordings**
  as `<q>_g1..g8` (same noul polarity, varied phrasing) — **144 new wordings**, file now
  **240 entries**.
- Updated `category_fit` to the **site’s real categories/tags** (adds Industry
  Collaboration, Risk Management, Travel & Tourism, AI, Economic Impact, etc.).

---

## 3. Learning — per-question AUC (reject vs accept)
`docs/variant-learning.json` (AUC of `noul` separating editor-rejects from published):

| question | best wording | AUC | base AUC |
|---|---|---|---|
| no_substance | `_1` | 0.984 | 0.928 |
| not_current | `_4` | 0.952 | 0.943 |
| no_editorial_value | `_g2` | 0.935 | 0.846 |
| category_fit | `_4` | 0.897 | 0.77 |
| not_sme_relevant | base | 0.895 | 0.895 |
| no_wider_value | `_4` | 0.895 | 0.87 |
| not_sme_voice | `_1` | 0.886 | 0.866 |
| is_it_commercial_intent | `_g5` | 0.863 | 0.775 |
| defamatory | `_g7` | 0.845 | 0.831 |
| not_geographically_relevant | `_g5` | 0.827 | 0.811 |
| political | `_2` | 0.671 | 0.435 |
| not_identifiable | `_2` | 0.65 | 0.52 |
| unattributed_claims | `_g6` | 0.61 | 0.596 |
| contact | `_g7` | 0.014 | 0.009 |
| royalty / religion / race | (n≈0.6–0.8, no true positives) | — | — |

**Note:** per-question AUC alone did **not** improve the combined verdict. So the wording
was instead chosen by **optimizing the end-to-end reject-F1** (greedy coordinate ascent),
which is the metric we actually care about.

---

## 4. Validation (`docs/variant-validation.json`, `docs/variant-cv.json`)

| | precision (reject) | recall (reject) | F1 | accuracy |
|---|---|---|---|---|
| Baseline (base wordings) | 0.385 | 0.25 | **0.303** | 0.808 |
| Optimized (in-sample) | 0.625 | 0.75 | **0.682** | 0.883 |
| **5-fold CV (learned)** | **0.524** | **0.592** | **0.529** | — |
| 5-fold CV (baseline) | — | — | 0.336 | — |

Honest generalisation estimate: **F1 ≈ 0.53** (vs 0.34 baseline). The big in-sample jump
(0.68) is optimistic — 120 items and 222 candidate wordings overfit easily.

---

## 5. Promoted wordings (source of truth = `docs/jev-variants.json`)
Base swapped to the learned variant for 9 scores (others kept base):

- `no_wider_value` ← `_g6`
- `is_it_commercial_intent` ← `_g6`
- `not_geographically_relevant` ← `_g3`
- `defamatory` ← `_g8`
- `no_substance` ← `_g4`
- `unattributed_claims` ← `_g3`
- `contact` ← `_g8`
- `category_fit` ← `_g6`
- `not_sme_voice` ← `_4`

Each `<q>_jev_best_qu` synced to the new base. Gates (`royalty/religion/race`) kept base
(no labelled sensitivity positives to learn from). Weights **unchanged**.
Re-frozen → **`b278cecfd96d0ffa`**; container rebuilt; Records/Reports regenerated.

---

## 5b. New variant `<q>_jev_learn` (each gate + score)
A dedicated variant family `_jev_learn` was added to `docs/jev-variants.json` (18 entries),
holding the **learned question** for every question (scores = end-to-end optimized winner;
gates = per-question best-AUC winner). It sits alongside `base`, `_1.._4`, `_jev_best_qu`
and is selectable in the Lab; the Records/Reports tables now include a `jev_learn` column.

| question | `_jev_learn` holds |
|---|---|
| royalty | `royalty_g8` |
| religion | `religion` (base) |
| race | `race_g1` |
| not_sme_relevant | base |
| no_wider_value | `_g6` |
| is_it_commercial_intent | `_g6` |
| not_geographically_relevant | `_g3` |
| defamatory | `_g8` |
| political | base |
| no_substance | `_g4` |
| not_identifiable | base |
| unattributed_claims | `_g3` |
| not_current | base |
| no_editorial_value | base |
| contact | `_g8` |
| category_fit | `_g6` |
| not_sme_voice | `_4` |
| is_negative_or_attacking | base |

UI support: `baseOf()` in `static/lab.html` + `static/testfilter.html` now strips `_jev_learn`;
`COLS` in `static/testfilter.html`, `gen_records.py`, `gen_reports.py` include `jev_learn`.

## 6. Findings & limitations
1. **Published ≠ our old intuition.** The site routinely publishes single-company
   launches; the filter must not treat those as off-topic. The labelled set fixes this.
2. **Negatives are few (20) and noisy** — editor rejects often look like published posts
   (both are single-company news). This caps achievable separation (~F1 0.53).
3. **Sensitivity gates have no labelled positives** (no royal/religion/race rejects in the
   set) → wording left as base; their AUC numbers are noise.
4. **`contact` is inverted** on this data (published pages omit press contacts, so positives
   score “no contact” high). Treat its learned AUC/wordings with suspicion.
5. **In-sample optimization overfits**; the CV number is the one to trust.
6. `filter.py` built-ins still hold the pre-learning wording; the **Lab file is the live
   source of truth** (rollback via *Reset to built-in*).

## 7. Files produced
- `docs/published-dataset.json`, `docs/published-index.json`
- `docs/negative-dataset.json`
- `docs/labelled-dataset.json`
- `docs/variant-matrix.json` (120 × 222 noul matrix)
- `docs/variant-learning.json` (per-question AUC)
- `docs/variant-validation.json` (in-sample before/after)
- `docs/variant-cv.json` (5-fold CV)
- `docs/filter-frozen.json` (sha `b278cecfd96d0ffa`)
- `docs/jev-variants.json` (240 entries; learned base + `_jev_best_qu`)

## 8. Recommended next steps
1. **Get more negatives** (aim ≥80) — the single biggest lever.
2. Re-optimise with **proper CV** (nested), not in-sample.
3. Build a **sensitivity-positive set** to learn `royalty/religion/race` wording.
4. Wire `published-index.json` into a **duplicate-detection** signal.
5. Optionally revisit weights (currently frozen) once the negative set is larger.

## 9. Appendix — compound-question split experiment (negative result)
Applied the “writing a good Noul question” rubric: single condition, high=yes,
“any”, criteria only when the boundary is subtle. Split the 3 compound questions:

- `not_sme_relevant` (18) → `nsr_consumer` + `nsr_single_company` + `nsr_event` + `nsr_education` + `nsr_foreign_delegation`
- `defamatory` (10) → `disc_content` + `unsubst_claims`
- `political` (6) → `partisan_campaign` + `attacks_government`

Each split part was tested with 4–5 candidate wordings (no criteria / statement form
/ short criteria / short criteria+examples) over the 120-article labelled set.

| configuration | in-sample reject-F1 | 5-fold CV reject-F1 |
|---|---|---|
| pre-split (learned wordings) — **kept** | 0.68 | **0.53** |
| split, weighted average (diluted) | 0.17 | 0.00 |
| split, re-combined with `max()` | 0.30 | 0.21 |
| split, `max()` + per-part wording learn | 0.30 | 0.21 |

**Conclusion:** splitting made it worse. Jev under-fires on concise single-condition
questions — it needs the explicit example lists (the “ANY of …” criteria) to raise the
noul for off-topic/commercial items. Splitting spread the 18-point weight across five
weak nouls and diluted the signal, even after re-combining with `max()`.

**Action:** reverted `filter.py` + `docs/jev-variants.json` to the pre-split learned
config; live sha verified equal to the frozen `b278cecfd96d0ffa`. Records/Reports
regenerated. So the rubric is sound in general, but for this task/model the compound
criteria currently answer better (rule 4: “keep whichever answers better”).

