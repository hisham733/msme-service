# MALAYSIA SME — guideline review, 30 October 2026 (Friday, 2.00 pm)

**Purpose.** Walk through the places where `MALAYSIA SME_AI Editorial Guidelines_Sept 2026` (the
`.docx`) and what the site actually publishes **disagree**, so MSME can either fix the guideline or
confirm the practice. Every item below carries a **traceable example**: the article, its URL slug, and
the actual file names.

**Prepared by:** EF (Empiflow) · **Built from:** 30 raw→published pairs whose images were traced back to
the released files by pixel matching (`analysis/imageeval/`), plus the site's own HTML.
**Attendees:** MG (EF) · MSME editorial + the person who owns the guideline.

**How to read the tables.** *The guideline says* = quoted from the `.docx`. *The site does* = measured on
the published page. *What we need* = the decision that unblocks the automation.

---

## Agenda (90 minutes)

| # | subject | time | decision needed |
|---|---|---|---|
| 1 | Featured image: "people first" — and the two articles that break it | 20 min | rule or exception? |
| 2 | A logo as the masthead | 10 min | confirm |
| 3 | Graphs and charts | 10 min | confirm + send us one |
| 4 | Captions | 15 min | enable them, or accept metadata-only? |
| 5 | File naming | 10 min | fix the guideline |
| 6 | "Use the maximum number of images" vs featured-only | 10 min | rule |
| 7 | AI-generated images (the open conflict) | 10 min | decide |
| 8 | Assets inside PDF/DOCX attachments + images we never receive | 5 min | who sends what |
| **A2** | **Filter stage (Stage One) — measured, plus decisions 9–11** | **10 min** | **see the appendix; drop if time is short** |
| **A3** | **The 20-article receive test — 9 of 20 published pictures were never sent** | **10 min** | **decisions 12–13; see the second appendix** |

---

## 1. Featured image: "people first" — and the two articles that break it

> **The guideline says:** *"Choose one featured image in this order of preference: 1) people relevant to
> the story; 2) in the absence of a suitable people image, the logo of the brand or brands quoted or
> featured."*

**The site does something the rule does not describe.** Measured on 30 published articles: people 14 ·
logo 12 · event-visual 2 · product 1 · **none 1**. The rule holds — except in two situations that the
guideline does not cover.

### 1a. A supplied portrait lost to a logo, twice

| article | supplied with the release | what MSME published | why it matters |
|---|---|---|---|
| **MICSEA minimum-wage statement** — `micsea-calls-for-gradual-productivity-linked-minimum-wage-revision-in-budget-2027` | `image001.png` — a portrait of a smiling man (unnamed in the release) | `MICSEA-Logo_June_2026_MALAYSIA-SME.jpg` | a people image **was** supplied and was **not** used |
| **Legacy Planning / Sun Life** — `malaysia-leads-asia-in-legacy-planning-but-80-fear-wealth-wont-last-beyond-the-next-generation` | `Ho Teck Seng Sun Life Malaysia President…jpg` — a named executive portrait | `Sun-Life-Logo_October_2026_MALAYSIA-SME.png` | the release **names** the person and quotes him; the logo still won |

**What we inferred (confirm or correct):** in a *statement*, *survey* or *policy* piece, the
**organisation** is the subject and the executive is only a *quotee* — so the logo wins. In an
*appointment*, *byline* or *event*, the person is the subject and the portrait wins (see 1b).

> **Decision 1:** is "logo wins over a quotee's portrait in a statement/survey" the intended rule?
> If yes we will write it into the guideline; if no, these two articles were mistakes and we will
> match the guideline instead.

### 1b. Where people *do* win — and the kind of people photo that wins

