# 38 — N-5 updated to the agreed rules

_2026-11-05 (S13) · docs only · no code touched._

## 1. What changed

Your answers are now the N-5 rule.

| Decision | Recorded in the spec |
|---|---|
| Detection = the word **“contribute”** | §3.1 (trigger); byline/insights are supporting signals only |
| No byline → **ask the sender who the author is** | §3.2 (silent sender fallback removed), §3.5 |
| **Normal filter for every article**; only repurpose is skipped | §3.3, §5 |
| Timing **B** — ask for the visual first, filter when it arrives | §3.3 |
| No author visual → **ask the sender** | §3.5, §5 |
| Category **insights** only | §3.3, §5 |
| Engine handoff **pending** | §3.6, §5, §8 |

Also updated:
- The flow diagram (§3) now branches: `"contribute"` → byline? → ask the sender → visual? → ask →
  `readyToFilter` → **normal filter** → export.
- §3.4 row states: **“Contribute — needs author”** and **“Contribute — needs author visual”**.
- §6 tests: no-byline case now asserts the sender ask; a new row asserts the normal filter runs.
- §7 touchpoints: `contribute.py` and `reply.py` descriptions reflect the two asks.

`NEXT_MEETING.md` §2 N-5:
- Rule line now says: as-is + insights + no repurpose, **normal filter**, current marker “contribute”,
  no byline → ask the sender.
- Question 1 now asks whether “contribute” is the right marker; question 3 asks to confirm as-is **and
  the normal filter**; question 4 asks for the exact wording, size/format and placement.

✅ nothing to decide — all five N-5 choices are recorded.

## 2. Verification

| Check | Result |
|---|---|
| Spec “contribute” trigger | §3.1, line 55-57 |
| Ask-sender author rule | §3.2 line 75; §3.5 |
| Silent sender fallback | **0** occurrences (only “no silent sender fallback”) |
| Normal-filter rule | §3.3 line 88; §5 line 163 |
| Timing B | §3.3 line 90; §5 line 164 |
| Engine pending | §3.6, §5, §8 |
| Meeting questions | 5 items at `NEXT_MEETING.md:185-195` |
| Spec length | 206 lines |
| Code changed | **0** |

✅ nothing to decide — measured.

## 3. What is still open on N-5

Only the **MSME answers** from the 11-Nov call:

- whether “contribute” is the right marker in all cases;
- the exact author-visual sentence, size/format and placement;
- whether to hold or publish with a fallback banner when the visual is missing.

The spec already codes the recommended hold-and-ask path; a different answer will change §3.5.

⭐ Decision — §3: at the call, confirm **“contribute” as the marker** and the **author-visual wording**;
otherwise the build follows the current spec.

## 4. What I recommend next

**Carry on in this session** (low effort): write the **N-6** original-email-link spec.
Reason: it is the last small N-rule; N-7 is engine-only, N-8/N-9 are operational.

| # | Item | State |
|---|---|---|
| 1 | N-5 decisions recorded | done |
| 2 | N-5 spec + meeting questions | done |
| 3 | N-6 spec | next |
| 4 | Build N-1…N-5 + engine handoff | after the 11-Nov call |
