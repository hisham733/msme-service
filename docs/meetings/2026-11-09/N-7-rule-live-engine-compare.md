# N-7 — the rule vs the live site vs the current engine

_One table to show at the 2026-11-11 call. Live = measured on the latest **100 published posts**
(2026-10-07 → 2026-11-06, `tools/n7_measure.py`). Rule = `docs/new-rules/N-7-chunk-image-rules.md`.
Current engine = the vendored code in `msme/repurpose/engine/` today._

| Point | Live site (100 posts) | N-7 rule | Current engine (today) | Change needed | Verdict |
|---|---|---|---|---|---|
| **Structure basis** | 1–3 headings with **7–9 paragraphs** (≈4–5 chunks) | Count **chunks**: 4–5 chunks of 2–3 paragraphs | Counts **headings**; requires **3–8 H2**, no chunk check | Replace the 3–8-heading rule with a chunk check | **differs** |
| **Headings (H2)** | median **2.5**; **65%** have 1–3; **19%** have >3 | **1–3** for a normal release | **3–8 required** (`SUBHEADERS_3_8`, a *fail*) | 3–8 fail → **1–3 warning** | **differs** |
| **Paragraph length** | median **~40 words** (~33 for releases); ≈2–3 lines | ~**50–60**, warn outside 35–75 | **no rule** | add a paragraph-word **warning** (range still to confirm: 35–75 vs ~30–45) | **differs** |
| **Chunks (4–5)** | **52%** of releases have 8–15 paragraphs; the rest are shorter or long features | 4–5 chunks (8–15 paragraphs), 3 = warning | **no chunk rule** | add **CHUNKS_4_5** (5 hard max, 3 = warning) | **differs** |
| **Images** | **92% exactly 1**; **0** releases exceed 6; features go 7–15 | **6 total** (1 masthead + max 5 in-body); 1 normal | featured + **0–6 in-body = up to 7** (`MAX_IN_BODY=6`) | **MAX_IN_BODY 6→5**, add `IMAGES_TOTAL_MAX_6` | **differs** (by one) |
| **Features** | about half the posts are long-form (proxy); types: profile, event, photo essay, explainer, study | **exempt** from 4–5 chunks (and 1–3 H2) | **not exempt** — treated as news (3–8 H2) | exempt **features** from the chunk/heading rules | **differs** |
| **Commentary / byline** | near-verbatim, no added headings | **exempt** from all chunk rules | commentary branch **already skips** the news rules | confirm — little to change | **matches** |
| **Charts** | **0** live pages show a chart image; APAC **dropped its 3 charts** | chart **in the body**, never the masthead | chart-never-featured **enforced** (D-008); charts can still be dropped on publish | keep a supplied chart **in the body** (publish step) | **differs** (publishing) |
| **About sections** | APAC has 3 H2 **without** an About H2 | "About the Study / About <org>" as **plain text or removed** (not an H2) | draft uses "About …" **as H2** | skill/contract: About = plain text; validator counts it | **differs** |

## Bottom line

- **Matches already:** commentary/byline exemption.
- **Off by one:** images (the engine can show 7; the rule wants 6).
- **Wrong lever:** the engine counts **headings (3–8)** where the site and rule count **chunks (4–5)**.
  This is the biggest change.
- **Missing rules:** paragraph length and chunk count are not checked at all today.
- **Open with MSME:** the exact paragraph length (live ~40 vs rule ~56) and how charts are published.

## What the engine change would be (target 2026-11-16)

1. `validate.py`: replace `SUBHEADERS_3_8` with an H2 **warning** (>3); add **CHUNKS_4_5** and
   **PARAGRAPH_WORDS**; add **IMAGES_TOTAL_MAX_6**; exempt features/commentary.
2. `llm_step.py` (DRAFT_CONTRACT): 4–5 chunks; 1–3 H2 for releases; paragraph/image limits.
3. `imgselect.py`: `MAX_IN_BODY = 5`; at most 1 in-body image per chunk.
4. `skills/msme-repurpose/SKILL.md`: Step 7 + final check updated.
5. `tests`: the 10 cases in the spec §7 (chunks, short release warning, paragraph band, 7-image fail,
   per-chunk image, feature/commentary exempt, chart-never-featured).