| article | what won | why |
|---|---|---|
| `tealive-revs-up-f1-season-with-high-octane-orange-coffee` | `IMG 1.jpg` — **3 people holding the product** | not `IMG 5.png`, which has 13 people: a **posed group with the product** beats a crowd |
| `malaysian-companies-generate-rm305-62-million-at-caexpo-2026` | `4. Group Photo at Malaysia Pavilion.heif` — ~40 people | the formal **group photo**, not the 15 B2B session shots |
| `japanese-wagyus-growing-malaysian-trade-puts-secondary-cuts-in-the-spotlight` | `Image 1.jpg` — 3 men with a **plaque** | a ceremony beats a crowd shot and beats the product plates |
| `ikea-malaysia-commentary-on-malaysia-national-budget-2027` | the author's portrait | a **byline**: the person is the story |
| `what-makes-a-workplace-worth-growing-with` | `[Main Photo] Satveer Bhatt…JPG` | the release itself marks the file `[Main Photo]` |
| `mercedes-amg-gt-coupes-bring-v8-power-and-electric-performance-to-malaysia` | `IMG 1.jpeg` — the **car** with 2 people | the only product-hero in 30; a vehicle launch |

> **Observation to put to them:** `[Main Photo]`, `Caption1:`, `Captions for Images.docx` — when the
> sender marks their hero image, that marking is the single most reliable signal we have. Please keep
> doing it (Tealive, REHDA, MYHK and Boehringer all did).

---

## 2. A logo as the masthead

> **The guideline says:** the logo is *"second choice"* only.

**In practice a logo is the masthead in 12 of 30** articles — every policy statement except one. In 7
of them **the logo was not in the release at all**; it was cropped out of the PDF letterhead by the
publisher:

| article | published as | where it actually was |
|---|---|---|
| `acccims-press-statement-on-the-national-budget-2027` | `ACCCIM-Logo.jpg` | the **PDF letterhead** |
| `sme-malaysia-welcomes-temporary-minimum-wage-exemption-for-msmes` | `SMEs-logo.png` | the PDF letterhead |
| `pikom-commentary-on-budget-2027` | `PIKOM-1.jpg` | the PDF letterhead |
| `micsea-calls-for-gradual-productivity-linked-minimum-wage-revision-in-budget-2027` | `MICSEA-Logo_June_2026…` | the PDF letterhead — the published file even shows the crop's blurred edge |

> **Decision 2:** may the publisher crop a logo out of a supplied PDF, or would you rather we ask the
> sender for a logo file? (Our default: **do not publish a letterhead crop automatically** — we raise it
> for a human; publish only a clean embedded logo image.)

---

## 3. Graphs and charts — *"will the AI identify them and fit them into the news?"*

**Our measured answer: we cannot yet show you an example, because there are none.** All 192 images in
our working set — every released image and every published featured image — were searched: **zero
charts, zero tables, zero infographics.** Every "analysis-looking" featured image turned out to be a
flat wordmark.

What we have today is a rule and a guard:

- a chart is classified as a graph, and **is never allowed to become the featured/masthead image**;
- it may be used in-body with a caption.

> **Decision 3:** please send us **one real MSME article whose visuals include a chart or a data table**
> — ideally the release and the published page. It is a 10-minute test for us, and it turns a rule into
> evidence. Until then we will not claim the capability.

---

## 4. Captions — the guideline requires them; the site shows none

> **The guideline says:** *"Every photograph must have a full-sentence caption that adds context…
> Identify people only where information is supplied."*
> **Example given:** *"Representatives from AFFIN BANK and IFC mark the signing of their financing
> partnership to expand access to capital for Malaysian MSMEs."*

**Measured on the published pages: the guideline's own example has no caption.** On
`ifc-and-affin-bank-partner-to-expand-us400-million-msme-financing-in-malaysia` and on all 30 articles
we inspected, every in-body image renders with `alt=""` and **no visible caption**. There is no caption
field being filled at upload.

This matters more than it looks, because the two reasons MSME gave us are both about *machine and
accessibility* use, not layout:

1. names in captions help **search and answer engines**;
2. captions help **visual readers**.

