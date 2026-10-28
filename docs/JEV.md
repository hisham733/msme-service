# Jev (TypeSafe System One) — Input / Output Reference

How the MSME editorial filter uses **Jev** to judge one archived article, with a
full worked example. The filter implementation is in `filter.py` (inside the combined app on `:8899`).

---

## 1. What Jev is

Jev is TypeSafe's flagship **System One** model — the first System One model. It
makes **fast, structured decisions for software**, not text for humans to read.
You send a **state** and typed **questions**; you get back **typed answers and
probabilities** — no prose to parse. (The name comes from Kahneman's *Thinking,
Fast and Slow*: fast, intuitive judgments.)

Jev is **text-only**: it evaluates strings / JSON / arrays of text. Images, audio
and video are not supported — which is why image checks (`hasPic`, `hasLogo`,
`hasImageInArticle`) live in the **receive** stage, not the filter.

### Primitives — we use only **Noul**

| Primitive | Question | Returns |
|---|---|---|
| Choice | pick one option from a list | `choice`, `probabilities`, `confidence` |
| Score | rate on a rubric | `score`, `probabilities`, `confidence` |
| **Noul** | **is this true? (yes/no)** | **`noul` (0–1)** |

A **Noul** value is the **probability that the answer is "yes"** (0 = no, 1 = yes).
There is **no separate `confidence`** for a Noul — the probability already carries
the uncertainty (0.5 = the model is torn). Optional `criteria` describe what a
yes and a no mean.

---

## 2. Endpoint, auth, model

```http
POST https://api.typesafe.ai/v1/systemone
Authorization: Bearer <TYPESAFE_API_KEY>
Content-Type: application/json
```

- `model`: `jev-latest` (from `config.JEV_MODEL`).
- Base URL from `config.TYPESAFE_BASE_URL`.
- You choose the **question ids**; they are **not sent to the model**, and answers
  come back under the same ids.

---

## 3. Minimal example (one Noul)

**Request**

```json
{
  "state": "I have asked three times now. Can I please just talk to a real person?",
  "model": "jev-latest",
  "questions": {
    "is_human_escalation": {
      "type": "noul",
      "instructions": "Is the customer asking for a human agent?"
    }
  }
}
```

**Response**

```json
{
  "model": "jev-1.13.0",
  "answers": {
    "is_human_escalation": { "type": "noul", "noul": 0.99 }
  },
  "usage": { "input_tokens": 360, "output_tokens": 39 }
}
```

---

## 4. The full MSME battery — 13 Noul questions

The filter asks **5 hard gates + 8 scored criteria = 13 Noul questions in one
request**. Gates are checked first (fail-fast); scores build the weighted
average. Listed in official guideline filter order.

### 4.1 Hard gates (`GATES` in `filter.py`) — any ≥ its threshold → REJECT

**`not_sme_relevant`** · display "Not SME-relevant" · default threshold 0.85
- **Instructions:** Is this submission not relevant to SMEs or the wider business ecosystem — for example, does it lack an SME, policy, financing, trade, technology, workforce or market-access angle?
- **criteria.true:** Off-topic for an SME/business audience: consumer, lifestyle, entertainment, celebrity or sports content aimed at the general public; self-promotional company news with no sector or ecosystem bearing (internal awards, office moves, personal milestones, venue/product plugs); personal-finance, academic/medical research, or product reviews unrelated to running an SME.
- **criteria.false:** Relevant: affects how SMEs operate, earn, compete or comply — financing/capital access, government policy & regulation, tax, trade & exports, market access, digitalisation/technology, talent & workforce, supply chain/logistics, cost of doing business; industry or sector development with an SME angle. Factual government policy counts (partisan politics is a separate gate).

**`no_wider_value`** · display "Single-company / no wider value" · default threshold 0.85 → **REJECT**
- **Instructions:** Is this a single-company or niche story that offers no wider development, lesson or perspective for other SME readers?
- **criteria.true:** Focused on one company's own product, award, appointment or internal news with nothing the wider SME community can learn or use. Merely being 'about an SME' is not enough.
- **criteria.false:** Communicates a wider development, trend, lesson or perspective relevant to SMEs beyond the one sender.

