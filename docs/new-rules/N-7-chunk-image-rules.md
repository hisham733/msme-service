# N-7 — Chunk and image rules for the draft

_Status: spec prepared 2026-11-06 · **engine task** (`MSME_AI_News`), target 2026-11-16 · no code in this repo._
_Source: 30-Oct 2026 MSME call `[57:24–63:31]`, `[77:32–78:26]`; `docs/meetings/2026-11-09/MEETING-BRIEF-2026-11.md:125`._

## 1. The rule

- A **chunk** is a block of **2–3 paragraphs**.
- A normal news release has **4–5 chunks = 8–15 paragraphs**; **5 is the hard maximum**, **4 is the
  target**; a genuinely short release may have 3 (warning, not a fail).
- **H2 headings stay 1–3** for a normal release; the engine must not force 4–5 H2.
- Paragraphs are **~50–60 words** (the live median is 56), not the call's 2–3 lines.
- **Images: 6 total maximum** — 1 masthead + at most 5 in-body; **most releases have 1**; never add an
  image the sender did not supply.
- **Features** (long profiles / interviews / event pieces) are **exempt** from the 4–5 chunk rule.
- **Commentary / byline** are exempt from all chunk rules.
- A chart is never the masthead; it may sit in the body.
- Keep the information, remove duplication, never add facts.

## 2. The live evidence (measured 2026-11-06)

Method: WordPress REST API, latest **30 published posts** (2026-10-23 → 2026-11-06); measured H2
headings, paragraphs (≥8 words), implied chunks (2–3 paragraphs each) and images (featured + in-body).

| Measure | Live result |
|---|---|
| H2 headings | 0–3 for normal releases; 4–7 only for long features |
| Paragraphs per article | median **7–9**; releases 6–12; features 17–34 |
| Implied chunks (2–3 paragraphs) | **21 / 30** fall in the 4–5 range |
| Words per paragraph | median **56**; only **23%** are 24–45 words (≈2–3 lines) |
| Images per article | **22 / 30 have 1** (masthead only); 5 have >6 (features/photo essays) |
| Chart as masthead | none in the sample |

**The key finding:** the live press releases have **1–3 H2 headings but 7–9 paragraphs** — i.e. **4–5
chunks of 2–3 paragraphs**. The H2 headings are a formatting layer, **not** the chunk count. Forcing
4–5 H2 would make the engine more structured than the live site.

**Paragraph length:** the live median is ~56 words, so the call's “2–3 lines” is **not** the live
pattern. The adopted rule follows the live pattern (decision B, 2026-11-06). MSME must confirm at the
11-Nov call.

**Images:** six is a **cap**, not a target. One masthead image is the normal case; extra images are used
only when the sender supplied them.

### 2.1 Follow-the-live-site baseline

The live site is the **structural target** (30 posts, 2026-10-23 → 2026-11-06):

| Class | H2 | Paragraphs | Words/para | Images |
|---|---|---|---|---|
| Normal press release (24/30) | **1–3** | 6–12 (4–5 chunks of 2–3) | median **56** | **1 normal, 6 max** |
| Long feature (6/30) | 4–7 | 17–34 | ~50–60 | 6–16 (exempt) |
| Commentary / byline | 0 added | near-verbatim | as supplied | author/logo |

**One exception:** follow the live site for **structure**, not for its **defects**. A supplied chart
stays in the body — the live APAC page lost all 3 charts.

**Sample note:** 30 posts (6 features, 24 releases). Expand to **50–100** before freezing the ranges.

## 3. What the engine does today (`msme/repurpose/engine/`)

| Rule | Today | Gap |
|---|---|---|
| 4–5 chunks | **3–8 H2 subheaders** (`SKILL.md:142`, `validate.py:107`, `llm_step.py:16`) | H2 count is the wrong lever; too many for releases |
| 2–3 paragraphs per chunk | already required (`SKILL.md:142`) | none |
| 2–3 lines per paragraph | **not checked** | replaced by the live word target |
| Max 6 images | featured + **0–6 in-body** (`imgselect.py:43`) = up to **7** | one too many |
| 1 image per chunk | in-body capped overall, **not per chunk** | missing |
| Chart never masthead | enforced (`IMG_NO_GRAPH_FEATURED`, D-008) | none |
| No duplication / no new facts | enforced (`REPEATED_PARAGRAPH`, `DUPLICATE_SUBHEADER`, rule 7) | none |
| Commentary / byline | no subheaders | confirm exempt |

## 4. Decisions (2026-11-06)

0. **Baseline:** follow the **live site** for structure (1–3 H2, 4–5 chunks of 2–3 paragraphs, ~50–60
   words, 1 image normal / 6 max); keep the chart-in-body content rule.
