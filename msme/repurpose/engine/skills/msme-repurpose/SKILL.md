---
name: msme-repurpose
description: "Repurpose an accepted MALAYSIA SME press release into an upload-ready article — news format (title, dateline excerpt, opening, 3–8 subheaders, compressed quotes) or commentary format for the statement/commentary class — then run the final upload check. Use for the repurpose stage of AI_news (stage two) after a release passes filtering, or whenever a raw press release must become a malaysiasme.com.my article."
---

# Repurpose a press release into a MALAYSIA SME article

**Standalone skill.** Every rule needed to run it is in this file. The decision ids in brackets
(D-002, D-004, D-006) are EF provenance only — you do not need any other document.

## The rules that decide the output

1. **No added facts (D-002).** The release and its supplied media materials are the only sources.
   Never introduce an external fact, statistic, interpretation, assumption or conclusion. Where a
   reader would want context, emit a `context opportunity` flag — *what to add · source class
   (wire/official/spec sheet) · where it would go* — never the value.
   - The release's own figures may be reformatted (69,104 → 69,000), never changed.
   - An **attribution-only line** ("Bernama reported the same figures", "According to X") adds no
     fact or number. Insert one only when the source is verifiable from the supplied material;
     otherwise flag `context opportunity: source line before publication`.
2. **The class selects the treatment (D-004/R2; D-006 = A).**
   - **News** — corporate news, announcement, appointment, partnership, milestone, or a data/research
     report → **rewrite**: title, excerpt, opening, 3–8 subheaders, selected quotes (Steps 4–9).
   - **Commentary** — an organisation's statement or response on a policy or decision that **also
     describes itself as opinion** (`opinion` · `commentary` · `column` · `viewpoint` · `perspective` ·
     `for your reader`) → **near-verbatim body, normalised front-matter** (Step 3).
     *Measured 2026-10-25 (30 corpus pairs + 20 fresh): "a statement on a policy" alone is not enough —
     8 policy statements in the corpus, only 5 were republished near-verbatim; the other 3 came back at
     12 %, 28 % and 41 % body reuse. Adding the self-description test keeps all 5 and drops the 3
     misses. On the 20 fresh releases it still fires 2/20 where the publisher rewrote all 20, so it is
     better, not exact. Evidence: `analysis/repurpose/grades/SUMMARY.md`.*
   - **Signed opinion / byline** — "By &lt;name&gt;" / "Kindly attribute to &lt;name&gt;", author
     portrait supplied → **news with the byline kept**, first person removed, until the client rules
     otherwise. *`By &lt;name&gt;` alone proves nothing: it appears in 20 of 22 house-style releases in
     the corpus. It is a layout signal, not a branch signal — never pick commentary on it alone.*
3. **Commentary front-matter (details in Step 3).** A clean org title is kept; a person/reaction
   headline becomes `<Org> Commentary on <Topic>` with the person moved to the credit line; a supplied
   subtitle stays as a deck; a body dateline becomes the inset; a separate meta line is dropped; a
   generic opening welcome may be trimmed (flag it); no excerpt, subheaders or blockquotes; one topic
   category; the credit line only when the release supplies attribution.
4. **Quote selection (details in Step 7).** Blockquote a **selected subset** of the strongest quotes,
   each ending at a **sentence boundary**; report the rest as past-tense reported speech. Median 2 ·
   max 6 · zero allowed when no quote earns it.
5. **Images** are selected by the companion skill `msme-image-select`: people first, then a related
   logo/banner, then event key-visual, then product hero; HOLD only when nothing related exists.
6. **Categories reuse the site's vocabulary.** Use category names the site already uses (from the
   supplied link/tags where present, or the conventional set: automotive · business · government ·
   technology · sme · financing · awards · events-happenings · news). Invent a slug only when no
   existing category fits, and keep it short (`aftersales`), never a phrase
   (`aftersales-and-warranty`). 1–4 categories; never PILLARS/COLUMN.
7. **Every section says something new.** Never repeat a paragraph, a sentence, or a section heading.
   If two sections would carry the same text, merge them or drop the weaker one — a reader must not
   meet the same paragraph twice. (Live-run failure 2026-10-23: one draft repeated a section three
   times; the engine now rejects it — do not rely on that, write it right the first time.)

## Agenda

1. Inventory the release; build a fact sheet — Steps 1–2.
2. Pick the branch — Step 3.
3. Draft: title → excerpt → opening → body → ending — Steps 4–8.
4. Clean up (Step 9), flag context opportunities (Step 10), run the final check (Step 11).
5. Hand images to `msme-image-select`.

