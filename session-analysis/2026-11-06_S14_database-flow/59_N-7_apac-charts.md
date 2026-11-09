# 59 — N-7 APAC chart case added with both links

_2026-11-06 (S14) · docs only · no code touched._

## 1. What changed

- `docs/meetings/2026-10-30/NEXT_MEETING.md:227` — new **question 6** in §9 N-7:
  “Charts in the published article — the APAC case”, with:
  - **Live:** `https://www.malaysiasme.com.my/apac-ceos-face-ai-and-geopolitical-pressures-but-are-confident-in-navigating-complexities/`
  - **Email:** `https://mail.google.com/mail/u/0/#all/1a15cd202b2900a9`
- Same question mirrored in `docs/new-rules/N-7-chunk-image-rules.md:93`, plus the draft-proof path.
- At-a-glance row 9 now says **6 answers**.

✅ nothing to decide — the question and both links are recorded.

## 2. What the evidence says

| Where | Charts |
|---|---|
| Email / PDF | **3** — `image001.jpg`, `image004.jpg`, `image005.jpg` (1664×1174) |
| Receive archive | all 3 saved (`images/` has 10 files) |
| Engine draft | `## Images` lists all 3 **in-body**, logo as featured |
| Live article (2026-10-23) | **0** charts; the body still carries the chart captions |

Two causes:

1. the live article is **older** (23 Oct) than the engine draft (27 Oct), so it was not published from it;
2. the draft’s in-body positions are generic (“after the relevant section”), and the renderer only
   inserts an image when the position matches a real H2 (`build_site.py:132-140`) — so even the local
   page shows only the cover.

## 3. Verification

| Check | Result |
|---|---|
| Question 6 in the meeting file | line 227 |
| Live link | line 232 |
| Email link | line 233 |
| Spec mirror | `N-7-chunk-image-rules.md:93-100` |
| At-a-glance | line 54, “6 answers” |
| Code changed | **0** |

✅ nothing to decide — measured.

## 4. What I recommend next

**Carry on** (low effort): the **N-8 / N-9** notes, then the 11-Nov call.
Reason: the rule set is complete; N-7 is an engine task for 2026-11-16.

| # | Item | State |
|---|---|---|
| 1 | APAC chart case + live/email links | done |
| 2 | N-1…N-7 specs | done |
| 3 | N-8 / N-9 notes | next |
| 4 | APAC live article republish | open — needs the publish path |
| 5 | Gmail token (`T-028`) | **open — user action** |
