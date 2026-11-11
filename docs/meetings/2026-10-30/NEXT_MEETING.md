# NEXT MEETING — the single file for the next MSME meeting

*Status: staging file. When the date is fixed, rename this file to* `YYYY-MM-DD_<subject>.md` *(then it
becomes that meeting's brief) and add a row to* `INDEX.md`*. Until then, this is the one place where both
MG and the partner merge **issues** and **MSME design decisions** for the next conversation.*

**Status 2026-10-31 — after the 30-Oct call:** that call answered `AG-01`…`AG-08` and `AG-15` (the answers
are `D-024`…`D-029`, see `AGENDA.md`), so the three-decision table below is stale and has been replaced with
the four items that were **never reached**. The next session is **Wednesday 2026-11-11, 2:00–3:00 PM
(SST)** (Teams invite); rename this file to `2026-11-11_<subject>.md` once the notes are final.

**Why one file:** the 30-Oct brief showed that issues raised from two sides (MG's pipeline measurements,
the partner's Receive/Filter findings) arrive as two documents and get reconciled by hand. One staging
file, appended by both, is the reconciliation. The append-only decision list stays in `AGENDA.md`; this
file is the running order and the narrative.

## How to use it

1. **Append, don't rewrite.** Add under the right heading, with your initials and the date:

   `[MG 2026-10-26] …`, `[HS 2026-10-27] …`. Never delete someone else's line; strike it with
     `~~…~~` and say why.
2. **An issue is one line + evidence.** Link the file or quote the measurement; "the images are bad" is

   not an issue, "9 of 20 published pictures were never delivered (receive_feedback.md)" is.
3. **A design decision needs an answer shape** (`D1 = A`) and an owner, like `AGENDA.md`.
4. **After the meeting:** answers that settle a rule go to `decisions\`; work goes to `todo\`; this file

   keeps the narrative and is renamed to the meeting date.

## 1. Running order (draft — confirm with MSME)

| # | subject | who leads | time |
|---|---|---|---|
| 1 | New rules: report link (`N-3`), government summary (`N-4`), contribute (`N-5`), email link (`N-6`), chunk rules (`N-7`), logo gallery (`N-1`), library updates (`N-2`) | HS | 30 min |
| 2 | Image library: matching, naming, shape, access, auto-update | MSME | 20 min |
| 3 | Filter tuning: cut 62, determinism, `c10` (`T-024`, `T-023`) | MG | 15 min |
| 4 | Remaining answers: `AG-09`, `AG-12`…`AG-14`, `AG-16` | MSME | 15 min |
| 5 | Next batch: who sends what | both | 5 min |

*The previous draft (image rules* `AG-01`*…*`AG-08`*) is closed — those were answered on 30 Oct.*

## 2. Questions and issues to raise

**At a glance**

| # | Topic | Raised by | What the call must produce |
|---|---|---|---|
| 1 | Image delivery — 9 of 20 pictures missing | MG | who sends the fallback image |
| 2 | PDF/DOCX extraction in Receive | MG | scope + date |
| 3 | N-3 — report link lost at publish | HS | owner, placement, source format |
| 4 | N-1 — logo matching + gallery access | HS | 4 answers |
| 5 | N-2 — logo/building updates | HS | 3 answers |
| 6 | N-4 — government summary + speech link | HS | 5 answers |
| 7 | N-5 — contribute/byline pieces | HS | 5 answers |
| 8 | N-6 — open the original email (internal) | HS | no answer needed |
| 9 | N-7 — chunk + image rules | HS | 7 answers |
| 10 | N-8 — agent name (decided AIN) | HS | no answer needed |
| 11 | N-10 — no invented facts (internal) | HS | no answer needed |
| — | Partner items | partner | — |

---

### 1. Image delivery — 9 of 20 published pictures never arrived

`[MG 2026-10-26]`

**What:** 9 of 20 published pictures were never delivered — not loose, not inside the attachment, not a
letterhead render; 4 could not be named from the release text.
**Evidence:** `../analysis/imageeval/receive_feedback.md`, `KNOWN_ISSUES.md` R2.
**Ask:** who sends the fallback when the sender's featured image is a logo that never arrived?

### 2. PDF/DOCX extraction in Receive

`[MG 2026-10-26]`

**What:** PDF/DOCX extraction is still not done in Receive — 7 of 20 folders arrived with no picture;
115 images were mined downstream.
**Evidence:** `KNOWN_ISSUES.md` R1.
**Ask:** is extraction in the Receive scope, and by when?

### 3. N-3 — the report link is lost at publish

`[HS 2026-11-04]`

**Rule (30-Oct call):** if the report is too long, add the link to the report in the published article.
**Email example:** "Fwd: Fifteen years of Digital reports: Meltwater & We Are Social's 2027 edition shows
6.15 billion online and 1 in 3 people using generative AI" (Thu 22 Oct, thread `1a162cc0b30af0e7`). It
offered the press release plus a Drive folder with the full report.
**Gap:** the live article has **no** report link (0 `wearesocial`/`meltwater` URLs in the page HTML;
published 27 Oct), while the release DOCX carries `wearesocial.com/digital-2027` and
`meltwater.com/en/global-digital-trends`.
**Live URL:** `https://www.malaysiasme.com.my/digital-2027-report-one-in-three-people-globally-use-genai-as-social-media-users-hit-5-8-billion/`
**Ask:** who adds it — editor or system — and where?

**Also applies to web-link emails (not attachments):** the email says “Please click on the link below
to access full release and photos” and the system fetches the article page. Rows: Three lessons from
Hangzhou (242), BigSeller 11.11 (400), Labuan IBFC (372), Indonesian delegation (247), IMAGO (257),
Sanct Social (245), Momcozy (408), ConverXion (320) — all `vritimes.com`. Also: Fast Retailing (240)
“Kindly find the press release **HERE**” → Google Drive; Aventra/Media OutReach “Click to download” →
`release.media-outreach.com`; Finnfund/Cision → `news.cision.com`.
**Ask:** confirm the same rule applies — when the email only gives a web link, fetch and publish from
it, and keep that link in the published piece.

**Questions for MSME:**

1. **Where the report lives — what do we link to?** If the report is an **email attachment**, a

   **Google Drive** file, or another cloud store (OneDrive / Box / Dropbox), what URL goes into the
     published article? If it is only an attachment with no public URL, do we skip the link, upload the
     file, or ask the sender for a link? Please give one real example.
2. **Link or summarise — when?** When do you publish the **link** instead of taking information from

   the report into the repurposed article? Does it depend on the **report size/length**, the type of
     report (insights vs product), or whether the report has an article-worthy story? Please show a
     short-report and a long-report example.
3. **Placement — where does the link sit?** At the **end of the body**, inline next to the relevant

   paragraph, or on a separate line next to the article? Please show the exact wording/format
     (e.g. “Read the full report: ”).
4. **File types — what counts as a report?** Only PDF/DOCX, or also **Excel / CSV / PowerPoint** and

   other formats? If the report is a spreadsheet or slide deck, should the pipeline still link it, or
     skip it?
5. **Several links — which one?** When the email offers more than one report URL (e.g. Meltwater and

   We Are Social), publish one, all, or the one the sender calls the full report?

### 4. N-1 — logo matching and gallery access

`[HS 2026-11-05]` · Spec: `docs/new-rules/N-1-logo-gallery.md`

**Rule:** before sending the ask email, the prototype searches a local 10–20 image gallery for the
email's brand and reuses the logo if found. We need MSME's own practice and the real library.

**Questions:**

1. **Matching — how do you match a logo today?** Brand tag, event name, date, sender, something else?

   Who does the matching?
2. **Naming — what is the file convention?** Does it follow brand + month + year + `MALAYSIA-SME`, with

   the date only for logos?
3. **Library shape — what is in it?** Structure, tags/fields, file types, how many images, and are logos

   and photos kept together?
4. **Access — copy or access?** Can we take a copy (zip export), or get access (read-only API /

   WordPress)? How often would it need refreshing?

### 5. N-2 — logo/building updates

`[HS 2026-11-05]` · Spec: `docs/new-rules/N-2-library-update.md`

**Rule:** a logo or building photograph is a library update, not “no article”; the prototype stores it
and stops sending the ask email.

**Questions:**

1. **Replace or version — what happens to the old file?** Replace it, keep both, or tag a new version?

   Who approves it before it is used?
2. **Auto-update or approval — who applies it?** Should the prototype update its gallery automatically

   from these emails, or hold each update for approval?
3. **Detection — how do you recognise an update?** The subject wording, a specific sender (e.g. an

   agency), or simply “only a logo and no article”?

### 6. N-4 — government budget/speech: summary + speech link

`[HS 2026-11-05]` · Spec: `docs/new-rules/N-4-government-summary.md`

**Rule:** for budget/government emails, the email summary is enough — publish it as written (no
paraphrase) and keep a link to the minister's speech; if the summary is too skeletal, open the speech
and process from it.

**Questions:**

1. **Summary or speech — when?** When is the email summary “good enough”, and when do you open the

   minister's speech? Is it length, the facts it contains, or the sender's instruction? Please give one
     example of each.
2. **As written — how exact?** Publish the summary word-for-word, or the normal near-verbatim

   commentary treatment (house formatting, headline/excerpt)? Anything we must never change?
3. **Placement — where does the speech link go?** End of the body, inline, or a separate line? Please

   show the exact wording (e.g. “Read the minister's speech: ”).
4. **Speech source — what formats?** Web page, PDF, YouTube/video? What should the pipeline do when the

   speech is only a video with no text?
5. **Scope — which emails?** Budget speeches only, or every ministry/government statement?

**Blocks:** the N-4 build — no summary-length threshold is coded until answer 1 arrives (decision B,
2026-11-05).

### 7. N-5 — contribute/byline pieces

`[HS 2026-11-05]` · Spec: `docs/new-rules/N-5-contribute-byline.md`

**Rule:** a contributed article is published as-is with the author's byline and category **insights**,
and is **not repurposed**. It still goes through the **normal filter**; only the repurpose step is
skipped. **Current detection:** the word **“contribute”**; if there is no byline, ask the sender who the
author is. If the author's visual is missing, ask for it for the banner.

**Evidence + examples (four real emails next to their live MSME pages, with the open questions):**
[`docs/meetings/2026-11-09/N-5-contributed-evidence-and-questions.md`](../2026-11-09/N-5-contributed-evidence-and-questions.md)

**Questions:**

1. **Detection — is “contribute” the right marker?** We currently use the word “contribute”. What else

   separates a contributed piece from a pitch — a byline, “please find the article”, the sender?
2. **Author — who is it when an agency sends it?** The byline inside the document, the sender, or the

   “About the author” block? If there is no byline, is asking the sender the right step?
3. **Treatment — confirm as-is + normal filter.** Publish the contributed text unchanged, with the

   byline and category **insights**, no repurpose, but still through the normal filter? Any allowed
     edits (typos, formatting, headline)?
4. **Author visual — what exactly do you ask for, and in what words?** A headshot, a company logo, or a

   banner? Preferred size/format, and where it appears on the page? Please give the sentence you send.
5. **No visual — hold or publish?** Wait for the author's visual before publishing, or publish with a

   fallback banner and add the visual later?

### 8. N-6 — open the original email (internal)

`[HS 2026-11-05]` · Spec: `docs/new-rules/N-6-email-link.md`

**No MSME question.** The checklist and editor detail panels now show **Open email ↗** and **Find in
Gmail**. Built 2026-11-05; 241 old rows were backfilled with their Gmail id.

### 9. N-7 — chunk and image rules

`[HS 2026-11-06]` · Spec: `docs/new-rules/N-7-chunk-image-rules.md`

**Live examples (100 posts, 2026-11-07):**
[`N-7-examples-follow-vs-not.md`](../2026-11-09/N-7-examples-follow-vs-not.md) — one article that
follows each rule and one that does not, per point.
[`N-7-single-article-explainer.md`](../2026-11-09/N-7-single-article-explainer.md) — one article
explained point by point (heading, paragraph, chunk, image).
[`N-7-rule-live-engine-compare.md`](../2026-11-09/N-7-rule-live-engine-compare.md) — one table:
the rule vs the live site vs the current engine.

**Rule (as proposed):** follow the **live site** for a normal release: **1–3 H2**, **4–5 chunks of
2–3 paragraphs** (8–15 paragraphs), **short paragraphs (~2–3 lines / ~30–45 words)**, **1 image normal /
6 max**; long **features** (profiles, interviews, event write-ups, photo essays, explainers, study
features) and **commentary/byline** are exempt. A supplied chart stays in the **body**, never the
masthead.

**Re-measured 2026-11-07 on the latest 100 posts** (2026-10-07 → 2026-11-06, `tools/n7_measure.py`):
median **2.5 H2** (65% have 1–3; 19% have >3); median **9 paragraphs** (52% in 8–15 = 4–5 chunks);
**median ~40 words per paragraph** (≈33 for releases) — **not** the earlier ~56; **92% have exactly 1
image** and **no release exceeds 6** (features run 7–15); **0 live pages show a chart** (the APAC page
dropped its 3). The "≥17 paragraphs" feature filter over-counts long press releases, so features are
judged by **editorial form**, not length.

**Questions:**

1. **Baseline confirm:** a normal release = **1–3 H2** and **4–5 chunks of 2–3 paragraphs** (headings

   are labels, not chunks). Is that the target?
2. **Paragraph length:** the earlier note said **~56 words**, but 100 posts measure **~40 (releases

   ~33)** and the call said **2–3 lines**. Should the engine follow **~2–3 lines (~30–45 words)** or
     longer (~50–60)?
3. **Short release:** is a **3-chunk** article acceptable with a warning, or must it always reach 4?
4. **Features:** confirm that long profiles, interviews, event write-ups, photo essays, explainers and

   study features are **exempt** from the 4–5 rule (and 1–3 H2) — and how to tell a feature from a
     *long press release* (length alone over-counts).
5. **Images:** confirm **6 total** (1 masthead + 5 in-body) and that **1 image is the normal case**.
6. **Charts in the published article — the APAC case.** The 30-Oct call said a chart goes **in the

   body**, never as the masthead. The APAC CEO release had **3 charts** (`image001/004/005`); the
     engine draft lists all 3 in-body, but the **live article has 0 images/charts** (0 of 100 live pages
     show a chart). Did MSME expect to add them manually, or should the system publish them? Who uploads
     the charts — the **editor** or the **system**? Please show the expected article.
   - Live: https://www.malaysiasme.com.my/apac-ceos-face-ai-and-geopolitical-pressures-but-are-confident-in-navigating-complexities/
   - Email: https://mail.google.com/mail/u/0/#all/1a15cd202b2900a9
7. **About sections:** do “About the Study” / “About ” count as H2/chunks, or should they be plain

   text? The live APAC page has 3 H2 without them; the engine draft has both as H2.

**Engine task**, not this repo: target **2026-11-16** (`T-049`).

### 10. N-8 — agent name (decided)

`[HS 2026-11-06]` · Spec: `docs/new-rules/N-8-agent-name.md`

**No MSME question.** The agent is **AIN**; the editor page title and header now read **AIN** (built
2026-11-06). If MSME prefers another spelling, it is a one-line change.

### 11. N-10 — no invented facts (internal)

`[HS 2026-11-06]` · Spec: `docs/new-rules/N-10-fact-trace.md`

**No MSME question.** The vendored engine now traces every **number, quote, date and name** to the
release and flags paragraphs with almost no release wording. It does **not** search the internet; missing
context is a `context opportunity` flag, never an inserted fact. Built 2026-11-06; 32 repurpose tests
pass (8 client-material tests skipped).

### Partner items

- *(partner — add yours here)*

## 3. MSME design decisions (append; one row per decision)

| id | decision | where it stands | what the next call needs |
|---|---|---|---|
| `AG-12` | what the archive's `Original status` actually records (two outcomes vs the guideline's four) | **open** — the brief's A2 was never presented | an answer; the three columns that would let us diagnose are in the A2 appendix |
| `AG-13` | why every rejection is dated on or before 14 October | **open** | an answer; the 40 releases after that date cannot be used as evidence until it comes |
| `AG-14` | one release carrying both `REJECT` and `ACCEPT` (KPMG, received 7 Oct) | **open** | a ruling on whether a duplicate may carry two statuses |
| `AG-16` | the input channel — email, WhatsApp, or both | **open** — never reached in October | the system of record, and which wins on a duplicate |
| `AG-09` | does the Receive stage extract embedded media from `.pdf`/`.docx`? | **open** — the partner's item | scope and a date |
| `N-3` | long reports: publish the link to the report | **verified gap** — live Digital 2027 article has no report link; the release DOCX has two | ruling + owner (editor or system), and where the link sits |

*The guideline decisions (*`AG-01`*…*`AG-08`*,* `AG-15`*) are answered — do not re-ask them; read* `AGENDA.md` *and*
`decisions\D-024`*…*`D-029` *first.*

## 4. Notes during the meeting (append, timestamped)

- `[HH:MM]` …

## 5. After the meeting

- answers → `decisions\D-xxx.md` + the `AGENDA.md` row's status;
- work → `todo\T-xxx.md`;
- rename this file to `YYYY-MM-DD_<subject>.md`, update `INDEX.md`, and start a fresh `NEXT_MEETING.md`
from this shape when the following meeting is scheduled.

when they said no fitch online means even not from the sender website ?????????
