# Meaning → generate → validate learning (jev_learn)

**Date:** 2026-10-12 · Files: `docs/filter/experiments/jev-learn-generated.json`, `docs/filter/experiments/jev-learn-adopt.json`

Previous learning only **picked** between the base and the paraphrase, so `jev_learn` was always a
copy of one of them. Now the learning **understands the meaning of each gate/score and authors a
new question**, then validates it.

## Process (per question)
1. **Meaning** — take the question’s instruction + its boundary/criteria (“what GOOD means”).
2. **Evidence** — show the model example articles that should score **high** (published accepts) and
   **low** (editor “Not relevant” rejects).
3. **Generate** — the LLM writes **one** yes/no question, phrased **positively** (high YES = good),
   one thing only, no meta-text (only the question, ending with `?`).
4. **Validate** — run the generated question over the 120-article labelled set and compute AUC
   (accepts should score higher than rejects).
5. **Adopt** — write it to `<q>_jev_learn` only if `AUC(gen) ≥ AUC(base)`; otherwise keep the base.

## Result
- **18 / 23** questions produced a valid new question (5 failed JSON/format → fall back to base:
  `nsr_consumer`, `disc_content`, `unsubst_claims`, `contact`, `category_fit`).
- **8 adopted** into `jev_learn`; the rest kept base (generated didn’t beat base).

| question | gen AUC | base AUC | adopted |
|---|--:|--:|:--:|
| not_sme_voice | 0.956 | 0.867 | ✔ |
| nsr_foreign_delegation | 0.761 | 0.730 | ✔ |
| unattributed_claims | 0.638 | 0.551 | ✔ |
| nsr_education | 0.630 | 0.608 | ✔ |
| religion | 0.628 | 0.369 | ✔ |
| royalty | 0.545 | 0.346 | ✔ |
| not_geographically_relevant | 0.685 | 0.679 | ✔ |
| not_identifiable | 0.442 | 0.322 | ✔ |

Kept base (gen ≤ base): `race`, `nsr_single_company`, `nsr_event`, `no_wider_value`,
`is_it_commercial_intent`, `partisan_campaign`, `attacks_government`, `no_substance`,
`not_current`, `no_editorial_value`.

Example generated wordings:
- `royalty` → “Does the article avoid any disparagement of or challenge to Malaysia's royal institution…?”
- `religion` → “Does the article avoid disparaging, mocking, or condemning any religion or its adherents?”
- `not_sme_voice` → “Is this written as a substantive news item that speaks directly to SME owners' business interests…?”

## Variants (unchanged layout)
`<q>` base · `<q>_1` paraphrase · `<q>_jev_learn` **generated** (or base where it didn’t win).
Excel exports refreshed: `docs/gates-def-base.xlsx`, `gates-def-paraphrase.xlsx`,
`gates-def-jev_learn.xlsx`.

## Notes
- Gates still have no sensitivity positives, so their AUC gain is modest/noisy — but the generated
  “avoid …” phrasing did lift `royalty` (0.35→0.55) and `religion` (0.37→0.63).
- `jev_learn` remains a **testing variant**; the live filter uses `base`.
