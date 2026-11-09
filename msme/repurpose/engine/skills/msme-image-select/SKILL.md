---
name: msme-image-select
description: "Choose the featured and in-body images for a MALAYSIA SME article from the pixels, not the filenames — gather loose images plus whatever the supplied .pdf/.docx hides, read every picture with a vision model, gate the ladder by story type (event/people, product hero, portrait, event poster, brand logo, declared asset), rename to <Subject>_<Month>_<Year>_MALAYSIA-SME.ext and caption each from supplied facts. Use after repurposing, or when asked which image or logo should go with a press release."
---

# Select images / logo for a MALAYSIA SME article (v4 — measured)

**Standalone skill.** Every rule needed to run it is here. Decision ids (D-003, D-008) are EF
provenance only. v4 is calibrated against **30 published MALAYSIA SME articles** whose published
image was traced back to the released files by pixels (`analysis/imageeval/`). Read §0 first: it is
the rule that changed everything.

## 0. You must LOOK at the pictures

A filename is not evidence. `1.jpg`, `image003.png`, `IMG 1.jpg` say nothing about who is in the frame,
and a skill that guesses from names produced the live failures of 2026-10-23 (claiming the people rung
for `1.jpg`). So:

1. **Gather** every picture: `images/`, `originals/`, the folder root — **and the supplied
   `.pdf`/`.docx`**, which is where MSME actually hides them. Measured on the 30 pairs: of the 17
   articles whose published featured image was not a loose file, **10 had that picture or the same logo
   artwork inside the attachment** — the ACCCIM, SME Malaysia, MICSEA, PIKOM, Sun Life and Securities
   Commission logos are literal crops out of the PDF header, and TP-Link's MoU photograph is
   `word/media/image2.png`. `pipeline/harvest.py` does the extraction; do the equivalent by hand when
   running without tools (open the attachment, pull its images).
2. **Read** every candidate: what is really in the frame — kind (`people / logo / graph / event-visual
   / product / junk`), how many people, whether text dominates. The pipeline uses a vision model
   (`pipeline/vision.py`); when you have no vision, say so and drop a rung — never claim a photograph's
   content from its name.
3. **Drop** junk before deciding: tracking pixels and icons (< ~10 KB), email signatures, social icons,
   blank strips, byte-identical duplicates. Keep one copy of a duplicate set (the largest).

## 1. The ladder — gated by story type (this is the whole skill)

Read the release, then pick the **first** rung that fits. Measured distribution of the 30 published
featured images: **people 14 · logo 12 · event-visual 2 · product 1 · none 1**.

| story type | what wins the featured slot |
|---|---|
| **product launch** — a new vehicle, device or model is the news | the **product hero** (vehicle/device clearly the subject). Food and drink launches are *people-first* (Tealive, Wagyu), so the product rung is for manufactured goods only |
| **event** — launch, ceremony, MoU, signing, award, AGM, expo | a **scene photograph of that event's people**: group photo, signing/ceremony line-up, plaque or certificate handover, speakers on stage. A crowd/booth/audience shot is weaker than a posed group |
| **commentary / byline** | the **author's portrait** — the person IS the story. Prefer the file the pack marks (`[Main Photo]`, `Caption1`) |
| **appointment / tenure** | the **named person's portrait** (podium, headshot) |
| **event with a supplied poster/banner** | the **event key-visual** (a poster is a supplied picture; a document header is not) |
| **statement / data-report / survey / policy** | the **organisation's logo** — even when a spokesperson portrait is supplied. Measured twice (MICSEA, Sun Life/Legacy Planning): a supplied portrait of a *quotee* loses to the logo because the organisation, not the person, is the subject |
| **nothing usable in the folder** | **declare an asset** (§3) — do not HOLD silently and do not guess |

Rules that ride along:

- **A graph is never the key visual** (D-008). A chart/table/infographic may sit in-body only.
- **A single unnamed person in a statement** is not the people rung. Ask: is the person the *subject*
  or just a *quotee*? Quotee → logo.
- **Never generate an image, never scrape an unrelated page.** Supplied material, the release media
  kit, or the publisher's library. (The boss's "self-generated images" request is still open — T-004 —
  and does not change this operating rule.)
- **Rename is evidence.** The site's convention embeds the subject, so the rename is also your identity
  claim: `Global-Electronics-Association_October_2026_MALAYSIA-SME.png` says which brand this is.

## 2. In-body images

0–6; **0 is the normal case** (25 of 30 published articles carried no in-body image). Add them when the
folder supplies several strong photographs of a photo-rich event — measured: Tealive 2, CAEXPO 4,
Wagyu 6, MYHK 1, Mercedes 6. Skip junk, duplicates, and a second frame of the featured's principal.
Prefer variety: the room, the detail, the audience, the speaker. A graph may appear here (never as
featured).

