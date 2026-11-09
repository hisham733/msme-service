# 81 — By-sender dashboard built

_2026-11-06 (S14) · code + docs · live container rebuilt._

## 1. What changed

| File | Change |
|---|---|
| `static/by-email.html` (new) | summary by sender + click-through email list; dark checklist style |
| `msme/receive/dashboard.py` | `/by-email.html`, `/senders.html`, `/api/senders.json`, `/api/sender.json` |
| `msme/db.py` | `sender_summary()`, `sender_emails()`; `save_email(..., received_at=…)` for backfill |
| `msme/auth.py` | both roles can GET the page + APIs (`EDITOR_GET`) |
| `static/checklist.html` · `static/editor.html` | **By sender** nav link |
| `tools/backfill_emails.py` (new) | fill `emails` from Gmail for the 241 old checklist rows |
| `tests/test_senders_dashboard.py` (new, 6 tests) | counts, no double-count on re-runs, latest status, empty, unknown sender, date override |
| `static/INDEX.md` · `docs/workflow/DATABASE-FLOW.md` | page row + `emails` reader |

**The page:** `/by-email.html` and `/senders.html` (same page). Summary columns: **Sender · Name ·
Emails · Last received**. Click a sender → that sender's emails (subject, received, ready, **Open
email ↗**).

## 2. Verification

| Check | Result |
|---|---|
| `compileall` | **OK** |
| Full suite | **207 tests, OK** (8 client-material skipped) |
| Container rebuilt | `/health` **200** |
| `/by-email.html`, `/senders.html` | **302** → login (route exists, auth active) |
| `/api/senders.json` without a session | **401** (protected) |
| Page in the image | `/app/static/by-email.html` present |
| `db.sender_summary()` in the container | **0 senders** — the `emails` table is still empty |

✅ nothing to decide — the page and APIs work; the data is the missing part.

## 3. The one thing still needed: the backfill

The page is **empty** because the `emails` table has no rows yet. The tool is ready:

```bash
python3 tools/backfill_emails.py            # dry run — lists the 241 message ids
python3 tools/backfill_emails.py --apply    # fetch from Gmail + write
```

- It uses each email's **Date header** for `received_at`, so the timeline is correct.
- It needs a valid Gmail token. The token is currently `invalid_grant` (`T-028`), so the run will fail
  until Gmail is re-authenticated.
- After the backfill, the page shows **241 emails grouped by sender**.

⭐ Decision — §3: **re-authenticate Gmail now (A, recommended)** so I can run the backfill and show the
241 emails by sender before 11 Nov, or **leave it (B)** and the page stays empty.

## 4. What I recommend next

**Carry on in this session** (low effort): re-auth, run the backfill, then open `/by-email.html` and check
the counts. Reason: it is the only way the new page has data before the call.

| # | Item | State |
|---|---|---|
| 1 | By-sender page + APIs | done |
| 2 | 207 tests + live container | verified |
| 3 | Backfill tool | done, not run |
| 4 | Gmail token (`T-028`) | **open — user action** |
| 5 | Run the backfill and check the page | next |
