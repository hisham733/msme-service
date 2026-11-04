# MSME Filter — Workflow, Logic & Why Jev + DeepSeek

The authoritative description of the **Stage-1 editorial filter** (inside the combined app on `:8899`,
`filter.py`). It explains **what the filter does**, the **current rule model**, the
**decision workflow**, and **why we added an LLM (DeepSeek) next to Jev**.

> Historical/working notes also live in `docs/filter/FILTER-LOGIC.md` and `docs/filter/JEV.md`; this
> file is the current, consolidated overview.

**Reading order:** 1–3 *what it is* · 4 *how it decides* · 5 *why two engines* ·
6 *examples* · 7–9 *history, tuning, limits*.

---

## 1. Where the filter sits

```
RECEIVE + FILTER  (one app, :8899)
Gmail → normalize → decide → Drive fetch
→ extract → logo scan → verify
→ if ready: filter.judge (preprocess → Jev → deterministic checks)
→ checklist row + filter_results → archive .md
→ ACCEPT / EDITOR REVIEW / REJECT
```

- **Receive** builds the article (`.md`) and decides `readyToFilter`.
- **Filter** judges that article and returns an **outcome**.
- They are separate services; the filter is stateless per article.

---



## 2. The rule model (current)

The filter is **15 Noul questions = 6 gates + 8 scores + 1 context**.
A **Noul** returns the probability that its (always negatively-phrased) question is
**true** — i.e. that the **defect is present**.

### 2.1 Hard gates — 6 (`GATES`)

Each gate asks the **defect** ("is it bad?"); a **high** `noul` means the defect is
present. Each has its **own threshold** (default `0.85`, editable per gate).


| #   | Key                           | Display                         | Fires →           |
| --- | ----------------------------- | ------------------------------- | ----------------- |
| 1   | `not_sme_relevant`            | Not SME-relevant                | **REJECT**        |
| 2   | `no_wider_value`              | Single-company / no wider value | **REJECT**        |
| 3   | `is_it_commercial_intent`     | Primarily commercial            | **REJECT**        |
| 4   | `not_geographically_relevant` | Not geographically relevant     | **REJECT**        |
| 5   | `defamatory`                  | Defamation risk                 | **EDITOR REVIEW** |
| 6   | `political`                   | Political or advocacy           | **EDITOR REVIEW** |


- **#1** `not_sme_relevant` — *topic/domain*: is the subject matter outside the
SME/business-ecosystem world (consumer, lifestyle, entertainment, personal
finance, unrelated product reviews)?
- **#2** `no_wider_value` — *breadth/benefit*: a single-company or niche story with  
**no wider development, lesson or perspective** for other SME readers ("merely  
being *about* an SME is not enough"). This enforces **“about an SME ≠ meaningful**  
**to SMEs”** .
- **#3** `is_it_commercial_intent` — **guideline-aligned: hard-sell only** (discounts,
sales offers, product promotion, direct customer acquisition). A product/service/event
**mention** within a wider SME-relevant development — **including a paid workshop with
substantive industry content** — does **not** trigger it. (Our earlier extra clauses
— *paid event/workshop* and *sponsored/advertorial/backlink* — were **removed**.)
- **#4** `not_geographically_relevant` — overseas/international development with no
Malaysian/ASEAN/trade/accessible-market relevance (no transferable impact).
- **#5** `defamatory` — a **risk flag** (allegations without evidence, misinformation,
discrimination, legal/reputational concern), **not** a truth judgment → human.
- **#6** `political` — **partisan/electoral** politics, advocacy that **attacks/blames/
  campaigns against** a party/leader/government, disparaging religion, or challenging
  the royal institution → human. **Constructive policy proposals/calls from industry
  bodies or SMEs (e.g. a Budget recommendation) are NOT flagged** (they auto-pass).

> Gates are **fail-fast and ordered**. Order = the table above.
> `defamatory` + `political` stop being auto-rejects and route to a person.



### 2.2 Scored criteria — 8 (`SCORES`), %-weights summing to 100

Each is a **negative** Noul; the good value is the **“no” side** `1 − noul`.
A **high NO% = good**.


