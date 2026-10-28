# MATRADE SEMICON WEST — why not ready, and the fix

**Session:** 2026-10-22_S02 · **Turn:** 20 · **Image:** `msme-service:google-native-20261022`
**IDs:** D17 · T-027 · T-028

---

## 1. Why it was not ready

| Measured | |
|---|---|
| Drive link | `…/file/d/1rAhZLrim7l5DRj9Et48uzJir71LWfA-x` — owner `communication@matrade.gov.my` |
| File | **Google-native**, size 0 — **not a PDF/DOCX** (Slides/Sheets/Drawing) |
| Old code | only exported a Google **Doc**; everything else → `unsupported_google_file` |
| Email body | only a MATRADE cover pitch, no full release |
| Result | `hasArticle=false`, `needs_human`; logo present but no article → not ready |

So the link was seen; the system could not read that **file type**.

⭐ **Decision — §1:** ✅ nothing to decide.

---

## 2. Fixed — Google-native export (`D17`)

`drive_fetch.fetch_file` now exports instead of rejecting:

- **Google Docs** → text;
- **Slides / Sheets** → **PDF** (text extracted + embedded images classified);
- **Drawings** → **PNG** (media asset);
- other Google-native types → still unsupported.

Unit test with a fake Drive service: Slides/Sheets → PDF with **9,036 chars** of text + image classification;
Drawing → PNG; Doc → text. Deployed in `msme-service:google-native-20261022`; health OK.

⭐ **Decision — §2:** ✅ nothing to decide.

---

## 3. Still blocking the live re-run

The **Gmail/Drive OAuth refresh token is expired** (`invalid_grant`) — `T-028`. The code is deployed, but the
service cannot call Google to export the MATRADE file until re-auth.

**After re-auth, re-run the MATRADE email; expected result:** the exported PDF text becomes the article,
the logo/photo are classified, and `readyToFilter` should be true. If the export is image-only, it will
still need a PDF from MATRADE (`T-027`).

⭐ **Decision — §3:** re-auth now (`T-028`: publish the OAuth app) — recommended; then I re-run MATRADE.

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | Why not ready | Google-native file + cover-only body |
| 2 | Export support | **built + unit-tested + deployed** |
| 3 | Live fetch/re-run | **blocked by expired OAuth (`T-028`)** |
| 4 | MATRADE row | still not ready until re-auth + re-run |

## What I recommend next

Do `T-028` (re-auth + publish the OAuth consent screen), then say **"re-run MATRADE"** — it should become
ready; if the export is image-only, send the PDF ask already drafted.
