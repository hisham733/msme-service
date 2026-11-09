# FILTER KIT — the measurement engine behind the Filter-stage numbers (optional)

*For the partner's LLM and the partner. This kit is **reference/measurement**, not a replacement for
your Filter engine. The Filter stage belongs to you; this repository only measures what a Filter report
contains and states what was measured. Integrate it, defer it, or ignore it — but tell your human which
you chose.*

---

## 1. What is in the export

| path | what it is |
|---|---|
| `filter_stage/FORMULATION.md` | the measured rule, the weight derivation, why re-weighting does not help, the ceiling |
| `filter_stage/ROUND-2.md` | the protocol for the next batch and what to ask MSME for |
| `filter_stage/EVIDENCE.md` | how the two 2026-10 reports were read, row by row |
| `filter_stage/INDEX.md` | the folder map |
| `filter_stage/tools/filter_stage.py` | the tool: `parse` · `report` · `fit` · `selftest` |
| `filter_stage/results/*.txt` | the recorded outputs of the 2026-10 runs (aggregate numbers, not client data) |

**Not included:** the two JEV report workbooks and `data/dataset.json`. They contain client rows; they
stay with MG. You run the kit on **your own** report.

## 2. What it does — and does not — decide

It does:

- read a JEV filter report (the `.xlsx` layout with an `Article` header row);
- score the 11 non-critical gates into the weighted score (`WAS`);
- measure agreement, false accepts/rejects, the self-flip, and the leave-one-out ceiling;
- derive a weight vector from each gate's measured separation (`fit`), and measure any operating point
  (`report --cut N`).

It does **not**:

- change your Filter engine, its weights, its cut, or where those are stored;
- ship a configuration file for your engine;
- prove that a different cut or weight is right for a future batch. The values in `FORMULATION.md` are the
  **2026-10 measurement**, not a universal prescription. `CUT = 62` is only the default this tool uses to
  reproduce that measurement; `report --cut N` measures any other value.

**Ownership rule (D-023):** the gate weights and the accept cut are **tunables of the Filter engine**, and
the Filter owner decides where they live and what they are set to. This kit is a measuring instrument.

## 3. Running it

`parse` needs `openpyxl` (the only non-stdlib dependency in this kit; the pipeline itself is stdlib-only):

```powershell
pip install openpyxl
python filter_stage\tools\filter_stage.py parse --in "<your report>.xlsx" --out filter_stage\data\dataset-r2.json
python filter_stage\tools\filter_stage.py report --data filter_stage\data\dataset-r2.json --cut 62
python filter_stage\tools\filter_stage.py fit    --data filter_stage\data\dataset-r2.json
```

`report` and `fit` read the JSON that `parse` wrote, so they need no `.xlsx` and no network. Keep your
generated `data/` out of git.

## 4. How to use the numbers in an integration

1. **Baseline first.** Run `report --cut 62` on your current batch. Compare with the round-1 values in
   `FORMULATION.md` (`84.83 %` agreement, `9/48` false accepts, `1/19` self-flip at 62). A different
   agreement is not automatically a bug — the batch may differ.
2. **Run the self-flip test before any fitting.** Score at least 10 releases twice. If the decision flips,
   the gate run is non-deterministic (KNOWN_ISSUES F2) and a re-fit is not trustworthy yet.
3. **Do not fit on plain agreement.** `accept everything` scores 67.6 % on the round-1 data; the protocol
   is *fit on balanced accuracy, report %agreement*.
4. **`c10` is still wrong-way and unfixed** (AUC 0.306, weight 6). Do not hand-edit the weight; the fix is
   a re-word plus a re-fit (KNOWN_ISSUES F3).

## 5. Your decision, in one line

Tell the human which you chose:

- **A — integrate the rule**: set the cut to the value you measured, keep the gate outputs, re-measure the
  self-flip; record the numbers in your integration report;
- **B — defer**: keep your current filter, note the issues, revisit after the next batch;
- **C — ignore**: the repurpose integration does not depend on this kit; say so and move on.

Whatever you choose, record it in `INTEGRATION_REPORT.md` §5–§7. No filter change is required for the
repurpose → `.html` chain to work.
