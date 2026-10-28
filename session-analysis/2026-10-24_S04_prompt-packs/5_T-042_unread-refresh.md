# T-042 fixed — Refresh is unread-only, and a single Run marks the email read

**Session:** 2026-10-24_S04 · **Turn:** 5 · **IDs:** T-042
**Verified live:** `GET /api/emails?force=1` → **2 emails, both `UNREAD`**; cache **2** (was 50).

---

## 1. What changed

- **`gmail.list_unread(..., unread_only=True)`** appends `is:unread` when the query lacks it;
  the reply thread lookup (`dashboard.py:436`, `thread:… in:anywhere`) passes
  `unread_only=False`.
- **Defaults/live config** now use `in:inbox is:unread -category:promotions` in `config.py`,
  `settings_store.py`, `data/settings.json` and `docker-compose.yml`.
- **Single Run marks read** in `dashboard._process_one` and `main._process_one` — both `success`
  and `needs_human`, as you chose; the duplicate `mark_read` in the run-all endpoints was removed.
- **Picker refreshes immediately after Run**: `success` and `needs_human` now call
  `loadEmails(true)`; `needs_human` stops polling instead of looping, and shows amber.
- The page-load cache is kept until Refresh, as you chose.

⭐ **Decision — §1:** ✅ nothing to decide — built as approved.

---

## 2. Verified

| Check | Result |
|---|---|
| Live Refresh (`force=1`) | **2 emails** |
| Every returned message has `UNREAD` | **2/2 true** |
| Cache after Refresh | **2 entries** (was 50 with read mail) |
| Query | `in:inbox is:unread -category:promotions` |
| Single-run mark-read | unit-tested for success + `needs_human` (not live-run, to avoid a write) |
| Tests | **52 pass** (8 new in `tools.test_gmail_unread`) |
| DB / archive | unchanged by the Refresh (cache only) |

⭐ **Decision — §2:** ✅ nothing to decide.

---

## 3. Behaviour notes

- The scheduler and `/run-all` now see only unread mail; they cannot re-process read emails.
- A single run now takes the email out of the queue: it is marked read and the picker force-refreshes.
- A `needs_human` run is also marked read (your choice); it is saved in the checklist and visible
  in the dashboard status.
- The first page load still shows the cached list; after one Refresh it is unread-only.

⭐ **Decision — §3:** ✅ nothing to decide.

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | Query enforces `is:unread` | **done** |
| 2 | Reply lookup exempt | **done** |
| 3 | Single run marks read (success + needs_human) | **done** |
| 4 | Picker refreshes after Run | **done** |
| 5 | Live Refresh | **2 unread / 0 read** |
| 6 | Tests | **52 pass** |

## What I recommend next

Move to **T-043** — make receive use the PitchMyStory published-release featured image
(1536×1024 WebP) and re-run Event Me Now; expected `readyToFilter=true`. Say **“go T-043”**.
