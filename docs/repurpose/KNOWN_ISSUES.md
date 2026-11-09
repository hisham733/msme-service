# KNOWN ISSUES — Receive and Filter, measured upstream of this export

*Read this before integrating. The pipeline in this repository starts **after** your Filter. These are the
issues we measured in the Receive and Filter stages — on your side of the seam — with their status. They
do not stop you importing the repurpose engine, and you should not silently "fix" them in ours. Log them,
apply what is decided, and integrate around the rest.*

---

## 1. What the numbers are

Measured on the 20 fresh folders delivered 2026-10-24 (the "B3" batch) and on the two October JEV filter
reports (146 scored rows, 106 distinct releases). Full evidence: `Jev\filter_stage\FORMULATION.md`,
`analysis\imageeval\receive_feedback.md` (both in the source repository; the measurement scripts stay
with MG because they need the client corpus and `openpyxl`).

## 2. Receive stage

| # | issue | measured | status | what you do |
|---|---|---|---|---|
| R1 | **Pictures inside `.pdf`/`.docx` are not extracted** | 7 of 20 folders arrived with no picture at all; 115 images had to be mined out of the attachments downstream | **open — your stage** | extract embedded media into `images\`; then the folder can be drafted |
| R2 | **A published picture was never delivered at all** | 9 of 20; in 4 of them the asset could not be named from the release text, so a different picture would be published | **open — you + MSME** | if the sender's featured image is a brand/event logo, it must arrive as a file; record a **named missing asset** rather than passing the folder on silently |
| R3 | **One e-mail can hold more than one release** | not yet measured in your pipeline | **open** | if true, split into one folder per article; this export's `preflight` refuses an ambiguous folder instead of choosing one |
| R4 | `link.md` quality | 20/20 clean on the last batch (was the worst defect in batch 1) | **closed for now** | keep the check |

## 3. Filter stage

| # | issue | measured | status | what you do |
|---|---|---|---|---|
| F1 | **The cut was 60; our measured operating point is 62** | agreement unchanged at 123/145 = 84.83 %; false accepts 13 → 9; false rejects 9 → 13; self-flip 3/19 → 1/19 | **measured — D-019; the cut is YOUR tunable** | set 62 if your engine exposes it, else leave it and say so (D-023); re-score the same batch and compare with 123/145 |
| F2 | **The gate run is not deterministic** | the same 19 releases scored twice flip decision on 3 at cut 60 (1 at cut 62); |WAS| delta mean ~2 points | **open — your stage** | pin temperature or average k runs; publish the self-flip count with every batch |
| F3 | **`c10` (political advocacy) points the wrong way** | AUC **0.306** (below 0.5 = anti-predictive) with weight **6 of 99** | **open — not fixed** | do **not** hand-edit the weight. See §4 |
| F4 | `c11` (overall editorial test) has AUC 0.772 but weight 1 | promoting it to 12 measures **worse** (84.14 %), because it correlates with `c1`/`c2` | **not a bug** | leave it; the information is already in the pool |
| F5 | **Six guideline filters have no gate** | no gate for events/awards, duplication, hard-sell, etc. | **open — design** | report them as gaps; do not invent gates during integration |
| F6 | The ceiling of these 11 gates is ≈ **85.52 %** (any weighting) / 88.68 % (5-NN, no formula) | measured leave-one-out | **open** | do not promise 100 %; a higher in-sample number is usually fitting |

## 4. How the weight set is produced — and why F3 must not be hand-patched

The weights are **not fitted**. Each weight is the gate's own measured separation (mean score on MSME
accepted minus mean on MSME rejected, floored at 0) — `W_MEASURED` in `filter_stage.py`. The only
adjustment the measurement justified is `W_ADJUSTED`: switch `c10` to **0** and promote `c11` to 12.

That matters for your integration:

- **If you set the cut to 62 and leave the weights alone**, you are running the rule MG approved (D-019).
  That is the intended state.
- **If you zero `c10` by hand** without re-deriving the rest, you have changed the rule in a way nobody
  measured. The measured variant is `W_ADJUSTED`; it is recorded, not shipped, because re-weighting is
  `T-023` and is **not** decided.
- **When `c10` is re-worded later**, the fix must also re-run the weight derivation (`filter_stage.py
  fit`) — a new definition changes that gate's separation, and therefore its weight. A re-word without a
  re-fit would leave the rule internally inconsistent.

**So the correct statement to carry into your integration is:** *the cut is 62; `c10` is known
wrong-way and unfixed (MG's decision T-023 = B: leave it, carry the caveat); the weight vector must not
be hand-patched, and a future `c10` fix is a re-word plus a re-fit.*

The instrument behind these numbers is exported as `filter_stage/` — see `FILTER_KIT.md` for what it
measures, its one dependency (`openpyxl` for `parse`), and your three options (integrate / defer /
ignore).

## 5. What to do in your integration (and what not to)

Do:

1. add a `KNOWN_ISSUES` row to your `INTEGRATION_REPORT.md` for each of R1–R3, F1–F3 that is present at
   your side, with your own evidence;
2. measure the cut if your filter exposes it as configuration (62 is the value measured on the 2026-10
   batch; where it is stored is your decision, D-023);
3. keep the per-gate outputs available — without them the next measurement round cannot diagnose;
4. tell MG which of these you **cannot** reproduce, because that is a divergence worth knowing.

Do **not**:

- change the repurpose engine to compensate for a filter issue — the seam exists so each side can be
  measured separately;
- edit `W_SHEET` / `W_INDEX` to "fix" `c10`;
- report agreement without the self-flip count (F2), or a percentage without its denominator;
- mark F1–F3 resolved in your report unless you re-measured them.

## 6. Why these do not stop the import

The repurpose → validate → `.html` chain does not read the filter's score. A folder that passed your
filter is the only input. So integration can proceed while F2/F3 are open; what changes is the **quality
of the upstream selection**, not whether the article can be drafted. The one thing that can block a
folder is R1–R3 (no picture, missing asset, ambiguous folder) — and `preflight` names each of those
before a model call.
