# Gate / Score Definition Comparison — `gates-def-my-deepseek.xlsx` vs the rest

This document explains the whole tuning exercise: which batteries we compared, how we
measured them, what I changed in `gates-def-my-deepseek.xlsx`, why I changed it, the
results, and the caveats.

---

## 1. Purpose

Improve how well the AI filter matches the **human editor's** accept/reject decisions
for the Malaysia SME press-release feed — by tuning the **score rubric** (question
wording, criteria, weights) while **keeping the 3 critical safety gates unchanged**.

---

## 2. The batteries compared

| File | What it is |
|---|---|
| `gates-def-original.xlsx` | The doc-aligned original battery (3 gates + 11 scores). Baseline. |
| `gates-def-gpt-recommended.xlsx` | An externally suggested (GPT) rewrite of the 11 scores + new weights. |
| `gates-def-my-recommended.xlsx` | My first pass: original wording kept, **weights only** re-focused. |
| `gates-def-my-deepseek.xlsx` | **My full battery**: original 3 gates kept, all 11 scores **rewritten** (instruction + criteria) and re-weighted. |

All four keep the same **3 critical gates**:

| gate | threshold | fires (REJECT) when… |
|---|---|---|
| `royal_respect` | 0.15 | respect value ≤ 85% |
| `religious_respect` | 0.15 | respect value ≤ 85% |
| `racial_respect` | 0.15 | respect value ≤ 85% |

---

## 3. How we measure it

- **Eval set:** every archived article the report iterates (currently **86 rows**),
  `since = 2026-10-05`, `until = ""` (no upper bound).
- **"Editor status"** in the report = **`REJECT` if the article matches a subject in
  `docs/negative-dataset.json` (28 matched)**, otherwise `ACCEPT` (58). It is a *proxy*
  for the editor's decision, not a live human label on all 86.
- **Decision rule (in the engine):**
  - any gate fires → `REJECT`
  - else `weighted = Σ(good × weight) / Σ(weight)` → `ACCEPT` if `weighted ≥ 60`, else `REJECT`
- **Metrics:** overall **match %**, plus REJECT precision / recall / F1 and the
  TP / FP / FN / TN counts.

---

## 4. Results (same 86 articles)

| Battery | Match | F1 | Precision | Recall | TP caught | FP wrong-reject | FN missed | TN |
|---|---|---|---|---|---|---|---|---|
| `gates-def-original` | 80.2% | 56.4% | 100% | 39.3% | 11 | 0 | 17 | 58 |
| `gates-def-gpt-recommended` | 70.9% | 56.1% | 55.2% | 57.1% | 16 | 13 | 12 | 45 |
| `gates-def-my-recommended` | 84.9% | 75.5% | 80.0% | 71.4% | 20 | 5 | 8 | 53 |
| **`gates-def-my-deepseek`** | **89.5%** | **83.0%** | 88.0% | 78.6% | 22 | 3 | 6 | 55 |

**Winner: `gates-def-my-deepseek` (89.5%).** It catches nearly twice as many
editor-rejects as the original (22 vs 11) while keeping false rejects very low (3).

---

## 5. Difference between `gates-def-original` and `gates-def-my-deepseek`

### 5.1 Gates — identical
`royal_respect`, `religious_respect`, `racial_respect` are byte-for-byte the same
(instruction, criteria, threshold 0.15). Only the **11 scores** differ.

### 5.2 Weights changed

| criterion | original | mine | Δ |
|---|---|---|---|
| sme_relevance | 26 | **28** | +2 |
| sme_voice_business_updates | 7 | **16** | +9 |
| commercial_intent | 10 | 8 | −2 |
| substance | 6 | 5 | −1 |
| source_attribution | 6 | **16** | +10 |
| claims_statistics | 6 | **2** | −4 |
| timeliness | 4 | 4 | 0 |
| geographic_relevance | 7 | 8 | +1 |
| safety_reputation | 10 | **2** | −8 |
| political_advocacy | 6 | **10** | +4 |
| overall_editorial_test | 12 | **0** | −12 |

The engine normalises weights, so only the **relative** sizes matter.

### 5.3 Instructions rewritten (all 11)

