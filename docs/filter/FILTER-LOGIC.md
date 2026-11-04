# MSME Filter — Jev Editorial Judge (Logic & Scoring)

The filter is the Stage-1 editorial judge for press-release intake. It runs inside the combined app on `:8899` and decides **ACCEPT / EDITOR REVIEW / REJECT** for each
archived article using TypeSafe's **Jev** System One model.

```
┌─ Receive pipeline (one app, :8899) ──────────────────┐
│ Gmail → normalize → decide → extract → logo scan      │
│ → verify → if ready: filter.judge → archive .md       │
│ → checklist row + filter_results                      │
└────────────────────────┬──────────────────────────────┘
                         │ verdict
                         ▼
┌─ Filter routes (:8899) ──────────────────────────────┐
│ manual/lab/report: POST /filter → Jev judges          │
│ → ACCEPT / EDITOR REVIEW / REJECT + verdict log       │
└───────────────────────────────────────────────────────┘
```

---

## 1. The pipeline

| Step | What happens |
|---|---|
| **Build State** | The article becomes the `state` Jev evaluates: `{subject, from, date, bodyText}` (body trimmed to ~12,000 chars) |
| **Jev Request** | `POST api.typesafe.ai/v1/systemone` with **15 questions in parallel** — no prose, calibrated probabilities only |
| **Hard Gates** | 6 (`noul`) gates — any ≥ **its own threshold** (default 0.85, editable per gate) → **REJECT immediately** (the `defamatory` and `political` **review gates** → **EDITOR REVIEW** instead) |
| **Weighted Score** | 8 criteria (`noul`, phrased negatively) — the **NO side** (1−noul) is the good score; **%-weights (sum 100)** → weighted % |
| **Verdict** | No gate fired AND weighted ≥ 60 → **ACCEPT**; else **REJECT (LOW_WEIGHTED_SCORE)**. Ambiguous weak gates / borderline weighted → **EDITOR REVIEW** (see the routing map in `docs/filter/FILTER-WORKFLOW.md`) |

---

## 2. The 15 questions

### 6 Hard gates (`noul` = probability 0–1 that the defect is TRUE)

