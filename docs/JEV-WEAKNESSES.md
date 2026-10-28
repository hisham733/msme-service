# Where Jev Is Weak — Per Filter, Why, How It Works, and Examples

A clear, filter-by-filter account of **where Jev is weak**, **why**, **how the system
works around it**, and **what we do about it** — with worked examples. Companion to
`docs/FILTER-WORKFLOW.md` (the full workflow) and `docs/JEV.md` (the Jev API reference).

> **Jev** = TypeSafe's "System One" model: a fast, calibrated, **text-only** classifier.
> You give it a **state** (the article text) + typed **questions** (our filters), it
> returns a **probability** (`noul`). It is **not** a keyword matcher, **not** a chatbot,
> and it **cannot go online or fact-check**.

---

## 0. The one-paragraph summary

Jev is **strong** at well-scoped "does this text mean X?" classification (e.g. *is this
about SMEs?*, *is this commercial?*). It is **weak** wherever a decision needs
**(1) world knowledge it doesn't hold**, **(2) exact/deterministic data** (dates,
addresses, literal strings), or **(3) subjective editorial judgment** (is there wider
value? is this defamatory?). For those cases we (a) do it in **code** (`prefilter.py`),
(b) ask a **general LLM (DeepSeek) for a second opinion** on a few gates, and (c) send
the genuinely hard/sensitive cases to a **human** (EDITOR REVIEW).

---

## 0.1 How Jev actually works (the mechanism)

Understanding *why* Jev is weak starts with *how* it works.

**1. It answers questions, it doesn't "score" an article by itself.**
We POST one HTTP call per article:

```
POST api.typesafe.ai/v1/systemone
{
  "state":  "<subject> | <from> | <date> | <article bodyText>",   # the text to judge
  "questions": {
     "not_sme_relevant":   { "type":"noul", "instructions":"...", "criteria":{...} },
     "no_wider_value":     { "type":"noul", "instructions":"...", "criteria":{...} },
     ... 15 questions (6 gates + 8 scores + 1 context) ...
  }
}
```
It returns `{ "answers": { "<question>": { "noul": 0.63 }, ... } }`.
A **`noul`** is Jev's probability that the answer to that question is **YES**
(0 = clearly no, 1 = clearly yes, 0.5 = torn).

**2. Each question is a tiny rubric.**
- `instructions` = the question, written as the **defect** ("Is this NOT relevant…?").
- `criteria` = what TRUE and FALSE mean, with boundaries and examples.
Jev does **semantic reasoning** over the text against that rubric (think a zero-shot /
entailment-style classifier). It does **not** look for keywords — a paraphrase triggers
it just as well. All "knowledge" it has is what we put in the prompt + its training.

**3. Each question is independent.**
Jev answers all 15 questions from the same text, in parallel, one call. It does **not**
hold a shared "model of our business"; every answer is just *this text + this question*.

**4. Our code turns probabilities into a decision** (`filter.py::decide`):
- **Gates, fail-fast, in order:** any gate's `noul ≥ 0.85` → its outcome
  (`REJECT` for most; `EDITOR REVIEW` for `defamatory` / `political`).
- **Otherwise the weighted score:** the 8 score-criteria are phrased negatively, so the
  *good* value is `1 − noul`; `weighted% = Σ((1−noul) × %weight)`. `≥ 60` → ACCEPT,
  else REJECT.
- The **ambiguity band `noul ∈ [0.50, 0.85)`** is where Jev is *unsure* — this is
  exactly where the second opinion (below) engages.

**5. Deterministic checks run beside Jev** (`prefilter.py`, no AI): dates, contacts,
sponsored strings. These are things Jev guesses at but code can know **exactly**.

