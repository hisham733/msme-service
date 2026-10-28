# Coloured Good / Contribution values in the filter modal

**Session:** 2026-10-26 · S05 · reply 16
**Status:** done.

## Change

- **Good** and **Contribution** values now use a red→orange→green scale:
  - 0% = red
  - 50% = orange
  - 100% = green
- Continuous hue (`0 → 30 → 120`) so 44% is orange-red, 63% yellow-green, 98% green.
- Colour is based on the **Good** percentage; Contribution uses the same colour because it is
  `Good × Weight`. Weight stays neutral.
- Added a one-line legend under the scores table.

No data, thresholds or filter logic changed. Rebuilt the app.

✅ nothing to decide