| Criterion                                      | Weight | Asks the defect (“Is this NOT…?”)                                          |
| ---------------------------------------------- | ------ | -------------------------------------------------------------------------- |
| `no_substance محتوى غير كافي`                  | 17     | …enough factual material to build an article from the submission alone?    |
| `not_identifiable لا يوجد معرف لمن قال الكلام` | 17     | …the issuing org / speakers identifiable?                                  |
| `unattributed_claims ادعائات غير مطلوبه`       | 17     | …stats/claims sourced (vs unsupported superlatives)?                       |
| `not_sme_voice`                                | 17     | …a useful perspective/insight for the wider SME community (vs pure promo)? |
| `not_current`                                  | 8      | …current (vs a stale, re-sent event)?                                      |
| `no_editorial_value`                           | 8      | …anything an SME reader learns (net takeaway)?                             |
| `contact`                                      | 8      | …an identifiable/contactable contact?                                      |
| `category_fit`                                 | 8      | …a clear site category? (Agri, Corporate, Government, Investment, Lifestyle, News, Opinion, Property, SME, Technology, Training & Education) |


Weights are **editable percentages** (Config page enforces a total of 100).

### 2.3 Context question — 1 (`EXTRA`)

`is_negative_or_attacking` — polarity/tone toward an identifiable target, shown to
editors. **Not** a gate and **not** weighted.

### 2.4 Routing map — what each filter leads to

There are **three** outcomes: **REJECT · EDITOR REVIEW · ACCEPT** (plus
receive-side `HOLD`). There is **no separate `FLAG` outcome** — a "flag" for a
human is exactly `EDITOR REVIEW`. This is what the code does today
(`filter.py::decide()` + `::assist()`):

| Disposition | Filters |
|---|---|
| **REJECT direct** | `not_sme_relevant`, `no_wider_value`, `is_it_commercial_intent`, `not_geographically_relevant` (gates G1–G4) |
| **EDITOR REVIEW** | `defamatory`, `political` (gates G5–G6, review gates); any **ambiguous** weak gate; a **borderline weighted** score |
| **ACCEPT direct** | no gate fired **and** weighted ≥ 60 |
| **REJECT (LOW_WEIGHTED_SCORE)** | no gate fired **and** weighted < 60 |
| **Feeds the weighted score** (not a direct outcome) | the 8 scored criteria: `no_substance`, `not_identifiable`, `unattributed_claims`, `not_sme_voice`, `not_current`, `no_editorial_value`, `contact`, `category_fit` |
| **Context only** | `is_negative_or_attacking` (shown to editors, never routes) |

> **`HOLD`** is a **receive-side** outcome (missing materials), not produced by the filter.

---



## 3. Outcomes

`ACCEPT` · `EDITOR REVIEW` · `REJECT` (plus `HOLD` on the receive side).

Reason codes: `REJECT–NOT_SME_RELEVANT`, `REJECT–NO_WIDER_VALUE`,
`REJECT–IS_IT_COMMERCIAL_INTENT`, `REJECT–NOT_GEOGRAPHICALLY_RELEVANT`,
`REJECT–LOW_WEIGHTED_SCORE`, `EDITOR REVIEW–POLITICAL`,
`EDITOR REVIEW–DEFAMATORY`, `EDITOR REVIEW–BORDERLINE` (+ `HOLD–…` receive-side).

---



## 4. The filter workflow (one article, in order)

1. **Preprocess (DeepSeek — optional, pattern 1).**
  Clean the text, translate Malay→English, strip cover notes/disclaimers/forward  
   headers, and extract metadata: `{orgs, speakers, contacts, dates, links, claims,  headline}`. On any failure it is skipped and the raw text is used (fail-safe) .
  1. so are saying JAV model cannot do this 
  2. why this step importent 
2. **Build the Jev** `state` = `{subject, from, date, bodyText}` (body ≤ ~12,000 chars).
3. **Jev battery (one HTTP request, questions run in parallel).**
  15 Noul questions = **6 gates + 8 scores + 1 context**.
   Each returns `noul` = the probability the answer is *yes*.
4. `decide()` **— deterministic decision in code.**
  - **Gates, fail-fast, in fixed order.** If any gate ≥ its threshold →
   returns that gate's outcome (`REJECT` for most; `EDITOR REVIEW` for
   `defamatory`/`political`). If several fire, `REJECT` wins over
   `EDITOR REVIEW`, and within a class the **earliest in order** is the label.
  - **Otherwise the weighted score:** scores are phrased **negatively**, so the
  good value = `1 − noul`; `weighted% = Σ((1−noul) × %weight)`. `≥ 60` → ACCEPT,
  else REJECT (`LOW_WEIGHTED_SCORE`).
