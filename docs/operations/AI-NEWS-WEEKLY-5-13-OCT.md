# AI News Weekly Report — 5–13 Oct

Source file: **`docs/FILTER-REPORT-gates-def-original-20261013-1309.xlsx`** (battery `gates-def-original` / frozen **0823cfa2abbb8be2**)
Scope: articles judged in the 5–13 Oct filter report, **de-duplicated** (the run contains a few press releases under two folder names)

> **Total email received = 66**
> **Rejected by editor = 20** (R1)
> **Rejected by AI_News = 7** (R2)
> **% disagreement on Reject = %R = |R1 − R2| / (R1 + R2) = |20 − 7| / 27 = 48.1%**
> **Accepted by editor = 46** (A1)
> **Accepted by AI_News = 59** (A2)
> **% disagreement on Acceptance = |A1 − A2| / (A1 + A2) = |46 − 59| / 105 = 12.4%**

## Report

**1. All R2 rejects are due to the aggregate score — none from the 3 Critical Gates.**
Every AI_News reject (7) had **Royalty / Religion / Race = 97–99**, far above the fire point, so **no Critical Gate fired**. Rejection came purely from the **weighted (aggregate) score: 45–59 (< 60)**.
AI reject precision = **7/7 = 100%** (every AI reject is also an editor reject); it **missed 13** editor rejects (those cleared the aggregate).

| AI-rejected (R2) | gates (Royalty/Religion/Race) | weighted |
|---|---|---|
| ICAEW Budget 2027 Commentary | 98 / 98 / 97 | 59 |
| Media Coverage Opportunity – EnerGex 2026 | 98 / 98 / 98 | 57 |
| Monash University Malaysia – Triple Alliance | 98 / 98 / 97 | 58 |
| Karaoke Manekineko – Opening 20 Outlets | 99 / 98 / 99 | 47 |
| IMAGO Technologies – PaperSmart Tablet | 99 / 98 / 98 | 50 |
| Allianz Life – Breast Cancer Awareness | 98 / 98 / 98 | 55 |
| CelcomDigi – Protect+ with AppleCare | 98 / 98 / 98 | 45 |

**2. %R is high (48.1%) → room for fine-tuning.**
The 13 disagreements are conservative **misses** (editor REJECT, AI ACCEPT). Averaged over them, the weakest contributors:

| weakest score | mean GOOD% | weight |
|---|--:|--:|
| SME Voice & Business Updates | 46 | 7 |
| SME Relevance | 50 | 26 |
| Overall Editorial Test | 64 | 12 |
| Timeliness | 70 | 4 |

**Major contributor = `SME Relevance`** (low mean × heaviest weight 26) — first candidate for fine-tuning. Detail for F2F discussion.

**3. “Receiving stage located press-release text + image with 100% accuracy” — NOT confirmed.**
From `data/msme.sqlite3` (`checklist`): text/article located **52/55 (94.5%)**; images well below 100% — `hasPic` 20/55, `hasImageInArticle` 36/55, `hasLogoInArticle` 30/55. So **text ≈ 95%, image detection < 100%**.

**4. To do next week**
- **a** – Continue tuning. Test AI_News with articles **known to violate the 3Rs** (Royalty/Religion/Race) — the Critical Gates never fired this week.
- **b** – Start training AI_News to **Repurpose** Accepted articles (pass both Critical Gates **and** the aggregate threshold).

## Details
1. **Filter Report.xlsx** (`docs/FILTER-REPORT-*.xlsx`)
   - Lists all **3 Critical Gates** (Royalty, Religion, Race) and the **non-critical gates** (11 weighted scores).
   - Value = **GOOD% = agreement probability** — higher is better (a gate fires when low).
2. **Gate Def.xlsx** (`docs/filter/original-gates.xlsx`, and runnable `docs/gates-def-*.xlsx`)
   - **Each tab = a gate definition** (instruction, TRUE/FALSE, weight/threshold).
   - Each gate’s **threshold** (Critical Gates) / **weight** (weighted scores) is **tunable**.

---

*Basis: file 1309 → 75 rows, 66 unique articles. R1 20 · R2 7 · %R 48.1% · %A 12.4% · all R2 by aggregate score, none by a Critical Gate.*
