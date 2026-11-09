# 32 — N-4 decision B recorded: no threshold until MSME answers

_2026-11-05 (S13) · docs + register only · no code touched._

## 1. What changed

Decision **B** (“leave it to MSME”) is now the recorded N-4 rule.

| File | Change |
|---|---|
| `docs/new-rules/N-4-government-summary.md:62` | §3.2 rewritten: **no summary-length threshold is coded**; detect the type and capture the speech URL only; do not auto-publish the summary or fetch the speech on a guess |
| `docs/new-rules/N-4-government-summary.md:135` | §5 decision 1 marked **B — decided 2026-11-05** |
| `docs/new-rules/N-4-government-summary.md:178` | §8 states the N-4 build is blocked on MSME's answer to question 1 |
| `docs/meetings/2026-10-30/NEXT_MEETING.md:171` | **Blocks:** line added under the N-4 questions |
| `todo/🟢 T-049.md:33` | N-4 row now marked **Blocked** on the summary-vs-speech rule |
| `todo/INDEX.md` | regenerated (`build_register_indexes.py`: 50 todo, 39 decisions) |

✅ nothing to decide — B is recorded as chosen.

## 2. Verification

| Check | Result |
|---|---|
| “400” threshold remaining in the spec | **0** matches |
| Decision B in the spec | line 135 |
| Blocks note in the meeting file | `NEXT_MEETING.md:171` |
| Blocked note in the register | `🟢 T-049.md:33` |
| Index rebuild | `OK: decisions=39; todo=50` |
| Code changed | **0** |

✅ nothing to decide — measured.

## 3. What B means for the build

- The receive side may still **detect** a government/budget email and **capture** the speech URL.
- It must **not** decide “summary is enough” or “too skeletal” on a guessed length.
- The Madani-style email stays on today's path (needs-human/editor) with the speech URL recorded, until
  MSME answers question 1.
- The N-4 build is therefore **parked on the 11-Nov answer**, not on code.

## 4. What I recommend next

**Carry on in this session** (low effort): write the **N-5** contribute/byline spec.
Reason: it is the last short rule doc before the build set is complete; N-6 is a small UI item.

| # | Item | State |
|---|---|---|
| 1 | N-4 threshold decision | B — recorded |
| 2 | N-4 build | blocked on MSME question 1 |
| 3 | N-5 spec | next |
| 4 | N-3 handoff A/B/C | still open (held for the meeting) |
| 5 | Build N-1…N-4 | after the call |
