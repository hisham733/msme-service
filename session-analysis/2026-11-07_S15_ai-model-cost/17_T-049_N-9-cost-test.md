# 17 — N-9 cost test measured (engine + full chain)

_2026-11-07 (S15) · "run 6 more / full / recommended / both / set it"._

## 1. What was run

- **6 fresh engine runs** on real archived articles (mix of size and images): BWH Hotels, Ant
  International, APAC CEOs, Meltwater, Tourism Malaysia, BigSeller.
- **+3 existing** live runs (AFFIN, MATRADE, Xendit) → **9 engine samples**.
- Receive/filter figures come from the stored data (169 receive, 30 filter).

## 2. Measured (at $0.65/M DeepSeek, $0.042/M Jev input)

| Stage | Sample | Tokens | Cost |
|---|---|---|---|
| Receive | 169 emails | avg 12,634 | $0.0082 |
| Filter | 30 results | avg 2,238 input | $0.0001 |
| Engine (all) | 9 runs | avg 55,364; median 59,118; range 24,033–93,826 | **$0.0360** |
| Engine (validated) | 6 | avg 46,462 | $0.0302 |
| Engine (HOLD) | 3 | avg 73,166 | $0.0476 |

**Both figures you asked for:**
- **Per received email** (receive + filter): **≈ $0.0083 (0.83¢)** → 100 emails ≈ **$0.83**.
- **Per published article** (receive + filter + engine, validated): **≈ $0.0385 (3.85¢)** → 100 ≈ $3.85.
- Worst observed (vision-heavy Tourism, HOLD): **≈ $0.069 (6.9¢)** — this is the call's **~7¢**.

So the call's 7¢ is the **worst case**; the typical published article is **~3.9¢**.

## 3. Doc + settings + verification

- `docs/operations/PROCESS-TOKEN-COST.md` updated: §1 short answer, §2/§3 refreshed, §4
  "not measured" → measured (9-run table), §6 caveats, §7 budget view, §8 re-measure.
- `data/settings.json` → `COST_BUDGET_USD = 10.64` (= balance $8.39 + logged spend $2.25), so the
  Cost page's **remaining** now equals the real balance.
- **Dashboard verified on values:** a DB recompute of `cost.build_summary` and the live
  `/api/costs.json` return identical numbers (`avg_per_email 0.008799`, `chain total 1.49577`,
  `budget remaining 8.392`). `tests.test_cost` — 10 pass.
- `T-049` N-9 marked done; registers regenerated.

## 4. Notes / caveats

- The 6 fresh engine runs were on **temp folders**, so they are **not** in `repurpose_runs`: the
  Cost page's "total spend" card is **~$0.26 low** (the balance correctly dropped $8.65 → $8.39).
- The Cost page's `avg_per_published` (5.1¢) is **repurpose-only divided by published count**
  (it includes a HOLD run in the numerator). The doc's **3.9¢** is the true full chain
  (receive + filter + validated engine); use that for pricing.
- HOLD runs cost more because the validator re-drafts (retries).

✅ nothing to decide — N-9 measured and recorded; the 7¢ is now replaced by 0.8¢/email and 3.9¢/published (worst 6.9¢).

## Recap

| # | Item | State |
|---|---|---|
| 1 | 6 fresh engine runs (+3 existing) | done |
| 2 | Engine cost measured (9 runs) | $0.0360 avg |
| 3 | Full chain per published article | ≈ $0.0385 |
| 4 | PROCESS-TOKEN-COST.md updated | done |
| 5 | Budget bar set ($8.39 remaining) | done |
| 6 | /api/costs.json verified vs DB | equal |

## What I recommend next

Carry on in this session (low effort): the remaining unblocked N-work is **N-7** (engine chunk/image
rules — now fully specified and backed by the 100-post data, waiting only on MSME's answers). N-5 also
waits on MSME. If you want a build that needs no answers, I can turn the N-7 measurement into the
engine tests first (the 10 cases), so the code change is mechanical when MSME confirms.
