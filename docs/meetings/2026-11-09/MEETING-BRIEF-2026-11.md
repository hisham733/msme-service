# Meeting brief — outcomes of 30 Oct 2026 and the next call

_Built only from two files: `docs/meetings/2026-10-30/transcript.md` (the call) and
`docs/meetings/2026-10-30/NEXT_MEETING.md` (the staging file updated after it)._

- **Call:** Friday 30 Oct 2026, 10:42–12:04 (1 h 21 min), MSME × EmpiFlow.
- **Attendees:** Wayne Lim (MSME), Ailee (MSME editor), MG OwYong (EF), Hisham (EF).
- **What it was:** Ailee walked the prototype's flagged emails and the guideline; most image,
  caption and naming questions were answered. MG committed to ~1.5 weeks of training/updates, then
  another review.

---

## 1. Decisions the call settled

`NEXT_MEETING.md` records that `AG-01`…`AG-08` and `AG-15` were answered (`D-024`…`D-029`).
The transcript supplies the answers and the cases behind them.

| Row | Decision | Example from the call |
|---|---|---|
| **AG-01** | **People first**, but only a real release photo counts. A photo in the sender's email signature is not a press image. | **Sun Life / Legacy Planning:** a named executive portrait was supplied → people first (the site used the logo; Wayne/Ailee say that was an editor's call). **MICSEA:** the only "person" was the sender's Gmail sign-off photo → logo wins. |
| **AG-02** | A **logo may be the masthead** when no suitable people photo exists. | MICSEA minimum-wage statement: logo used; correct. |
| **AG-03** | A **graph/chart is never the masthead**; it may appear in-body only. The 4–5 chunk rule wins over "use every chart". Don't discard information; reduce duplication; never inject new facts. | A release with 7 charts: pick the most relevant, keep the information, do not use 7. |
| **AG-04** | Captions are required and must **add context, not state the obvious**. Name people left-to-right for 5–7 people; a **Prime Minister/minister must be named**. Format: `(Featured pic: names…)` after the paragraph. | ISM Selangor event with the PM: identify him. A 9–10 person group: a generic "representatives at the event" is acceptable. |
| **AG-05** | File name: **`Brand_Month_Year_MALAYSIA-SME`**. For a **logo**, include the date so a newer logo supersedes an older one. | `Tealive`, `MISC`, `MRCA` + month + year + `MALAYSIA-SME`; a logo named `AFFIN 17 September 2023`. |
| **AG-06** | **Maximum 6 images**: 1 masthead + 1 per chunk, capped by 4–5 chunks. | 5 chunks → 1 masthead + 5 in-body = 6. |
| **AG-07** | **No AI-generated images and no editing** of supplied images/logos. | "If the email has an image, use it as it is." |
| **AG-08** | Extract media inside `.pdf`/`.docx`; when a picture is missing, **ask the sender**. | Logos and signing photos inside PDFs/DOCX; missing logo → ask. |
| **AG-15** | Not described in either file — the answer is in `AGENDA.md`/`D-024`…`D-029`, which are not part of this brief. | — |

Also settled in the call (no AG row in these files):

| Rule | Example |
|---|---|
| **Repurpose adds no new facts**; it may paraphrase and add a concluding line, but must not use outside sources. | Ailee: "must not introduce new facts"; the team sometimes does, the guide does not. |
| **Repurpose applies to every article type**: press release, feature, opinion, sponsored/paid, contributed. | MG's C2 confirmation. |
| **Ailee's guide is the rulebook**; train the AI to follow her, not the team's variations. | F1: "the guide is for me". |
| **Article shape:** 4–5 chunks, 2–3 paragraphs per chunk, 2–3 lines per paragraph. | Wayne's chunk explanation; Tealive F1 repetition is the duplication example. |

---

## 2. Still open — from `NEXT_MEETING.md`