**`is_it_commercial_intent`** · display "Primarily commercial" · default threshold 0.85
- **Instructions:** Does this submission primarily hard-sell a particular product or service — content centred on discounts, sales offers, product promotion or direct customer acquisition — rather than merely mention a product or service as part of a wider development relevant to SME readers?
- **criteria.true:** Primarily hard-selling the sender's product or service: content centred on discounts, deals, pricing, sales offers, 'buy now'/'register now' offers, product promotion, or direct customer acquisition — with little or no wider SME-relevant development.
  - examples: `"50% OFF our ERP this month — sign up now" with no other news`; `A page of superlatives, pricing and CTAs with zero factual milestone`; `A pure event flyer that is only ticket price + register-now, no editorial substance`
- **criteria.false:** A product or service MAY be mentioned when it forms part of a wider development relevant to SME readers. Genuine news/editorial where the product, service or event is context within a wider SME-relevant development — INCLUDING a paid workshop/conference that carries substantive industry content (insights, strategies, speakers, agenda) — does NOT trigger this. An ordinary PR/business mention alone must not trigger it.
  - examples: `A genuine expansion/launch announcement with facts`; `The Pos Malaysia SME Jumpstart Workshop — paid, but a substantive editorial write-up`; `A free public briefing, a policy date, or a published report with no commercial ask`
- **Note:** guideline-aligned (hard-sell only); the earlier *paid-event* and *sponsored/advertorial/backlink* clauses were **removed** from this gate.

**`not_geographically_relevant`** · display "Not geographically relevant" · default threshold 0.85
- **Instructions:** Is this an overseas or international development that has no meaningful relevance to Malaysian SMEs, ASEAN business, trade or accessible markets?
- **criteria.true:** Overseas corporate announcements, or foreign/general news, with no Malaysian, ASEAN or regional SME angle and no accessible-market or trade relevance.
- **criteria.false:** Malaysia-first content; or an international development with meaningful relevance to Malaysian SMEs, ASEAN business, trade or accessible markets — including a clearly transferable business impact on Malaysian/ASEAN SMEs. (Geographic scope only; topical SME relevance is the separate `not_sme_relevant` gate.)

**`defamatory`** · display "Defamation risk" · default threshold 0.85 → **EDITOR REVIEW**
- **Instructions:** Does this contain potentially defamatory allegations, unsubstantiated accusations, obvious misinformation, discriminatory material, or other significant legal or reputational concerns?
- **criteria.true:** Accusations/attacks without evidence; defamatory or discriminating claims; obvious misinformation; illegal/gambling/MLM content; other significant legal or reputational risk.
- **criteria.false:** Clean factual announcement with attributed, evidence-based statements.

**`political`** · display "Political or advocacy" · default threshold 0.85 → **EDITOR REVIEW**
- **Instructions:** Is this partisan/electoral politics, an advocacy piece that attacks/blames/campaigns against a party, leader or the government, or content that disparages religion or challenges Malaysia's royal institution — rather than factual government policy or a constructive policy proposal?
- **criteria.true:** ANY of: (a) party campaign material, endorsements or partisan/electoral messaging (including partisan/bylined opinion); (b) advocacy that attacks, condemns, blames or campaigns against a political party, leader or the government, or takes a partisan side; (c) disparaging, mocking, insulting or attacking any religion, or inflaming religious sensitivities; (d) questioning, challenging or insulting Malaysia's royal institution or similar sedition-sensitive content. Merely mentioning religion or a ruler in a factual, respectful policy context does NOT count.
- **criteria.false:** Factual government policy/regulatory development, OR a constructive policy proposal/call from an industry body, association, company or SMEs (e.g. a Budget recommendation asking the government to act) — with no partisan/electoral angle, no attack/blame on a party/leader, and no disparagement of religion or the royal institution.

### 4.2 Scored criteria (`SCORES` in `filter.py`) — %-weights sum to 100

Each is a **negative** Noul: the good value is the **"no" side** `1 − noul`, times
its **% weight**. A HIGH NO% = good.

**`no_substance`** (17%) — Is there NOT enough factual material to construct a meaningful article from the submission alone — no clear development, context or supporting detail?
- true: A bare announcement or pitch with almost no detail — e.g. 'Company X is excited to announce its new product' — nothing to build a story from.
- false: A clear development plus context and supporting detail — enough to write the article from the submitted material alone, WITHOUT adding outside facts.

