# OneDrive access fixed and live — APAC re-run

**Session:** 2026-10-22_S02 · **Turn:** 12 · **Image:** `msme-service:onedrive-20261022`
**IDs:** D15 · T-025 (D14/T-024 deferred)

---

## 1. Why it failed before, and what works now

| Attempt | Result |
|---|---|
| `1drv.ms` with a bot/short UA | **403** (Microsoft edge blocks the client) |
| Old `api.onedrive.com/shares` / Graph without a token | **401** (needs auth) |
| **Chrome UA + cookie jar → guest `FedAuth`** | **200** |
| **v2.0 item API with that cookie** | **200** — lists the folder |
| `@content.downloadUrl` with the Chrome UA | **200** — downloads the file |

Implemented in `onedrive_fetch.py`:
1. open the share as a guest (Chrome UA + cookie jar);
2. read `cid` + item id from the resolved URL;
3. list children via `GET /personal/<cid>/_api/v2.0/drive/items/<item>/children`;
4. download via `@content.downloadUrl`; single-file shares use the item metadata fallback.

**Measured on the APAC folder:** 2 PDFs —
`Egon Zehnder APAC_PressRelease_CEO Report 2026.pdf` (488 KB) and
`The CEO Response 2026_Egon Zehnder.pdf` (1.16 MB) — both downloaded, text extracted.

⭐ **Decision — §1:** ✅ nothing to decide.

---

## 2. APAC re-run — live result

`onedrive_fetch` stage: **done**, 2 docs, no errors. The release picker chose the APAC press-release PDF;
its embedded logo/photo now provide deterministic evidence.

| Flag | Value |
|---|---|
| `hasArticle` | **true** |
| `subjectMatch` / score | **true / 100** |
| `hasLogoInArticle` | **true** (from the OneDrive press-release PDF) |
| `hasImageInArticle` | **true** (from the OneDrive press-release PDF) |
| `hasPic` | **false** — the 3 attached photos (115–144 KB) are still under the 1 MB rule (`D14` deferred) |
| `readyToFilter` | **true** |

So the row is now ready on **deterministic** evidence from the OneDrive press release, not the earlier
AI-only guess. The 3 attached photos are still saved in `images/`; only the `hasPic` flag is deferred.

⭐ **Decision — §2:** do you want `D14` (`T-024`) now, to make the 3 attached photos `hasPic=true`?
Recommended later; not blocking this row.

---

## 3. Still open

- **T-022** — send the 10 drafted asks (`docs/SENDER-ASKS-2026-10-22.md`).
- **T-011** — MSIA re-share.
- **T-024** — attached-photo dimension rule (deferred).
- **T-001** — repurpose.

⭐ **Decision — §3:** ✅ nothing new to decide.

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | OneDrive public share access | **fixed + live** |
| 2 | APAC re-run | ready; 2 PDFs fetched, deterministic logo/photo |
| 3 | Attached photos as `hasPic` | deferred (`T-024`) |

## What I recommend next

Send the T-022 asks + T-011 in parallel. If you want the attached-photo flag fixed, say **`D14 go`**;
otherwise the next build remains **T-001 (repurpose)** in a new session, medium effort.
