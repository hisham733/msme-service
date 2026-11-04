# Process token cost — measured

**Session:** 2026-10-30 · S09 · reply 1
**Document:** `docs/PROCESS-TOKEN-COST.md`
**State:** written and indexed; the Meltwater filter result is saved; the repurpose draft is
created and still in the image/validator step.

## 1. The average cost

| Part | Average per email | Cost |
|---|---:|---:|
| Receive (DeepSeek) | **12,799 tokens** (8,485 in / 4,314 out) | **≈ $0.0083** |
| Filter (Jev) | **2,524 tokens** (2,251 in / 273 out) | **≈ $0.0001–0.00015** |
| **Receive + filter** | — | **≈ $0.0084** |
| Repurpose engine | **not recorded** | **not measured** |

At the measured D27 rate, **100 emails ≈ $0.84** and **1,000 ≈ $8.40**, before the engine. The
active DeepSeek balance is **$8.82**.

Measured from **168** latest successful receive runs and **24** filter results. The largest receive
case is the Meltwater 2027 report at **48,909 tokens** (906-page PDF); the smallest is 4,782.

✅ nothing to decide.

## 2. The Meltwater email — processed from the archive

- The email was already received and archived; its checklist row **378** is `readyToFilter=true`.
- The Gmail token is still expired, so this was processed from the saved article, not by a new
  Gmail fetch.
- **Filter result 24: ACCEPT 76.** Scores: SME relevance 0.64, SME voice 0.91, commercial 0.84,
  substance 0.97, source 0.96, claims 0.62, timeliness 0.77, **geographic 0.22**, safety 0.71,
  overall 0.68.
- This is a **global report**; under the suggested article-type/local-development review it would
  be an **editor-review** case. The MSME may say it is not relevant.
- Repurpose: the export created the inbox folder; the worker has a **draft** (11:14, status
  `drafted`). The image step reports `image_rung=logo` with **no image file**, and the validator is
  still running. **The local page is not built yet.** If it fails, the issue is the report’s
  featured image/media, not the filter.
- Cost for this email: receive **≈ $0.032**, filter **≈ $0.0001**; the engine cost is not measured.

✅ nothing to decide.

## 3. The remaining gap

The repurpose engine’s `run.json` has **no usage field**, so the full receive → publish cost cannot
be quoted exactly. Recommendation: log `usage` (prompt/completion/total/model) in the engine’s
`run.json`; then the per-article cost is complete. The current balance is enough for roughly
1,000 service runs before the engine.

✅ nothing to decide.

## 4. What I recommend next

1. Let the Meltwater validator finish; if it holds on the featured image, add the report image or
   treat it as a media issue.
2. Add usage logging to the engine.
3. For the meeting/MD: treat the Meltwater as another **global-report** example for the
   article-type/local-development review, not only Ant/BWH.

## Recap

| Item | State |
|---|---|
| Cost document | `docs/PROCESS-TOKEN-COST.md` |
| Average receive | 12,799 tokens · ≈ $0.0083 |
| Average Jev | 2,524 tokens · ≈ $0.0001 |
| Meltwater filter | ACCEPT 76 · result 24 |
| Meltwater repurpose | Drafted; image/validator pending |
| Engine cost | Not recorded |
| Balance | $8.82 |
