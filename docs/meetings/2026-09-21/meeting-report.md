# Meeting Report — AI_News Project Kickoff (MSME × EmpiFlow)

**Date:** Monday, 21 September 2026
**Time:** 3:08 PM – 3:42 PM (recording 34 min 07 s)
**Platform:** Microsoft Teams
**Meeting:** AI News – EmpiFlow
**Prepared by:** MG (EmpiFlow / EF)
**Source of record:** [`MSTeam_transcript_2026_Sept_21.md`](transcript.md) — the full per-speaker transcript (inferred labels; see its header).

## Attendees

| Name | Role | Side |
|------|------|------|
| **Wayne Lim** | Director / Founder | MSME (MALAYSIA SME Media Group) |
| **Ailee** | Editor | MSME |
| **MG OwYong** | Project Manager | EF (EmpiFlow) |
| **Hisham** | Partner / technical | EF (EmpiFlow) |

---

## 1. Meeting Minute

### 1.1 Purpose and framing
EF presented the project kickoff for **AI_News** — the automation of MSME's "news churning" pipeline (filter → repurpose → upload). The MSME editorial guidelines (`.docx`) and the Rival Flow AEO report were the shared basis. EF flagged upfront that the guidelines are **clear to a human but not uniformly operationalisable by an AI**, and proposed to walk the 17 filters one by one.

### 1.2 Stage 1 (Filter) — design and reporting
- EF has tentatively designed Stage 1 as a binary **ACCEPT / REJECT** output.
- EF offered to auto-send MSME a **daily report** (email or WhatsApp): number of articles received, acceptance percentage, and decisions.
- **Wayne** asked to personally review that report during testing, to validate the filter's behaviour. EF agreed.

### 1.3 The core difficulty — subjective filters
- EF explained each filter was scored 1–10 for "operationalisability" (see `analysis/State1_filter.md`). Easy discriminators (e.g. **geographic relevance** — Malaysia/ASEAN) vs hard ones (e.g. **commercial intent**).
- **Hisham** asked whether any historical record exists of *why* items were rejected/held. **Ailee:** no such record exists for Stage 1 (she has before/after **Stage 2** repurposed articles, but not Stage 1 accept/reject logs).
- **Wayne** explained the rejection decision is inherently **subjective and person-dependent** — "the AI modelled after Ailee" ≠ "modelled after Wayne" ≠ a junior's decision. Therefore the AI must be trained on the **general MSME editorial direction**, not on one individual.

### 1.4 EF's proposed approach — score, then train the hard cases
- Each filter produces a **score**; scores roll up to ACCEPT/REJECT, each with a short **reason**.
- Hard cases (e.g. a bank loan program that is *both* commercial *and* SME-relevant) require **training data** — accepted and rejected examples. This is a **later stage**; the first build is rules-based.
- Output framing: "evaluate the performance of this employee" — EF will monitor the AI like a new hire and **upscale** it over time.

### 1.5 ⭐ Wayne's key suggestion — train on the published website
- **Everything already published on malaysiasme.com.my has already passed the editorial guidelines.** Wayne proposed using the live site as the positive training set: build a crawler, sample published articles, and let the AI learn "what passes".
- EF **agreed** and will build a **crawler** to gather a representative sample of published articles as the training/quality reference.

### 1.6 Input handling — links vs attachments
- **Ailee** clarified **Submission Completeness**: an email must contain the **press release + images**. Images supplied with junk filenames (e.g. `DSC1456`) must be **re-labelled** (`MALAYSIA SME_AFFIN`) so they become SEO/AEO assets. If a media kit is only a **link**, the system must follow it.
- **Wayne's staged logic:** many PR emails carry only a hyperlink to a drive (folders labelled "press release" and "photo") instead of attachments.
  - **Phase 1 (simple):** if no attachment → AI sends an **auto-reply** asking the sender to resend as **Word/PDF + photos**.
  - **Phase 2 (upscale):** AI learns to **click the link**, navigate the drive, and pull the files.