**6. DeepSeek second opinion (only for weak gates)**
`filter.py::assist` sends the *same* article + the *same* `instructions` + the *same*
`criteria` + **Jev's probability** to DeepSeek, which returns
`{judgment: true/false, agree_with_primary, reason, confidence}`. The **only** gates
eligible are `_WEAK_GATES = ("no_wider_value", "not_geographically_relevant",
"defamatory", "political")`, and only when Jev is **ambiguous or fired** (plus the
overall test when `weighted ∈ [45, 65]`). DeepSeek can only **escalate** (never downgrade)
and is **fail-safe** (error → Jev's verdict stands).

```
Jev noul  ──►  < 0.50   confident "no"     -> ignore the gate        (no review)
              [0.50, 0.85)  unsure          -> DEEPSEEK second opinion / human
              ≥ 0.85   fired               -> REJECT or EDITOR REVIEW
```

**7. Failure is never silent.**
The pipeline raises `AIError` (→ `ai_error` status, no checklist row, no reply) if the AI
returns an empty verdict, rather than treating a model outage as "not an article".

---

## 0.2 Quick table

| Filter | Kind | Jev strength | Why | Remedy |
|---|---|---|---|---|
| `not_sme_relevant` | gate | **Strong** | topic classification | Jev alone |
| `no_wider_value` | gate | **Weak** | evaluative judgment | DeepSeek 2nd opinion → human |
| `is_it_commercial_intent` | gate | **Mostly OK** | lexical cues (price/CTA/promo) | `prefilter.py` + Jev |
| `not_geographically_relevant` | gate | **Weak** | needs world knowledge | DeepSeek 2nd opinion |
| `defamatory` | gate | **Weak** | can flag risk, can't verify truth | DeepSeek reason → **human** |
| `political` | gate | **Weak** | Malaysian nuance (advocacy vs partisan) | DeepSeek 2nd opinion → human |
| `no_substance` | score | OK | amount of material | Jev |
| `not_identifiable` | score | **Weak** | entity extraction | `prefilter.py` + Jev |
| `unattributed_claims` | score | **Weak** | spotting unsupported stats | Jev; DeepSeek if borderline |
| `not_current` | score | **Weak** | needs the real date | **`prefilter.py` dates** |
| `no_editorial_value` | score | **Weak** | subjective | DeepSeek if weighted borderline |
| `contact` | score | **Weak** | literal string | **`prefilter.py` regex** |
| `category_fit` | score | **Weak** | needs the site taxonomy | taxonomy given (11 categories) + Jev |
| `not_sme_voice` | score | **Weak (overlap)** | overlaps commercial / wider-value | Jev; DeepSeek if borderline |
| `is_negative_or_attacking` | context | **Weak** | tone/polarity | editor only |

---

## 1. The three kinds of Jev weakness

"Jev is weak" never means "Jev is bad in general". It means **the question needs
something Jev structurally cannot supply**:

| Kind | What it means | Examples |
|---|---|---|
| **A. World knowledge** | Jev only knows what's in the prompt (+ training). It can't know "is a US story transferable to Malaysia?" or "is this partisan in the Malaysian context?". | `not_geographically_relevant`, `political`, `defamatory` |
| **B. Exact / deterministic data** | Jev guesses; a regex/date-parser is exact. | `not_current` (date), `contact` (email/phone), sponsored strings, `not_identifiable` (names) |
| **C. Subjective editorial judgment** | Genuinely arguable, high-stakes. | `no_wider_value`, `no_editorial_value`, `defamatory` |

Everything else — **well-scoped text classification** — is where Jev shines.

---

## 1.5 The deeper reasons — *why* the mechanism fails

These are the concrete failure modes behind the three kinds above.

- **No retrieval / no internet.** Jev (and DeepSeek) only "know" what's in their
  training. Today's news, whether a foreign policy applies to Malaysia, whether an
  allegation is true — none of that is available. Training knowledge is **frozen in
  time** and can be stale or wrong, while a date/entity is a **fact of the text**.
- **A probability is not evidence.** Jev's `noul` is a calibrated *opinion*, not a fact.
  For a literal thing (an email address, a date, a promo code) an opinion is strictly
  worse than a regex: it can be silently wrong at high confidence.
- **Subjective questions have no ground truth.** "Is there wider value for other SMEs?"
  is genuinely arguable — two human editors can disagree. Jev returns *its* best guess;
  when it lands in the ambiguous band, even it isn't sure. That's why a **second reader**
  (DeepSeek) and finally a **human** are needed.
- **Cultural slash-line.** Malaysian politics, religion sensitivity, the royal
  institution, and "advocacy vs constructive proposal" are culturally loaded. A generic
  model generalises from its training, which is not tuned to Malaysian editorial norms.
- **Confidence ≠ correctness.** Jev can be *very sure* and *wrong* (e.g. confidently
  calling a US tax story "relevant" because it says SME). We therefore (a) never trust a
  single opinion for the sensitive/hard gates, and (b) keep the routing thresholds in our
  control.

---

## 2. Per-filter breakdown (why + example)

### 2.1 `not_sme_relevant` (gate) — **Jev is strong**
- **Asks:** is the *topic* outside the SME/business-ecosystem world?
- **Why strong:** classic theme classification; the criteria enumerate the domain well
  (financing, policy, trade, tech, workforce, market access…). This is exactly the kind
  of "does this text mean X" question Jev is built for.
- **How it works:** Jev matches the article's *subject area* against that enumerated
  domain and returns how likely it is **off**-topic.
- **Examples:**
  - **CelcomDigi "Protect+ with AppleCare"** (consumer telco product) → `0.87` →
    **REJECT `NOT_SME_RELEVANT`**. Correct, decisive.
  - A **MITI SME export-grant PR** → `0.07` → passes.
  - A **celebrity lifestyle piece** ("K-pop star opens café") → high → REJECT.
- **Remedy:** Jev alone (calibrated, deterministic routing).

### 2.2 `no_wider_value` (gate) — **Weak (judgment)** ⚠️
- **Asks:** a single-company/niche story with **no wider value** for other SME readers?
- **Why weak:** "value to *other* SMEs" is an **evaluative** call, not a keyword match.
  The boundary ("about an SME is not enough") requires editorial judgment, so Jev often
  lands in the ambiguous band instead of being decisive.
- **Reason it fails:** there's no objective truth — "could another SME learn from this?"
  is a judgment. Jev's calibration is decent but it can't *reason* the way a second reader
  can.
- **How the fix works:** when Jev is ambiguous (`noul ∈ [0.5, 0.85)`) or the gate fired,
  DeepSeek re-judges the SAME question and returns a `reason`; if it agrees "no wider
  value", the item escalates (from ACCEPT → REJECT). It only ever **escalates**, never
  downgrades.
- **Examples:**
  - *"Acme Sdn Bhd appoints a new regional sales manager."* → Jev ~**0.68** (below 0.85)
    → DeepSeek agrees "no wider SME value" → **REJECT**.
  - *"Company X wins a 'Top Employer' internal award."* → single-company, no peer lesson.
  - *"MITI announces RM500m SME digitalisation grant."* → **wider development** → Jev low
    (passes) — this is the difference the gate is meant to catch.
- **Remedy:** DeepSeek second opinion when ambiguous/fired → then human.

### 2.3 `is_it_commercial_intent` (gate) — **Mostly OK** *(guideline-aligned)*
- **Asks:** does it **primarily hard-sell a product/service** (discounts, sales offers,
  product promotion, direct acquisition)? A product/service/event may be **mentioned**
  within a wider SME-relevant development.
- **Why mostly OK:** price/CTA/promo/`buy now` are **lexical** cues — Jev generalises
  these well. But **normal press-release language** also trips it a little (genuine PRs
  score ~0.7–0.8), which is why the threshold is **0.85**, not 0.7.
- **History / why it over-fired:** our earlier wording added *paid event/workshop* and
  *sponsored/advertorial* clauses that the client's guideline does **not** contain. That
  falsely REJECTed the **Pos Malaysia SME Jumpstart Workshop** article (a paid event with
  substantive editorial content) — which the site actually **published**. The clause was
  **removed**; the gate is now hard-sell only.
- **Examples:**
  - *"50% OFF our ERP this month — sign up now"* → `≈0.99` → REJECT (hard-sell).
  - **Pos Malaysia SME Jumpstart Workshop (paid, but substantive)** → `0.12` → **ACCEPT**
    (was `0.88` → REJECT before the fix).
  - *"Lion Parcel expands to Malaysia"* (genuine news, product as context) → passes.
- **Remedy:** Jev alone. (Sponsored/backlink strings are still surfaced as a deterministic
  `prefilter.py` signal for editors — not a gate.)

### 2.4 `not_geographically_relevant` (gate) — **Weak (world knowledge)** ⚠️
- **Asks:** overseas development with no Malaysian/ASEAN/trade relevance?
- **Why weak:** deciding "is a foreign story **transferable** to Malaysia?" needs outside
  context Jev doesn't have (it has no up-to-date geography/trade knowledge).
- **Reason it fails:** Jev sees the word "SME" or "tax" and leans "relevant" — it can't
  reason "this is a US-only policy with no Malaysian/ASEAN/export impact".
- **How the fix works:** ambiguous/fired → DeepSeek (which has broader parametric world
  knowledge) re-judges and can escalate or confirm; fat confirmation can still go to a
  human.
- **Examples:**
  - *"US small-business tax overhaul"* → Jev ~**0.60** (unsure — sees "business") →
    DeepSeek/human resolves: no Malaysian impact → flag/reject.
  - *"EU introduces carbon-border adjustment (CBAM)"* → **relevant** to Malaysian
    exporters — Jev may under-flag; we want it to pass. This is a *hard* case where world
    knowledge matters.
  - *"MITI export PR"* → `0.05` → passes.
- **Remedy:** DeepSeek second opinion (world knowledge) when ambiguous/fired.

### 2.5 `defamatory` (gate) — **Weak (no fact-check)** ⚠️
- **Asks:** potentially defamatory allegations / misinformation / legal risk?
- **Why weak:** Jev can only return a **risk probability** — it **cannot verify** the
  claim. There is no retrieval in the pipeline (no web lookup, no fact database).
- **Reason it fails:** "is this allegation true?" is a **fact**, not a text-classification.
  Jev can say "this *looks* defamatory" but never "this is false/unverified".
- **How the fix works:** when Jev fires or is ambiguous, DeepSeek adds a **reason** string,
  and the item is **EDITOR REVIEW** — a human verifies. This is the one case we
  **never** automate the outcome.
- **Examples:**
  - *"A viral post claims Company X's milk formula is unsafe."* → Jev risk prob +
    DeepSeek reason → **EDITOR REVIEW**; a human checks the facts.
  - *"Director of Company X embezzled millions"* (no evidence) → high risk → EDITOR REVIEW.
  - *"Company X appoints new CFO"* (clean) → `0.02` → passes.
- **Remedy:** DeepSeek reason → **human** (accuracy verification is out of scope).

### 2.6 `political` (gate) — **Weak (Malaysian nuance)** ⚠️ *(recently narrowed)*
- **Asks:** partisan/electoral politics, advocacy that **attacks/blames/campaigns
  against** a party/leader/government, religion disparagement, or royal-institution
  content — vs factual policy or a **constructive proposal**?
- **Why weak:** the line between "policy advocacy" and "partisan politics" is a
  **judgment** with Malaysian cultural nuance, and it's high-stakes (sedition/religion).
- **Reason it fails:** generic models aren't tuned to Malaysian editorial norms; and an
  over-broad criterion ("any advocacy") made it worse. Both had to be fixed.
- **Examples (real):**
  - **SMEAM "OUR CALL FOR BUDGET 2027"** proposal:
    - *Before the fix:* the criterion lumped **all advocacy** in → Jev `political = 0.63`
      (ambiguous) → DeepSeek said "advocacy" → **EDITOR REVIEW `POLITICAL`** — even though
      `defamatory = 0.06` and `is_negative_or_attacking = 0.22` (not bad/attacking).
    - *After* narrowing the criterion (Option B): Jev `political = 0.04` → **ACCEPT**.
  - *"Vote out the government — it is the worst administration"* (partisan/attacking)
    → high → EDITOR REVIEW.
  - *"Religious group demands X"* → religion-advocacy → review.
- **Takeaway:** the weakness was both Jev's *nuance* **and** an over-broad criterion.
  Narrowing the question fixed it without losing the religion/royal triggers.
- **Remedy:** DeepSeek second opinion when ambiguous → human for genuine partisan cases.

### 2.7 `not_current` (score) — **Weak (deterministic)**
- **Asks:** stale / long-past event with no new development?
- **Why weak:** the source often has **no year** ("Event: 3 Sep") — Jev guesses.
- **Reason it fails:** dates are **facts**; a calendar-aware parser is exact, a probability
  is approximate. Jev has no clock and no memory of "today".
- **Examples:**
  - *"Join our workshop on 3 Sep"* (no year, no new info) → Jev unsure → **`prefilter.py`**
    parses the date and computes `days_old`.
  - *"BREAKING: grant applications open 15 Oct"* (upcoming) → fresh → passes.
- **Remedy:** **`prefilter.py`** parses the real date + `days_old` (deterministic).

### 2.8 `contact` (score) — **Weak (deterministic)**
- **Asks:** is there an identifiable/contactable contact?
- **Why weak:** an email/phone is a **literal string**; obfuscation (`nur [at] co [dot] com`)
  defeats an LLM guess.
- **Reason it fails:** Jev "infers" presence; a regex **reads** it. Obfuscation (anti-spam
  formatting) is designed to fool text extraction — Jev has no reason to normalise it.
- **Examples:**
  - *"Contact: nur [at] company [dot] com"* → Jev unsure, `prefilter.py` normalises →
    contact = present.
  - *"For enquiries, email press@company.com"* → regex finds it.
  - *No contact block at all* → `prefilter.py` `has_contact: false` (and the last SMEAM
    verdict showed exactly this: `contact` norm 0.4).
- **Remedy:** **`prefilter.py`** regex (emails/phones/"MEDIA CONTACT").

### 2.9 `not_identifiable` (score) — **Weak (entity extraction)**
- **Asks:** are the issuing org and speakers **not** identifiable?
- **Why weak:** names/designations are **entities** — easy to miss or miscount.
- **Reason it fails:** entity extraction is a structured task; a robust extractor
  (regex + patterns for "said X, title", org + designation) is more reliable than a
  probability from a general classifier.
- **Examples:**
  - *"A spokesman said…"* (no name) → not identifiable.
  - *"Dato' X, CEO of Company Y, said…"* → identifiable (org + speaker + designation).
- **Remedy:** `prefilter.py` entity patterns + Jev.

### 2.10 `unattributed_claims` (score) — **Weak (judgment)**
- **Asks:** are stats/rankings/claims **not** attributed (unsupported "No.1", bare numbers)?
- **Why weak:** spotting "is this claim backed by a source *inside the submission*?" is a
  judgment Jev is okay at but can miss on slipped-in numbers.
- **Examples:**
  - *"We are the fastest-growing company in Malaysia"* (no source) → flagged.
  - *"Malaysia's exports rose 12% (DOSM)"* → attributed → passes.
- **Remedy:** Jev; DeepSeek if the weighted score is borderline; retrieval later.

### 2.11 `no_editorial_value` (score) — **Weak (subjective)**
- **Asks:** does an SME reader learn nothing?
- **Why weak:** "is there a net takeaway?" is subjective and holistic.
- **When it matters:** the overall test is used for the *borderline weighted* band
  (`weighted ∈ [45, 65]`) → DeepSeek gives an independent editorial view; disagreement →
  **EDITOR REVIEW (`BORDERLINE`)**.
- **Examples:**
  - *"We are excited to announce… sign up today"* (no substance) → learn nothing.
  - A gates-passing article scoring `weighted 58` → borderline → second opinion.
- **Remedy:** DeepSeek second opinion **only** when `weighted ∈ [45, 65]` (borderline).

### 2.12 `category_fit` (score) — **Weak (external data)** → now improved
- **Asks:** does it fit NONE of the site's categories?
- **Site categories:** Agriculture, Corporate, Government, Investment, Lifestyle, News,
  Opinion, Property, SME, Technology, Training & Education.
- **Why weak:** needs the taxonomy (now supplied); previously the placeholder list was wrong.
- **Caveat:** "**News**" is broad → almost anything fits → this 8% criterion rarely discriminates.
- **Remedy:** taxonomy in the criterion; Jev decides.

### 2.13 `not_sme_voice` (score) — **Weak (overlap)**
- **Asks:** does it fail to contribute insight (only promoting the sender)?
- **Why weak:** overlaps `no_wider_value` / `is_it_commercial_intent` — partially redundant.
- **Remedy:** Jev; DeepSeek if borderline.

### 2.14 `is_negative_or_attacking` (context) — **Weak (tone)**
- **Asks:** polarity/tone toward an identifiable target.
- **Why weak:** subtle and high-stakes; **not** a gate and **not** weighted.
- **Example:** the SMEAM budget call scored **0.22** — i.e. "advocacy, but not hostile".
- **Remedy:** shown to editors only; never auto-routes.

---

## 3. The remedy ladder (preferred → last resort)

```
exact/deterministic data   ->  prefilter.py (regex/date)     # best: no AI
well-scoped classification ->  Jev (calibrated)              # default judge
ambiguous / evaluative     ->  DeepSeek second opinion       # only weak gates + borderline
truth / legal / advocacy    ->  human (EDITOR REVIEW)         # never automated
```

**Rule of thumb:** if the answer is a **fact a machine can parse/look up**, do it in
**code**; if it's a **judgment about the text**, let **Jev** decide; only when Jev is
**genuinely unsure or the stakes are high** spend an LLM call; and for **truth / legal /
advocacy a human decides**.

---

## 4. How we mitigate the weaknesses (mechanics)

- **Pattern 1 — DeepSeek preprocess** (every article): clean / translate / extract
  before Jev judges, so Jev sees tidy input (helps Malay, messy forwards). Fail-safe:
  raw text on error.
- **Pattern 2 — DeepSeek second opinion** (`filter.py::assist`): only for the **weak
  gates** — `_WEAK_GATES = ("no_wider_value", "not_geographically_relevant", "defamatory",
  "political")` — when Jev is **ambiguous (noul ∈ [0.5, 0.85))** or the gate fired, plus
  the overall editorial test when **weighted ∈ [45, 65]**. It can only **escalate**
  (never downgrade) and is **fail-safe** (LLM error → Jev's verdict stands).
- **No-LLM mode** (`ENABLE_LLM_ASSIST=false`): replaces Pattern 2 with a deterministic
  rule (`filter.py::_route_ambiguity`) — ambiguous weak gate or borderline weighted →
  **EDITOR REVIEW** ("uncertainty goes to a human").
- **Deterministic checks** (`prefilter.py`): dates, contacts, sponsored strings — the
  exact-data weaknesses.
- **Human (EDITOR REVIEW)**: safety/reputation, genuine ambiguity, borderline quality,
  missing materials, and anything needing truth verification.

> **Deliberately NOT second-opinioned:** `not_sme_relevant` and
> `is_it_commercial_intent` — these stay **pure Jev** (calibrated routing), plus all 8 scores.

---

## 4.5 A full walkthrough — the SMEAM "Budget 2027" article (real)

This shows the mechanism end-to-end, and *where* Jev was weak.

**Step 1 — DeepSeek preprocess:** cleans the text, extracts headline
*"OUR CALL FOR BUDGET 2027…"*, orgs `[SMEAM, SME Malaysia]`, notes *no contacts supplied*.

**Step 2 — Jev battery (one call, 15 questions):** returns, among others:

| Question | noul | reading |
|---|---|---|
| `not_sme_relevant` | 0.01 | clearly on-topic |
| `no_wider_value` | 0.03 | clearly has wider value |
| `is_it_commercial_intent` | 0.04 | not commercial |
| `defamatory` | 0.06 | not attacking anyone |
| `political` | **0.63** (old criterion) | **ambiguous → DeepSeek** |
| `category_fit` | 0.02 | fits a category |

**Step 3 — decide():** no gate ≥ 0.85; weighted = **84 ≥ 60** → would be **ACCEPT**.

**Step 4 — assist() (old criterion):** `political` is a *weak gate* and it's *ambiguous*
(0.63 ∈ [0.5, 0.85)). DeepSeek gets the same question+criteria+0.63, returns
`{judgment: true, reason: "...explicitly an advocacy document... 'OUR MESSAGE TO
GOVERNMENT'..."}` → **escalates ACCEPT → EDITOR REVIEW `POLITICAL`**.

**Step 5 — the fix:** we narrowed the `political` criterion (Option B) so constructive
policy calls are explicitly NOT advocacy. Re-run:

| Question | noul | reading |
|---|---|---|
| `political` | **0.04** | no longer flagged |
| outcome | — | **ACCEPT** (weighted 83) |

**Lesson:** Jev wasn't "wrong" in a way we could trust blindly — it was *unsure* (0.63),
and DeepSeek's second opinion agreed under the *old*, over-broad wording. Fixing the
**rubric** fixed both. Other fragile cases (e.g. a genuinely partisan attack) still
escalate to a human.

---

## 5. Code references

| Concern | Where |
|---|---|
| Gates / scores / criteria / labels | `filter.py` (`GATES`, `SCORES`, `EXTRA`, `GATE_LABELS`, `GATE_OUTCOMES`) |
| Weak-gate list | `filter.py::_WEAK_GATES` |
| Second opinion + escalation | `filter.py::assist()` |
| No-LLM deterministic router | `filter.py::_route_ambiguity()` |
| DeepSeek calls | `filter_llm.py::preprocess()` / `second_opinion()`; `prompts/filter_preprocess.txt`, `prompts/filter_second_opinion.txt` |
| Deterministic checks | `prefilter.py` |
| Thresholds / bands | `config.py` (`GATE_THRESHOLD`, `ACCEPT_THRESHOLD`, `LLM_GATE_BAND`, `LLM_WEIGHTED_BAND`) |

---

## 6. Worked examples at a glance

| Example | Filter | Jev | Outcome | Lesson |
|---|---|---|---|---|
| CelcomDigi consumer telco launch | `not_sme_relevant` | 0.87 | **REJECT** | Jev strong on topic |
| "Acme appoints a manager" | `no_wider_value` | ~0.68 | REJECT (via DeepSeek) | judgment → needs 2nd opinion |
| "Company X wins Top Employer award" | `no_wider_value` | high | REJECT | single-company, no peer lesson |
| US small-business tax overhaul | `not_geographically_relevant` | ~0.60 | review / flag | world knowledge → 2nd opinion |
| EU carbon-border adjustment (CBAM) | `not_geographically_relevant` | unsure | passes (relevant) | under-flag risk; know your exporters |
| "Milk formula unsafe" viral claim | `defamatory` | risk prob | **EDITOR REVIEW** | cannot fact-check → human |
| SMEAM "Budget 2027 call" | `political` | 0.63 → **0.04** | EDITOR REVIEW → **ACCEPT** | narrowed criterion fixed the over-flag |
| "Vote out the worst government" | `political` | high | EDITOR REVIEW | partisan/attacking stays human |
| "Join workshop on 3 Sep" (no year) | `not_current` | unsure | uses `prefilter.py` | exact data → code |
| `nur [at] co [dot] com` | `contact` | unsure | uses `prefilter.py` | literal string → regex |
| "No contact block at all" | `contact` | — | `has_contact:false` | exact data → code |
| Genuine product-news PR | `is_it_commercial_intent` | ~0.7 | passes (thr 0.85) | normal PR language ≈ noise |
| "50% OFF ERP this month" | `is_it_commercial_intent` | ~0.98 | REJECT | lexical cue, Jev strong |

---

## 7. The design principle worth remembering

> **Jev routes what it can judge; code fixes what is knowable; a second model helps on
> ambiguous judgment; and a human decides truth, safety, and everything genuinely
> arguable.**

### 7.1 Recent change worth remembering

The **`political`** criterion was **narrowed (Option B)**: it now targets **partisan/
attacking** politics + **religion/royal** sensitivity, and explicitly lets **constructive
policy proposals/calls from industry bodies or SMEs auto-pass**. This removed a real
false-positive (the SMEAM Budget 2027 proposal) while keeping the sensitive triggers.
See `docs/FILTER-REVIEW.md` (G5) and `docs/FILTER-WORKFLOW.md` (worked examples C / C2).