**`not_identifiable`** (17%) — Are the issuing organisation and quoted speakers NOT identifiable — no named organisation, and no named speakers or designations?
- true: Anonymous or unattributed: the issuing organisation is not clearly named, and no speakers/quotes are named with designations.
- false: The issuing organisation is clearly identifiable — that alone is enough when no speakers are quoted. Where speakers/quotes are present, they are named with designations. (Sourcing of statistics/claims is a separate check.)

**`unattributed_claims`** (17%) — Are the statistics, rankings, performance or market claims NOT attributed — unsupported superlatives ('No.1', 'leading', 'fastest-growing') or bare numbers presented as fact, with no source in the submitted material?
- true: A factual or market CLAIM is presented as fact with no attribution in the submission — e.g. 'No.1 in Malaysia', 'fastest-growing', or a bare statistic. A superlative that carries NO factual/market claim does NOT count.
- false: All figures, rankings and claims are contained in, or attributable to, the submitted material. Self-reported figures present in the submission count as attributed; this is NOT a fact-check.

**`not_current`** (8%) — Is this significantly outdated with no new development (a long-past event re-sent)?
- true: Stale — a clearly long-past event or date with no new information to make it current.
- false: Fresh — announced recently or upcoming; or evergreen insight that is still useful.

**`no_editorial_value`** (8%) — Overall, is there nothing an SME reader learns from this submission — the only meaningful takeaway being a sales message about the sender's product or service?
- true: The net takeaway is a sales or registration message ('come buy / register / sign up / visit the booth'); an SME reader gains no useful editorial value from the piece as a whole.
- false: An SME reader learns something useful about SMEs, policy, markets or the economy — or gains a meaningful business update — even if a product or event is mentioned.

**`contact`** (8%) — Is there NO named, identifiable, contactable contact person/organisation?
- true: No identifiable or contactable contact.
- false: Named person with role and contact details (or a body that names an official contact).

**`category_fit`** (8%) — Does this fit NONE of the site's categories? (Agriculture, Corporate, Government, Investment, Lifestyle, News, Opinion, Property, SME, Technology, Training & Education)?
- true: Fits none of the site categories.
- false: Clearly fits a defined category.

**`not_sme_voice`** (17%) — Does this submission fail to contribute useful knowledge, experience or perspective to the wider SME community — leaving only promotion of the sender's own product, service or business?
- true: Pure promotion with no peer takeaway: product/service advertising, 'buy now' / pricing / sales offers, or company-only news other SMEs cannot learn or act on ('our product is the best').
- false: Contributes genuine value to the wider SME community — shares experience, lessons, market insight, opinion or a meaningful business update that other SMEs gain from. A product, service or the sender's own business MAY be mentioned as context; that alone must NOT lower this score.

**Weights:** 17 + 17 + 17 + 8 + 8 + 8 + 8 + 17 = **100**.

---

## 5. Worked example A — the real Pos Malaysia article → **REJECT**

Source: `delet/unused/test-articles/pos-malaysia-sme-jumpstart-workshop.md` (moved for review) (a paid workshop
promo — tickets RM90, registration closing date, goodie bags).

### 5.1 Request (as `filter.py` sends it)

`state` (the article with metadata; `bodyText` is trimmed to ~12,000 chars — shown
here abridged):

