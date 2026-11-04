# Jev_learn rerun — best wording per gate & score

**Date:** 2026-10-12 · Data: `docs/filter/experiments/jev-learn-rerun.json`, `docs/filter/experiments/jev-learn-rerun-matrix.json`
**Config tested:** the current (split) filter — 3 gates + 20 scores.
**What it does:** re-runs the wording learning and writes the winning wording into every
`<question>_jev_learn`.

---

## Method

- **Articles:** the labelled set (`docs/filter/experiments/labelled-dataset.json`) — **100 published positives
  (accept)** + **20 editor “Not relevant” negatives (reject)** = 120.
- **Candidates per question:** every wording variant in `docs/jev-variants.json` for that
  question — `base`, `_1.._4`, `_g1.._g8` (the pointer ids `_jev_best_qu` / `_jev_learn` are
  excluded). **103 candidate wordings** across **23 questions**.
- **Scoring:** one Jev batch per article returning each candidate’s `noul` (YES = defect).
  For each candidate we compute **AUC** = probability a random editor-reject has a higher
  `noul` than a random published-accept (higher = better separation).
- **Winner:** the highest-AUC candidate per question (ties keep `base`). The winner is written
  into `<question>_jev_learn`.

## Result — winner written to `<q>_jev_learn`

| question | jev_learn ← | AUC | base AUC | changed |
|---|---|--:|--:|:--:|
| royalty | `royalty` | 0.51 | 0.51 | |
| religion | `religion` | 0.536 | 0.536 | |
| race | `race` | 0.544 | 0.544 | |
| nsr_consumer | `nsr_consumer_3` | 0.773 | 0.69 | ✔ |
| nsr_single_company | `nsr_single_company_2` | 0.743 | 0.65 | ✔ |
| nsr_event | `nsr_event_3` | 0.667 | 0.494 | ✔ |
| nsr_education | `nsr_education` | 0.57 | 0.57 | |
| nsr_foreign_delegation | `nsr_foreign_delegation_2` | 0.695 | 0.618 | ✔ |
| no_wider_value | `no_wider_value_4` | 0.892 | 0.876 | ✔ |
| is_it_commercial_intent | `is_it_commercial_intent_3` | 0.832 | 0.809 | ✔ |
| not_geographically_relevant | `not_geographically_relevant_3` | 0.806 | 0.805 | ✔ |
| disc_content | `disc_content` | 0.611 | 0.611 | |
| unsubst_claims | `unsubst_claims_3` | 0.63 | 0.62 | ✔ |
| partisan_campaign | `partisan_campaign` | 0.63 | 0.63 | |
| attacks_government | `attacks_government` | 0.617 | 0.617 | |
| no_substance | `no_substance_1` | 0.982 | 0.892 | ✔ |
| not_identifiable | `not_identifiable_2` | 0.648 | 0.565 | ✔ |
| unattributed_claims | `unattributed_claims_2` | 0.587 | 0.577 | ✔ |
| not_current | `not_current_4` | 0.904 | 0.809 | ✔ |
| no_editorial_value | `no_editorial_value_4` | 0.878 | 0.851 | ✔ |
| contact | `contact_4` | 0.013 | 0.011 | ✔ |
| category_fit | `category_fit_4` | 0.897 | 0.751 | ✔ |
| not_sme_voice | `not_sme_voice_4` | 0.885 | 0.881 | ✔ |

**17 of 23** got a wording change; the 3 gates kept `base`.

## Notes / caveats

- **Gates (royalty / religion / race) AUC ≈ 0.5** — the labelled set has **no sensitivity
  positives** (no royal/religion/race rejects), so there’s nothing to learn from; base kept.
- **`contact` is inverted (AUC ≈ 0.01)** — a dataset artifact: published site pages omit the
  press contact, so accepts score “no contact” high. Its learned wording is meaningless;
  recommend keeping `contact` on base in practice.
- These winners are stored as the **`jev_learn` variant only** (a testing variant). The **live
  base is unchanged** — nothing here changes the running filter until promoted.
- Live via the mounted `docs/jev-variants.json` (verified through `/lab/payload`); no rebuild
  was needed.

## Files
- `docs/filter/experiments/jev-learn-rerun.json` — winners + all candidate AUCs
- `docs/filter/experiments/jev-learn-rerun-matrix.json` — raw noul matrix (120 articles × 103 candidates)
- `docs/jev-variants.json` — updated `<q>_jev_learn` entries
