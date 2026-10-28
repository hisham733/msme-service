# Compare: old (pre-split) vs new (split) — Karaoke Manekineko

**Article:** *Karaoke Manekineko Celebrates Opening 20 Outlets with New Promotions*
(editor “Not relevant” case — a **negative**)
**Date:** 2026-10-12 · Source: `docs/compare-karaoke-manekineko.json`

Same article, one Jev batch, same `state`; only the relevance/defamation/political structure differs.

## Headline

| config | outcome | weighted | gates fired |
|---|---|---|---|
| **OLD (pre-split, compound)** | **REJECT** | **44%** | none |
| **NEW (split, single-condition)** | **REJECT** | **56%** | none |

**Both reject** — but the OLD config rejects with a much bigger margin (44% vs 56%,
threshold = 60%).

## Per-question (YES% = defect present; GOOD% = 100−YES)

### OLD compound
| question (weight) | YES% | GOOD% |
|---|--:|--:|
| `not_sme_relevant` (18) | **95** | 5 |
| `defamatory` (10) | 12 | 88 |
| `political` (6) | 1 | 99 |

### NEW split
| question (weight) | YES% | GOOD% |
|---|--:|--:|
| `nsr_consumer` (4) | 6 | 94 |
| `nsr_single_company` (6) | **91** | 9 |
| `nsr_event` (3) | 7 | 93 |
| `nsr_education` (2) | 2 | 98 |
| `nsr_foreign_delegation` (3) | 3 | 97 |
| `disc_content` (5) | 1 | 99 |
| `unsubst_claims` (5) | 2 | 98 |
| `partisan_campaign` (3) | 3 | 97 |
| `attacks_government` (3) | 7 | 93 |

### Shared scores (identical in both) — all strong defects
| question (weight) | YES% | GOOD% |
|---|--:|--:|
| `no_wider_value` (10) | **95** | 5 |
| `is_it_commercial_intent` (9) | **98** | 2 |
| `not_geographically_relevant` (7) | 5 | 95 |
| `no_editorial_value` (4) | **73** | 27 |
| `not_sme_voice` (6) | **73** | 27 |

## What the comparison shows

1. **Same direction, weaker force.** Both configs correctly REJECT this “opening/promotions”
   piece — it’s a single-company consumer/karaoke promo with no wider business value
   (`no_wider_value` 95%, `is_it_commercial_intent` 98%).

2. **The compound question carried the same evidence with more weight.**
   OLD’s `not_sme_relevant` scored **95%** on an **18-point** weight → it alone dragged the
   weighted down to **44%** (a comfortable reject).
   NEW splits that evidence into `nsr_single_company` = **91%** but only a **6-point** weight,
   so it contributes ~5.5 points of drag; the weighted lands at **56%** — still a reject, but
   only **4 points above** the ACCEPT threshold.

3. **Same conclusion as the Pos Malaysia test, on a negative:**
   the split **loses decision margin**. It’s still correct here, but for this class of
   “single-company but otherwise clean” item, the thin split weights make the reject fragile —
   a few points of model noise could flip it to ACCEPT.

4. **Both agree the split is more diagnostic** (`nsr_single_company` names exactly *why* it’s
   off-topic), but the **pre-split compound is more decisive** for this negative.

## Files
- Raw results: `docs/compare-karaoke-manekineko.json`
- Split explanation: `docs/QUESTION-SPLIT.md`
- Positive-case counterpart: `docs/COMPARE-POS-MALAYSIA.md`