| id | Open decision | What the next call needs | What the call already showed |
|---|---|---|---|
| **AG-09** | Does Receive extract embedded media from `.pdf`/`.docx`? | scope + a date | The need is real: logos/signing photos are inside PDFs/DOCX; the row is still open. |
| **AG-10** | Missing brand/event logo: ask the sender, crop the letterhead, or publish the logo we hold? | a formal ruling | The call leans **gallery → ask the sender**; cropping the letterhead was not endorsed. |
| **AG-12** | What does archive `Original status` record — the guideline's 4 outcomes or the report's 2? | an answer | Not discussed in the call. |
| **AG-13** | Why is every rejection dated on/before 14 Oct? | an answer | Not discussed in the call. |
| **AG-14** | May one release carry two statuses (KPMG)? | a ruling | Not discussed in the call. |
| **AG-16** | Input channel: email, WhatsApp, or both? | the system of record + duplicate rule | Not discussed in the call. |
| **Filter** | Cut **62**, determinism, `c10` (`T-024`, `T-023`) | a decision on the cut and the determinism fix | Not discussed in the call. |
| **Next batch** | Who sends what | operational | — |

---

## 3. New rules from the call (not yet in `NEXT_MEETING.md`)

### N-1 — Logo gallery fallback

**Rule:** before asking the sender, search MSME's internal image gallery for a matching logo and reuse
it. The prototype gets a **small gallery (10–20 images)**; **no WordPress/server access now**; **do not
crawl the internet for logos**.

**Example:** BPMB sent a new logo + building photo to update MSME's records. If the gallery holds
BPMB's earlier logo, a later release from BPMB can reuse it instead of asking the sender again.

**Change:** a gallery store + a matcher (brand/name + image similarity); run it before the ask-email;
config for the gallery path. No internet search.

### N-2 — "Library update" emails are not "no article"

**Rule:** an email whose purpose is to update a logo or a building photo is a **gallery update**, not a
press release. File it as such; do not mark it "no article" and do not send the "send us the article"
reply.

**Example:** BPMB group logo + building photograph — the AI correctly said "no article"; the fix is the
*classification*, not the email.

**Change:** a new intake category `library_update`; skip the article/reply path; store the assets.

### N-3 — Report emails are valid articles, and the report link is published

**Rule:** when the email offers a press release **and a full report**, the report can be the article
source; publish it and include a link to the report for the reader.

**Example:** Meltwater "15 years of digital reports" — the email said "access the press release and full
report here"; the AI reported "no article"; Wayne: it *is* the article, and the report link belongs in
the published piece.

**Change:** a `report` article type + a `reportUrl` field carried through receive → draft → publish.

### N-4 — Government budget/speech emails: use the summary, link the speech

**Rule:** for budget/government emails, the email summary is enough; publish it as written (do not
paraphrase or risk misquoting) and keep a link to the minister's speech. If the email text is too
skeletal, open the linked speech and process from it.

**Example:** Madani Budget 2027 POV — the email summary plus the minister's speech link.

**Change:** a `government_summary` article type + `speechUrl`; a rule to fetch the linked speech when
the body is below a minimum length.

### N-5 — Contributed / byline pieces

**Rule:** a contributed article ("contribute", "byline", "please find the article") is published
**as-is**, with the author's byline and category **insights**; it is **not repurposed**. If the author's
visual is missing, ask for it for the banner.

**Example:** "What Malaysian SME should verify in AI" — a research pitch by Yi Jin, Head of SEO at Alik
Studio, with the article as a PDF; publish with the byline, no rewrite.

**Change:** a `contribute` article type; skip repurpose; extract the author from the document; request
the author's visual if no image.

### N-6 — Open the original email from the prototype

**Rule:** a row in the prototype should link to the original Gmail message so MSME can check the email
without searching.

**Example:** Wayne repeatedly asked to see the exact email behind a flagged row.

**Change:** a `mail.google.com/.../<messageId>` link in the checklist/editor row.

### N-7 — Chunk and image rules for the draft

