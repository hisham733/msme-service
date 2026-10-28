# Jobstreet — inline image was the logo; now ready

**Session:** 2026-10-22_S02 · **Turn:** 30 · **Image:** `msme-service:attachment-logo-20261022`
**IDs:** D21 · T-033

## 1. What was wrong

The email has the full commentary in the body (subject 95) and one attachment:

| | |
|---|---|
| Attachment | `inline_image`, `image/png`, 33,569 bytes |
| Actual image | **1033×275** — the **Jobstreet by SEEK logo** (verified visually) |
| Old flags | `hasLogo=false`, `hasPic=false` → not ready |

`hasLogo` only checked attachment **filenames** for "logo"; `hasPic` requires ≥1 MB. The wide logo was
also classified as a photo by dimensions. So the logo was present but never counted.

## 2. Fixed (`D21` / `T-033`)

- `_kind_from_bytes` now treats wide banners (`max/min ≥ 3.0`, `max ≥ 500`) as **logo**.
- Every standalone image attachment is classified; a logo ≥200 px sets **`hasLogo=true`** and is saved as
  `images/attachmentlogo-1.png`.
- Photos still need the deferred `D14` dimension rule for `hasPic`; this case is a logo.

**Live run `fb5cd9a2-…`:** row 365 → `hasArticle=true`, `hasLogo=true`, subject 95,
**`readyToFilter=true`**; the logo is archived.

## 3. Totals

**149 emails · 130 ready · 19 not ready**; asks **13** (Jobstreet removed). Old Jobstreet rows are hidden
by the latest-row dedupe.
