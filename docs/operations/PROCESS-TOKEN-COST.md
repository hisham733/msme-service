# Process token cost — measured

_Measured 2026-10-30 from the live SQLite data. No guessed prices; the DeepSeek rate is the
measured D27 A/B cost and the Jev rate is from `docs/filter/2_JEV_LLM-vs-JEV.md`._

> **Live dashboard (2026-11-07, `T-055`/`D42`):** `/ai-model.html` → **Cost** tab (admin only)
> shows total spend, chain spend, avg/email, avg/published, stage split, a budget bar, a 14-day
> sparkline and a per-email table; `/api/costs.json` powers it. The repurpose engine now records
> usage in `run.json` and `repurpose_runs.usage_json`, so the publish stage is priced from the
> next run. Rates are editable on **Config → Cost**. The figures below stay the measurement record.

## 1. Short answer

| Part | Average per email | Cost at the measured rates |
|---|---:|---:|
| Receive (DeepSeek) | **12,799 tokens** (8,485 in / 4,314 out) | **≈ $0.0083** |
| Filter (Jev) | **2,524 tokens** (2,251 in / 273 out) | **≈ $0.0001–0.00015** |
| **Receive + filter** | — | **≈ $0.0084** |
| Repurpose engine | **not recorded** | **not measured** (see §4) |

At this rate **100 emails ≈ $0.84** and **1,000 emails ≈ $8.40**, before the repurpose engine.
The active DeepSeek balance is **$8.82**.

## 2. Receive — measured

Source: latest **successful** `pipeline_results` run per email; the `tokens` stage; the
`deepseek/deepseek-flash` model. **168 emails** with token data.

| Metric | Prompt | Completion | Total |
|---|---:|---:|---:|
| Average | 8,485 | 4,314 | **12,799** |
| Median | 7,502 | 3,600 | 11,904 |
| Minimum | 3,926 | 569 | 4,782 |
| Maximum | 35,478 | 13,549 | 48,909 |

Largest: Meltwater Digital 2027 **48,909**; Malaysia Trade Performance 39,154; Mercedes-AMG
32,182; BWH Hotels 27,400; EAP media package 26,811.

Smallest: EnerGex 4,782; BPMB 5,277; Google OAuth notice 6,095; Sustainable Action 6,251;
MSECC 6,346.

### Cost basis

D27 measured **$0.10 for 12 email runs** → **$0.0083 per receive run**. That is the blended
DeepSeek rate at the current model: **≈ $0.65 per 1M total tokens**. The official price can
change; the D27 figure is the measured one.

## 3. Filter — measured

Source: `filter_results` verdict `usage`, model `jev-1.14.0`; **24 results** (including the Meltwater filter result).

| Metric | Input | Output | Total |
|---|---:|---:|---:|
| Average | 2,251 | 273 | **2,524** |
| Median | 2,249 | 273 | 2,522 |
| Minimum | 1,407 | 273 | 1,680 |
| Maximum | 3,338 | 273 | 3,611 |

Jev is input-token priced: **$0.042 per 1M input**, output free. 2,251 input →
**≈ $0.000095**. With the documented overhead (≈ $0.00015/article) use **$0.0001–0.00015**.

## 4. Repurpose engine — the gap

The vendored engine's `run.json` (in-process since `D40`) has **no token or usage field** (16 local
drafts checked). Its DeepSeek calls are therefore **not measured**. The same key/balance is used;
the engine is the only unmeasured part of the full receive → publish cost.

**Recommendation:** add `usage` (prompt/completion/total/model) to the engine's `run.json`; then
the full per-article cost can be quoted exactly.

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

- **Repurpose engine:** no usage field; see §4.
- **DeepSeek price:** the $0.0083/email is the measured D27 blended rate, not a vendor quote; the
  current model is `DeepSeek-V4.1-Flash-1017`. Re-check the invoice if the model or price changes.
- **Jev price:** input $0.042/M, output free, from `docs/filter/2_JEV_LLM-vs-JEV.md`; the current plan may
  differ.
- **Old key:** `creds/deepseek.json` holds an older key at $0 balance; the service uses the
  settings key and the engine uses its `.env` key — both at **$8.82** now.

## 7. Budget view

| Emails | Receive + filter | Plus engine |
|---:|---:|---:|
| 50 | ≈ $0.42 | not measured |
| 100 | ≈ $0.84 | not measured |
| 500 | ≈ $4.20 | not measured |
| 1,000 | ≈ $8.40 | not measured |

The current **$8.82** balance covers roughly **1,000 service runs** (or fewer if the Meltwater-size
PDFs are common) before the engine. Add engine usage logging before setting a hard monthly budget.

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

The filter usage is in `filter_results.verdict.usage`; `check_deepseek_key.py` prints the active
balance without printing the key.