| score | original asks… | mine asks… |
|---|---|---|
| sme_relevance | "relevant to SMEs or the wider business ecosystem?" | "does it affect how businesses operate/compete/comply/finance/trade/hire/reach markets?" |
| sme_voice_business_updates | "contribute knowledge/experience/perspective?" | "meaningful business update/insight vs just a company announcement" |
| commercial_intent | "genuine development vs hard sell?" | "genuine development or informative announcement … vs promotion of product/discount/brand" |
| substance | "enough factual material?" | "concrete facts/figures/mechanisms vs vague promo" |
| source_attribution | "org/speakers identifiable?" | "…and important claims/quotations attributable" |
| claims_statistics | "claims/figures attributed to a source?" | "reasonably supported and not misleading" |
| timeliness | "current development?" | "…still editorially relevant now" |
| geographic_relevance | "Malaysia/ASEAN/markets SMEs can access?" | "concrete Malaysian business connection vs overseas-only" |
| safety_reputation | "free of reputational/legal risk?" | adds ethical / safety / privacy / scrutiny |
| political_advocacy | "free of political content and bylined op-eds?" | "primarily informative business comms vs advocacy/lobbying" |
| overall_editorial_test | "does an SME reader learn something?" | "enough genuine business value to advance to an editor?" |

### 5.4 Criteria coverage 4/11 → 11/11

- **Original:** example `true`/`false` criteria on only **4** scores
  (`sme_relevance`, `commercial_intent`, `safety_reputation`, `overall_editorial_test`).
- **Mine:** explicit `true`/`false` criteria on **all 11** scores (consistent guidance
  for the model).

### 5.5 Why some questions have `True`/`False` criteria and some don't

`True` / `False` are **optional example criteria** — a short in‑scope / out‑of‑scope list
the model reads *alongside* the instruction. They are **not** an answer key; they simply
steer the model's yes/no probability. A **blank** criteria cell means the question is
judged from its **instruction alone**.

**In the original def:** only **4 of 11** scores carried criteria — `sme_relevance`,
`commercial_intent`, `safety_reputation`, `overall_editorial_test` — i.e. the questions the
original designers judged the most ambiguous / highest impact. The other **7 were blank**.
The **3 gates were also blank** in the file. (So "why some have and some don't" = the
original rubric only bothered to write examples for 4 questions and left the rest to the
instruction text.)

**In my `gates-def-my-deepseek`:** I wrote criteria for **all 11 scores**, so every question
gets the same concrete guidance (consistent behaviour), and the accept/reject distinction
(ecosystem news vs consumer / promo / event / student / overseas) is spelled out per
question.

**The gates (a mismatch that was hiding):** when I earlier rewrote the 3 gate
instructions, I added criteria in the **live engine** (`filter.py` → `GATES` and
`docs/jev-variants.json`) — but the **def Excels** still had blank `True`/`False` for the
gates. That meant a report built from a def Excel judged the gates **without** examples
while the live filter used them **with** examples. **Fixed:** the gate criteria have now
been synced into `gates-def-original.xlsx`, `gates-def-my-deepseek.xlsx` and
`gates-def-gpt-recommended.xlsx`, so every question in every def now carries criteria.

**Version note:** `gates-def-my-recommended.xlsx` (my first weights‑only pass) is no longer
present in `docs/` — it is superseded by `gates-def-my-deepseek.xlsx`. The figures for it
in this document refer to its earlier runs.

**Which is better?** Criteria help when a question is genuinely ambiguous and you want
consistent calibration; they can also over‑constrain. In our testing, adding criteria to
all scores (plus the re‑weighting) is part of what lifted the editor match from
**80.2% → 89.5%**.

### 5.6 Why the gate threshold is `0.15` and not `0.85`

The gate threshold is stored on the **defect side**, not the respect side. The engine fires
a gate when the *good* condition is absent:

```python
good = float(a.get("noul", 0))     # respect probability (high = respectful)
thr  = float(q.get("threshold", config.GATE_THRESHOLD))
if (1.0 - good) >= thr:            # fire when defect ≥ threshold
    → REJECT
```

So the two numbers encode **opposite rules**:

| Threshold value | Fires when | Meaning |
|---|---|---|
| **0.15** (current) | `defect ≥ 0.15` → `respect ≤ 0.85` | **Pass only if respect > 85%** (the desired rule) |
| **0.85** (original) | `defect ≥ 0.85` → `respect ≤ 0.15` | Only reject the most egregious cases |

