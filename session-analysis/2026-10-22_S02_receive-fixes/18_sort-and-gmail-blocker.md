# Sorted by date asc — and a Gmail blocker

**Session:** 2026-10-22_S02 · **Turn:** 18

---

## 1. Sorted lists

- `docs/NOT-READY-TO-FILTER-2026-10-22.md` — new **Chronological view — 23 remaining (date ascending)**;
  the 6 backlog rows in section D are now date-sorted too.
- `docs/SENDER-ASKS-2026-10-22.md` — the 15 asks now carry a **Date** column and are sorted ascending.

Order of the 6 backlog not-ready rows:

| Date | Email | Action |
|---|---|---|
| 28 Sep | BPMB logo/photos | ignore (asset-only) |
| 28 Sep | AICPA & CIMA opinion | ask for media |
| 29 Sep | ConverXion KL 2026 | ask for media |
| 30 Sep | Finnfund / EVF | ask for media |
| 2 Oct | Contributed Article (Atlas Copco) | ask for the article |
| 21 Oct | MATRADE SEMICON WEST | ask for PDF (`T-027`) |

⭐ **Decision — §1:** ✅ nothing to decide.

---

## 2. ⚠ Gmail is now blocked — refresh token expired

`GET /api/emails` returns:

```
invalid_grant: Token has been expired or revoked
```

The 46-email batch finished **before** the token died, so all **149 processed rows are safe** — but **new
emails cannot be received** until re-auth. `/api/health` is still OK because it does not call Gmail.

**Likely cause:** the OAuth consent screen is still in **Testing** (refresh tokens expire after 7 days), or
the client/consent changed. Logged as **`T-028`**.

**What you must do:**

1. Run `python3 reauth_google.py url` (or `oauth_catch.py`) with the live client
   `279187771445-oicp…`, open the consent URL, sign in as the newsroom account, and paste the code back.
2. In Google Cloud → OAuth consent screen, **Publish to Production** (long-lived refresh tokens) — or keep
   Testing and re-auth every 7 days.
3. Confirm the live client secret in `creds/gmail.json` matches the current Google client (ties to `D3`).

⭐ **Decision — §2:** publish the OAuth app (A, recommended) · keep Testing and re-auth every 7 days (B)?

---

## 3. State

- 149/149 inbox processed; no data loss.
- 23 not-ready (17 original + 6 backlog); 15 asks drafted.
- Future receives **blocked** until `T-028` is done.

⭐ **Decision — §3:** ✅ nothing else to decide.

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | Sort by date asc | done in both reports |
| 2 | Gmail refresh token | **expired/revoked — new receives blocked** |
| 3 | Existing rows | safe (149) |
| 4 | Fix | `T-028` — re-auth + publish OAuth |

## What I recommend next

Do **`T-028` first** (nothing new can be received without it). Then send the 15 asks + MSIA (`T-011`).
Repurpose (`T-001`) stays next after that.