> **Decision 4:** do you want captions (a) **displayed** under the image, (b) **stored but hidden**
> (in the media library / alt text), or (c) not at all? We generate one factual sentence per used image
> either way — but if they are stored, please tell us **which field** so they actually feed search.

**And the naming prerequisite.** We will name a person **only** when the release names them. Two of the
30 releases supplied a photograph with no caption and no name; a caption that guesses is the one failure
that would embarrass MSME. The practical fix is on the sender's side — any of:

- a `Captions for Images.docx` (Tealive already does this — please make it standard),
- names in the filename (`Ho Teck Seng Sun Life Malaysia President…jpg` worked),
- one line in the email body.

---

## 5. File naming — the guideline's example contradicts the site

> **The guideline says:** *"Rename files using the event or subject, brand and date —
> `AFFIN_IFC_MoU_17Sept2026.jpg`."*

**The site's own file for that article is not that.**
`https://www.malaysiasme.com.my/wp-content/uploads/2026/09/IFC-and-AFFIN-BANK_SEPTEMBER_2026_MALAYSIA-SME-1500x500.jpeg`

Every published image we inspected follows **`<Subject>_<MONTH>_<YEAR>_MALAYSIA-SME`** (with a `-2`,
`-3` suffix for additional images), not `DDmmmYYYY`:

| published file | pattern |
|---|---|
| `Tealive-Orange-Coffee_SEPTEMBER_2026_MALAYSIA-SME.jpg` | Subject_MONTH_YEAR_MALAYSIA-SME |
| `MICSEA-Logo_June_2026_MALAYSIA-SME.jpg` | month in title case, not caps |
| `CAExpo-2026_MALAYSIA-SME_OCTOBER_2026.png` | **year before month** — a variant |
| `MRCA-logo-September_2025_MALAYSIA-SME.jpg` | the *previous year* in the name |

> **Decision 5:** which is authoritative — the guideline's `DDmmmYYYY` or the site's
> `Subject_Month_Year_MALAYSIA-SME`? We currently emit the site's pattern with the month capitalised
> (`October`) because 22 of 22 file-based cases fit it. **The `MRCA-logo-September_2025` name is worth a
> look** — a September 2026 article carrying 2025 in the filename will hurt it in search.

---

## 6. "Use the maximum number of images" vs featured-only

> **The guideline says:** *"Use the maximum number of relevant, publication-quality images supplied."*

**Measured: 25 of 30 published articles carry no in-body image at all** (featured only). In-body images
appear only on photo-rich events:

| article | in-body images | supplied |
|---|---|---|
| `japanese-wagyus-growing-malaysian-trade-puts-secondary-cuts-in-the-spotlight` | 6 | 8 |
| `mercedes-amg-gt-coupes-bring-v8-power-and-electric-performance-to-malaysia` | 6 | 6 |
| `malaysian-companies-generate-rm305-62-million-at-caexpo-2026` | 4 | 20 |
| `tealive-revs-up-f1-season-with-high-octane-orange-coffee` | 2 | 5 |
| `malaysia-and-hong-kong-women-entrepreneurs-strengthen-cross-border-business-ties` | 1 | 2 |
| **the other 25 articles** | **0** | 0–5 |

> **Decision 6:** is "maximum" the goal, or is featured-only the house style and in-body the exception
> for events? Our current rule follows the measured behaviour: in-body only for event/product-launch
> stories that supplied several strong photographs (0–6, usually 0).

---

## 7. AI-generated images — the open conflict

> **The guideline says:** *"AI must not introduce information, interpretation or conclusions that are not
> contained in the submitted press release and accompanying media materials"* — no generated images.
> **The brief we first received says:** *"add self-generated image."*

These are mutually exclusive and we have been operating on the guideline (supplied material only,
because it is also the safer position for a client publication). The rule has been **removed from our
project's hard-rules list** so it is no longer asserted as settled — it is now **T-004**, a question for
this table.

