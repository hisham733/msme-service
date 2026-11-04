# Guideline filter ↔ our gate/score mapping

Source: `docs/reference/MALAYSIA SME_AI Editorial Guidelines_Sept 2026.docx` — Stage One AI Filtering table (17 filters).
Battery: `docs/filter/experiments/filter-frozen.json` (3 gates + 20 scores; positive polarity, high YES = good).

## Guideline filter → our question(s)

| # | Guideline filter | Our gate/score(s) | Notes |
|---|---|---|---|
| 1 | Submission Completeness | *(receive-side)* | HOLD if press release/images missing — handled in the receive pipeline, not a Jev question |
| 2 | SME Relevance | `nsr_consumer`, `nsr_single_company`, `nsr_education`, `nsr_foreign_delegation`, `no_wider_value` | split of the old `not_sme_relevant` |
| 3 | SME Voice & Business Updates | `not_sme_voice`, `no_editorial_value` | |
| 4 | Commercial Intent | `is_it_commercial_intent` | |
| 5 | Editorial vs Advertisement | `no_editorial_value` (+ `is_it_commercial_intent`) | “does anything remain after removing promo?” |
| 6 | Substance | `no_substance` | |
| 7 | Source & Attribution | `not_identifiable` | |
| 8 | Claims & Statistics | `unattributed_claims` | |
| 9 | Duplication | *(none)* | not implemented — roadmap via `docs/published-index.json` |
| 10 | Timeliness | `not_current` | |
| 11 | Geographic Relevance | `not_geographically_relevant` | |
| 12 | Events, Awards & Appointments | `nsr_event` + `nsr_single_company` | event previews + own award/appointment news |
| 13 | Images & Media Assets | *(receive-side)* | HOLD if no usable image — receive pipeline |
| 14 | Safety & Reputation | `disc_content`, `unsubst_claims` | split of the old `defamatory` |
| 15 | Political / Advocacy Content | `partisan_campaign`, `attacks_government` (+ sensitivity gates `religion`, `royalty`, `race`) | |
| 16 | Sponsored / Advertorial Indicators | `is_it_commercial_intent`, `no_editorial_value` | backlink/SEO/promo-code signals NOT modelled |
| 17 | Overall Editorial Test | `no_editorial_value` + `not_sme_voice` + the **weighted verdict** | “what does an SME reader learn?” |

### Sensitivity gates (added beyond the 17 filters)
`royalty`, `religion`, `race` — map to **#15 Political / Advocacy Content** (and partly **#14 Safety & Reputation**).

### Not tied to a Stage-One filter
`contact` (Stage-2 “remove contact info” / reachability) and `category_fit` (Stage-2 “max 3 categories”) are our additions.

## Reverse map (our question → guideline filter)

| our gate/score | guideline filter # |
|---|---|
| `royalty`, `religion`, `race` (gates) | 15 (Political/Advocacy / sensitivity) |
| `nsr_consumer` | 2 |
| `nsr_single_company` | 2, 12 |
| `nsr_event` | 12 (also 2) |
| `nsr_education` | 2 |
| `nsr_foreign_delegation` | 2, 11 |
| `no_wider_value` | 2 |
| `is_it_commercial_intent` | 4, 16 |
| `not_geographically_relevant` | 11 |
| `disc_content` | 14 |
| `unsubst_claims` | 14 |
| `partisan_campaign` | 15 |
| `attacks_government` | 15 |
| `no_substance` | 6 |
| `not_identifiable` | 7 |
| `unattributed_claims` | 8 |
| `not_current` | 10 |
| `no_editorial_value` | 5, 17 (also 3) |
| `contact` | — (Stage-2) |
| `category_fit` | — (Stage-2) |
| `not_sme_voice` | 3, 17 |

## Gaps vs the guideline
- **#9 Duplication** — not implemented (needs a published index).
- **#1 / #13 Completeness & Images** — handled as **HOLD** on the receive side, not by Jev.
- **#16 Sponsored/Advertorial** — only the “commercial ask” part is modelled; **backlink/SEO/guaranteed-publication/promo-code** signals are not.
- Guideline reason codes (`REJECT – NO_SME_RELEVANCE`, `REJECT – HARD_SELL`, `EDITOR REVIEW – POLITICAL_CONTENT`, …) are not yet emitted by our filter (we emit ACCEPT / REJECT / EDITOR REVIEW).