1. **Chunk definition:** a block of **2–3 paragraphs**; **4–5 chunks**; H2 stays **1–3** for a normal
   release (live pattern).
2. **Paragraph length:** follow the **live pattern (~50–60 words)**; warn outside **35–75 words**.
3. **Features:** exempt from the 4–5 chunk rule. Trigger (recommended): the extracted source is
   **> ~1,200 words or > ~16 paragraphs**; features may use 4–7 H2.
4. **Minimum:** **4 is the target, 5 is the hard maximum**; a 3-chunk short release is a warning only.
5. **Commentary / byline:** exempt.
6. **Images:** **6 total** (1 masthead + max 5 in-body); **1 is normal**; never add supplied-less images.
7. **About sections:** the live APAC page has **3 H2 and no About H2**; the engine draft uses “About the
   Study” and “About Egon Zehnder” as H2. Under 1–3 H2, About must be plain text or removed.

## 5. Engine changes (handoff, file by file)

| File | Change |
|---|---|
| `.claude/skills/msme-repurpose/SKILL.md` | Step 7 and the final check: 4–5 chunks of 2–3 paragraphs; 1–3 H2 for releases; ~50–60 words per paragraph; 6 images total; features/commentary exempt |
| `pipeline/llm_step.py` | `DRAFT_CONTRACT`: 4–5 chunks; 1–3 H2 for releases; same paragraph/image limits |
| `pipeline/validate.py` | replace `SUBHEADERS_3_8` with an H2 **warning** (>3 for a normal release); add `CHUNKS_4_5`, `PARAGRAPH_WORDS` (35–75, warning), `IMAGES_TOTAL_MAX_6` |
| `pipeline/imgselect.py` | `MAX_IN_BODY = 5`; at most 1 in-body image per chunk |
| `pipeline/tests/test_pipeline.py` | update the 3–8 tests; add chunk, paragraph-length, image-cap and per-chunk tests |

**The engine is vendored** (`D40`); the changes land in `msme/repurpose/engine/`, target **2026-11-16**
(`T-049`).

## 6. Questions for MSME (2026-11-11)

Recorded in `docs/meetings/2026-10-30/NEXT_MEETING.md` §2 (N-7).

1. **Chunks or H2?** The live site uses **1–3 H2** with **7–9 paragraphs** (4–5 chunks of 2–3). Is that
   the target, rather than 4–5 H2 headings?
2. **Paragraph length:** the live median is **~56 words**; the call said 2–3 lines. Which should the
   engine follow?
3. **Short release:** is a **3-chunk** article acceptable with a warning, or must it always reach 4?
4. **Features:** confirm that long profiles/interviews/event pieces are **exempt** from the 4–5 rule.
5. **Images:** confirm **6 total** (1 masthead + 5 in-body) and that **1 image is the normal case**.
6. **Charts in the published article — the APAC case.** The 30-Oct call said a chart goes in the body,
   never as the masthead. The APAC CEO release has **3 charts** (`image001/004/005`); the engine draft
   lists all 3 in-body, but the live article has **0 charts** and still shows the chart captions. Did
   MSME expect to add them manually, or should the system publish them? Who uploads them — the editor
   or the system?
   - Live: https://www.malaysiasme.com.my/apac-ceos-face-ai-and-geopolitical-pressures-but-are-confident-in-navigating-complexities/
   - Email: https://mail.google.com/mail/u/0/#all/1a15cd202b2900a9
   - Draft proof: `repurpose_inbox/APAC CEOs face the same AI and geopolitical pressures as their global peers but are more c/draft.md` → `## Images` lists `image001`, `image005`, `image004` in-body.
7. **About sections:** do “About the Study” / “About <org>” count as H2/chunks? The live APAC page has
   3 H2 without them; the engine draft has both as H2.

## 7. Tests (engine repo, when built)

| Case | Assertion |
|---|---|
| 4–5 chunks of 2–3 paragraphs | passes |
| 6 chunks | fails (hard max) |
| 3 chunks | warning, not a fail |
| paragraph 35–75 words | passes; outside → warning |
| featured + 5 in-body | passes (6 total) |
| featured + 6 in-body | fails (7 total) |
| 2 in-body images in one chunk | fails |
| long feature (source >1,200 words) | exempt from the 4–5 rule |
| commentary / byline | exempt |
| chart as featured | fails (existing D-008) |

## 8. Schedule

- **Spec:** 2026-11-06 (this file).
- **MSME answers:** 2026-11-11 call.
- **Sample:** expand from 30 to **50–100** posts before freezing the ranges.
- **Engine build + tests:** target **2026-11-16** (`T-049`).
- **Receive side:** no change needed; it already exports the article and images.