> **Decision 7:** choose one — **(a)** supplied images only (guideline stands), **(b)** AI-generated
> images permitted under conditions (which conditions? labelling? only when nothing is supplied?), or
> **(c)** decided per article by an editor. Everything downstream depends on this one line.

---

## 8. Two things about *receiving* files (partner's side, but you should know)

1. **Pictures are hidden inside the attachment.** Of the 17 published images that were not a loose file
   in the release, **10 were inside the supplied `.pdf`/`.docx`** — the ACCCIM, SME Malaysia, MICSEA,
   PIKOM, Sun Life and Securities Commission logos are literally the PDF letterhead, and TP-Link's
   signing photograph is `word/media/image2.png` inside the `.docx`. Our receive stage now extracts
   them; **the fix is already with our coding partner.**
2. **Three published images were never sent to us at all**: an author portrait (AICPA), a
   launch-stage photograph (Event Me Now), and an expo banner (MIHAS). These can only come from a media
   kit or from MSME.
   > **Decision 8:** when a release has no usable picture, is it acceptable for MSME to be asked
   > *(via the automated reply the receive stage already sends)* to supply the media kit — and will you
   > send us the MSME media-library location for logos so we can fetch a brand logo ourselves?

---

## Appendix — what we measured, so the numbers can be challenged

- **30** raw→published pairs; the published featured image of each was downloaded and matched to the
  released files **by pixels**, not by name (MSME renames everything, so names prove nothing).
- Match quality: same picture ≥0.90 pixel score · crop/rescale 0.60–0.90 · a different asset of the same
  brand ≤0.31. The 0.31–0.60 gap is empty, so the threshold is not delicate; the four ambiguous pairs
  were also checked by eye.
- **13 of 30** published featured images came from a file in the release folder; **17 did not.**
- Rung of the *published* image was re-derived from the pixels (not from any label), which is how the
  "Featured image type" counts above were produced.
- Working material: `analysis/imageeval/` (truth, dataset, tags, score) · rulebook
  `pipeline/IMAGE_GUIDE.md` · the skill `/.claude/skills/msme-image-select/SKILL.md` (v4).

## After the meeting — what changes in our system

Each decision above lands in one place: the skill's rules (`SKILL.md`), the evaluation rulebook
(`pipeline/IMAGE_GUIDE.md`), and — if a guideline line is wrong — a note to MSME's `.docx` so the next
sender reads the same rule we do.

---

# A2 — Appendix: the FILTER stage (Stage One) was measured too

*Tabled from the appendix if time allows — 10 minutes. It is the one agenda item that did not exist when
this brief was written, and it asks MSME three questions that block our Stage-One work. Everything below
is measured on the two JEV filter reports MG's partner produced on 2026-10-24 (146 scored articles,
106 distinct releases). Detail: `../Jev/filter_stage/FORMULATION.md`.*

## What Stage One does today

The filter turns fourteen yes/no questions into probabilities and accepts a release when a weighted
average of the eleven scored ones reaches 60 out of 100. It has three "critical gates" (respect for the
royal institution, religion, and race) that can veto outright.

**Measured against your own decisions, it agrees on 123 of 145 releases (84.8 %).** Of the disagreements,
13 are releases you rejected that we would have accepted, and 9 are releases you accepted that we would
have rejected.

**We are not asking you to fix that number.** We measured what is reachable: a scorer that assumes no
formula at all, given only the same eleven numbers, tops out at 88.7 %. The rule is already one article
from the best any weighting of those numbers can do. Closing the last 11 % needs different inputs, not a
better formula.

## What we found that you should know about