- Because these are **unpaid** releases, MSME will not offend submitters, but the **courtesy auto-reply** is still wanted — both to raise article quality and because submitters are **potential customers**.

### 1.7 Data / sample collection — start from today
- Rather than reconstruct history, **Wayne** decided: **MSME will CC/forward incoming press-release emails to EF from today onward.** EF shares a dedicated email/link; MSME adds it to the group chat and CCs EF on selection decisions ("so you have an idea of why it was selected").
- **Hisham** asked for ~20–30 sample emails to capture the **variation** across PR formats. Wayne's approach (live CCs) supersedes a historical pull.
- EF will **human-review** the CC'd emails, then build the base model.

### 1.8 Stage 3 (Repurpose + Upload) — clarification
- EF understood repurposing was followed by **manual** WordPress upload. **Ailee / Wayne** clarified the target is **self-publish to WordPress with zero human involvement**: the AI repurposes, prepares the images, and publishes; if anything goes wrong it is **taken down**. Wayne's guardrail: **3R/4R content (religion, race, royalty)** must never publish — but he expects such content simply won't arise given the SME-benefit editorial premise.
- EF will **scope the first deliverables to Stage 1 (filter) + Stage 2 (repurpose)** — "from the AI perspective they are similar" — and discuss upload/commercialisation later.

### 1.9 Cadence and access
- **Next meeting in ~1 to 1.5 weeks** — EF to return with **either a working product or more questions**.
- **Wayne:** don't wait for a meeting — for quick questions while reviewing emails, **call him directly** (he prefers calls over text); a snapshot + a 1-minute call is fine.

### 1.10 3R / 4R guardrail
- Confirmed as **religion, race, royalty** (Wayne initially mis-stated it as "4R / lawyer / royal family"; clarified: it is the **3R**, and "4R" was his joke about owning a Rolls Royce). **Politics** is also avoided. Business news naturally excludes these; not explicitly in the guidelines because the SME-benefit premise filters them out. Agreed to record it.

### 1.11 Duplication filter
- **Hisham** raised the **duplication** filter: catching an article already published on WordPress. Wayne agreed it is **not easy** — it requires the AI to **keep a database of everything already uploaded**. EF: "we'll see what we can do."

### 1.12 Close
- Both sides expressed enthusiasm. Wayne: develop a good model first, then take on **commercialisation to the market**. Wayne asked EF to **stop recording** and continued off-record with Ailee for a separate personal matter.

---

## 2. ⭐ Agreed "To-Do" / Deliverables for EF

> Agreed in the meeting; owner = EF unless noted.

| # | Action | Owner | Notes / Due |
|---|--------|-------|-------------|
| **EF-1** | Share a **dedicated email/link** and post it in the Teams group chat | EF (MG) | Immediately after the meeting |
| **EF-2** | **Collect incoming press-release emails** CC'd/forwarded by MSME | EF (MG) | Starts from 21 Sep; ongoing |
| **EF-3** | **Human-review** the received emails to learn MSME's accept/reject style | EF (MG) | Before building the model |
| **EF-4** | Build the **Stage 1 filter base model** (generic, from the 17 filters + website reference) | EF | Target ~1–1.5 weeks |
| **EF-5** | Filter output = **ACCEPT / REJECT + short reason** | EF | First cut |
| **EF-6** | Produce a **daily report** (email/WhatsApp): articles received, accept %, decisions | EF | For Wayne to review during testing |
| **EF-7** | Build a **crawler** to sample published website articles as the positive training/quality set | EF | Phase 2 |
| **EF-8** | Prototype **link-vs-attachment detection** + **auto-reply** asking sender for Word/PDF + photos | EF | Phase 1 (simple version) |
| **EF-9** | **Return in ~1–1.5 weeks** with a working product or more questions | EF (MG) | Next meeting |
| **EF-10** | **Scope** the project to Stage 1 (filter) + Stage 2 (repurpose) as the first deliverables | EF | Upload/self-publish scoped later |
| **EF-11** | Explore **duplication detection** — requires a database of already-uploaded articles | EF | Open / research |
| **EF-12** | Record the **3R (religion, race, royalty) + politics** guardrail into the filter design | EF | Confirmed this meeting |

