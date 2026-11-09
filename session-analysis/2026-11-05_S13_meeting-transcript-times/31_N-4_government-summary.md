# 31 — N-4 spec written; five MSME questions added

_2026-11-05 (S13) · docs only · no code touched._

## 1. What changed

| File | Change |
|---|---|
| `docs/new-rules/N-4-government-summary.md` (new, 173 lines) | N-4 spec: detection, summary-vs-speech, public speech fetch, `meta.json`, commentary branch, tests, touchpoints |
| `docs/meetings/2026-10-30/NEXT_MEETING.md:150` | `### 6. N-4` with five **Questions for MSME** |
| `docs/meetings/2026-10-30/NEXT_MEETING.md:32,51` | running order row 1 + at-a-glance row 6 now include N-4 |
| `docs/INDEX.md` | `new-rules/` description + N-4 file row |

**Five questions** (also spec §4): summary-vs-speech rule; how exact “as written” is; link placement
and wording; speech formats (page/PDF/video); scope (budget only vs all ministry statements).

✅ nothing to decide — the spec and questions are exactly what was asked.

## 2. Verification

| Check | Result |
|---|---|
| Spec file | `docs/new-rules/N-4-government-summary.md` — 173 lines |
| Meeting questions | `NEXT_MEETING.md:150-173`, 5 numbered items |
| At-a-glance row | line 51 |
| `docs/INDEX.md` | folder row line 15; N-4 row line 68 |
| Code changed | **0** — docs only |
| Compile/tests | not run — no `.py` touched |

✅ nothing to decide — measured.

## 3. Evidence the spec records

The real Madani email (checklist rows 204/347) is **“Budget 2027 POV: Where should SMEs start with
MADANI's AI funding?”**. Today the pipeline treats it as a media pitch: `bodyTextLen=0`,
`needsHumanFetch=true`, `hasArticle=false` — so it goes to the ask/needs-human path, although the call
says the summary + speech link is publishable.

The spec therefore adds a `government_summary` path: summary ≥400 chars + one budget fact → verbatim
article; otherwise fetch the speech (HTML today, PDF via a new public-document fetch); if the speech is
a video, keep the summary + link only.

## 4. The one open value that blocks the build

**What “good enough” means.** The call gives no number, and the raw Madani body is not in the saved
trace (the archive folder is empty), so the threshold must be set or measured.

**Options:**
- **A (recommended)** — start with **400 characters + one budget/government fact**, then calibrate on the
  Madani and OCBC Budget 2027 emails.
- **B** — leave it entirely to MSME’s answer on 11 Nov; no detector threshold until then.
- **C** — require a dateline/structure instead of a length (e.g. “KUALA LUMPUR, …” or a minister named).

**Effect of not deciding:** N-4 can be coded with a placeholder, but the first live test may classify a
pitch as a summary (or the reverse), and the 11-Nov demo has no defensible rule.

**Blocks:** N-4 code and its demo. Needed before the N-4 build, not before the spec.

**Register:** `docs/new-rules/N-4-government-summary.md` §3.2, §5 · `todo/🟢 T-049.md` (N-4 row).

⭐ Decision — §4: **A / B / C** for the summary threshold.

## 5. What I recommend next

**Carry on in this session** (low effort): write the **N-5** contribute/byline spec, then N-6.
Reason: two short rule docs remain, and they complete the 11-Nov answer sheet before the build session.

| # | Item | State |
|---|---|---|
| 1 | N-1, N-2, N-3, N-4 specs | done |
| 2 | MSME questions for N-1…N-4 | done |
| 3 | N-4 summary threshold A/B/C | **open — §4** |
| 4 | N-5 / N-6 specs | next |
| 5 | Build N-1 → N-4 + engine handoff | after the call |
