# 66 — N-7 now follows the live-site baseline

_2026-11-06 (S14) · docs only · no code touched._

## 1. What changed

| File | Change |
|---|---|
| `docs/new-rules/N-7-chunk-image-rules.md:45` | new **§2.1 Follow-the-live-site baseline** |
| `docs/new-rules/N-7-chunk-image-rules.md:75` | decision **0**: follow the live site for structure |
| `docs/new-rules/N-7-chunk-image-rules.md:85` | decision **7**: About sections must be plain text, not H2 |
| `docs/new-rules/N-7-chunk-image-rules.md:120` | question **7** for MSME (About sections) |
| `docs/new-rules/N-7-chunk-image-rules.md:142` | sample note: expand 30 → **50–100** |
| `docs/meetings/2026-10-30/NEXT_MEETING.md:211` | Rule now says **follow the live site** |
| `docs/meetings/2026-10-30/NEXT_MEETING.md:221` | question 1 now “Is the live site the baseline?” |
| `docs/meetings/2026-10-30/NEXT_MEETING.md:235` | question 7 (About sections) |
| `docs/meetings/2026-10-30/NEXT_MEETING.md:54` | at-a-glance row 9 → **7 answers** |

The baseline table:

| Class | H2 | Paragraphs | Words/para | Images |
|---|---|---|---|---|
| Normal release | **1–3** | 6–12 (4–5 chunks of 2–3) | median **56** | **1 normal, 6 max** |
| Long feature | 4–7 | 17–34 | ~50–60 | 6–16 (exempt) |
| Commentary / byline | 0 added | near-verbatim | as supplied | author/logo |

**One exception:** follow the live site for **structure**, not for its **defects** — a supplied chart
stays in the body (the live APAC page lost all 3).

✅ nothing to decide — the live-site baseline is recorded in both files.

## 2. Verification

| Check | Result |
|---|---|
| §2.1 baseline | line 45 |
| Decision 0 / 7 | lines 75, 85 |
| Question 7 | spec line 120; meeting line 235 |
| Meeting rule | line 211 |
| At-a-glance | line 54, “7 answers” |
| Code changed | **0** |

✅ nothing to decide — measured.

## 3. What is still open

- **MSME answers on 11 Nov** to the 7 N-7 questions, especially:
  - is the live site the baseline (1–3 H2, ~56 words)?
  - About sections as H2 or plain text?
  - charts: editor or system?
- **Engine implementation** in `MSME_AI_News`, target **2026-11-16** (`T-049`).
- **Sample expansion** to 50–100 posts before freezing the ranges.

## 4. What I recommend next

**Stop here for the 11-Nov call** (low effort): the rule set is complete; the engine work needs the
answers.
Reason: building N-7 before MSME confirms the baseline risks a second rewrite.

| # | Item | State |
|---|---|---|
| 1 | Live-site baseline in N-7 + meeting file | done |
| 2 | N-1…N-7 specs | done |
| 3 | N-7 engine build | 2026-11-16 |
| 4 | MSME answers (7 questions) | **open — 11 Nov** |
| 5 | Gmail token (`T-028`) | **open — user action** |
