# Process token cost — measured

_Measured 2026-10-30 (receive/filter) and re-measured 2026-11-07 (N-9 engine cost test) from the
live SQLite data. No guessed prices; the DeepSeek rate is the measured D27 A/B cost and the Jev rate
is from `docs/filter/2_JEV_LLM-vs-JEV.md`._

> **Live dashboard (2026-11-07, `T-055`/`D42`):** `/ai-model.html` → **Cost** tab (admin only)
> shows total spend, chain spend, avg/email, avg/published, stage split, a budget bar, a 14-day
> sparkline and a per-email table; `/api/costs.json` powers it. The repurpose engine records usage
> in `run.json` and `repurpose_runs.usage_json`, so the publish stage is priced from **real runs**
> (N-9: 9 runs, §4). Rates are editable on **Config → Cost**. The figures below are the measurement
> record.

## 1. Short answer

| Part | Average per article | Cost at the measured rates |
|---|---|---:|
| Receive (DeepSeek) | **12,634 tokens** (8,381 in / 4,253 out) | **≈ $0.0082** |
| Filter (Jev) | **2,238 input tokens** | **≈ $0.0001** |
| **Receive + filter** (per received email) | — | **≈ $0.0083** |
| Repurpose engine (draft + vision) | **55,364 tokens** (9 runs; validated **46,462**) | **≈ $0.0360** (validated **≈ $0.0302**) |
| **Full chain** (per published article) | — | **≈ $0.0385** (range **$0.023–$0.069**) |

At these rates **100 received emails ≈ $0.83**, and **100 published articles ≈ $3.85** (validated;
$4.43 if HOLD/retry runs are included). The call's preliminary **~7¢** is the **worst case**
(vision-heavy, retried); a typical published article is **~3.9¢**. The active DeepSeek balance is
**$8.39** (measured 2026-11-07, N-9 cost test).

## 2. Receive — measured

Source: latest **successful** `pipeline_results` run per email; the `tokens` stage; the
`deepseek/deepseek-flash` model. **169 emails** with token data.

| Metric | Prompt | Completion | Total |
|---|---:|---:|---:|
| Average | 8,381 | 4,253 | **12,634** |
| Median | 7,501 | 3,586 | 11,855 |
| Minimum | 4,063 | 569 | 4,782 |
| Maximum | 35,478 | 11,834 | 39,154 |

Largest in the current sample: Meltwater Digital 2027 and Malaysia Trade Performance at the top
(~39k); Mercedes-AMG 32,182; BWH Hotels 27,400; EAP media package 26,811.

Smallest: EnerGex 4,782; BPMB 5,277; Google OAuth notice 6,095; Sustainable Action 6,251;
MSECC 6,346.

### Cost basis

D27 measured **$0.10 for 12 email runs** → **$0.0083 per receive run**. That is the blended
DeepSeek rate at the current model: **≈ $0.65 per 1M total tokens**. The official price can
change; the D27 figure is the measured one.

## 3. Filter — measured

Source: `filter_results` verdict `usage`, model `jev-1.14.0`; **30 results** (including the Meltwater filter result).

| Metric | Input | Output | Total |
|---|---:|---:|---:|
| Average | 2,238 | 273 | **2,511** |
| Minimum | 1,407 | 273 | 1,680 |
| Maximum | 3,338 | 273 | 3,611 |

Jev is input-token priced: **$0.042 per 1M input**, output free. 2,251 input →
**≈ $0.000095**. With the documented overhead (≈ $0.00015/article) use **$0.0001–0.00015**.

## 4. Repurpose engine — measured (N-9, 2026-11-07)

The engine records per-run usage in `run.json` / `repurpose_runs.usage_json` (D42 / T-055). **Nine
runs** measured — 3 already in the live DB (AFFIN, MATRADE, Xendit) plus 6 fresh engine runs on real
archived articles (BWH Hotels, Ant International, APAC CEOs, Meltwater, Tourism Malaysia, BigSeller).
The receive/filter figures above come from the stored data; the engine is the measured gap.

| Set | n | avg tokens | median | min | max | avg cost |
|---|---:|---:|---:|---:|---:|---:|
| **All runs** | 9 | 55,364 | 59,118 | 24,033 | 93,826 | **$0.0360** |
| **Validated (published)** | 6 | 46,462 | 45,406 | 24,033 | 63,525 | **$0.0302** |
| **HOLD (validator retries)** | 3 | 73,166 | 66,554 | 59,118 | 93,826 | **$0.0476** |