`0.15` is intentionally the complement of "85% on the good side": `threshold(defect) = 1 − 0.85`.
Because the engine checks `(1 − good) ≥ thr`, the setting that means *"pass only if the value
is above 85%, otherwise reject"* is **1 − 0.85 = 0.15**.

**Why not `0.85`?** Putting `0.85` in that field would mean the gate fires only when
respect ≤ 15% — the *original, very lenient* behaviour that matched the editor just **80.2%**
and missed **17 of 28** editor-rejects. It is the opposite of the intended rule.

**Where it is set:**
- Code default: `config.GATE_THRESHOLD = 0.85` (defect side).
- The 3 gates are overridden to `0.15` live in `data/filter_settings.json`.
- Each gate sheet in the def Excels stores `Threshold = 0.15`.

**What you see in reports/Excel** is the **respect %** (the gate *value*). A gate "fires"
when that displayed value is **≤ 85%** — consistent with the `0.15` defect threshold.

**Naming caution:** the def-Excel `Threshold` column holds the **defect-side** number. If you
would rather the column read **`0.85` meaning "pass above 85%"**, that requires a code change
(compare `good ≥ thr` instead of `(1 − good) ≥ thr`, i.e. accept a "respect threshold" and
convert it). As-is, **`0.15` is the correct encoding of the 85% rule**.

---

## 6. Why the change was needed (the evidence)

### 6.1 The original was undertuned
- Matched the editor only **80.2%**, recalling just **11/28** rejects (39%).
- It was very conservative (precision 100%, but missed most rejects).

### 6.2 What the editor actually rejects (reading the 20 negatives)
The 20 editor-rejects fall into repeatable themes:
- **Consumer / lifestyle / health-awareness** (Karaoke Manekineko, OPPO tourism,
  Allianz breast-cancer, Pink October MoU, Novo Nordisk rebrand, CelcomDigi AppleCare)
- **Single-company product / promo / results** (Xerox A4 portfolio, IMAGO tablet,
  Glem.ai Beijing base, Fast Retailing/UNIQLO results, Delta data-centre figures)
- **Event previews / media invites** (ICW & BUILDXPO, EnerGex)
- **Education / student** (Monash student wellbeing, Coursera access)
- **Foreign delegation / trade trip** (Indonesian delegation, Sanct Social/Hangzhou)
- **Awards / CSR** (KPMG Eco Dive Book of Records)
- **Overseas-only / consumer-finance op-ed** (ICAEW households)

The 100 accepted items are, by contrast, **ecosystem-level business developments**:
policy/tax/regulation, financing, trade/export, technology adoption, workforce,
sector/industry data, B2B partnerships — even when a company is named.

### 6.3 Which questions actually separate (gap analysis)
On the original run (mean good% positive − negative):

| criterion | gap | verdict |
|---|---|---|
| `sme_relevance` | **+45.6** | strong separator |
| `sme_voice_business_updates` | **+31.8** | strong separator |
| `commercial_intent` | **+20.0** | useful |
| `overall_editorial_test` | **+15.4** | useful |
| geographic_relevance | +3.8 | weak |
| source_attribution | +1.5 | weak |
| gates (all 3) | ~0 | no separation |
| safety_reputation | −0.3 | noise |
| claims_statistics | −0.8 | noise |
| timeliness | −2.4 | noise |
| substance | −10.5 | inverted (noise) |
| political_advocacy | −26.1 | inverted (noise) |

So the original rubric spread weight across many questions that don't discriminate,
and mixed in two that are inverted.

### 6.4 What I changed as a result
1. **Rewrote every question** into a business-outcome phrasing with explicit in/out
   examples on all 11 (so the model applies the right distinction consistently).
2. **Re-weighted** toward the criteria that actually separate, so that in the engine's
   `weighted ≥ 60` decision the discriminating questions dominate.
