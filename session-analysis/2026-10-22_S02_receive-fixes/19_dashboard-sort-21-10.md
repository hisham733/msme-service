# Dashboard — received date, newest → oldest

**Session:** 2026-10-22_S02 · **Turn:** 19 · **Image:** `msme-service:dashboard-sort-20261022`

---

## 1. What changed

- The Checklist dashboard now sorts by **received date, latest → oldest**.
- The date column displays **DD/MM** (e.g. `21/10`) and the search box matches it — type `21/10` (or
  `21 Oc`) to filter.
- Original date string kept in the cell tooltip.

⭐ **Decision — §1:** ✅ nothing to decide.

---

## 2. Records received on 21/10 — 7 rows (newest date at the top)

| Date | Subject | Ready | Article | Pic | Logo |
|---|---|---|:--:|:--:|:--:|
| 21/10 | APAC CEOs — AI & geopolitical pressures *(run 1)* | ✅ | ✅ | — | — |
| 21/10 | APAC CEOs — AI & geopolitical pressures *(run 2 — OneDrive re-run)* | ✅ | ✅ | — | — |
| 21/10 | Mercedes-Benz Malaysia — regional HQ | ✅ | ✅ | ✅ | — |
| 21/10 | The Throne Awaits — National Luminous Dragon King | ✅ | ✅ | ✅ | ✅ |
| 21/10 | Setia Awan Land — industrial ecosystems | ✅ | ✅ | ✅ | — |
| 21/10 | **MATRADE — Malaysia Pavilion SEMICON WEST** | ❌ | ❌ | — | ✅ |
| 21/10 | SME Bank — RM2.8 billion for entrepreneurs | ✅ | ✅ | ✅ | — |

**Notes**

- APAC appears **twice** because it was run twice today (earlier + OneDrive re-run). Same thread; the
  dashboard shows both checklist rows by design.
- MATRADE is the `needs_human` row: the Drive link is a **Google-native file** (not Doc/PDF), so the release
  text is missing; logo present. `T-027`.

⭐ **Decision — §2:** ✅ nothing to decide.

---

## 3. Still blocking new receives

`GET /api/emails` still returns `invalid_grant: Token has been expired or revoked` (`T-028`). The
dashboard **table** works from SQLite; only the Gmail dropdown/new receives are blocked until re-auth.

⭐ **Decision — §3:** ✅ nothing new to decide.

---

## What I recommend next

Re-auth Gmail (`T-028`) before any new receive. The 21/10 rows are now at the top of the dashboard with
`21/10` in the date column.
