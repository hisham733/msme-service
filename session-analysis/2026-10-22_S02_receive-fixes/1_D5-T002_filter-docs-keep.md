# T-002 closed — filter files are test variants, kept as written

**Session:** 2026-10-22_S02 · **Turn:** 1 · **IDs:** D5 · T-002 · T-009

---

## 1. What changed (small, reversible)

| Change | Why |
|---|---|
| `todo/✅ T-002.md` → **closed** | the reconciliation is withdrawn; the item now records your instruction and quotes it |
| `decisions/D5.md` **new** | the standing rule: filter definition docs and gate variants are kept as test material, never "corrected" to the live battery |
| `docs/INDEX.md` rows | `FILTER-LOGIC.md` / `FILTER-REVIEW.md` now read "kept as test variants — do not reconcile"; `ARCHITECTURE.md` marked "keep as written" |
| `filter.py` FILE HEADER | the one-line pointer now says the 96-vs-100 and 6-vs-3 mismatch is intentional (`D5`), live truth = `/filters.json` |
| `todo/✅ T-009.md` **new** | map each gate-definition variant to the test it serves (so nobody deletes a "duplicate") |

Indexes regenerated: `OK: decisions=5 {'decided': 5}; todo=9 {'open': 4, 'closed': 1, 'parked': 4}`.
`python3 -m compileall -q filter.py` → OK.

⭐ **Decision — §1:** ✅ nothing to decide.

---

## 2. What I did **not** touch

- `docs/FILTER-LOGIC.md`, `docs/FILTER-REVIEW.md`, `docs/ARCHITECTURE.md` — content unchanged.
- All 10 definition files: `gates-def-base/-1/-2/-3/-original/-my-deepseek/-nocriteria/-gpt-recommended/`
  `my-v1/my-v8`, `original-gates.xlsx`, `gates def.gnumeric` — unchanged.
- `docs/jev-variants.json` (Lab source of truth) — unchanged.
- The `SCORES` comment in `filter.py` that says "weights sum to 96" — left as written; the live weights
  in that same file sum to 100 and `/filters.json` is the check.

⭐ **Decision — §2:** ✅ nothing to decide.

---

## 3. The variant map — do you want it built?

Right now nothing says which definition file tests which variant or when it was last used, so a future
session could mistake one for a stale copy and remove it (`T-009`). Building the map means reading the 10
Excel files + `report-runs.jsonl` and writing one table in `docs/`; no filter logic or wording changes.

**Cost:** ~15 minutes of reading, no risk. **Blocks:** nothing. **Benefit:** makes the "do not reconcile"
rule (`D5`) self-enforcing.

⭐ **Decision — §3:** build the variant map now (A) · leave it parked until you run the next variant test (B)?

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | T-002 reconciliation | **closed** — cancelled per your instruction |
| 2 | D5 rule (docs = test variants) | recorded, indexed |
| 3 | Variant map (`T-009`) | open, awaiting your A/B |

## What I recommend next

**Carry on in this session** at **low** thinking effort if you answer A: the variant map is file reading +
one table, no design. If you answer B, start a **new session** at **medium** effort for `T-001` (repurpose)
or `T-008` (image-detection accuracy), since those are build/debug work.

> Ready-to-paste prompt (only if B + a new session):
> Read `README.md`, `NOW.md`, `todo/INDEX.md` and today's replies. Work `T-008` (receive image-detection
> accuracy, measured 20/55 · 36/55 · 30/55). Verify by re-running the SQL counts, not by re-reading docs.
