# 55 — N-7 spec prepared (engine task)

_2026-11-06 (S14) · docs only · no code in this repo._

## 1. What changed

| File | Change |
|---|---|
| `docs/new-rules/N-7-chunk-image-rules.md` (new, 114 lines) | N-7 spec: live evidence, adopted rules, engine handoff, MSME questions, tests, schedule |
| `docs/meetings/2026-10-30/NEXT_MEETING.md:207` | `### 9. N-7` with five questions; at-a-glance row 9; running order updated |
| `docs/INDEX.md` | `new-rules/` description + N-7 row (line 73) |

**Adopted rules (your answers):**

- chunk = a block of **2–3 paragraphs**;
- normal release = **4–5 chunks** (8–15 paragraphs); **5 hard maximum**, **4 target**, 3 allowed with a
  warning;
- **H2 stays 1–3** for a normal release;
- paragraphs **~50–60 words** (live median 56), not 2–3 lines;
- **6 images total** (1 masthead + max 5 in-body); **1 is normal**;
- **features exempt**; **commentary/byline exempt**.

✅ nothing to decide — all four choices are recorded.

## 2. The live check (30 posts, 2026-10-23 → 2026-11-06)

| Measure | Result |
|---|---|
| H2 per article | 0–3 for normal releases; 4–7 for long features |
| Paragraphs per article | median 7–9 (releases); 17–34 (features) |
| Implied chunks (2–3 paragraphs) | **21 / 30** in the 4–5 range |
| Words per paragraph | median **56**; only 23% in 24–45 |
| Images per article | **22 / 30 have 1**; 5 have >6 (features) |
| Chart masthead | none in the sample |

This is why the spec separates **chunks** (paragraph blocks) from **H2 headings**, and follows the live
paragraph length instead of the call's 2–3 lines. MSME will confirm both on 11 Nov.

## 3. Engine changes (not this repo)

The spec hands these to `MSME_AI_News` (`D35`):

- `SKILL.md` · `llm_step.py` — 4–5 chunks, 1–3 H2, ~50–60 words, 6 images, features exempt.
- `validate.py` — H2 becomes a warning; add chunk count, paragraph words (35–75 warning), image total.
- `imgselect.py` — `MAX_IN_BODY = 5`; max 1 image per chunk.
- `tests/test_pipeline.py` — update the 3–8 tests and add the new checks.

Target **2026-11-16** (`T-049`).

## 4. Verification

| Check | Result |
|---|---|
| Spec file | 114 lines; all sections present |
| Meeting questions | `NEXT_MEETING.md:207-228`, 5 numbered items |
| At-a-glance | row 9 at line 54 |
| `docs/INDEX.md` | N-7 row line 73 |
| Code changed | **0** |
| Compile/tests | not run — no `.py` touched |

✅ nothing to decide — measured.

## 5. What I recommend next

**Carry on** (low effort): write the short **N-8 / N-9** notes, then stop for the 11-Nov call.
Reason: the rule set is complete and the engine work waits for the answers.

| # | Item | State |
|---|---|---|
| 1 | N-1…N-7 specs | done |
| 2 | N-6 code + live build | done |
| 3 | N-7 engine build | 2026-11-16 |
| 4 | N-8 / N-9 notes | next |
| 5 | Gmail token (`T-028`) | **open — user action** |