```json
{
  "state": {
    "subject": "Pos Malaysia launches SME Jumpstart Workshop 2026",
    "from": "Corporate Communications",
    "date": "24 September 2026",
    "bodyText": "KUALA LUMPUR, 24 SEPTEMBER 2026 - The SME Jumpstart Workshop 2026 will equip Malaysian SMEs and entrepreneurs with practical insights into direct-to-consumer strategies, digital commerce, customer retention, logistics and fulfilment. ... Organised by Pos Malaysia and supported by title partner ZUS Coffee ... Participants will also receive a Brew Passport ... redeemed for an exclusive goodie bag containing complimentary products, special offers and partner giveaways. ... Tickets are priced at RM90, with registration closing on 30 September 2026. Places are limited."
  },
  "model": "jev-latest",
  "questions": {
    "not_sme_relevant":            { "type": "noul", "instructions": "Is this submission not relevant to SMEs or the wider business ecosystem...?", "criteria": { "true": "...", "false": "..." } },
    "is_it_commercial_intent":     { "type": "noul", "instructions": "Is this submission primarily commercial...?" },
    "not_geographically_relevant": { "type": "noul", "instructions": "Is this an overseas or international development that has no meaningful relevance...?" },
    "defamatory":                  { "type": "noul", "instructions": "Does this contain potentially defamatory allegations...?" },
    "political":                   { "type": "noul", "instructions": "Is this partisan/electoral politics, an advocacy piece that attacks/blames/campaigns against a party/leader/government, or content that disparages religion or challenges the royal institution..." },
    "no_substance":                { "type": "noul", "instructions": "Is there NOT enough factual material..." },
    "not_identifiable":            { "type": "noul", "instructions": "Are the issuing organisation and quoted speakers NOT identifiable...?" },
    "unattributed_claims":         { "type": "noul", "instructions": "Are the statistics, rankings, performance or market claims NOT attributed...?" },
    "not_current":                 { "type": "noul", "instructions": "Is this significantly outdated with no new development...?" },
    "no_editorial_value":          { "type": "noul", "instructions": "Overall, is there nothing an SME reader learns from this submission...?" },
    "contact":                     { "type": "noul", "instructions": "Is there NO named, identifiable, contactable contact person/organisation?" },
    "category_fit":                { "type": "noul", "instructions": "Does this fit NONE of the site's categories (Agriculture, Corporate, Government, Investment, Lifestyle, News, Opinion, Property, SME, Technology, Training & Education)?" },
    "not_sme_voice":               { "type": "noul", "instructions": "Does this submission fail to contribute useful knowledge, experience or perspective..." }
  }
}
```

> All 13 questions are sent with their full `criteria` from §4; abbreviated here
> for readability. The ids are ours and are not sent to the model.

### 5.2 Response

```json
{
  "model": "jev-1.13.0",
  "answers": {
    "not_sme_relevant":            { "type": "noul", "noul": 0.06 },
    "is_it_commercial_intent":     { "type": "noul", "noul": 0.93 },
    "not_geographically_relevant": { "type": "noul", "noul": 0.04 },
    "defamatory":                  { "type": "noul", "noul": 0.02 },
    "political":                   { "type": "noul", "noul": 0.03 },
    "no_substance":                { "type": "noul", "noul": 0.30 },
    "not_identifiable":            { "type": "noul", "noul": 0.20 },
    "unattributed_claims":         { "type": "noul", "noul": 0.25 },
    "not_current":                 { "type": "noul", "noul": 0.05 },
    "no_editorial_value":          { "type": "noul", "noul": 0.55 },
    "contact":                     { "type": "noul", "noul": 0.40 },
    "category_fit":                { "type": "noul", "noul": 0.10 },
    "not_sme_voice":               { "type": "noul", "noul": 0.70 }
  },
  "usage": { "input_tokens": 4210, "output_tokens": 240 }
}
```

*(Illustrative values; the real run returned a high commercial/advertorial score.)*

### 5.3 Decision (code, in `filter.decide`)

1. **Gates fail-fast** — `is_it_commercial_intent = 0.93 ≥ 0.85` → **REJECT** with
   reason `IS_IT_COMMERCIAL_INTENT`. The weighted score is **never computed**.
2. A genuine PR scores ~0.02–0.15 on the gates, so normally none fires.

**Outcome:** `REJECT (IS_IT_COMMERCIAL_INTENT)`.

---

## 6. Worked example B — a genuine government PR → **ACCEPT**

State: "Fwd: [Press Release] MITI announces RM500m grant for SME digitalisation"
(a dateline, attributable quotes, real development, no commercial ask).

### Response (illustrative)

