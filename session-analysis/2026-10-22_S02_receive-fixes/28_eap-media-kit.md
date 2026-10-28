# EAP media-kit link — fixed and ready

**Session:** 2026-10-22_S02 · **Turn:** 28 · **Image:** `msme-service:media-kit-link-20261022`
**IDs:** D19 · T-031

## 1. The link

`https://bit.ly/mem-oct2026` resolves to:

```
https://drive.google.com/drive/folders/1Pn55saEt7ktYelWTqWzjNDeMqKLTykuh
```

The pipeline previously relied on normalize's redirect list; on the re-run the link was not in it, so the
kit was skipped. Fixed: a non-Drive/OneDrive/Box `linkToFetch` is now resolved **directly**, and the final
Drive folder/file or OneDrive share is used.

## 2. What the kit contains

| File | Text |
|---|---:|
| `Macro Poverty Outlook - Malaysia - October 2026.pdf` | 9,511 chars (the report) |
| `Media Advisory - October 2026 EAP EU & MEM Part 1.pdf` | 2,360 chars (briefing invitation) |

No separate press-release document. The report was selected as the substantive article; the advisory has
an embedded logo.

## 3. Live result

Run `356dfd62-…` → row 363: `hasArticle=true`, `hasLogoInArticle=true`, subject **78**,
**`readyToFilter=true`**; archive has `MALAYSIA.md` + both PDFs.

Old EAP rows are hidden by the latest-row dedupe.

## 4. Totals

**149 emails · 128 ready · 21 not ready** (EAP removed from the not-ready list; asks unchanged at 14).
