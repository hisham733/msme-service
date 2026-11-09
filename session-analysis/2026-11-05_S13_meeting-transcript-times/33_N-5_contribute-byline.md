# 33 — N-5 spec written; five MSME questions added

_2026-11-05 (S13) · docs only · no code touched._

## 1. What changed

| File | Change |
|---|---|
| `docs/new-rules/N-5-contribute-byline.md` (new, 179 lines) | N-5 spec: detection, author/byline, insights category, no repurpose, author-visual ask, tests, touchpoints |
| `docs/meetings/2026-10-30/NEXT_MEETING.md:175` | `### 7. N-5` with five **Questions for MSME** |
| `docs/meetings/2026-10-30/NEXT_MEETING.md:32,52` | running order + at-a-glance row 7 now include N-5 |
| `docs/INDEX.md` | `new-rules/` description + N-5 file row |

**Five questions**: how to recognise a contributed piece; who the author is when an agency sends it;
confirm as-is + insights + no repurpose; what to ask for when the author visual is missing; hold or
publish without the visual.

✅ nothing to decide — the spec and questions are exactly what was asked.

## 2. Evidence the spec records (verified)

The Yi Jin case (rows 190/344):

- Subject: “Fwd: Research pitch: what Malaysian SMEs should verify in an AI supplier shortlist”.
- The PDF `MSME-article-house-style-v3.pdf` was extracted: **5,759 characters**, article found.
- Row: `hasArticle=true`, `hasPic=false`, `hasLogo=false`, `readyToFilter=false`; **no reply sent yet**.
- The article itself carries the byline: **“By Yik Jinn, Head of SEO and AI Search, ALIQ Studio”**, plus
  an “About the author” block at the end.
- The engine already has a **byline / signed-opinion branch** (`D-006`), so “publish as-is” has a home;
  it needs the type, author and category hint.

## 3. Verification

| Check | Result |
|---|---|
| Spec file | `docs/new-rules/N-5-contribute-byline.md` — 179 lines |
| Meeting questions | `NEXT_MEETING.md:175-199`, 5 numbered items |
| At-a-glance row | line 52 |
| `docs/INDEX.md` | folder row line 15; N-5 row line 69 |
| Code changed | **0** |
| Compile/tests | not run — no `.py` touched |

✅ nothing to decide — measured.

## 4. The decision that shapes the build

**When the author's visual is missing: hold the article or publish with a fallback banner?**

**What it means operationally:** the contributed text is ready, but the page needs a banner.

**Real example:** Yik Jinn's article. The PDF is complete; the email had no photo. Today the row is
`readyToFilter=false` with a generic “no media” ask.

**Options:**
- **A (recommended)** — **hold** and send the specific author-photo ask; publish when the visual
  arrives. Matches the call (`[46:12]`).
- **B** — publish with a fallback banner (generic/insights image or the author's initials), add the
  visual later.
- **C** — publish with no banner.

**Effect of not deciding:** the build cannot set `readyToFilter` for a contribute piece without a
visual; the article either waits forever or ships with an unintended banner.

**Blocks:** the N-5 build (the ready/reply rule). Needed before the N-5 build, not before the spec.

**Register:** `docs/new-rules/N-5-contribute-byline.md` §3.4–§3.5, §5 · `todo/🟢 T-049.md` (N-5 row).

⭐ Decision — §4: **A / B / C** for a contribute piece with no author visual.

## 5. What I recommend next

**Carry on in this session** (low effort): write the **N-6** original-email-link spec — it is a small
UI change and closes the receive-side rule set.
Reason: N-6 is the last N-rule before the engine-only N-7 and the operational N-8/N-9.

| # | Item | State |
|---|---|---|
| 1 | N-1…N-5 specs | done |
| 2 | MSME questions for N-1…N-5 | done |
| 3 | N-5 no-visual A/B/C | **open — §4** |
| 4 | N-6 spec | next |
| 5 | Build N-1…N-5 + engine handoff | after the call |
