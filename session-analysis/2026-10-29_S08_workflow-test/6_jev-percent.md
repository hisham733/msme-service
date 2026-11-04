# Jev result as a coloured percentage

**Session:** 2026-10-29 · S08 · reply 6
**Page:** `/filter-history.html` (gates + weighted criteria)

## 1. What changed

The **Jev result** column is now a **0–100% pill** instead of raw decimals:

- gates: the positive Jev answer is `1 − defect`; e.g. `YES 0.990 · defect 0.010` → **99%**
- weighted criteria: the stored `norm`; e.g. `0.250` → **25%**
- colour: hue `0 → 120` (red → green) as the value rises; the pill text is coloured and
  background-tinted, so 99–100% is green and 0–25% is red/orange
- the gate **fired/pass** badge and the **threshold** column stay so the gate logic is still visible
- missing/legacy values show `—`

✅ nothing to decide.

## 2. Evidence

- **145 tests pass**; no backend/data change.
- Live `/filter-history.html` contains `function jevPill`, the `hue = x*120` / `pct = x*100`
  helper and `hsl(...)` styling; the old `YES 0.` / `defect 0.` strings are gone.
- Example values from the live result: `royal_respect 0.01 defect` → **99% green**;
  `sme_relevance norm 0.25` → **25% red/orange**.

✅ nothing to decide.

## 3. What I recommend next

Send the prepared Tenun Nusantara email; when its filter result is saved, open **Filter history**
and each gate/weighted criterion will show the coloured percentage. Then tell me **“sent”** and I
will verify the full chain, including the new article at the top of the DLW index.

## Recap

| Item | State |
|---|---|
| Gate Jev value | **0–100%** pill (`1 − defect`) |
| Weighted Jev value | **0–100%** pill (`norm`) |
| Colour | green near 100, red near 0 |
| Gate pass/fired + threshold | Kept |
| Tests | 145 pass |
| Live page | Verified |
