# Filter Review — 15 Rules (editable)

> **How to use this file:** For each rule, read the current logic + sample verdict,
> then fill in the **Your call** line: `OK` / `EDIT` / `DROP` and any corrected
> wording. We'll apply your decisions to `filter.py`.

**Legend for "Needs data?":**

- 🧠 **AI** — reading-comprehension judgment; Jev stays (no data can replace it)
- 🔌 **Data** — could be deterministic if we get the data (site index, categories, regex)
- ✅ **Receive** — already handled upstream by the receive pipeline

---

## 5 HARD GATES (noul · each gate has its own threshold, default 0.85 → REJECT)

Listed in **official guideline filter order** (#2, #4, #11, #14, #15).

---

### G1 · `not_sme_relevant` (#2) (was `no_relevance`)

- **Type:** gate (noul) · fires REJECT if ≥ **0.85**
- **Current logic:** *Is this submission NOT relevant to SMEs or the wider business ecosystem — no SME, policy, financing, trade, technology, workforce or market-access angle?* **(topic only — geography is G3)**
  - true: "Off-topic for an SME/business audience: consumer/lifestyle/entertainment/celebrity/sports; self-promo with no sector bearing; personal-finance, academic/medical or product reviews."
  - false: "Affects how SMEs operate/earn/compete/comply — financing, policy & regulation, tax, trade & exports, market access, digitalisation, talent, supply chain, cost of doing business; industry/sector development with an SME angle."
- **Needs data?:** 🧠 AI
- **Sample verdict:** MITI export PR → `0.07` (passes). Off-topic consumer piece → `0.92` (REJECT).

**Your call:** `___OK__` (OK / EDIT / DROP + wording)

---



### G1b · `no_wider_value` (NEW)

- **Type:** gate (noul) · fires REJECT if ≥ **0.85**
- **Current logic:** *Is this a single-company or niche story that offers no wider development, lesson or perspective for other SME readers?*
  - true: "Focused on one company's own product, award, appointment or internal news with nothing the wider SME community can learn or use. Merely being 'about an SME' is not enough."
  - false: "Communicates a wider development, trend, lesson or perspective relevant to SMEs beyond the one sender."
- **Needs data?:** 🧠 AI
- **Notes:** enforces "about an SME ≠ meaningful to SME readers". Routed REJECT.

**Your call:** `_____` (OK / EDIT / DROP + wording)

---

### G2 · `is_it_commercial_intent` (#4) — aligned to the guideline

- **Type:** gate (noul) · fires REJECT if ≥ **0.85**
- **Current logic:** *Does this submission primarily **hard-sell a particular product or service** — content centred on discounts, sales offers, product promotion or direct customer acquisition — rather than merely mention a product/service as part of a wider development relevant to SME readers?*
  - true: "Primarily hard-selling the sender's product/service — discounts, deals, pricing, sales offers, 'buy now'/'register now', product promotion, direct customer acquisition, with little/no wider SME-relevant development."
  - false: "A product or service **may be mentioned** when it forms part of a wider development relevant to SME readers. Genuine news/editorial (the product/service/**event as context**) does NOT trigger this — **including a paid workshop/conference with substantive industry content**."
- **Needs data?:** 🧠 AI
- **Note:** the guideline's Commercial Intent covers **hard-sell only**. The earlier extra clauses (**paid event/workshop** and **sponsored/advertorial/backlink/guaranteed-publication**) were our additions and have been **removed** from this gate. Sponsored/backlink strings are still surfaced as a deterministic signal (`prefilter.py`) for editors.
- **Sample verdict:** "50% OFF ERP" → `0.99` (REJECT). **Pos Malaysia SME Jumpstart Workshop (paid, but substantive)** → `0.12` (**ACCEPT**, w=86). MITI export PR → passes.

**Your call:** `__OK___` (OK / EDIT / DROP + wording)

---



### G3 · `not_geographically_relevant` (#11) — NEW (split out from #2)

- **Type:** gate (noul) · fires REJECT if ≥ **0.85**
- **Current logic:** *Is this an overseas/international development with NO meaningful relevance to Malaysian SMEs, ASEAN business, trade or accessible markets?*
  - true: "Overseas corporate announcements, or foreign/general news, with no Malaysian/ASEAN/regional SME angle and no accessible-market or trade relevance."
  - false: "Malaysia-first content; or an international development with meaningful relevance to Malaysian SMEs, ASEAN business, trade or accessible markets — including a clearly transferable business impact."
- **Needs data?:** 🧠 AI
- **Sample verdict:** MITI export PR → `0.05` (passes). "US firm opens Nevada office" → `0.90` (REJECT).

**Your call:** `___OK__` (OK / EDIT / DROP + wording)

---



### G4 · `defamatory` (#14) — Safety & Reputation

- **Type:** gate (noul) · fires **EDITOR REVIEW** if ≥ **0.85** *(review gate — routes to a human, not an auto-reject)*
- **Current logic:** *Does this contain potentially defamatory allegations, unsubstantiated accusations, obvious misinformation, discriminatory material, or other significant legal/reputational concerns?*
  - true: "Accusations/attacks without evidence; defamatory or discriminating claims; obvious misinformation; illegal/gambling/MLM content; other significant legal/reputational risk."
  - false: "Clean factual announcement with attributed, evidence-based statements."
- **Needs data?:** 🧠 AI
- **Sample verdict:** Lenovo → `0.02` (clean).

**Your call:** `___ok__` (OK / EDIT / DROP + wording)

---



### G5 · `political` (#15) — Political / Advocacy Content

- **Type:** gate (noul) · fires **EDITOR REVIEW** if ≥ **0.85** *(review gate — routes to a human, not an auto-reject)*
- **Current logic:** *Is this partisan/electoral politics, an advocacy piece that attacks/blames/campaigns against a party, leader or the government, or content that disparages religion or challenges Malaysia's royal institution — rather than factual government policy or a constructive policy proposal?*
  - true: "(a) party campaign material, endorsements, partisan/electoral messaging (incl. partisan/bylined opinion); (b) advocacy that attacks/condemns/blames/campaigns against a party, leader or the government, or takes a partisan side; (c) disparaging/mocking/insulting or attacking any religion; (d) questioning, challenging or insulting Malaysia's royal institution (Agong/Sultans/monarchy) or similar sedition-sensitive content."
  - false: "**Constructive policy proposal/call from an industry body, association, company or SMEs** (e.g. a Budget recommendation asking the government to act), OR factual government policy/regulatory development — with no partisan/electoral angle, no attack/blame on a party/leader, and no disparagement of religion or the royal institution."
  - **Note:** narrowed (Option B) so legitimate SME policy advocacy auto-passes; only partisan/attacking politics + religion/royal sensitivity go to review.
- **Boundary:** merely mentioning religion or a ruler in a factual, respectful policy context does NOT trigger.
- **Needs data?:** 🧠 AI
- **Sample verdict:** Lenovo → `0.01` (not political). Partisan/royal-sensitivity piece → `0.9` (REJECT).

**Your call:** `___OK__` (OK / EDIT / DROP + wording)

---



### ~~`stale`~~ — MOVED to the Weight side as S4 `not_current`

- **Type:** no longer a gate. Timeliness is now a **weighted score** (#10), so a stale piece **lowers the score** instead of hard-rejecting.
- See **S4 · `not_current`** below.

---



## 8 SCORED CRITERIA (noul · phrased NEGATIVELY · the NO side = accept)

Weights sum = **100%**. Each criterion asks the defect ("Is this **NOT** ...?").
The good score = **NO side (1 − noul)**, × its **% weight**, summed → **weighted %**. **HIGH NO% = ready to accept.**

`sme_relevance` was moved out of the scores: SME relevance is now the HARD GATE
`not_sme_relevant` (see G3).

---



### S1 · `no_substance` (was `substance`) — weight **17%**

- **Current logic:** *Is there NOT enough factual material to construct a meaningful article from the submission alone — no clear development, context or supporting detail?*
  - true: "A bare announcement or pitch with almost no detail — 'Company X is excited to announce its new product' — nothing to build a story from."
  - false: "A clear development plus context and supporting detail — enough to write the article from the submitted material alone, WITHOUT adding outside facts."
- **Needs data?:** 🧠 AI
- **Carve:** amount/richness of material only — quote *identifiability* is S2 `not_identifiable`.
- **Sample verdict:** (NO% — high = rich article).

**Your call:** `_____` (OK / EDIT / weight / DROP)

---
### S2 · `not_identifiable` (was `attribution`) — weight **17%**

- **Current logic:** *Are the issuing organisation and quoted speakers NOT identifiable — no named organisation, and no named speakers or designations?*
  - true: "Anonymous or unattributed: the issuing organisation is not clearly named, and no speakers/quotes are named with designations."
  - false: "The issuing organisation is clearly identifiable — that alone is enough when no speakers are quoted. Where speakers/quotes are present, they are named with designations."
- **Needs data?:** 🧠 AI (+ partly regex for "said by X, title")
- **Carve:** source/people identity only — sourcing of statistics/claims is S3 `unattributed_claims`.
**Your call:** `_____` (OK / EDIT / weight / DROP)

---



### S3 · `unattributed_claims` (was `claims_attributed`) — weight **17%**

- **Current logic:** *Are the statistics, rankings, performance or market claims NOT attributed — unsupported superlatives ('No.1', 'leading', 'fastest-growing') or bare numbers presented as fact, with no source in the submitted material?*
  - true: "A factual/market claim is presented as fact with no attribution — e.g. 'No.1 in Malaysia', 'fastest-growing', or a bare statistic. A superlative carrying NO factual/market claim does NOT count."
  - false: "All figures/rankings/claims are contained in or attributable to the submitted material. Self-reported figures count as attributed; not a fact-check."
- **Needs data?:** 🧠 AI
- **Boundary:** sourcing within the submission only — no truth-verification, no outside data.
**Your call:** `_____` (OK / EDIT / weight / DROP)

---



### S4 · `not_current` (was gate `stale`) — weight **8%**

- **Current logic:** *Is this significantly outdated with no new development (a long-past event re-sent)?*
  - true: "Stale — a clearly long-past event or date with no new information to make it current."
  - false: "Fresh — announced recently or upcoming; or evergreen insight that is still useful."
- **Needs data?:** 🧠 AI + 🔌 date field
- **Note:** moved from gate to score — a stale piece now **lowers the weighted %** rather than hard-rejecting.
**Your call:** `_____` (OK / EDIT / weight / DROP)

---



### S5 · `no_editorial_value` (#17 Overall Editorial Test) — weight **8%**

- **Current logic:** *Overall, is there nothing an SME reader learns from this submission — the only meaningful takeaway being a sales message about the sender's product or service?*
  - true: "The net takeaway is a sales/registration message; an SME reader gains no useful editorial value from the piece as a whole."
  - false: "An SME reader learns something useful about SMEs, policy, markets or the economy, or gains a meaningful business update."
- **Note:** holistic (#17) — small weight so it doesn't double-count S8 `not_sme_voice`.
- **Needs data?:** 🧠 AI
**Your call:** `_____` (OK / EDIT / weight / DROP)

---



### S6 · `contact` — weight **8%**

- **Current logic:** *Is there NO named, identifiable, contactable contact person/organisation?*
  - true: "No identifiable or contactable contact."
  - false: "Named person with role and contact details (or a body that names an official contact)."
- **Needs data?:** 🧠 AI + 🔌 regex-checkable (email / phone / "MEDIA CONTACT")
**Your call:** `_____` (OK / EDIT / weight / DROP)

---



### S7 · `category_fit` — weight **8%**

- **Current logic:** *Does this fit NONE of the site's categories?* The site categories are: **Agriculture, Corporate, Government, Investment, Lifestyle, News, Opinion, Property, SME, Technology, Training & Education.**
  - true: "Fits none of the site categories."
  - false: "Clearly fits at least one of the site categories."
- **Needs data?:** 🧠 AI (taxonomy now provided by the site: Agriculture, Corporate, Government, Investment, Lifestyle, News, Opinion, Property, SME, Technology, Training & Education)
**Your call:** `_____` (OK / EDIT / weight / DROP)

---



### S8 · `not_sme_voice` (was `sme_voice`) — weight **17%**

- **Current logic:** *Does this submission fail to contribute useful knowledge, experience or perspective to the wider SME community — leaving only promotion of the sender's own product, service or business?*
  - true: "Pure promotion with no peer takeaway: product/service advertising, sales offers, or company-only news other SMEs cannot learn from."
  - false: "Shares experience, lessons, market insight, opinion or a meaningful business update the SME community gains from. A product/business mention is allowed as context."
- **Needs data?:** 🧠 AI
- **Scope:** any content (value to the SME reader, not authorship); product mention must NOT lower the score.
**Your call:** `_____` (OK / EDIT / weight / DROP)

---



## Weights summary (current)


| Criterion         | Weight | Share of total |
| ----------------- | ------ | -------------- |
| no_substance         | 17%      | 17%            |
| not_identifiable       | 17%      | 17%            |
| unattributed_claims | 17%      | 17%            |
| not_current        | 8%      | 8%             |
| no_editorial_value   | 8%      | 8%             |
| contact           | 8%      | 8%             |
| category_fit      | 8%      | 8%             |
| not_sme_voice     | 17%      | 17%            |
| **Total**         | **100%** | 100%           |


**Accept threshold:** 60% · **Gate threshold:** 0.85

**Final call on weights/thresholds:** `_____`

---



## Decision log


| #   | Rule                      | Your call | Notes                       |
| --- | ------------------------- | --------- | --------------------------- |
| G1  | not_sme_relevant          |           | #2; renamed from no_relevance; topic only (geography = G3) |
| G1b | no_wider_value            |           | NEW; single-company/niche → REJECT ("about an SME" ≠ meaningful) |
| G2  | is_it_commercial_intent   |           | #4; guideline-aligned (hard-sell only). Removed our extra paid-event + sponsored/advertorial clauses |
| G3  | not_geographically_relevant |         | #11; NEW — split out from not_sme_relevant |
| G4  | defamatory                |           | #14                         |
| G5  | political                 |           | #15                         |
| S1  | no_substance              |           | weight 17% (negative noul); renamed from substance; amount only (identifiability = S2) |
| S2  | not_identifiable          |           | weight 17% (negative noul); renamed from attribution; named org alone suffices |
| S3  | unattributed_claims       |           | weight 17% (negative noul); renamed from claims_attributed; self-reported counts, superlative alone doesn't |
| S4  | not_current               |           | weight 8% (negative noul); moved from gate `stale` to score |
| S5  | no_editorial_value           |           | weight 8% (negative noul); #17 Overall Editorial Test, holistic (from editorial_value) |
| S6  | contact                   |           | weight 8% (negative noul)    |
| S7  | category_fit              |           | weight 8% (negative noul) · needs data? |
| S8  | not_sme_voice             |           | weight 17% (negative noul); renamed from sme_voice, any-content scope |