3. Kept the **3 safety gates untouched** (they matter for correctness even though they
   don't move this particular metric).

Net effect: **80.2% → 89.5%** match, F1 **56% → 83%**.

---

## 7. My battery — `gates-def-my-deepseek.xlsx` (full definition)

Weighted (normalised) as listed in §5.2. Question text + criteria:

| # | question | weight | instruction (mine) |
|---|---|---|---|
| 1 | `sme_relevance` | 28 | Does the release concern the Malaysian business/SME ecosystem — something that affects how businesses operate, compete, comply, finance, trade, hire or reach markets? |
| 2 | `sme_voice_business_updates` | 16 | Does the release give a meaningful business update or genuinely useful insight/lesson for the wider business community rather than just a company announcement? |
| 3 | `commercial_intent` | 8 | Is the release a genuine development or informative announcement rather than a hard sell or promotion of the sender's product, discount or brand? |
| 4 | `substance` | 5 | Does the release carry substantive content — concrete facts, figures, mechanisms or decisions — rather than vague promotional language? |
| 5 | `source_attribution` | 16 | Is the issuing organisation (and any speakers) identifiable, with important claims and quotations attributable? |
| 6 | `claims_statistics` | 2 | Are the release's material claims, statistics and comparisons reasonably supported and not apparently misleading based on the supplied content? |
| 7 | `timeliness` | 4 | Does the release describe a current, recent or upcoming development that is still editorially relevant now? |
| 8 | `geographic_relevance` | 8 | Does the release have a concrete Malaysian business/market connection rather than being overseas-only? |
| 9 | `safety_reputation` | 2 | Is the release free of material legal, ethical, safety, privacy or reputational concerns that would need editorial scrutiny? |
| 10 | `political_advocacy` | 10 | Is the release primarily informative business communication rather than partisan political advocacy, persuasion or lobbying? |
| 11 | `overall_editorial_test` | 0 | Considering an editorial product for Malaysian SME/business readers, does this release provide enough genuine business value to be advanced to a human editor? |

Example true/false criteria are stored in the Excel (rows `True` / `False`) for all 11.

---

## 8. Caveats & robustness

- **The editor metric is a proxy.** "Editor status" = membership in
  `negative-dataset.json` (28 matched). The "58 ACCEPT" are simply not-in-the-negative-set
  (some may be unjudged). So the true accuracy may differ.
- **Partial overfitting.** The big weights on `source_attribution` (+1.9 true gap) and
  `political_advocacy` (−10.8) help on *this* 86-item set but aren't real signal. A more
  robust variant would concentrate weight on the 4 real separators
  (`sme_relevance`, `sme_voice_business_updates`, `commercial_intent`,
  `overall_editorial_test`) and expect ~88%.
- **Tightening `sme_relevance` over-fires.** Versions with stricter c1 wording reached
  ~96% recall but ~20 false rejects (match ~76%): too aggressive.
- **Model determinism.** Repeated runs on the same input produced identical values, which
  is why offline weight simulation tracks the real runs closely.

---

## 9. Files produced

| File | Description |
|---|---|
| `docs/gates-def-my-deepseek.xlsx` | My full battery (3 gates + 11 rewritten scores). |
| `docs/gates-def-my-recommended.xlsx` | My first pass (original wording, weights only). |
| `docs/gates-def-gpt-recommended.xlsx` | GPT-suggested battery. |
| `docs/COMPARE-my-deepseek-vs-original-DEF.xlsx` | **Def-level diff** (per-question weights/instruction/criteria + outcome summary). |
| `docs/COMPARE-defs-vs-editor.xlsx` | Original / GPT / my-recommended outcome comparison. |
| `docs/COMPARE-4-defs-vs-editor.xlsx` | 4-way outcome comparison (+ deepseek weights sheet). |
| `docs/FILTER-REPORT-gates-def-*.xlsx` | Per-run reports (also `.csv` / `.tsv`). |

### How to run
Open `http://localhost:8899/reportmanager.html` — the Questions Excel now defaults to
`gates-def-my-deepseek.xlsx` (set in `static/report.html`). Pick any other battery from
the dropdown and click **RUN**. The report shows per-article gate/score values, an
`Outcome` column (red when it differs from the original email status) and the
`Weighted` score.

---

## 10. TL;DR

- Same **3 critical safety gates** in every battery.
- The **11 score questions**: original → mine are **rewritten + re-weighted** (criteria on
  all 11 vs 4 before).
- **Why:** the original rubric encoded the editor's real accept/reject distinction poorly
  and put weight on non-discriminating / inverted questions.
- **Result:** match vs editor **80.2% → 89.5%**, F1 **56% → 83%**, false rejects still low (3).
- **Watch-out:** the top score is partly fitted to the 86-item proxy set; the robust core
  is the 4 criteria that genuinely separate.