5. **Deterministic checks (code, no AI).** See §4.1.
6. **Second opinion (DeepSeek — optional, pattern 2).** See §5.
  May escalate an ambiguous weak gate or a borderline weighted score.
7. **Verdict** is logged to `data/filter_verdicts.jsonl` and shown on the
  Verdicts/Logs pages.



### 4.1 Deterministic checks (`prefilter.py`, no AI)

Computed for every article and attached to the verdict as `deterministic`:

- **Staleness** — `date` vs today (`days_old`).
- **Contacts** — emails/phones/“media contact” via regex.
- **Sponsored signals** — backlink/SEO/promocode/guaranteed-publication strings.

These cover things an AI is weak at (dates, exact strings) and are candidates to
**replace** the corresponding Jev questions in a later tuning pass.

---



## 5. Why we added DeepSeek (an LLM) next to Jev

**Jev is the calibrated router** — we did **not** replace it. DeepSeek covers the
things Jev is structurally weak at. They are complementary, not competing.

### 5.1 What Jev is good at (why it stays the router)

- **Calibrated probabilities** for thresholding/routing (an LLM's “93% confident”
is not a real probability).
- **Structured, constrained output** — no prose to parse, no schema drift, no retries.
- **Fast & cheap** — many Nouls in one request, evaluated in parallel.
- **Consistent** across runs.



### 5.2 Where Jev is weak (why an LLM helps)


| Weakness                                                                 | Why                                                 | DeepSeek’s role                                           |
| ------------------------------------------------------------------------ | --------------------------------------------------- | --------------------------------------------------------- |
| **World knowledge** (is a foreign story transferable? Malaysian nuance?) | Jev’s “knowledge” is only what we put in the prompt | second opinion on `not_geographically_relevant`           |
| **Malaysian political/legal nuance**                                     | culturally specific, high-stakes                    | second opinion on `political` / `defamatory`              |
| **No reasons/explanations**                                              | Jev returns probabilities only                      | produces a **rationale** for editors (HOLD/EDITOR REVIEW) |
| **Malay-only text**                                                      | Jev is English-first                                | **preprocess**: translate → English                       |
| **Messy email text**                                                     | wrappers, disclaimers, forward headers              | **preprocess**: clean + extract metadata                  |
| **No fact-checking**                                                     | no retrieval                                        | flagged for a **human**; a retrieval stage is future work |
| **Deterministic data** (dates, contacts, URLs)                           | not Jev’s job                                       | handled in **code** (`prefilter.py`)                      |




### 5.3 The two DeepSeek patterns we implemented

**Pattern 1 — Preprocess (every article).** Clean/translate/extract *before* Jev
judges, so Jev sees good input. Fail-safe: raw text on error.

**Pattern 2 — Second opinion (only where needed).** DeepSeek re-judges:

- a **weak gate** (`no_wider_value`, `not_geographically_relevant`, `defamatory`,
`political`) when Jev is **ambiguous** (noul in `0.5–0.85`) **or** the gate fired
(to give the editor a reason); and
- the **overall editorial test** when the **weighted score is borderline**
(45–65).

**Fusion:** agreement acts; if the LLM flags a defect in an ambiguous case it
escalates (review gate → EDITOR REVIEW, reject gate → REJECT); a borderline
disagreement → EDITOR REVIEW.

**Deliberately NOT second-opinioned:** `not_sme_relevant` and
`is_it_commercial_intent` — these stay **pure Jev** (calibrated, deterministic
routing), plus all 8 scores.

### 5.4 Guardrails

- **Never route on LLM probabilities** — only Jev’s numbers set thresholds.
- **JSON validated + retries**; LLM failure → keep Jev’s verdict (never auto-accept).
- The article is treated as **data**, not instructions (injection).
- DeepSeek calls fire **only** for the preprocess pass and the ambiguous/borderline
cases, so most articles still cost one Jev call.



### 5.5 Where Jev is weak, per filter

> **Full standalone doc:** [`docs/filter/JEV-WEAKNESSES.md`](JEV-WEAKNESSES.md) — the same
> matrix plus a per-filter **why** and **examples** (real + synthetic).

“Jev is weak” here means **one of three structural things** — it is *not* a claim
about accuracy in general:

1. **Needs world knowledge** Jev cannot hold (is a foreign story transferable to
  Malaysia? is this direct political advocacy?). Jev only knows what we put in the
   prompt.