## 3. When nothing usable exists — declare, don't HOLD

Hold the *publication*, but always name what has to be fetched, in the same shape TARGET uses:

```
asset = { kind: people | logo | event-visual, subject: "<the brand / person / event>", fetch: true }
```

Pick `kind` from the story: a **staged** launch/ceremony → a photograph of the event (`people`); a
**byline** → the author's portrait (`people`); an **expo** → its own banner (`event-visual`); a
**statement/policy/survey** → the organisation's logo. Measured outcome of this rule on the 17
articles whose published picture was not on disk: every one of them was a logo or an event visual
except three (an author portrait, a launch-stage photo, an expo banner) — those three are recoverable
only from the release's media link, so the declaration must name them exactly.

Naming the asset is not fetching it: the file must exist on disk before build (`FEATURED_EXISTS`).
An un-fetched library logo still blocks the article (T-018).

## 4. Rename

`<Subject>_<Month>_<Year>_MALAYSIA-SME.ext`, then `-2`, `-3` for subsequent images. No spaces.
Subject = the brand or event, hyphenated (`Sun-Life`, `Tealive-Orange-Coffee`, `ACCCIM`). Month as the
site writes it (`October`), year 4 digits. Keep the original extension. The published corpus shows the
month's casing varies and the year sometimes comes last — the **token order above is the one to emit**.
100% of the corpus's 22 file-based decisions are expressible in this pattern.

## 5. Caption

**One factual sentence** per used image, from supplied facts only. Store it with the image — the site
renders alt="" and no caption today, so a caption that only lives in the CMS is invisible, but it is
still required (accessibility + AEO + the client's own guideline).

- Name a person **only** when the release names them, and then give the role the release gives.
- No editorial notes, no brackets, no "confirm", no `[FLAG]` inside a caption (engine check
  `CAPTION_CLEAN`). Uncertainty goes to `Flags`.
- Describe what is actually in the frame (that is why §0 exists): "Three people hold iced orange drinks
  at the Tealive Orange Coffee launch." — not "Tealive executives at the launch" when no name is given.

## 6. Output contract

```
featured { file, source, renamed, rung, caption, why }
in_body[] { file, renamed, position, caption }
captions{}
asset { kind, subject, fetch }        # only when nothing usable exists
flags[]  [FLAG] items — uncertainty, missing asset, unverifiable identity
```

## 7. Gate

- [ ] every candidate was **seen**, not inferred from its name
- [ ] the attachment (`.pdf`/`.docx`) was mined before declaring anything missing
- [ ] the rung matches the **story type** in §1, and `why` names it
- [ ] a graph is not the featured image; no generated image; nothing from an unrelated source
- [ ] junk, duplicates and icons dropped
- [ ] rename carries `_MALAYSIA-SME.` in `<Subject>_<Month>_<Year>` order
- [ ] one factual caption per used image; no invented identity
- [ ] nothing usable → a declared `asset` with a specific subject, and the article does not publish
- [ ] 0–6 in-body images

## Worked examples (measured)

| article | what the folder had | decision |
|---|---|---|
| Tealive F1 | 5 photos: 3 people + 2 posters | featured = the 3 people with drinks (a posed group beats a 13-person kiosk crowd); 2 in-body; `Tealive-Orange-Coffee_September_2026_MALAYSIA-SME` |
| CAEXPO 2026 | 20 photos, 16 with people | featured = the delegation group photo at the Malaysia Pavilion (`.heif` — convert); 4 in-body |
| Wagyu trade | 8 photos | featured = the three men with the wooden plaque (ceremony beats crowd and product) |
| IKEA / Boehringer | one supplied portrait each | featured = that portrait (commentary: the author is the story) |
| MICSEA / Sun Life | a supplied spokesperson portrait | featured = the **organisation logo** (statement/survey: the org is the story) |
| ACCCIM ×2, SME Malaysia, PIKOM, SC | a PDF whose header carries the logo | featured = that logo, cropped out of the supplied PDF (not "missing") |
| TP-Link | images only inside the .docx | featured = the MoU photograph from `word/media/` |
| Mercedes-AMG | people beside cars | featured = the car-dominant frame (product launch) |
| Pos Malaysia | logo + workshop poster | featured = the poster (an event's own key visual beats a logo) |
| MIHAS, AICPA, Event Me Now | nothing at all | declare: `event-visual 'MIHAS'`, `people 'author portrait'`, `people 'launch photo'` |
| AFFIN commentary | nothing | TARGET published **no** featured image — a recorded deviation, not a target |

## Provenance

D-003 (logo/banner fallback) · D-008 (a graph is never the key visual) · T-004 (generated images: open)
· T-018 (library asset must be fetched). Evidence and scoring: `analysis/imageeval/` ·
`pipeline/IMAGE_GUIDE.md` · code: `pipeline/imgselect.py`.