| finding | measured |
|---|---|
| **Every rejection in our data is dated on or before 14 October.** Of the 40 releases received 15–22 October, **all 40 were accepted, none rejected.** | A rule using only the received date scores 60 % with no content at all |
| **One release carries both of your verdicts.** *KPMG in Malaysia's Eco Dive Programme earns Malaysia Book of Records Recognition*, received 7 October — `REJECT` in one report, `ACCEPT` in the other | same release, same date |
| **You split near-identical releases.** *CelcomDigi to offer iPhone Duo* — accepted; *CelcomDigi to offer Protect+ with AppleCare* — rejected. *Sanct Social* — the short film accepted, *now available in Malaysia* and *Three lessons from Hangzhou* rejected | same sender, same week |
| **Six of your seventeen Stage-One filters have no question of ours behind them.** Most keenly **12 Events, Awards & Appointments** — your guideline says routine awards and attendance "should be low priority or rejected", and that is exactly the shape of most of our 13 false accepts. Also missing: 1 Submission Completeness · 5 Editorial vs Advertisement · 9 Duplication · 13 Images & Media Assets · 16 Sponsored/Advertorial | 11 of your 17 covered |

> **Decision 9 — what does `Original status` in the archive actually record?** An editorial rejection, a
> `HOLD` for missing images, or an `EDITOR REVIEW` that was not pursued? Your guideline defines **four**
> outcomes; our report has **two**, so HOLD and EDITOR REVIEW must be recorded as one of ACCEPT or REJECT
> somewhere. Which one, and where?

> **Decision 10 — why is every rejection dated on or before 14 October, and none after?** Either the
> later batch was genuinely cleaner or the field means something different for it. We cannot use the
> post-14-October rows as evidence until we know, and we would rather ask than guess.

> **Decision 11 — the KPMG release carries both verdicts.** Which is right? We are not looking for a
> correction; we need to know whether a duplicated submission can legitimately end up with two different
> statuses, because our deduplication depends on the answer.

## The three columns that would let us diagnose instead of describe

We can currently say *that* we disagree. With these we could say *why* — and none of them needs any new
work from you, they are already in your archive:

| column | what it unlocks |
|---|---|
| **your reason code** — `REJECT – HARD_SELL`, `REJECT – NO_SME_RELEVANCE`, `REJECT – DUPLICATE`, `HOLD – IMAGES_MISSING`, `EDITOR REVIEW – COMMERCIAL_CONTENT` (the guideline already defines these) | turns "13 false accepts" into "9 of the 13 are HARD_SELL" — which is directly a question we can add |
| **the issuing organisation** | we can then measure per-sender behaviour instead of finding it by eye |
| **the release body or a link** | the only way to build a question for filter 12 (Events, Awards & Appointments) |

## Two things inside the filter that are simply wrong, that we are fixing ourselves

- One gate ("Political / Advocacy Content") is **inverted**: you rejected the releases that scored
  highest on it. We are switching it off and re-wording it — no action needed from you.
- One release in our report has **all fourteen scores blank** because a scoring call failed, and the
  report recorded that as a **REJECT**. A failure to evaluate must not read as a verdict. Same ruling as
  the image side (D-012).

## What changes in our system after this

One line: the accept threshold moves from 60 to **62**. Measured, the agreement is unchanged and four of
the thirteen false accepts disappear. Beyond that, the filter waits on the determinism fix and on
decisions 9–11 above.

---

# A3 — Appendix: the 20-article receive test (measured 2026-10-25)

The partner rebuilt the Receive stage and delivered **20 fresh release folders**. We ran the whole image
chain over them and compared every decision with what MALAYSIA SME actually published. Method and every
row: `analysis/imageeval/receive_feedback.md`; the score ledger: `analysis/imageeval/tuning_ledger.md`.

## What the batch looked like on arrival

| check | result |
|---|---|
| folders delivered | 20 |
| `link.md` present and a URL | **20/20** — the batch-1 link faults did not recur |
| folders where the Receive stage extracted **no picture at all** | **7/20** |
| pictures it did extract | 61 |
| pictures that were only inside the supplied `.pdf`/`.docx` | **115**, of which 19 are page-header renders |
| zero-byte files, images that will not open | **0** |
| `.heif`/`.heic` files | 5 in 1 folder — all opened correctly |