Listed in **official guideline filter order** (#2, #4, #11, #14, #15).

| Gate | Fires when |
|---|---|
| `not_sme_relevant` | **Topic** NOT relevant to SMEs / the wider business ecosystem — no SME, policy, financing, trade, tech, workforce or market-access angle (#2) → **REJECT** |
| `no_wider_value` | Single-company/niche story with no wider development, lesson or perspective for other SME readers (mere mention of an SME is not enough) → **REJECT** |
| `is_it_commercial_intent` | Primarily **hard-sells a product/service** — discounts, sales offers, product promotion, direct customer acquisition (#4) → **REJECT**. A product/service may be **mentioned** within a wider SME-relevant development (**incl. a paid workshop with substantive industry content**) — that does NOT trigger |
| `not_geographically_relevant` | Overseas/international development with **NO meaningful relevance to Malaysian SMEs, ASEAN business, trade or accessible markets** — no transferable impact (#11) → **REJECT** |
| `defamatory` | Defamation **risk** — allegations without evidence, unsubstantiated accusations, obvious misinformation, discriminatory material, or legal/reputational concerns (#14) → **EDITOR REVIEW** |
| `political` | Partisan/electoral politics, advocacy that **attacks/blames/campaigns against** a party/leader/government, disparaging religion, or challenging Malaysia's royal institution (#15) → **EDITOR REVIEW**. **Constructive policy proposals/calls from industry bodies or SMEs (e.g. a Budget recommendation) are NOT flagged** (auto-pass) |

Outcomes are **ACCEPT / EDITOR REVIEW / REJECT** (HOLD is receive-side). The
`defamatory` and `political` gates route to a human, not an auto-reject.

`duplicate` was **removed** — it was an AI guess that couldn't see the site; real
duplicate detection needs the WordPress index later. `hard_sell` and
`advertorial_or_sponsored` were folded into one **`is_it_commercial_intent`**
gate (#4 Commercial Intent). It is now **guideline-aligned = hard-sell only**; the
extra *paid-event/workshop* and *sponsored/advertorial/backlink* clauses were removed
(the guideline's Commercial Intent text covers hard-sell only). `no_relevance`
was renamed **`not_sme_relevant`** (defect-form name so the "NO" answer = good),
and **geographic scope split out** into **`not_geographically_relevant`** (#11),
so #2 is now topic-only and #11 is geography-only. `sme_relevance` was **moved
out of the weighted scores** so SME relevance is now a HARD GATE only.

### 8 Scored criteria (`noul`, phrased NEGATIVELY — the NO side = good/accept)

Each criterion asks the defect ("Is this **NOT** ...?"); the "no" answer
(1 − probability) is the good score. **A HIGH NO% = ready to accept.**
Weights are **percentages summing to 100%** (editable on the Config page).

| Criterion | Weight | The question (defect form) → what "NO" means |
|---|---|---|
| `no_substance` | **17%** | "Is there NOT enough factual material to build an article from the submission alone (no clear development/context/detail)?" → no = rich article |
| `not_identifiable` | **17%** | "Are the org and speakers NOT identifiable (no named org / no named speakers with designations)?" → no = identifiable |
| `unattributed_claims` | **17%** | "Are the stats/rankings/claims NOT attributed (unsupported 'No.1'/'leading' or bare numbers with no source)?" → no = sourced within the submission |
| `not_current` | **8%** | "Is this significantly outdated with no new development?" → no = fresh/useful |
| `no_editorial_value` | **8%** | "Overall, does an SME reader learn nothing — only a sales/registration message left?" → no = real editorial value (#17, holistic) |
| `contact` | **8%** | "Is there NO identifiable contact?" → no = contactable |
| `category_fit` | **8%** | "Does this fit NONE of the site's categories (Agriculture, Corporate, Government, Investment, Lifestyle, News, Opinion, Property, SME, Technology, Training & Education)?" → no = fits |
| `not_sme_voice` | **17%** | "Does this fail to contribute useful knowledge/experience/perspective to the wider SME community (only promoting the sender)?" → no = genuine peer value |

`images` was **removed** — the receive stage already checks images
(`hasPic` / `hasImageInArticle` / `hasLogo`). `sme_relevance` (weight 3) was
**removed from the scores** because SME relevance is a hard gate now.

---

## 3. The decision logic (in code)

```python
# 1) HARD GATES — fail-fast: any gate ≥ ITS threshold → REJECT with that reason
for gate in gates:
    if gate.noul >= gate.threshold:         # per-gate, default 0.85
        return REJECT, gate_code            # e.g. IS_IT_COMMERCIAL_INTENT

# 2) WEIGHTED SCORE — each score criterion is a NEGATIVE noul, so its good
#    value is the "no" side:
#       norm_i = 1 - noul_i
total  = Σ( norm_i × weight_i )
denom  = Σ( weight_i )
weighted% = total / denom × 100

# 3) VERDICT
if weighted >= config.ACCEPT_THRESHOLD:      # 60
    return ACCEPT
else:
    return REJECT (LOW_WEIGHTED_SCORE)
```

- **Gates are fail-fast** — commercial/advertorial content, defamation,
  or off-topic content is rejected even if its other scores are high.
- **Per-gate `threshold`** (default **0.85**, editable per gate on the Config page)
  — tuned because Jev flags genuine PRs at ~0.7–0.8 on commercial/advertorial
  language; 0.85 only catches genuinely promotional content. Lower a specific
  gate (e.g. `political`) if it should fire more readily.
- **Scores are NEGATIVE questions** — e.g. "Is this NOT relevant to SMEs?".
  The "no" answer (1 − probability) is the good score, so **a HIGH NO% = accept**.
- **Weights are percentages summing to 100** (editable on the Config page); the
  weighted % is the weighted average of the NO-side scores.
- **Fail-safe** — any Jev error routes to REJECT, never auto-ACCEPT.

---

## 4. How the weighted % (total) is calculated

### Step 1 — Jev returns a `noul` probability per criterion
Each criterion asks the defect ("Is this NOT ...?"), so Jev returns 0–1:
```
no_substance noul     = 0.49   (49% chance NOT enough material -> 51% enough)
not_identifiable noul   = 0.86   (86% chance speakers NOT identifiable -> 14% attributed)
```

### Step 2 — The good score = the "no" side

```python
norm = 1 - noul
```

```
no_substance norm     = 1 - 0.49 = 0.51
not_identifiable norm   = 1 - 0.86 = 0.14
```

### Step 3 — Multiply by weight and sum

```python
total = Σ(norm × weight)
denom = Σ(weight)
weighted% = total / denom × 100
```

| Criterion | norm | weight (%) | norm × weight |
|---|---|---|---|
| no_substance | 0.510 | 17 | 8.670 |
| not_identifiable | 0.140 | 17 | 2.380 |
| unattributed_claims | 0.855 | 17 | 14.535 |
| not_current | 0.765 | 8 | 6.120 |
| no_editorial_value | 0.605 | 8 | 4.840 |
| contact | 0.575 | 8 | 4.600 |
| category_fit | 0.995 | 8 | 7.960 |
| `not_sme_voice` | 0.265 | 17 | 4.505 |

```
total = 8.670 + 2.380 + 14.535 + 6.120 + 4.840 + 4.600 + 7.960 + 4.505
      = 53.610
denom = 17 + 17 + 17 + 8 + 8 + 8 + 8 + 17 = 100
weighted% = 53.610 / 100 × 100 = 53.6
```

### Step 4 — Compare to threshold
```python
if no gate fired AND weighted >= 60:   ACCEPT
else:                                  REJECT
```

### Key point: it's a weighted average, not a raw sum
- Each criterion contributes its **normalized** score (0–100%) × its **% weight**.
- Weights sum to **100**, so the result is directly a 0–100 score.
- The four 17% criteria (`no_substance`, `not_identifiable`, `unattributed_claims`, `not_sme_voice`) count ~2× more than the 8% ones (`not_current`, `no_editorial_value`, `contact`, `category_fit`).

### The exact code (`filter.py`)
```python
total = sum((scores_out[n]["norm"] or 0) * q["weight"] for n, q in _scores.items())
denom = sum(q["weight"] for q in _scores.values())
weighted = round((total / denom) * 100) if denom else 0
```

These `norm` values (e.g. 0.995 → 99.5%) are what the radar chart shows on each axis.

---

## 5. Worked examples

### Lion Parcel (real) → ACCEPT
- Gates: `is_it_commercial_intent=0.33, not_sme_relevant=0.12, ...` — all < 0.85 → **no gate**
- Scores: no_substance 1.0, not_identifiable 1.0, category_fit 0.99, not_sme_voice 0.9
- Weighted (denom 12) ≥ **60** → **ACCEPT**

### "50% OFF ERP this month" (synthetic) → REJECT
- `is_it_commercial_intent = 0.98 ≥ 0.85` → **REJECT (IS_IT_COMMERCIAL_INTENT)** immediately — score irrelevant

### Off-topic consumer piece (synthetic) → REJECT
- `not_sme_relevant = 0.92 ≥ 0.85` → **REJECT (NOT_SME_RELEVANT)** immediately

### MICSEA minimum wage (real) → ACCEPT
- Gates clean, weighted ≥ **60** → **ACCEPT**

---

## 6. Live tuning

Weights, gate wording, criteria levels and thresholds are editable from the
**Config page** (`:8899/filter-config.html`):

- Saves to `data/filter_settings.json`
- Applied on the **next** judgement — no restart
- Thresholds also env-overridable: `GATE_THRESHOLD`, `ACCEPT_THRESHOLD`, `JEV_MODEL`

Every verdict is logged to `data/filter_verdicts.jsonl` (viewable on the
Verdicts / Logs pages, and clearable with the 🗑 Empty data button).