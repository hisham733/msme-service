# N-5 — Contributed / byline pieces

_Status: spec for the 2026-11-11 MSME call · 2026-11-05 · **PARKED 2026-11-07 pending MSME** (behaviour questions; evidence: `docs/meetings/2026-11-09/N-5-contributed-evidence-and-questions.md`)._
_Source: 30-Oct 2026 MSME call `[39:16–46:12]`; `docs/meetings/2026-11-09/MEETING-BRIEF-2026-11.md:104`._

## 1. The rule

A contributed article — “contribute”, “byline”, “please find the article”, “research pitch” — is
published **as it is**, with:

- the **author's byline**,
- the category **insights**,
- **no repurpose** (no rewrite, no paraphrase).

If the author's visual is missing, ask the sender for it, to use as the banner. The article itself does
not need a logo or a news photo (`[45:51]`); the banner visual is the only missing asset (`[46:12]`).

## 2. What the Yi Jin case shows (verified)

| Check | Result |
|---|---|
| Subject | “Fwd: Research pitch: what Malaysian SMEs should verify in an AI supplier shortlist” (rows 190, 344) |
| Attachment | `MSME-article-house-style-v3.pdf` (107 KB) — the contributed article |
| Extract | `articleSource=attachment_pdf`, `bodyTextLen=5759`, `needsHumanFetch=false` |
| Row | `hasArticle=true`, `hasPic=false`, `hasLogo=false`, `readyToFilter=false` |
| Reply | **not sent yet** (`replySent` empty); on a live run the generic “no media” ask would fire |
| Article head | “Before You Hire From an AI Shortlist…” · **“By Yik Jinn, Head of SEO and AI Search, ALIQ Studio”** |
| Article foot | “About the author: Yik Jinn is Head of SEO and AI Search at ALIQ Studio…” |

So the article is already found and extracted; the gaps are the **classification** (`contribute`), the
**author**, the **category**, and the **specific ask** for the author's visual.

The engine already has a **byline / signed-opinion branch** (`docs/repurpose/decisions/D-006.md`;
`pipeline/parser.py` accepts `news | commentary | signed opinion | byline`), so the publish-as-is path
exists; it needs the input hint and the author/category.

## 3. Design — receive side

```text
article extracted
      ↓
"contribute" marker?
      ↓ yes
byline / "About the author"? ── no ──► ask the sender who the author is
      │ yes
      ▼
articleType=contribute, author, category=insights, requestedBranch=byline
      ↓
author visual present? ── no ──► ask the sender for the author photo
      │ yes
      ▼
readyToFilter=true → normal filter → export → engine byline branch (as-is)
```

### 3.1 Detection — current marker: “contribute”