Two things to note. The extraction fix is **half delivered**: loose images and `.heif` now work, but
**PDF/DOCX extraction is still not happening** — 7 folders arrived as a document plus nothing, and we only
recovered their pictures by mining the attachment ourselves. And `link.md` is now clean across the batch,
which was the worst defect in the first set.

## The finding that matters: 9 of 20 published pictures were never sent

For each folder we established, from the pixels, which supplied file MSME actually published. Then we
asked a second, different question: was that picture in the pack **at all** — loose, inside the
attachment, or as a letterhead render?

| | folders |
|---|---|
| the published picture (or its brand) was in the pack | **11/20** |
| **it was nowhere in the pack** | **9/20** |
| …of which we could still name the right asset from the release text | 5 |
| …of which we could not, and published a different picture | **4** |

Nine folders where the featured image MSME published was never delivered, even inside the attachment.
The four that hurt are named in the table we are handing the partner, with the asset named the way MSME's
own file names it:

| release | the picture MSME published |
|---|---|
| IDECS26 Brings Five Tracks Together | `IDECS26_MALAYSIA-SME_OCTOBER_2026` (the conference banner) |
| Leaders Gather in Kuching (IDECS26) | `IDECS-26` (the IDECS26 logo) |
| Sarawak Shifts Startup Focus (IDECS26) | `IDECS-26` (the same logo) |
| MRCA Celebrates 34 Years | `MRCA-Inauguration-of-President-34-years` (the stage photograph) |

**This is the single most useful number in the whole exercise**, because it changes what "the AI is only
70 % right" means. Nine of the twenty misses are not a decision the AI got wrong — the picture was not in
the folder. On the eleven folders where the picture *was* delivered, the skill scored **80 %**.

## Decisions needed (12–13)

12. **Will the Receive stage extract embedded media from `.pdf`/`.docx` itself?** Today it only collects
    files named `*.jpg`/`*.png`, so a release sent as one PDF arrives with no picture; we mine it on our
    side, which we can keep doing, but it belongs downstream of the sender, not in the AI.
13. **When the featured image is a brand or event logo that was never supplied, do you want us to (a) ask
    the sender for the file, (b) crop it out of the letterhead ourselves, or (c) publish the logo of the
    organisation we *were* given?** This is the same question as decision 2, asked from the receive side,
    and it decides the 9 rows above.

## What changes in our system after this

One line: the image skill's score is now reported as **two numbers** — match on folders where the picture
was actually delivered (80 %), and the count of folders where it never arrived (9 of 20). Publishing that
as one percentage would have blamed the AI for the partner's gaps. The next batch is the clean test.

## The three "never supplied" pictures (T-021) — now formally classified

The three published images we had recorded as never supplied anywhere were re-checked with the same
pixel ground truth that produced the table above. All three are `RECEIVE_GAP` with `in_pack=none` — the
published file is traceable to nothing in the pack, not even a letterhead render:

| article | the file MSME published | what we did |
|---|---|---|
| Malaysian startup Event Me Now | `image-2.png` — thirteen people on stage holding award discs | declared a logo; **the page carries a different picture** |
| MIHAS 2026 delivers RM6.78 billion | `MIHAS_22ND-BANNER_SEPTEMBER_2026_MALAYSIA-SME` | declared the MIHAS banner correctly |
| AI in accounting (AICPA CIMA) | `Saritha-Subramaniam_AICPA-CIMA_SEPTEMBER_2026_…` | declared the author portrait correctly |

So two of the three we can name blind from the release text, and one we cannot. That is the same split as
the fresh batch (5 of 9 handled), which is the useful thing to say at the meeting: **a named gap is
recoverable, a silent one is not.**
