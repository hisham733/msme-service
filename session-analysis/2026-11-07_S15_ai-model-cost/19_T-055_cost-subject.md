# 19 — Cost dashboard: email subject column

_2026-11-07 (S15)._

## 1. What changed

- `static/ai-model.html` — the Cost table now shows a **Subject** column right after the Email ID
  (truncated with an ellipsis; the full subject is in the cell's tooltip). Search already matched
  subject, so no API change was needed.
- Rebuilt the container so the served page includes it.

## 2. Verification

| Check | Result |
|---|---|
| Served `ai-model.html` | contains `<th>Subject</th>` + the subject cell render |
| `/api/costs.json` rows | carry `subject` (e.g. "Fwd: [FOR IMMEDIATE RELEASE] 31% of Malaysian cart abandonments…") |
| Container | rebuilt, `/health` 200 |

✅ nothing to decide.

## Recap

| # | Item | State |
|---|---|---|
| 1 | Subject column on the Cost table | done |
| 2 | Full subject in the tooltip | done |
| 3 | Rebuilt + verified | yes |
