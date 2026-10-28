# i-City — shared-drive folder was invisible; now ready

**Session:** 2026-10-22_S02 · **Turn:** 31 · **Image:** `msme-service:shared-drive-20261022`
**IDs:** D22 · T-034

## 1. Why it was not ready

The Drive link is a folder in a **shared drive** (`driveId: 0AMnBpjEPxFL7Uk9PVA`). The Drive API’s
`files.list` omits shared-drive items unless `supportsAllDrives` / `includeItemsFromAllDrives` are set, so
the pipeline saw **0 files** and recorded an empty folder → no article, no media.

With the flags, the folder contains:

| File | Size |
|---|---|
| `Photo.png` | 15.4 MB |
| `Photo Caption.docx` | 416 KB |
| release **PDF** | 304 KB |
| release **DOCX** | 2.45 MB |

## 2. Fixed

`drive_fetch._list_children` now passes `supportsAllDrives=True` + `includeItemsFromAllDrives=True`;
`fetch_file` metadata and `_download` pass `supportsAllDrives=True`.

**Live run `ed396fdb-…`:** release PDF selected, `Photo.png` counted → `hasArticle=true`,
`hasPic=true`, subject **99**, **`readyToFilter=true`**; row 368; release originals + photo archived.

## 3. Totals

**149 emails · 131 ready · 18 not ready**; asks **12** (i-City removed).
Old i-City rows are hidden by the latest-row dedupe.