```json
{
  "model": "jev-1.13.0",
  "answers": {
    "not_sme_relevant":            { "type": "noul", "noul": 0.03 },
    "is_it_commercial_intent":     { "type": "noul", "noul": 0.07 },
    "not_geographically_relevant": { "type": "noul", "noul": 0.02 },
    "defamatory":                  { "type": "noul", "noul": 0.01 },
    "political":                   { "type": "noul", "noul": 0.05 },
    "no_substance":                { "type": "noul", "noul": 0.10 },
    "not_identifiable":            { "type": "noul", "noul": 0.08 },
    "unattributed_claims":         { "type": "noul", "noul": 0.20 },
    "not_current":                 { "type": "noul", "noul": 0.05 },
    "no_editorial_value":          { "type": "noul", "noul": 0.15 },
    "contact":                     { "type": "noul", "noul": 0.30 },
    "category_fit":                { "type": "noul", "noul": 0.05 },
    "not_sme_voice":               { "type": "noul", "noul": 0.12 }
  },
  "usage": { "input_tokens": 3120, "output_tokens": 210 }
}
```

### Decision

**Gates:** all five `< 0.85` → no gate fires.

**Weighted score:** good value = `1 − noul`, × % weight (denom 100):

| Criterion | noul | norm = 1−noul | weight | norm × weight |
|---|---|---|---|---|
| no_substance | 0.10 | 0.90 | 17 | 15.30 |
| not_identifiable | 0.08 | 0.92 | 17 | 15.64 |
| unattributed_claims | 0.20 | 0.80 | 17 | 13.60 |
| not_current | 0.05 | 0.95 | 8 | 7.60 |
| no_editorial_value | 0.15 | 0.85 | 8 | 6.80 |
| contact | 0.30 | 0.70 | 8 | 5.60 |
| category_fit | 0.05 | 0.95 | 8 | 7.60 |
| not_sme_voice | 0.12 | 0.88 | 17 | 14.96 |
| **total** | | | **100** | **87.10** |

`weighted ≈ 87 ≥ ACCEPT_THRESHOLD (60)` → **ACCEPT**.

---

## 7. How the verdict is computed (summary)

```python
# 1) HARD GATES — fail-fast: any gate >= ITS OWN threshold -> REJECT
for name, q in gates().items():
    if answer[name].noul >= q["threshold"]:      # default 0.85, editable per gate
        return REJECT, name.upper()

# 2) WEIGHTED SCORE — scores are NEGATIVE nouls; the good side is (1 - noul)
total = Σ (1 - noul_i) * weight_i
denom = Σ weight_i                               # 100
weighted% = round(total / denom * 100)

# 3) VERDICT
if weighted% >= ACCEPT_THRESHOLD:   # 60
    return ACCEPT
else:
    return REJECT (LOW_WEIGHTED_SCORE)
```

- **Fail-safe:** any Jev error → **REJECT**, never auto-accept (`filter.py` `_post`/`judge`).
- **Weights** are editable **percentages** (should sum to 100).
- **Thresholds** are editable **per gate** (default `GATE_THRESHOLD = 0.85`).

---

## 8. Good to know

- **Noul = the answer and the certainty in one.** Near 1 = strong yes, near 0 =
  strong no, near 0.5 = the model is unsure. It is the probability the answer is
  **yes**, not a degree scale.
- **No `confidence` on Noul.** Only Choice/Score return `confidence`. If you want
  a confidence-style number for a Noul, use `|2p − 1|` (0 at p=0.5, 1 at p=0 or 1).
  ⚠️ The current `judge()` computes a mean of `answer["confidence"]`, which Noul
  answers don't carry — so the verdict's `confidence` field is effectively **0.0**.
- **Thresholds are yours and scale with risk.** Raise when a false yes is
  expensive; lower when a false no is expensive (safety categories). You can set a
  lower `threshold` on `political`/`defamatory` to over-flag rather than miss.
- **One request, all questions in parallel and isolated.** Adding questions barely
  changes response time, and questions don't interfere (no "context rot").
- **Atomic questions, composed in code.** Each Noul asks one specific thing; the
  weighting/threshold logic lives in `filter.decide`, so priorities change without
  rewriting prompts (this is why the battery is 13 small questions, not one big one).
- **Text-only.** Images are handled in the receive stage.
- **Calibration caveat.** Probabilities are calibrated *across groups* of
  predictions; that doesn't guarantee an individual answer is correct.
- **Cost/usage.** Every response includes `usage` (`input_tokens`, `output_tokens`).
  TypeSafe pricing is input-token based (Jev output is minimal — no prose).
- **Model version** is returned in the response (`"model": "jev-1.13.0"`), useful to
  record with each verdict for reproducibility.