**MSME side (for completeness):** CC/forward incoming press-release emails to EF from today; add EF's address to the group chat; provide before/after Stage 2 articles (Ailee); be available for quick calls (Wayne).

---

## 3. ⭐ Agreed AI_News Project Scope (as of 21 Sep 2026)

### 3.1 In scope
- **Content type:** **unpaid press releases only** (as per the `.docx`).
- **Input channel (primary):** **email** (WhatsApp mentioned but email is the working channel for now).
- **Stage 1 — AI Filtering:** apply the **17 editorial filters** to incoming releases → **ACCEPT / REJECT** (with score and short reason). HOLD / EDITOR REVIEW per the `.docx` remain part of the model.
- **Stage 2 — AI Repurposing:** restructure accepted releases into the **MSME house style** (title, dateline, excerpt, subheaders, quotes, images, categories) — strictly source-faithful.
- **Training strategy:** **rules-based first**, then AI trained on **MSME's published website articles**; a **scored** filter model; deeper training (with accepted/rejected examples) later for subjective filters such as **commercial intent**.
- **Image handling:** use supplied media; **re-label** images into MSME's SEO/AEO asset convention.
- **Link handling (phased):** Phase 1 = detect missing attachment → **auto-reply** for Word/PDF + photos; Phase 2 = AI navigates the link/drive.

### 3.2 Explicitly out of scope (for now)
- **Paid advertorials / sponsored content** (the "paid client" path stays human).
- **Feature / opinion / contributed pieces** (human-written by MSME's own writers).
- **WhatsApp Business API integration** (email is the focus; WhatsApp only as a report channel).
- **Commercialisation to market** — a later phase, after a good model exists.

### 3.3 Deferred / to be scoped
- **Stage 3 — Auto-upload / self-publish to WordPress with zero human involvement.** Agreed as the *target behaviour* conceptually, but EF is scoping the first build to filter + repurpose only.
- **Duplication database** — needs a store of already-published articles.
- **Link/drive navigation** — the "upscale the employee" Phase 2.
- **Editorial guardrails beyond the `.docx`** — the **3R + politics** rule is confirmed but must be encoded.

### 3.4 Editorial guardrails (confirmed)
- Must **benefit the SME** — the core premise that filters most irrelevant content out.
- **3R: religion, race, royalty** — never publish; plus **politics**.
- **Source-faithful** repurposing — no external facts/interpretation (from the `.docx`).
- Images must become **branded, re-labelled media assets** (SEO/AEO value).

---

## 4. Open Questions / Risks (carried forward)

| # | Item | Note |
|---|------|------|
| 1 | **Commercial-intent calibration** | Subjective and person-dependent; needs training examples. First build will be imperfect by design. |
| 2 | **Duplication detection** | Requires an uploaded-article database; feasibility not yet confirmed. |
| 3 | **Link/media-kit navigation** | Complex; deliberately deferred to Phase 2 with the auto-reply workaround in Phase 1. |
| 4 | **No Stage 1 historical data** | MSME has no accept/reject log, so the model is bootstrapped from live emails + the published website. |
| 5 | **Zero-human self-publish** | High-trust behaviour; take-down is the only safety net. EF scoped it out of the first build. |
| 6 | **Name/culture rules** (from prior analysis) | Malay/Indian/Chinese/Western referencing is a known hard AI problem — flag for accuracy testing. |

---

## 5. Next Meeting
- **When:** ~1 to 1.5 weeks from 21 Sep 2026 (early October 2026).
- **Expected output from EF:** a working Stage 1 filter model (or a clear set of follow-up questions).
- **Between now and then:** MSME CCs/forwards press-release emails; EF reviews them; quick questions by phone to Wayne.

---

*Full transcript: [`MSTeam_transcript_2026_Sept_21.md`](transcript.md)*
*Supporting analysis: `../analysis/guideline_analysis.md`, `../analysis/State1_filter.md`, `../analysis/MSME_AI_restructure.md`*