## Inputs / outputs

**Input** — the release (text, `.docx` or `.pdf`), its supplied images, and any media-kit links. The
release is the ONLY fact source.

**Output** — one upload-ready article object:

```
title / excerpt / byline? / body (markdown: H2 subheaders, "> " blockquotes) /
categories (1–4; never PILLARS/COLUMN) / images (via msme-image-select) / flags[]
```

## Steps

### 1. Inventory
List every file; load the release text; record its dateline, quotes, numbers and attribution. Note
(never block on): missing image, a missing or wrong published link.
Done when: the fact source is unambiguous and completeness is recorded.

### 2. Fact sheet
Rows: who (orgs, people + designations) · what · when · where · why (stated purpose) · every number ·
every direct quote verbatim with speaker.
Done when: every quote and statistic in the release appears in a row; later sentences trace to rows only.

### 3. Branch (rule 2)
Classify the release, then route:

- **News** — brand/org as actor ("announces/launches/signs/reveals"), surveys/results, figures-first
  → Steps 4–9.
- **Commentary** — org voice; "welcomes/urges/calls on/response to"; a policy named; signed or not
  → near-verbatim body; skip Steps 5–8.
- **Signed opinion / byline** — signed commentary whose treatment is unclear → **news with the byline
  kept** and a `[FLAG]`.

**Commentary output (front-matter is editor-normalised):**

- **Title** — keep a clean org label as supplied (`<Org> Press Statement on <Topic>`;
  `<Org> Commentary on <Topic>`). Normalise a person/reaction form to `<Org> Commentary on <Topic>`
  (`RESPONSE FROM <PERSON>, <ROLE> OF <ORG> ON THE <TOPIC>`; `<Org> Reaction to <Topic>`;
  `Media Statement by <PERSON>…`): the person moves to the credit line, never the title.
- **Deck** — keep a supplied subtitle as a deck.
- **Credit line** — only when the release supplies attribution: `Response from <Name, Role>` or
  `By <Name, Role>`. Convert `Kindly attribute to: <Name, Role>` → `By <Name, Role>`.
- **Dateline** — when the release carries the dateline in the body, inset it at the start of
  paragraph 1 (`9 OCTOBER 2026, KUALA LUMPUR – `); a separate standfirst/meta line
  (`Kuala Lumpur | Friday, 9 October 2026`) is dropped.
- **Opening/body** — keep the full body. A generic opening welcome that carries no measure, figure or
  position may be dropped when the next paragraph starts the substantive response; record
  `[FLAG] commentary opening trimmed`.
- First person and org voice kept; About/contacts removed; no excerpt, subheaders or blockquotes;
  one topic category (e.g. `budget-2027`).

Recorded deviation (not a target): three early policy statements were published in news format by a
different editor; the class rule above still applies.

Done when: the branch is recorded in the output object.

### 4. Title
**News:** title case; keep the brand/org as the actor when it is the story's subject; factual;
SEO-shaped rewrite allowed (`announces Top Nominees` → `Reveals 12 Top Nominees`).
**Commentary:** per Step 3.
Done when: the title makes no promise the release doesn't.

### 5. Excerpt (news only)
One sentence, 25–42 words, rewritten (not lifted). Dateline prefix:

| situation | form |
|---|---|
| location + date | `LOCATION, DD MONTH YYYY -` |
| location only | `LOCATION -` |
| date only | `DD MONTH YYYY -` |
| multi-part (`HANGZHOU, CHINA … (TUESDAY) –`) | keep place; drop weekday/newswire tokens |
| statement/opinion with no dateline | no prefix; the sentence starts the excerpt |

### 6. Opening (news)
Up to ~4 short paragraphs (measured: 3–4): who, what, stated purpose. Announcement first, history after.

### 7. Body (news)
- **3–8 H2 subheaders** — short factual labels, 2–3 paragraphs each; add subheaders the release lacks.
- **Quotes (rule 4)** — blockquote a selected subset of the strongest quotes. Each blockquote ends at
  a **sentence boundary**: a short quote in full; a long quote may contribute its complete first
  sentence, with the remainder reported. Every other quote is past-tense reported speech (`said Tan`,
  `Tan added`). Corpus: median 2 · max 6 blockquotes; zero is valid when no quote earns it; never stop
  mid-sentence.