### Where it lives in the code
| Concern | Location |
|---|---|
| Build the `state` | `filter.py` `build_state()` |
| Build the 13 questions | `filter.py` `build_questions()` + `GATES` / `SCORES` |
| HTTP call + retries | `filter.py` `_post()` |
| Decision logic | `filter.py` `decide()` |
| Full verdict object | `filter.py` `judge()` |
| HTTP API / config UI | `filter_service.py` (`/filter`, `/config.json`, `:8899`) |
| Tuning (live) | `data/filter_settings.json` via `:8899/filter-config.html` |

### Config knobs
- `JEV_MODEL` (default `jev-latest`), `TYPESAFE_BASE_URL`, `TYPESAFE_API_KEY`
- `GATE_THRESHOLD` (global default 0.85) — overridable **per gate**
- `ACCEPT_THRESHOLD` (60)
- Score **% weights** and gate **thresholds** — editable on `:8899/filter-config.html`

---

## 9. Field reference

**Request**
| Field | Type | Notes |
|---|---|---|
| `state` | string / object / array | The content to evaluate. Here: `{subject, from, date, bodyText}` (body ≤ 12,000 chars). |
| `model` | string | `jev-latest`. |
| `questions` | object | Map of `id → question`. |
| `questions[id].type` | string | `"noul"`. |
| `questions[id].instructions` | string | The yes/no question. |
| `questions[id].criteria` | object (optional) | `{true, false}` descriptions of the boundary. |

**Response**
| Field | Type | Notes |
|---|---|---|
| `model` | string | Model version used (e.g. `jev-1.13.0`). |
| `answers` | object | Map of `id → answer`. |
| `answers[id].type` | string | `"noul"`. |
| `answers[id].noul` | number 0–1 | Probability the answer is yes. |
| `usage.input_tokens` | int | Input tokens billed. |
| `usage.output_tokens` | int | Output tokens. |

---

## 10. Official docs

- Index: https://docs.typesafe.ai/llms.txt
- Intro: https://docs.typesafe.ai/
- System One: https://docs.typesafe.ai/concepts/system-one
- Noul: https://docs.typesafe.ai/primitives/noul
- Quick start: https://docs.typesafe.ai/introduction/quickstart
- Confidence: https://docs.typesafe.ai/confidence
- API reference: https://docs.typesafe.ai/api

---

## 11. DeepSeek assist, outcomes & context question (hybrid)

Jev is the **calibrated router**; DeepSeek (`deepseek-flash`) assists where Jev is
weak. Both are optional (`ENABLE_LLM_ASSIST`, default on).

**Pattern 1 — preprocess (every article).** DeepSeek cleans the text, translates
Malay → English, and extracts metadata `{orgs, speakers, contacts, dates, links,
claims}` before Jev judges. Fail-safe: on error the raw text is used.

**Pattern 2 — second opinion (only where needed).** DeepSeek re-judges:
- a **weak gate** when Jev is ambiguous (noul in `LLM_GATE_BAND`, default 0.5–0.85)
  or when the gate fired (to produce a rationale for the editor);
- the **overall editorial test** when the weighted score is borderline
  (`LLM_WEIGHTED_BAND`, default 45–65).
Fusion: agreement acts; if the LLM flags a defect in an ambiguous case it escalates
(review gate → EDITOR REVIEW, reject gate → REJECT). Disagreement on the borderline
band → EDITOR REVIEW.

**Outcomes:** `ACCEPT` · `EDITOR REVIEW` · `REJECT` (+ `HOLD` on the receive side).
- `defamatory` and `political` gates → **EDITOR REVIEW** (a human decides; the AI
  cannot verify truth and must not auto-publish).
- all other gates → **REJECT**; weighted ≥ 60 → ACCEPT.

**Context question** (not a gate, not weighted): `is_negative_or_attacking` — is the
tone negative/attacking toward an identifiable target? Shown to editors.

**Deterministic checks** (code, not AI): date staleness, contacts (regex),
backlink/SEO/promo-code strings. Exposed in the verdict as `deterministic`.

> ⚠️ **Jev cannot fact-check.** Without web retrieval, no model here can verify that
> a claim is true. Defamation/misinformation is treated as a **risk flag** for a human
> editor; accuracy verification is a separate (human or retrieval) step.
