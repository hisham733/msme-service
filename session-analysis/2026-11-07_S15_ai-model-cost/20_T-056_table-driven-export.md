# 20 — Table-driven export (T-056 Phase 3) — the Xendit email published

_2026-11-07 (S15) · "go with A"._

## 1. Why it hadn't published

The Xendit email was **ready** (`readyToFilter=true`, filter **ACCEPT 85**) but the repurpose engine
**HELD** it: the inbox `images/` was empty, so `FEATURED_EXISTS/RENAME/CAPTION` failed. Root cause: the
export picked the wrong archive copy — the `received-2026-10-15-and-above/…` folder (no images) beat
the fresh `…_4/` folder where the **Xendit gallery logo** actually was. The `email_media` table **did**
have the logo (`source=gallery`, `chosen=1`, 600×183); the old export just never read it.

## 2. What was built (Phase 3 — table-driven export)

- `msme/receive/media_index.py` — stores the **real archive path** in `email_media.path` (resolves
  `images/`, `originals/`, and the `_1` collision suffix).
- `msme/repurpose/repurpose_export.py` — new `_copy_media()` / `_media_source()`:
  - copies each `email_media` row's file into the inbox `images/` (by `path`, with an archive `rglob`
    fallback for old rows);
  - the **skip branch now adds missing media to an existing draft** (plus `meta.json` from
    `email_links`) so a HOLD article can be re-validated.
- This removes the folder-ranking guess entirely for images.

## 3. Live proof — the Xendit email is now published

- Export copied the logo → `repurpose_inbox/…/images/xendit_07-November-2026_MALAYSIA-SME.png`.
- Re-ran the image choice on the folder → the draft's `## Images` now names the file, rung `logo`,
  renamed `Xendit_October_2026_MALAYSIA-SME.png`, caption "Xendit logo."
- Validator **ok**; `run.json` → `validated`; `build_all` rebuilt the site.
- **Page:** `repurpose_site/articles/xendit-report-finds-malaysia-s-e-wallet-payments-up-286-as-duitnow-qr-.html`
  (featured image present in `repurpose_site/images/`). `repurpose_runs.status = validated`.

## 4. Verification

| Check | Result |
|---|---|
| Full suite | **294 tests OK** (8 skipped; +3: archive-path resolve, export copies table media, skip branch adds media) |
| Container | rebuilt; `/health` 200; `repurpose_export` has `_copy_media`/`_media_source` |
| Xendit | page built + logo copied + `repurpose_runs=validated` |

## 5. Notes

- The engine is still file-based; the **export** now materialises the folder from the tables (option A).
- Old `email_media` rows (path = bare filename) still work via the archive `rglob` fallback.
- The 6 N-9 temp engine runs are unrelated (temp folders) and not in `repurpose_runs`.

✅ nothing to decide — the tables now drive repurpose, and the Xendit article is live.

## Recap

| # | Item | State |
|---|---|---|
| 1 | Store archived path in `email_media` | done |
| 2 | Export reads `email_media` + `email_links` | done |
| 3 | Skip branch adds missing media to a draft | done |
| 4 | Xendit email published | done |
| 5 | Tests + container | 294 pass; rebuilt |