2. **Needs exact/deterministic data** (a real date, a literal email address, a promo
  code) — an AI guess is strictly worse than a regex.
3. **Needs subjective editorial judgment** (“is there a takeaway for readers?”,
  “does this send a defamatory signal?”) — high-stakes and genuinely arguable.

Everything else — well-scoped text classification — is where Jev is **strong** and
stays the sole judge.

#### The per-filter matrix


| Filter                        | Type    | Why Jev is OK / weak here                                                                         | Remedy (in order)                            |
| ----------------------------- | ------- | ------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| `not_sme_relevant`            | gate    | **OK** — classic topic classification; the criteria enumerate the domain well                     | Jev alone                                    |
| `no_wider_value`              | gate    | **WEAK (judgment)** — deciding “value to *other* SMEs” is an evaluative call, not a keyword match | **DeepSeek** (ambig/fired), then human       |
| `is_it_commercial_intent`     | gate    | **Mostly OK** — price/CTA/promo are lexical signals                                               | `prefilter.py` strings + Jev                 |
| `not_geographically_relevant` | gate    | **WEAK (world knowledge)** — “is an overseas story transferable to MY?” needs outside context     | **DeepSeek** (ambig/fired)                   |
| `defamatory`                  | gate    | **WEAK (judgment + no fact-check)** — can only flag *risk*, never verify truth                    | **DeepSeek** rationale → **human**           |
| `political`                   | gate    | **WEAK (world/Malaysian nuance)** — partisan/attacking politics vs constructive policy proposal    | **DeepSeek** (ambig/fired) → **human**       |
| `no_substance`                | score   | Mostly OK — “is there enough material?”                                                           | Jev; DeepSeek only if weighted borderline    |
| `not_identifiable`            | score   | **WEAK (exact extraction)** — orgs/speakers are entities, easily missed                           | `prefilter.py` entities + Jev                |
| `unattributed_claims`         | score   | **WEAK (judgment)** — spotting unsupported stats/superlatives                                     | Jev; DeepSeek if borderline; retrieval later |
| `not_current`                 | score   | **WEAK (deterministic)** — needs the *real* date                                                  | `prefilter.py` **dates**                     |
| `no_editorial_value`          | score   | **WEAK (subjective)** — “is there a net takeaway?”                                                | **DeepSeek** if weighted borderline (45–65)  |
| `contact`                     | score   | **WEAK (deterministic)** — an email/phone is a literal string                                     | `prefilter.py` **regex**                     |
| `category_fit`                | score   | Taxonomy now provided: Agriculture, Corporate, Government, Investment, Lifestyle, News, Opinion, Property, SME, Technology, Training & Education | Jev                      |
| `not_sme_voice`               | score   | **WEAK (overlap)** — perspective-vs-promo overlaps `commercial` / `no_wider_value`                | Jev; DeepSeek if borderline                  |
| `is_negative_or_attacking`    | context | **WEAK (tone)** — polarity is subtle and high-stakes                                              | **human only** (never auto-routes)           |




#### The remedy ladder (preferred → last resort)

```
exact/deterministic data  ->  prefilter.py (regex/date)      # best: no AI
well-scoped classification ->  Jev (calibrated)               # default judge
ambiguous / evaluative    ->  DeepSeek second opinion         # only weak gates + borderline
truth / legal / advocacy   ->  human (EDITOR REVIEW)          # never automated
```



#### Examples of each weakness

