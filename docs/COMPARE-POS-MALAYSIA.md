# Compare: old (pre-split) vs new (split) — Pos Malaysia article

**Article:** *Pos Malaysia Launches SME Jumpstart Workshop 2026 to Help Malaysian SMEs Grow Beyond Online…*
**Date:** 2026-10-12 · Source: `docs/compare-pos-malaysia.json`

Both configurations judge the same article (one Jev batch, same `state`). The only difference is
how the “relevance / defamation / political” checks are structured.

## Headline

| config | outcome | weighted | gates fired |
|---|---|---|---|
| **OLD (pre-split, compound)** | ACCEPT | **81%** | none |
| **NEW (split, single-condition)** | ACCEPT | **77%** | none |

Same outcome; the split moved the weighted score down 4 points.

## Per-question (YES% = defect present; GOOD% = 100−YES)

### OLD compound questions
| question (weight) | YES% | GOOD% |
|---|--:|--:|
| `not_sme_relevant` (18) | 9 | 91 |
| `defamatory` (10) | 13 | 87 |
| `political` (6) | 1 | 99 |

### NEW split questions
| question (weight) | YES% | GOOD% |
|---|--:|--:|
| `nsr_consumer` (4) | 2 | 98 |
| `nsr_single_company` (6) | **62** | 38 |
| `nsr_event` (3) | **73** | 27 |
| `nsr_education` (2) | 22 | 78 |
| `nsr_foreign_delegation` (3) | 2 | 98 |
| `disc_content` (5) | 2 | 98 |
| `unsubst_claims` (5) | 2 | 98 |
| `partisan_campaign` (3) | 2 | 98 |
| `attacks_government` (3) | 5 | 95 |

### Shared scores (identical in both)
| question (weight) | YES% | GOOD% |
|---|--:|--:|
| `no_wider_value` (10) | 6 | 94 |
| `is_it_commercial_intent` (9) | 80 | 20 |
| `not_geographically_relevant` (7) | 1 | 99 |
| `no_editorial_value` (4) | 13 | 87 |
| `not_sme_voice` (6) | 9 | 91 |

## What the comparison shows

1. **Same decision.** Both configs ACCEPT this article (no gate fires; weighted well above 60).
   The article is a genuine SME-training/workshop story, so both agree it’s in scope.

2. **The split exposes hidden detail the compound question averaged away.**
   - OLD bundled “single-company launch” **and** “event preview” into one `not_sme_relevant`
     number, which came out low (**9%**) — i.e. it looked *fully relevant*.
   - NEW measures them separately: `nsr_single_company` = **62%** and `nsr_event` = **73%**
     (both clearly triggered). So the split shows this is *also* a single-company event
     announcement, which the one combined number hid.

3. **But it doesn’t change the verdict, because the split parts carry little weight.**
   The 18 points that used to ride on `not_sme_relevant` are spread across 5 parts. Here the
   only triggers (`nsr_single_company` 6, `nsr_event` 3) contribute ~13 points of drag, so the
   weighted moves only **81 → 77**. The dominant commercial signal
   (`is_it_commercial_intent` = **80%**) is shared by both and keeps the score high.

4. **Trade-off in one line.** The split buys **diagnostic transparency** (you can now see *why*
   an item is borderline — single-company? event?) at the cost of **decision sensitivity**: the
   same evidence, spread thin, moves the final score less.

## Files
- Raw results: `docs/compare-pos-malaysia.json`
- Split explanation: `docs/QUESTION-SPLIT.md`
