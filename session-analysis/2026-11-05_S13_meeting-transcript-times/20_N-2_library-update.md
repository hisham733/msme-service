# 20 — N-2 spec written; MSME questions added

_2026-11-05 (S13) · docs only · no code touched._

## 1. What changed

| File | Change |
|---|---|
| `docs/new-rules/N-2-library-update.md` (new, 170 lines) | the N-2 spec: detection after extract, signals, storage, promotion policy C, `emailType`, tests, touchpoints |
| `docs/new-rules/N-1-logo-gallery.md` | gallery schema gains `status` (`active` / `pending` / `superseded`); N-1 matches only `active` |
| `docs/meetings/2026-10-30/NEXT_MEETING.md:79` | `[HS 2026-11-05]` N-2 questions: replace/keep old logo + who approves; auto-update vs approval |
| `docs/INDEX.md` | `new-rules/` folder row + N-2 file row |

The three choices you made are now the spec: **1 = after extract**, **2 = C** (auto-active only for a
logo, high brand confidence, and an existing active brand entry; everything else pending),
**3 = A** (`emailType` column + “Library update” badge). No code was written.

✅ nothing to decide — the choices are recorded exactly.

## 2. Verification

| Check | Result |
|---|---|
| N-2 spec exists | `docs/new-rules/N-2-library-update.md` — 170 lines |
| N-2 questions | 2 numbered items at `NEXT_MEETING.md:79-86` |
| `docs/INDEX.md` | folder row line 15; N-1 line 65, N-2 line 66 |
| N-1 schema | `"status": "active"` at line 161; rule at line 169 |
| Code changed | **0** — docs only |
| Compile/tests | not run — no `.py` touched |

✅ nothing to decide — measured.

## 3. What the spec commits us to

- The classifier runs **after `extract.extract`** and **before Verify**; a hit skips Verify, Filter and
  Reply.
- A hit needs: `body_text < 400` chars, no ≥400-char candidate, ≥2 positive signals, 0 negative
  signals.
- Assets go to `data/gallery/updates/<date>_<brand>/`; no `article.md`, nothing in `all_emails/`.
- Promotion C: auto-active only when logo + high brand confidence + an existing active logo for that
  brand; otherwise `pending` with a recorded reason.
- The 14-column CSV contract stays; `emailType` is an extra column and a UI badge.
- N-2 depends on N-1 for the gallery store, brand matcher and admin tool.

✅ nothing to decide — the design follows your 1/2/3 answers.

## 4. What I recommend next

**Carry on in this session** (low effort): write the **N-3 report + link** spec next, the same way.
Reason: the rule documents are quick and the meeting is close; the N-1 + N-2 build should then be one
fresh session with the code context.

If you prefer to build now: start **N-1 first** (N-2 depends on it), medium effort, new session.

| # | Item | State |
|---|---|---|
| 1 | N-1 spec | done |
| 2 | N-2 spec + decisions 1=B, 2=C, 3=A | done |
| 3 | MSME questions for N-1 and N-2 | done |
| 4 | N-1 code + tests | next build session |
| 5 | N-2 code + tests | after N-1 |
| 6 | N-3…N-9 specs | next |