**Decided 2026-11-05:** MSME's current marker for a contributed piece is the word **“contribute”**.
The detector treats that word (in the subject or the sender's pitch sentence) as the trigger.

Supporting signals raise confidence but are **not** the trigger:

- “contribution”, “byline”, “please find the article”, “research pitch”, “insights piece”,
  “thank you for the opportunity to contribute”, “about the author”;
- a byline line in the source document: `By <Name>` near the top;
- the sender may be the author or an agency.

A normal press release that contains the word “contribute” only inside the article body is still a
press release; the word must be the sender's contribution marker.

### 3.2 Author extraction

1. The `By <Name>` line — take the name before the first comma or role (e.g. “Yik Jinn” from
   “Yik Jinn, Head of SEO …”).
2. The `About the author:` block at the end.
3. If neither exists → **ask the sender who the author is** (see §3.5). Do not fall back silently to the
   sender's name.
4. Never the agency when a document byline exists.

Store `author` and `authorRole` (e.g. “Head of SEO and AI Search, ALIQ Studio”) when available, with
`authorConfidence=high` for a document byline and `unknown` when the sender must be asked.

### 3.3 Type, category and branch

- `articleType=contribute`.
- `category=insights`.
- `requestedBranch=byline`.
- `noRepurpose=true` — the engine must publish the contributed text as-is.
- **The normal filter runs on every article** — the 3R gates, the 11 scores and the threshold. A
  `contribute` piece is filtered like any other; only the repurpose treatment changes.
- **Timing (decision B, 2026-11-05):** keep today's order — ask for the author visual first; the filter
  runs when `readyToFilter=true`, i.e. after the visual arrives.

The receive side records these in `meta.json` (the N-3 plumbing):

```json
{
  "articleType": "contribute",
  "author": "Yik Jinn",
  "authorRole": "Head of SEO and AI Search, ALIQ Studio",
  "category": "insights",
  "requestedBranch": "byline",
  "noRepurpose": true,
  "detectedBy": "contribute_marker",
  "authorConfidence": "high"
}
```

### 3.4 Row and UI

- `emailType=contribute` — the generic N-2 column.
- Add an `author` extra column (same migration style, not in `_COLUMNS`) for the editor.
- Author unknown → the row reads **“Contribute — needs author”**, not “no article”.
- Author known but no visual → **“Contribute — needs author visual”**.
- `readyToFilter` stays **false** until both the author and the visual are resolved; the article is not a
  rejection.

### 3.5 The ask email

One reply can cover both cases:

- author unknown → “Who is the author of the contributed article?”
- author known, visual missing → “Please send the author's photo for the banner.”

`reply.build_reasons()` needs a `contribute` branch:

- reason: “The contributed article is accepted; we need the author's photo for the banner.”
- provide: “A headshot of the author (JPG/PNG, at least 800 px wide), or the author's preferred visual.”

The exact wording, size/format and page placement are confirmed at the 2026-11-11 call (question 4).
One reply per article, as today.

### 3.6 Export and engine handoff

- `repurpose_export.py` copies `meta.json` and adds `author`, `category`, `requestedBranch`,
  `noRepurpose` to `data/repurpose_export.json`.
- The engine reads `meta.json`/the manifest and selects the **byline** branch with category
  **insights**; it must not rewrite the article.
- **Pending (2026-11-05):** this handoff will change after the engine is reworked. Until then, receive
  captures the type/author but the draft is not guaranteed to stay verbatim.

## 4. Questions for MSME (2026-11-11)

Recorded in `docs/meetings/2026-10-30/NEXT_MEETING.md` §2 (N-5).

1. **Detection — is “contribute” the right marker?** We currently use the word “contribute”. What else
   separates a contributed piece from a pitch — a byline, “please find the article”, the sender?
2. **Author — who is it when an agency sends it?** The byline inside the document, the sender, or the
   “About the author” block? If there is no byline, is asking the sender the right step?
3. **Treatment — confirm as-is + normal filter.** Publish the contributed text unchanged, with the
   author's byline and category **insights**, no repurpose, but still through the normal filter? Any
   allowed edits (typos, formatting, headline)?
4. **Author visual — what exactly do you ask for, and in what words?** A headshot, a company logo, or a
   banner? Preferred size/format, and where it appears on the page? Please give the sentence you send.
5. **No visual — hold or publish?** Do we wait for the author's visual before publishing, or publish
   with a fallback banner and add the visual later?

## 5. Decisions before coding

1. **Detection:** the word **“contribute”** (decided 2026-11-05); byline/insights signals are supporting,
   not the trigger.
2. **Author source:** document byline → “About the author” → **ask the sender** (decided 2026-11-05); no
   silent sender fallback.
3. **Filter:** the **normal filter runs on every article** (decided 2026-11-05); `contribute` only skips
   repurpose.
4. **No visual:** **ask the sender** for the author visual (decided 2026-11-05); timing **B** — ask first,
   filter after it arrives.
5. **Category:** `insights` only (decided 2026-11-05).
6. **Engine handoff:** **pending** — will change after the engine is reworked (2026-11-05).

## 6. Tests

| Case | Assertion |
|---|---|
| Yi Jin PDF | `emailType=contribute`, author `Yik Jinn`, category `insights`, `requestedBranch=byline`, `noRepurpose=true` |
| author visual missing | specific author-photo ask, not the generic media ask |
| author visual present | `readyToFilter=true`, no ask |
| no byline anywhere | asks the sender who the author is; no silent fallback |
| normal press release containing “contribute” | stays `press_release` |
| contribute article reaches the filter | normal 3R/score filter runs; only repurpose is skipped |
| agency sends a byline article | author from the document, not the agency |
| engine preflight | still one release text (only `meta.json` added) |

Proving run: `python3 -m compileall -q msme run.py tools tests` +
`python3 -m unittest discover -s tests -p 'test_*.py'`.

## 7. Code touchpoints (planned)

| File | Change |
|---|---|
| `msme/receive/contribute.py` (new) | “contribute” trigger, byline/author extraction, ask-author/ask-visual decision |
| `msme/receive/report_link.py` (N-3) | shared hyperlink/text helpers if needed |
| `msme/receive/pipeline.py` | `contribute` detection after extract; `emailType`/`author` in the row |
| `msme/receive/reply.py` | contribute-specific reason for the missing author visual |
| `msme/receive/archive.py` | write `meta.json` |
| `msme/repurpose/repurpose_export.py` | copy `meta.json`; add author/category/branch to the manifest |
| `msme/db.py` | `emailType` + `author`; write/select |
| `msme/receive/editor_data.py` · `static/editor.html` | show the author and the contribute status |
| `tests/test_contribute.py` (new) | detection, author, ask wording, row/meta |

## 8. Dependencies

- **N-3** provides the `meta.json` handoff.
- **N-2** provides the `emailType` column.
- **The engine handoff is pending** (2026-11-05): it will change after the engine is reworked. Until then,
  receive captures the type/author but the draft is not guaranteed to stay verbatim.
- Build after N-1…N-4; ≈half a working day for the receive side plus the engine change.