Per run: BWH 40,864 · Ant 63,525 · APAC 59,539 · Meltwater 59,118 (HOLD) · Tourism 93,826 (HOLD) ·
BigSeller 24,033 · AFFIN 46,404 · MATRADE 44,409 · Xendit 66,554 (HOLD).

**Why the call's ~7¢ is close but high:** the worst observed run (Tourism, 93,826 tokens = $0.061
engine) gives a full chain of **~$0.069** — that is the "7¢" figure. A HOLD run re-drafts (validator
retries), so it costs more than a clean published article. The typical **published** article is
**~3.9¢** full chain.

The engine's usage field is now present, so the publish stage is priced from real runs — the old
"not measured" gap is closed.

## 5. Worked examples

| Case | Receive tokens | Receive cost | Filter tokens | Filter cost |
|---|---:|---:|---:|---:|
| **Meltwater Digital 2027** (906-page PDF) | **48,909** (35,360 / 13,549) | **≈ $0.032** | 2,299 / 273 | ≈ $0.0001 |
| **Tenun Nusantara** test | 7,139 (4,468 / 2,671) | ≈ $0.0047 | 2,365 (2,092 / 273) | ≈ $0.0001 |
| Average email | 12,799 | ≈ $0.0083 | 2,522 | ≈ $0.0001 |

The Meltwater report is the **largest** case — 3.8× the average receive tokens — because of the
906-page PDF (capped by D25 at 30 pages / 150k chars). Its successful run was 05:56 on 23 Oct;
the latest re-run (06:29) failed at verify with a 402 and stored 0 tokens. The current key checks
OK at $8.82.

The Meltwater was **filtered from the archive** on 30 Oct: **ACCEPT 76**, filter result **24**,
Jev usage **2,299 / 273**. Its scores are SME relevance 0.64, SME voice 0.91, geographic 0.22,
overall 0.68 — a **global report**, not a Malaysia-specific story. Under the suggested
article-type / local-development review it would be an editor-review case. The repurpose worker
created a draft at **11:14 MYT** (status `drafted`); the image/validator step is still running
(`image_rung=logo`, no image file); the local page is not built yet.

## 6. What is not measured / caveats

- **Repurpose engine:** measured 2026-11-07 across 9 runs (see §4); usage comes from
  `repurpose_runs.usage_json` / `run.json`.
- **DeepSeek price:** **$0.65 per 1M total tokens** (the measured D27 blended rate, not a vendor
  quote); the current model is **`deepseek-flash`**. Re-check the invoice if the model or price changes.
- **Jev price:** input $0.042/M, output free, from `docs/filter/2_JEV_LLM-vs-JEV.md`; the current plan may
  differ.
- **Keys:** the service uses the settings key and the engine uses the same creds/key — balance
  **$8.39** now (after the N-9 test). `creds/deepseek.json` may hold an older key at $0.

## 7. Budget view

| Articles | Received emails (receive + filter) | Published articles (full chain, validated) |
|---|---:|---:|
| 50 | ≈ $0.42 | ≈ $1.93 |
| 100 | ≈ $0.83 | ≈ $3.85 |
| 500 | ≈ $4.15 | ≈ $19.25 |
| 1,000 | ≈ $8.30 | ≈ $38.50 |

The current **$8.39** balance covers roughly **1,000 received emails** or **~217 published articles**
(at ~3.9¢ full chain; fewer if many HOLD/retry runs, at ~5.6¢ each).

## 8. How to re-measure

```bash
python3 - <<'PY'
import db, statistics
rows = db.list_pipeline_results(limit=2000)
latest = {}
for r in rows:
    if r.get("status") != "success":
        continue
    eid = r["email_id"]
    if eid not in latest or r["created_at"] > latest[eid]["created_at"]:
        latest[eid] = r
vals = [((r["stages"] or {}).get("tokens") or {}).get("detail") or {} for r in latest.values()]
vals = [t for t in vals if t.get("total")]
print("n", len(vals))
for k in ("prompt", "completion", "total"):
    xs = [t[k] for t in vals]
    print(k, "avg", round(statistics.mean(xs)), "median", round(statistics.median(xs)),
          "min", min(xs), "max", max(xs))
PY
```

The filter usage is in `filter_results.verdict.usage`; the engine usage is in
`repurpose_runs.usage_json` (and each folder's `run.json` → `usage`);
`check_deepseek_key.py` prints the active balance without printing the key.