**Rule:** 4–5 chunks; 2–3 paragraphs per chunk; 2–3 lines per paragraph; maximum 6 images
(1 masthead + 1 per chunk); keep the information, reduce duplication, add no new facts.

**Example:** a 7-chart release → choose the relevant charts, keep all the information, do not exceed
5 chunks; Tealive F1 repeats the same story → remove the repetition, keep the name.

**Change:** engine/draft rules; the receive side only needs to pass the article type and media.

### N-8 — Agent name

**Rule:** the call tried **IAN/AIN** and did not settle it cleanly. Confirm the spelling before using it
in the UI or emails.

### N-9 — Cost and credit (operational)

**Rule:** image evaluation is the expensive part; the call's preliminary figure was about **7 US cents
per article** (≈30 sen). The prototype ran out of DeepSeek credit during the demo, so the failed row was
an AI-credit issue, not an email issue.

**Change:** top up the key; run a proper cost test over several articles before quoting a price.

---

## 4. The cases discussed, in one table

| Case | What happened | Rule it proves |
|---|---|---|
| **Meltwater — 15 years of digital reports** | AI said "no article"; the report link was the article | N-3 report + link |
| **BPMB — logo + building photo** | "No article" was correct; it is a library update | N-2 library update |
| **MICSEA — minimum wage** | The "person" was a Gmail signature photo; the logo was used | AG-01 people-first exception |
| **Sun Life — legacy planning** | A real named portrait was supplied; the site used the logo | AG-01 people-first |
| **Climahart / Najwa — missing attachment** | The sender forgot the items; MSME asked her to resend | AG-08 ask the sender |
| **Budget 2027 recommendations — Drive link** | The Drive owner disabled download | AG-08 ask for access; needs_human |
| **Madani Budget 2027** | Email summary + minister's speech link | N-4 government summary |
| **Research pitch — Yi Jin, Alik Studio** | PDF article, "contribute", byline | N-5 contribute/byline |
| **ISM Selangor — PM in the photo** | PM must be named; caption after the paragraph | AG-04 captions |
| **Tealive F1** | The same story repeated in several chunks | N-7 reduce duplication |

---

## 5. Where each change lands

| Item | Where | Concrete change |
|---|---|---|
| N-1 gallery | receive | gallery store + matcher; before the ask-email |
| N-2 library update | receive | new `library_update` category; skip article/reply |
| N-3 report | receive + draft | `report` type + `reportUrl` |
| N-4 government summary | receive + draft | `government_summary` + `speechUrl`; fetch the speech if the body is short |
| N-5 contribute | receive + engine | `contribute` type; skip repurpose; author + visual |
| N-6 email link | dashboard/editor | Gmail message link on the row |
| N-7 chunk rules | engine | draft rules (4–5 chunks, 2–3 paras, 2–3 lines, max 6 images) |
| AG-01…AG-08 | engine/image skill | image choice, captions, naming, max images, no AI images |
| AG-09/AG-10 | receive + MSME | embedded-media scope; missing-logo ruling |
| AG-12…AG-14, AG-16 | MSME | answers only |
| Filter cut 62 / determinism / c10 | filter engine | threshold + determinism fix |

---

## 6. Answer sheet for the next call

```text
AG-09  = <scope + date>
AG-10  = gallery first, then ask the sender? <yes/no>
AG-12  = <4 outcomes or 2>
AG-13  = <answer>
AG-14  = <one status / two statuses>
AG-16  = <email only / email + WhatsApp>
Filter = cut 62? <yes/no>; determinism fix <owner>; c10 <decision>
N-8    = agent name <IAN / AIN / other>
```

---

## 7. What these two files do not answer

- The text of `D-024`…`D-029` (`NEXT_MEETING.md` points to `AGENDA.md`).
- What `AG-15` is.
- The filter measurements and the `AG-12`…`AG-14` evidence (not in the transcript).
- The exact next-meeting date — `NEXT_MEETING.md` says ≈ week of 2026-11-09; the call says ~1.5 weeks
  from 30 Oct.