- **World knowledge —** `not_geographically_relevant`**.** A story about a US
small-business tax overhaul. Jev sees “SME” and may score it *relevant*; a human
knows it has no Malaysian transferable impact. → DeepSeek is asked only when the
gate is **ambiguous (0.5–0.85) or fired**, to confirm/reason.
- **Deterministic —** `not_current` **/** `contact`**.** An email that says “Event: 3 Sep”
with no year, or a contact written as `nur [at] company [dot] com`. Jev can guess
wrong; `prefilter.py` parses the **actual date** and normalises the **literal
address** — so these are done in **code**, not by an AI, and only *supplemented*
by Jev.
- **Judgment / overlap —** `no_wider_value`**.** “Acme Sdn Bhd appoints a new regional
sales manager.” It *is* about an SME (so `not_sme_relevant` passes) but there is nothing other SME readers can use. This is the classic weak gate → DeepSeek confirms the reasoning, then it **REJECTS         how** .
- 
- **No fact-check —** `defamatory`**.** “A viral post claims Company X’s milk formula is
unsafe.” Jev can only return a **risk probability**; it has no retrieval to verify
the claim. → DeepSeek produces a reason string, and the item is **EDITOR REVIEW** —
a **human** decides. (This is the one place we explicitly never automate the
outcome.)



#### Where this is in the code

- `filter.py::_WEAK_GATES = ("no_wider_value", "not_geographically_relevant", "defamatory", "political")` — the only gates the LLM may second-opinion.
`not_sme_relevant` and `is_it_commercial_intent` are **deliberately excluded**.
- `filter.py::assist()` — triggers a second opinion for a weak gate that is
**fired or ambiguous**, and for a **borderline weighted** score.
- `filter_llm.py::second_opinion()` / `preprocess()` — the DeepSeek calls.
- `prefilter.py` — dates, contacts, sponsored strings (the deterministic remedies).

> **Rule of thumb:** if the answer is a **fact a machine can look up or parse**, fix
> it in **code**; if it is a **judgment about the text**, let **Jev** decide; only
> when Jev is **genuinely unsure or the stakes are high** do we spend an LLM call —
> and for **truth/legal/advocacy** a **human** decides.

### 5.6 No-LLM mode (DeepSeek fully removed)

Set **`ENABLE_LLM_ASSIST=false`** (env or `data/settings.json`, or the toggle on the
Config page). This is the mode to use if the LLM must be removed entirely.

What changes:

- **Pattern 1 is skipped** — Jev judges the **raw archived text** (no clean/translate/extract).
- **Pattern 2 is replaced** by a deterministic router, `filter.py::_route_ambiguity()`:

| Situation (no LLM) | Result |
|---|---|
| a **weak gate** (`_WEAK_GATES`) with `noul` in `[0.50, threshold)` on an otherwise-ACCEPT article | **EDITOR REVIEW** (`AMBIGUOUS_<GATE>`) |
| **weighted** in the borderline band `[45, 65]` | **EDITOR REVIEW** (`BORDERLINE`) |
| a gate already **fired** (REJECT) or a review gate fired (EDITOR REVIEW) | **unchanged** (never downgraded) |

- **No external model is called** — the decision path is Jev + code only.
- **Trade-off:** noticeably **more EDITOR REVIEW** items ("uncertainty goes to a
  human" instead of an LLM tie-break).
- **What is lost:** DeepSeek's *reason strings*, plus any chance of resolving an
  ambiguous case automatically. Facts are still best handled deterministically
  (`prefilter.py`).
- **Scope:** this removes the LLM from the **filter** only. The **receive** stage
  (`extract.py`, `decide.py`, `verify.py`, `reply.py`, `pipeline.py`) still uses an
  LLM and is unaffected.

> Code: `filter.assist()` returns `_route_ambiguity(...)` when the assist is off;
> `filter_llm.preprocess()` returns `{}` when off, so Jev sees the raw text.

---



## 6. Worked examples

> Gate cards in the UI read `NO x% · YES y%` where **YES = the defect** (`noul`).
> Gates are checked **in order** and **fail-fast**.



### A. CelcomDigi Protect+ / AppleCare (consumer telco promo) → **REJECT —** `NOT_SME_RELEVANT`

Real verdict (`data/filter_verdicts.jsonl`):


| Gate                          | noul (YES)                                    |
| ----------------------------- | --------------------------------------------- |
| `not_sme_relevant`            | **0.87** ✅ fires                              |
| `no_wider_value`              | 0.77                                          |
| `is_it_commercial_intent`     | **0.87** (also over 0.85, but later in order) |
| `not_geographically_relevant` | 0.08                                          |
| `defamatory`                  | 0.05                                          |
| `political`                   | 0.02                                          |


- **Decision:** first gate over threshold → **REJECT** `NOT_SME_RELEVANT`.
- **Weighted 61%** — computed for the record but **not used** (a gate fired).
- **Second opinion:** `no_wider_value` (0.77, ambiguous) → DeepSeek agreed
*“one company’s product launch, no wider SME takeaway”*; outcome unchanged.
- **Why:** it is **off-domain** (consumer product, not an SME matter) **and**
**single-company** (no wider value) → both relevant gates are high.



### B. Paid workshop promo (Pos Malaysia SME Jumpstart) → **REJECT —** `IS_IT_COMMERCIAL_INTENT`

- A paid event: **RM90 tickets, registration closing 30 Sep, limited seats, goodie bag**.
- `is_it_commercial_intent ≈ 0.87 ≥ 0.85` → **REJECT** (fail-fast; weighted not used).
- **Why:** the merged commercial gate explicitly covers **paid events/workshops**.



### C. Policy proposal (SME budget call) → **ACCEPT** (constructive advocacy is allowed)

- “**OUR CALL FOR BUDGET 2027** … SME Malaysia … *Government should* reduce cumulative
  costs / defer the minimum-wage review…”.
- `political = 0.04` → **not** flagged → no gate → weighted ≈ **83 ≥ 60** → **ACCEPT**.
- **Why:** the narrowed `political` criterion targets **partisan/attacking** politics and
  religion/royal sensitivity; a **constructive policy proposal/call from an industry body
  or SMEs auto-passes**. (Before the Option-B change this was wrongly `EDITOR REVIEW – POLITICAL`.)

### C2. Partisan / attacking politics → **EDITOR REVIEW —** `POLITICAL` (shows pattern 2)

- e.g. “**Vote out** the government — it is the **worst** administration and treats voters
  like fools…”, or advocacy that **attacks/blames** a party or leader.
- `political` ambiguous/high → **DeepSeek second opinion** confirms partisan/attacking →
  **EDITOR REVIEW**; a human decides.
- **Why:** partisan/attacking politics is a “review” gate — the LLM second opinion catches
  what Jev is unsure about, and a human makes the final call.



### D. Genuine government PR (MITI RM500m SME digitalisation grant) → **ACCEPT**

- All gates `< 0.85` → no gate fires.
- Scores (good side) high → **weighted ≈ 85 ≥ 60** → **ACCEPT**.
- **Why:** SME-relevant, on-domain, non-commercial, current, attributable, real
editorial value.



### E. “Single SME wins an internal award” → **REJECT —** `NO_WIDER_VALUE`

- `not_sme_relevant` **passes** (it *is* about a business) but
`no_wider_value` **fires** → **REJECT**.
- **Why:** this is exactly the “about an SME ≠ meaningful to SMEs” case — in-domain
but nothing for other SME readers.

---



## 7. Why the rule set looks like this (design decisions)

- #2 `not_sme_relevant` and #11 `not_geographically_relevant` were **split** from one
combined check, so each measures one axis (topic vs geography).
- `is_it_commercial_intent` was **aligned to the guideline** (hard-sell only). The
earlier broadened clauses — *paid events/workshops* and *sponsored/advertorial* — were
**removed** (the guideline's Commercial Intent covers hard-sell only).
- `sme_relevance` was **removed from the scores** and made a **gate** (#1).
- `no_wider_value` was **added** because “about an SME” ≠ “meaningful to SMEs”.
- Timeliness moved from a **gate** (`stale`) to a **score** (`not_current`).
- `defamatory`/`political` became **EDITOR REVIEW** (the guideline says so; the AI
cannot verify truth, and advocacy needs a human).
- Removed: `duplicate` (needs the WordPress index), `images` (handled at receive),
#5 Editorial-vs-Ad, #12 Events/Awards.

---



## 8. Tuning & config

- **Config page** (`:8899/filter-config.html`): edit gate wording, **per-gate threshold**,
score **% weights** (must total 100), add/delete rules; saved to
`data/filter_settings.json`, applied on the next judgement (no restart).
- **Env/settings**: `JEV_MODEL`, `GATE_THRESHOLD`, `ACCEPT_THRESHOLD`,
`ENABLE_LLM_ASSIST`, `LLM_GATE_BAND`, `LLM_WEIGHTED_BAND`, DeepSeek keys/model.

---



## 9. Known limitations

- **Jev cannot fact-check.** With no retrieval, defamation/misinformation is only a
**risk flag** for a human. Accuracy verification is a separate (human/retrieval) step.
- **Correlated gates:** `not_sme_relevant` and `no_wider_value` overlap for
single-company, off-domain content (both may fire); the ordered fail-fast picks
the label. (Candidate to sharpen or merge after measurement.)
- **Weights/thresholds are design values**, not yet validated against a labelled
corpus — the pilot (positives vs negatives) is the next step.
- **7-day refresh expiry** on the Google OAuth app (Testing status) affects receive
creds, not the filter.

