# 18 — Cost: estimate vs real, and live auto-refresh

_2026-11-07 (S15) · follow-up to N-9._

## 1. Answer: is the cost real, and does it depend on the config?

- **The per-article money is an ESTIMATE**, not the vendor invoice. The **token counts are real**
  (read from each API response), but the dollars = tokens × the editable rates
  (`COST_DEEPSEEK_PER_M`, `COST_JEV_INPUT_PER_M`, `COST_GEMINI_PER_M`). Change a rate on
  **Config → Cost** and the displayed cost changes on the next refresh — same tokens, different money.
- **The only real money figure is the DeepSeek balance** (vendor `/user/balance`). Before this change
  the page did not show it; it now does.

## 2. What was added (live / auto)

- `msme/cost.py` → `real_balance()`: fetches `https://api.deepseek.com/user/balance` (server-side, the
  configured key). Never raises; returns `{available, balance, currency, error, checked_at}`.
- `msme/receive/dashboard.py` → `GET /api/costs/balance` (admin-only; 401 without a session).
- `static/ai-model.html` → the Budget/credit card now shows **Real DeepSeek balance** (with the time),
  and the page **auto-refreshes**: the estimate every **30 s**, the balance every **60 s**, paused when
  the tab is hidden. No manual reload needed.

## 3. Verification

| Check | Result |
|---|---|
| `/api/costs/balance` (admin) | `{"available": true, "balance": 8.35, "currency": "USD"}` |
| Without a session | **401** (admin-only) |
| Served `ai-model.html` | contains the balance element + `api/costs/balance` + `setInterval` |
| Tests | `tests.test_cost` 10 pass · compile OK |
| Container | rebuilt, `/health` 200 |

## 4. Notes / limits

- "Realtime" here is **polling** (30 s / 60 s), not push: the estimate updates as new runs land in the
  DB; the balance is the live vendor figure at the last poll.
- The estimate still excludes any API spend that was not logged in `pipeline_results` /
  `filter_results` / `repurpose_runs` (e.g. the 6 N-9 temp-folder engine runs, ≈ $0.26). The balance
  reflects that spend; the estimated "total" does not.
- The budget bar uses `COST_BUDGET_USD`; set it to `balance + logged_spend` so "remaining" matches the
  real balance (currently 10.64 → 8.39; the live balance now reads 8.35).

✅ nothing to decide — the Cost page now shows the real balance and auto-refreshes; the estimate depends
on the config rates as designed.

## Recap

| # | Item | State |
|---|---|---|
| 1 | Estimate vs real explained | estimate from tokens; balance is real |
| 2 | Live balance endpoint | `/api/costs/balance` (admin) |
| 3 | Real balance on the page | done |
| 4 | Auto-refresh (30 s / 60 s) | done |
| 5 | Verified + rebuilt | yes |

## What I recommend next

Carry on in this session (low effort): if you want the estimated "total spend" to match the balance
exactly, log the N-9 temp-folder runs into `repurpose_runs` (or subtract the untracked spend) — a small
reconciliation. Otherwise the remaining unblocked N-work is the N-7 engine tests (waiting on MSME's
answers for the ranges).
