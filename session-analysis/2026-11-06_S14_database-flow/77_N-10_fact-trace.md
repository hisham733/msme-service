# 77 — N-10 built: the engine traces facts, it does not browse

_2026-11-06 (S14) · code + docs · vendored engine · live container rebuilt._

## 1. What changed

| File | Change |
|---|---|
| `msme/repurpose/engine/validate.py` | **`QUOTE_TRACE`** (fail: quotes verbatim in the release), **`ENTITY_TRACE`** (dates/amounts fail; names/acronyms warn), **`SENTENCE_SUPPORT`** (warn: paragraph must share ≥20% of its content words) |
| `tests/repurpose/test_pipeline.py` | `TestFactTraceRules` — 6 tests: valid quote, invented quote, new date, new name, low-support sentence, default draft passes |
| `docs/new-rules/N-10-fact-trace.md` (new) | the rule, the four checks, what is not built (LLM claim audit) |
| `docs/meetings/2026-10-30/NEXT_MEETING.md` | `### 11. N-10` (no MSME question) + at-a-glance row 11 |
| `docs/INDEX.md` | N-10 row + `new-rules/` description |
| `docs/new-rules/N-7-chunk-image-rules.md` | engine reference corrected: the engine is **vendored** (`msme/repurpose/engine/`), not the external repo |

✅ nothing to decide — the safeguard is built.

## 2. What the engine does now

| Check | Level | Catches |
|---|---|---|
| `NUMBERS_TRACE` | fail | a number not in the release |
| `QUOTE_TRACE` | fail | a quote (text only, attribution ignored) not in the release |
| `ENTITY_TRACE` | fail / warn | a new **date/amount** (fail); a new **name/org/acronym** (warn) |
| `SENTENCE_SUPPORT` | warn | a paragraph with almost no release wording (possible invented claim) |

No web search or browse call exists. Missing context stays a **`context opportunity`** flag; the value is
never inserted.

## 3. Verification

| Check | Result |
|---|---|
| `compileall` | **OK** |
| Full suite | **201 tests, OK** (8 client-material skipped) |
| APAC draft | **overall True** — numbers ✓, quotes ✓, dates/names ✓, sentence support ✓ |
| Live container | rebuilt; `/health` **200**; the new checks are in `/app/msme/repurpose/engine/validate.py` |
| APAC draft in the container | **overall True** with the same four checks |

The APAC check also fixed two false positives: dates now compare as tokens (“21 OCTOBER 2026” vs
“October 21, 2026”), and the proper-noun regex no longer glues a name to the next sentence.

## 4. What is still open

- A **qualitative claim** (“the largest”, “founded in 1999”) has no number/name; `SENTENCE_SUPPORT`
  warns only if the paragraph shares <20% of its wording. The optional **LLM claim audit** is
  documented in N-10 §4, not built (cost, N-9).
- Gmail intake is still down (`T-028`); the checks run on the archive.

## 5. What I recommend next

**Stop here for the 11-Nov call** (low effort): the rule set and the safeguard are in place.

| # | Item | State |
|---|---|---|
| 1 | N-10 fact trace | done |
| 2 | 201 tests + APAC draft + live container | verified |
| 3 | N-9 cost/credit note | next / after the call |
| 4 | Gmail token (`T-028`) | **open — user action** |
| 5 | N-7 engine changes | 2026-11-16 |
