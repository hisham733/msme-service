# T-028 done — OAuth restored, MATRADE now ready

**Session:** 2026-10-22_S02 · **Turn:** 22 · **Image:** `msme-service:matrade-folder-20261022`

---

## 1. T-028 — re-auth succeeded

- OAuth consent completed at **15:49**; `creds/{gmail,drive,sheets}.json` now carry fresh access + refresh
  tokens (same client `279187771445-oicp…`).
- `/api/emails` works again (the Gmail list is back); Drive metadata works.
- Scope includes Gmail modify, Drive and Sheets.
- **Still recommended:** publish the OAuth consent screen to **Production**; if it is in Testing, refresh
  tokens expire again in 7 days.

⭐ **Decision — §1:** ✅ nothing to decide (re-auth done).

---

## 2. MATRADE — the Drive link was a **folder**

| Measured | |
|---|---|
| Link | `/file/d/1rAhZLrim7l5DRj9Et48uzJir71LWfA-x` |
| Metadata | `mimeType: application/vnd.google-apps.folder` — **a folder, not a file** |
| Contents | `[PRESS RELEASE] MATRADE-LED …docx` (5,155 chars), `Press Release Report.docx` (1,783), 3 photos (1.7–4.7 MB) + logo |
| Old behaviour | file branch → `unsupported_google_file` → `needs_human` |

**Fixed (`D18` / `T-029`):**
- a `/file/d/` link that resolves to a folder is fetched as a **media kit**;
- the picker now penalises `report`/`summary` names, so the **full release** wins over the short report.

**Live re-run `c09bbb5c-…`:** `hasArticle=true`, `hasPic=true` (3 photos), `hasLogo=true`,
`hasLogoInArticle=true`, subject **96**, **`readyToFilter=true`**; 4 images + both DOCX originals archived.

The earlier 21/10 MATRADE row remains as history (`not ready`); the **latest row is ready**. The dashboard
shows both because re-runs append rows.

⭐ **Decision — §2:** ✅ nothing to decide.

---

## 3. Records updated

- `docs/NOT-READY-TO-FILTER-2026-10-22.md` → **22 remaining** (was 23; MATRADE resolved).
- `docs/SENDER-ASKS-2026-10-22.md` → **14 asks** (MATRADE removed; a PDF is no longer needed).
- `T-027` closed (Google-native export support built/unit-tested; MATRADE was a folder, not a native file).
- `T-028` closed; `T-029` closed; `D18` recorded.

⭐ **Decision — §3:** ✅ nothing new to decide.

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | Gmail/Drive OAuth | **restored** |
| 2 | MATRADE link | was a **folder** → now fetched as a kit |
| 3 | MATRADE latest row | **ready** (subject 96, photos + logo) |
| 4 | Not-ready total | 22 |
| 5 | Asks | 14 |

## What I recommend next

Publish the OAuth app to Production to avoid a 7-day expiry. Then send the 14 asks + MSIA (`T-011`).
Repurpose (`T-001`) remains the next build.