- **Names** — first mention: full name + designation; then Malay/Indian → personal name,
  Chinese/Western → surname, uncertain structure → full name (`[FLAG]`); similar names → keep full
  names. Full official org name first, acronym thereafter. Never invent or upgrade titles.
Done when: every body sentence traces to the fact sheet.

### 8. Ending (news)
Neutral 1–2 sentences restating the outcome; no verdict, no new fact. Release boilerplate may become a
factual closing section (e.g. "About <org>").

### 9. Clean-up (mechanical, checked)
Drop: URLs/emails/phones/PR contacts, `FOR IMMEDIATE RELEASE`, `###`, newswire tokens, tracking links.
Convert (news branch): `29th September` → `29 SEPTEMBER`; `–`/`—` → ` - `; bullets → prose; first
person → third.
Commentary keeps the supplied date form and the inset ` – ` when a dateline is used, and keeps the org
voice — do not convert.

### 10. External context — never insert (rule 1)
Scan for reader gaps: a reaction to a decision (flag the decision's date + authority), a milestone
with a comparable market size (flag the market number), a product/price launch (flag the spec/price
table), a statistic with no named source (flag a source line). Emit one flag per gap:

`context opportunity: <what to add> — source class <wire/official/spec-sheet> — place <excerpt/context para>`

The value itself is entered by the editor, never by you. Never flag competitor information,
speculation, anything contradicting the release, or an editorial verdict.

### 11. Final check (each item: pass · fix · flag)
- [ ] branch recorded; only release facts in the body; opportunities flagged, not inserted
- [ ] news: title case, brand/org as actor · commentary: title per Step 3 (person in the credit line, not the title)
- [ ] news: dateline per Step 5, date in CAPS, dash ` - ` · commentary: inset per Step 3, date form as supplied
- [ ] news: excerpt + opening state the main intent
- [ ] news: 3–8 subheaders, 2–3 paragraphs each · commentary: none added
- [ ] news: quotes attributed, past tense, each blockquote at a sentence boundary · commentary: text reposted, first person/org voice kept
- [ ] commentary: front-matter flags recorded (title normalised · dateline/opening trimmed)
- [ ] no links/contacts/boilerplate (except a kept About section)
- [ ] commentary: credit line only if supplied; one topic category
- [ ] images selected + renamed + captioned via `msme-image-select`
- [ ] categories 1–4; none of PILLARS/COLUMN
- [ ] ending adds no verdict (news); commentary ends as the release does
- [ ] names per Step 7; nothing guessed

### Failure modes → EDITOR REVIEW
Ambiguity · misleading/legal/reputational content · political/advocacy tone · bylined material ·
unclear commercial intent · insufficient material · no usable visual at all → HOLD (the image skill
decides).

## Worked examples

### News — C-016 Tealive (F1 Orange Coffee launch)

**Raw signals:** a launch; brand as actor; CEO quotes; product facts; links and an About block.
**Output:**
- title `Tealive Revs Up F1 Season with 'High-Octane' Orange Coffee`;
- excerpt `SEPANG, 29 SEPTEMBER 2026 - The Malaysian beverage brand enters the coffee race with a
  limited-time Orange Coffee series made with beans from Ethiopia, Indonesia and China.` (25–42 words,
  location-date form);
- 3 opening paragraphs; 4 H2s; 2 blockquotes (both short Loo quotes in full, sentence boundaries);
- links/contacts/About removed; no external facts; featured = 3 people with the product.

### Commentary — C-023 IKEA Malaysia (Budget 2027)

**Raw signals:** `IKEA Malaysia Commentary on Malaysia National Budget 2027`; `Kindly attribute to:
Takeshi Murai, Country Retail Director, IKEA Malaysia`; a separate meta line `Kuala Lumpur | Friday,
9 October 2026`; 7 body paragraphs; About block; contact header.

**Output:**
- title kept — it is already a clean org label;
- credit line `By Takeshi Murai, Country Retail Director, IKEA Malaysia`;
- no inset dateline (the meta line is separate, so it is dropped);
- the generic opening welcome paragraph is dropped (`[FLAG] commentary opening trimmed`); paragraphs
  2–7 are reposted near-verbatim;
- About/contacts removed; no excerpt/subheaders/blockquotes; category `budget-2027`;
- featured = the supplied author portrait (`msme-image-select`).

## Provenance

D-002 (no added facts) · D-004/R2 (house style + class trigger) · D-006 (class selects treatment) ·
T-008 (quote selection, commentary front-matter, source-line boundary). The EF decision register is the
source of record; this file is the operative copy.
