# N-7 — live examples: one that follows the rule, one that does not (per point)

_Measured 2026-11-07 on the latest **100 published posts** of `malaysiasme.com.my`
(WordPress REST API; 2026-10-07 → 2026-11-06). Method: count H2 headings, split `<p>` paragraphs
with ≥8 words, count words per paragraph, count images (1 featured + in-body). "Chunks" are inferred:
a chunk = 2–3 paragraphs, so **4–5 chunks = 8–15 paragraphs**. Script: `tools/n7_measure.py`._

**The rule (N-7):** 4–5 chunks of 2–3 paragraphs · 1–3 H2 headings for a normal release · paragraphs
~2–3 lines (~35–75 words; the spec targets ~50–60) · 6 images max, 1 normal · long **features** and
**commentary/byline** exempt.

> ⚠ Word-of-caution for the call: over 100 posts the **paragraph median is ~40 words**, not ~56, so
> the "50–60" target in the spec is the point most worth confirming.

---

## 0. What is a "feature"?

A **feature** is a long-form piece — a profile, an interview, an extended event write-up, a photo
essay, or an in-depth explainer — as opposed to a standard press release. The rule **exempts**
features from the 4–5-chunk limit (and the 1–3-heading limit).

### Types of feature (with a live example of each)

| Type | What it is | Live example | Size |
|---|---|---|---|
| **Profile / personality** | one person's story or career | [Puteri Irene — Reinvention Is Real (TalentCorp WIN)](https://www.malaysiasme.com.my/puteri-irene-reinvention-is-real-how-talentcorps-women-industry-network-win-helped-her-turn-a-20-year-career-pause-into-a-new-life-in-ai/) | 34 paras, 5 H2, 8 imgs |
| **Event write-up** | coverage of a conference / expo / ceremony | [Sarawak Targets AI, Semiconductor and Space Economy at IDECS26](https://www.malaysiasme.com.my/sarawak-targets-ai-semiconductor-and-space-economy-growth-at-idecs26/) | 34 paras, 6 H2, 1 img |
| **Photo essay / gallery** | the photographs carry the story | [From Screen to Workplace — MECA IR Convention 2026](https://www.malaysiasme.com.my/from-screen-to-workplace-how-the-meca-ir-convention-2026-brought-industrial-relations-to-life/) | 19 paras, 5 H2, **15 imgs** |
| **Human-interest feature** | a narrative built around people/places | [What Makes a Taste of Home So Special?](https://www.malaysiasme.com.my/what-makes-a-taste-of-home-so-special-three-malaysians-one-restaurant-and-heartwarming-journey-in-barcelona/) | 17 paras, 7 H2, 10 imgs |
| **Explainer / "how-why-what"** | explains a topic in depth | [What Will Keep Malaysia Cool? (HVAC&R)](https://www.malaysiasme.com.my/what-will-keep-malaysia-cool-reimagining-hvacr-for-a-smarter-hotter-future/) | 19 paras, 7 H2, 5 imgs |
| **Report / study feature** | writes up a survey or study | [AI Search Tools May Rely on Marketing Agencies' Own Websites (ALIQ report)](https://www.malaysiasme.com.my/ai-search-tools-may-rely-on-marketing-agencies-own-websites-when-recommending-providers-study-finds/) | 29 paras, 6 H2, 0 imgs |
| **Commentary / opinion** *(separate exempt class)* | an organisation's view on a policy | [Khazanah Research Institute Commentary on Budget 2027](https://www.malaysiasme.com.my/khazanah-research-institute-commentary-on-budget-2027/) | 8 paras, 4 H2, 0 imgs |

**Interview / Q&A:** there is no clean Q&A in this 100-post sample; the "voice" format is covered by
the **commentary/opinion** pieces (which are a separate exempt class, not a feature).

**Proxy caveat:** the spec's measurable filter — **≥17 paragraphs or ≥1,200 words** — is only a rough
net and **over-counts**: many long *press releases* (e.g. “Budget 2027: MATRADE Gets RM60 Million”,
“OCBC Expands Cross-Border Payments”) clear 17 paragraphs but are **not features**. A feature should be
judged by its **editorial form** (profile, event, photo essay, explainer, study), not by length alone.
So treat the "52 of 100 long-form" figure as an upper bound, not a feature count.

**Contrast (a normal release):** [Epson A3 Dye-Sublimation Printer](https://www.malaysiasme.com.my/epson-introduces-its-first-a3-desktop-dye-sublimation-printer/)
— 8 paragraphs, 3 H2, 0 images. Must follow the 4–5-chunk and 1–3 heading rules.

---

## 1. Paragraph length — target ~50–60 words, warn outside 35–75

| | Article | Measured | Why |
|---|---|---|---|
| **Follows** | [#JomLokal MSMEs Record 140% Sales Growth](https://www.malaysiasme.com.my/jomlokal-msmes-record-140-sales-growth-on-tiktok-shop-as-malaysians-buy-local/) | 13 paragraphs, **median 55 words**, 3 H2 | Sits right on the rule's target (~55) |
| **Does not** | [Khazanah Research Institute Commentary on Budget 2027](https://www.malaysiasme.com.my/khazanah-research-institute-commentary-on-budget-2027/) | 8 paragraphs, **median 95.5 words**, 4 H2 | Paragraphs almost twice the target — long walls of text |

## 2. Chunks — 4–5 chunks = 8–15 paragraphs

| | Article | Measured | Why |
|---|---|---|---|
| **Follows** | [Epson A3 Dye-Sublimation Printer](https://www.malaysiasme.com.my/epson-introduces-its-first-a3-desktop-dye-sublimation-printer/) | **8 paragraphs** (≈4 chunks), 3 H2 | Exactly the 4-chunk target |
| **Does not** | [Release: Banking Industry Strengthens SME Support as SME SRF](https://www.malaysiasme.com.my/release-banking-industry-strengthens-sme-support-as-sme-srf/) | **4 paragraphs** (≈2 chunks), 0 H2 | Too short — below the 4-chunk target (should be a *warning*, not a fail, per the rule) |

## 3. Headings (H2) — 1–3 for a normal release

| | Article | Measured | Why |
|---|---|---|---|
| **Follows** | [Lotus's Malaysia & KPDN — JOM Malaysia 2026](https://www.malaysiasme.com.my/lotuss-malaysia-and-kpdn-drive-long-term-growth-for-malaysian-smes-through-jom-malaysia-2026/) | **2 H2**, 9 paragraphs | Inside the 1–3 range |
| **Does not** | [SME Bank — RM2.8 Billion under Budget 2027](https://www.malaysiasme.com.my/sme-bank-welcomes-approximately-rm2-8-billion-in-strategic-initiatives-under-national-budget-2027/) | **6 H2**, only 6 paragraphs | Over-structured: 6 headings on a short release |

## 4. Images — 1 normal, 6 maximum

| | Article | Measured | Why |
|---|---|---|---|
| **Follows (normal)** | [MATRADE — RM453M at SEMICON West 2026](https://www.malaysiasme.com.my/matrade-led-malaysia-pavilion-secures-rm453-million-in-export-deals-at-semicon-west-2026/) | **1 image** (the CEO photo) | Exactly the normal case |
| **Not the normal case** | [AiSED International Conference 2026](https://www.malaysiasme.com.my/aised-international-convention-2026-2-4-dec-2026-harnessing-ai-empowering-innovation-advancing-sustainable-futures/) | **5 images**, 8 paragraphs, 5 H2 | Still inside the 6 cap, but far from the normal 1 |

**Cap check:** **no normal release exceeds 6 images** (0 of 100). The only posts above 6 are **features**
(7, 8, 8, 15, 10 images) — exempt as long-form/photo pieces. So "6 max for releases, 1 normal" holds.

## 5. Features — exempt from the 4–5 chunk rule

| | Article | Measured | Why |
|---|---|---|---|
| **Feature (exempt)** | [Puteri Irene — Reinvention Is Real](https://www.malaysiasme.com.my/puteri-irene-reinvention-is-real-how-talentcorps-women-industry-network-win-helped-her-turn-a-20-year-career-pause-into-a-new-life-in-ai/) | 34 paragraphs, 5 H2, 8 images | A long profile — allowed to be long |
| **Normal release** | [Epson A3 Printer](https://www.malaysiasme.com.my/epson-introduces-its-first-a3-desktop-dye-sublimation-printer/) | 8 paragraphs, 3 H2 | Not a feature — must obey 4–5 chunks |

Another feature: [Sarawak at IDECS26](https://www.malaysiasme.com.my/sarawak-targets-ai-semiconductor-and-space-economy-growth-at-idecs26/)
(34 paragraphs, 6 H2).

---

## 6. Charts — is there any article with a chart?

**Measured result: no.** Across the 100 live pages there are **0 chart images** and **0**
"Chart / Infographic / Figure N / Source:" captions. (An earlier rough count of "16" was a false
positive: the letters *graph* hide inside the word *paragraph*, and *figure* appears as an ordinary
English word.)

The important case is **APAC CEOs** — [live page](https://www.malaysiasme.com.my/apac-ceos-face-ai-and-geopolitical-pressures-but-are-confident-in-navigating-complexities/):
its source had **3 charts**, but the live page has **0 images at all**. So the live site currently
**drops charts**, which is exactly what the N-7 rule says *not* to do ("a chart lives in the body,
never as the main image").

---

## 7. One-line summary per point

| Point | Rule | Live follows | Live does not |
|---|---|---|---|
| Paragraph length | ~50–60, warn 35–75 | #JomLokal (55) | Khazanah (95.5) |
| Chunks | 4–5 chunks (8–15 paras) | Epson (8 paras) | Release: Banking SME SRF (4 paras) |
| Headings | 1–3 H2 | Lotus's (2) | SME Bank (6) |
| Images | 1 normal, 6 max | MATRADE (1) | AiSED (5, still ≤6) |
| Features | exempt | Puteri Irene (34 paras) | Epson is a normal release (not a feature) |
| Charts | chart in body, never main image | — (none on the live site) | APAC dropped its 3 charts |
