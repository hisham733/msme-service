# N-10 — No invented facts in the draft (fact trace)

_Status: **built** 2026-11-06 in the vendored engine (`msme/repurpose/engine/validate.py`)._
_Source: D-002 (no external facts) · 30-Oct 2026 MSME call `[35:12]`, `[35:38]` · the N-9 cost review._

## 1. The rule

The repurpose engine uses **only the release text and the supplied images**. It does not search or fetch
the internet for facts, and it must not write a fact that is not in the release.

- Every **number**, **date**, **name**, **organisation** and **quote** in the draft must come from the
  release.
- Where a reader would want context (a date, market size, price), the engine emits a
  **`context opportunity`** flag — what to add, source class, where — and **never inserts the value**.
- This rule applies to **news and commentary**; the title/excerpt may be rephrased for house style.

## 2. What the engine does

| Check | What it traces | Level |
|---|---|---|
| **`NUMBERS_TRACE`** (existing) | every number in the draft must appear in the release | **fail** |
| **`QUOTE_TRACE`** (new) | each quoted segment must appear **verbatim** in the release; attribution outside the quotes is ignored | **fail** |
| **`ENTITY_TRACE`** (new) | **dates** must be in the release (**fail**); **names / organisations / acronyms** warn | fail / warn |
| **`SENTENCE_SUPPORT`** (new) | each paragraph must share **≥20%** of its content words with the release | **warn** |

The engine has **no web-search or browse call**. Its only outbound calls are the LLM and the vision model
APIs. Missing pictures are **declared**, not fetched.

## 3. What the checks caught

On the APAC draft:

- the quote “Expecting more disruption and feeling ready for it…” is in the release — **passes** once the
  check reads the **quote text**, not the rewritten attribution;
- “21 OCTOBER 2026” is in the release as “October 21, 2026” — **passes** once dates are compared as
  tokens, not as one string;
- a name glued to the next sentence (“Berlin Global Dialogue. Seventy”) was a regex artefact — fixed by
  removing `.` from the proper-noun pattern.

The draft now passes all four checks. A synthetic **invented quote**, **new date**, **new name** or a
**wholly new sentence** is flagged by the tests.

## 4. What is not built yet

A **qualitative claim** (“the largest”, “founded in 1999”) has no number/name to trace. The optional next
step is a second LLM **claim audit**: list each claim + the exact release quote that supports it, then
check the quote is a real substring. It is not built (cost, N-9); `SENTENCE_SUPPORT` is the current
guard.

## 5. Code and tests

| File | Change |
|---|---|
| `msme/repurpose/engine/validate.py` | `DATE_RE`, `PROPER_RE`, `_entity_scan`, `_quote_segments`, `_content_words`; `QUOTE_TRACE`, `ENTITY_TRACE`, `SENTENCE_SUPPORT` |
| `tests/repurpose/test_pipeline.py` | `TestFactTraceRules` (6 tests): valid quote, invented quote, new date, new name, low-support sentence, default draft passes |

Proving run: `python3 -m unittest tests.repurpose.test_pipeline -q` → **32 tests, OK** (8 client-material
tests skipped).

## 6. No MSME question

This is an internal safeguard: it enforces the rule MSME already gave (“no new facts; link or flag the
rest”). It does not need a meeting question.
