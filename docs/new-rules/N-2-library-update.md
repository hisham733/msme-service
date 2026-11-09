# N-2 — “Library update” emails are not “no article”

_Status: spec for the 2026-11-11 MSME call · 2026-11-05 · **built 2026-11-07** (`msme/receive/library_update.py`, `D44`)._
_Source: 30-Oct 2026 MSME call `[26:45–28:12]`; `docs/meetings/2026-11-09/MEETING-BRIEF-2026-11.md:71`._

## 1. The rule

An email whose purpose is to send a **new logo or building photo** is a **gallery update**, not a
press release.

- File it as `library_update`.
- Store the assets in the gallery.
- **Do not** mark it “no article” in the UI.
- **Do not** send the “send us the article” reply.
- Do not run the filter.

Example: **BPMB Group Logo and Building Photographs** (`[27:14]`). The AI said “no article”, which is
factually correct; the fix is the *classification*, not the email (`[27:45]`, `[28:12]`).

## 2. Current behaviour (verified)

- A no-article email still gets a checklist row, is archived, and then `pipeline.py:1454` sends the
  rejection reply because `readyToFilter=false`.
- The checklist has only the 14 contract columns — there is **no email category**.
- `_no_article/` is a **manual sort tool** (`tools/reorganize_archive.py`), not a pipeline category.
- No gallery store exists yet; N-1 creates it.

## 3. Detection — after extract (decision 1 = B)

The classifier runs **after `extract.extract(...)`**, when the article text and all collected media are
known, and **before Verify**:

```text
decide → collect media → extract → [library_update check] → verify → filter → reply
```

Why after extract: a short body must never be classified as an update while the extract AI can still
prove an article exists. The cost is one extract call per update — acceptable.

On a confident hit: **skip Verify, Filter and Reply**, store the assets, write the `library_update`
row, and return. On anything ambiguous: continue to Verify exactly as today.

### 3.1 Signals

A hit needs **all three**:

1. **No article text** — `body_text` is shorter than 400 characters, and no ranked candidate carries
   ≥400 characters of text.
2. **At least two positive signals:**
   - subject/body phrase: “new logo”, “updated logo”, “logo update”, “building photograph”,
     “building photo”, “facade”, “update our records”, “for your records”, “update our library”;
   - attachments are images only (`logo`, `building`, `.png/.jpg`) and no release DOCX/PDF;
   - Decide returned `chosenFileName=""` and `imagesAvailable=true`.
3. **Zero negative signals:**
   - “for immediate release”, “press release”, “media release”, “siaran akhbar”;
   - a report/contribute/byline marker;
   - any candidate with ≥400 characters.

If `needs_human=true` and no asset was collected, the normal path runs.

### 3.2 Insertion point

After the logo scan and `has_pic`/`has_logo` are computed (`pipeline.py:1151-1156`), before Verify
(`:1179`). The classifier gets the extraction dict, the raw body, the attachment names, and the media
signals (`has_pic`, `has_logo`, `doc_logo`, `doc_photo`, `embed_images`, `body_*`, `asset_*`).

## 4. Storage

```text
data/gallery/updates/<YYYY-MM-DD>_<brand-or-subject>/
    update.json          # id, brand, fromEmail, subject, messageId, date, status, files, notes
    images/              # logo and/or building photos
    originals/           # attached PDF/DOCX
```

- No `article.md`; nothing written to `all_emails/`, so the Report Manager never treats it as an
  article.
- `update.json` records each file with `name`, `sha1`, `bytes`, `width`, `height`, `kind`
  (`logo`/`photo`/`unknown`) and the promotion result.
- File size cap: `GALLERY_MAX_FILE_BYTES` (shared with N-1).

## 5. Promotion — decision 2 = C

A captured update is **auto-active only** when all four are true; otherwise it stays **pending**.

| Condition | How it is checked |
|---|---|
| the file is a **logo** | classifier kind `logo`, `max(width,height) ≥ BODY_LOGO_MIN_DIM`, name hint not “building/facade” |
| **brand confidence high** | sender domain exact match, or exact alias in subject **plus** one corroborating field |
| the brand already has an **active logo** | index entry with the same brand, `status: active`, `type: logo` |
| file readable and within the size cap | dimensions parse, bytes ≤ cap |

- **Auto-active:** copy into `data/gallery/` under the AG-05 name; mark the previous entry
  `status: superseded`; add the new entry `status: active`, `source: sender`, `updated: <date>`.
- **Pending:** everything else — new brand, building/photo, low brand confidence, unreadable file.
  `update.json` records `promotionBlockedReason` (`new-brand`, `not-a-logo`, `low-brand-confidence`,
  `unreadable`).
- Human path: `tools/gallery_admin.py promote <id>` to accept a pending file, or `discard <id>`.

N-1 matches **only `status: active`** entries, so a pending or superseded file can never be published
automatically. History is kept by superseding, not deleting — this matches AG-05's date-in-filename
reason (`[76:01]`).

## 6. Row, reply and UI — decision 3 = A

- **Column:** `emailType TEXT` added by migration in `db.init_db` (same style as `replySent`); it is
  **not** added to `_COLUMNS`, so the 14-column CSV contract is untouched.
- **Values:** `press_release` (default) · `library_update`.
- **Row:** `hasArticle=false`, `readyToFilter=false`, `articleFile=""`, `emailType=library_update`.
- **Reply:** gate at `pipeline.py:1454` — skip when `_emailType == "library_update"`.
- **Filter:** skipped (already implied by `readyToFilter=false`).
- **Run status:** keep `success`; record `stages["library_update"]`. No new run status, so the Logs
  and Editor status maps need no new branch.
- **Checklist / Editor:** show a **“Library update”** badge instead of “no article” when
  `emailType == "library_update"`. `db.list_checklist()` selects `c.emailType`; `editor_data` passes it
  through.

## 7. Dependency on N-1

N-2 uses N-1's gallery module:

- `data/gallery/index.json` (with `status`),
- brand matching (`aliases`, `domains`),
- `gallery.promote_if_safe(...)` (the decision-C rules above),
- the admin tool and the AG-05 naming helper.

Build N-1 first, then N-2. If N-2 is built alone, the update store must still be written; only the
auto-promotion step is skipped.

## 8. Tests

| Case | Assertion |
|---|---|
| BPMB logo + building email | `emailType=library_update`, assets stored, **no reply**, no filter, Verify skipped |
| normal press release with a logo | stays `press_release` (article text present) |
| new logo for a brand already active | auto-active; old entry `superseded`; index has one active logo |
| new logo for an unknown brand | `pending`, `promotionBlockedReason=new-brand` |
| building photo only | `pending`, `promotionBlockedReason=not-a-logo` |
| Climahart missing attachment | **not** library_update; reply still sent |
| library update that also has a release | `press_release` wins (article text ≥400 chars) |
| missing/corrupt updates dir | no crash; run continues to the normal path |

Proving run: `python3 -m compileall -q msme run.py tools tests` +
`python3 -m unittest discover -s tests -p 'test_*.py'`.

## 9. Code touchpoints (planned)

| File | Change |
|---|---|
| `msme/receive/library_update.py` (new) | detector + `store_update()` + `promote_if_safe()` call |
| `msme/receive/pipeline.py` | branch after `has_logo` (`:1156`), before Verify; reply gate (`:1454`); `emailType` in the row |
| `msme/db.py` | `emailType` migration; write in `save_checklist`; select in `list_checklist` |
| `msme/receive/editor_data.py` | pass `emailType` through |
| `static/checklist.html` · `static/editor.html` | “Library update” badge |
| `tools/gallery_admin.py` | `promote <id>` / `discard <id>` (shared with N-1) |
| `tests/test_library_update.py` (new) | classifier + storage + promotion + reply suppression |

## 10. Questions for MSME (added to `NEXT_MEETING.md` §2)

1. When a logo or building photograph arrives, do you **replace** the old file, keep both, or tag a new
   version? Who approves it before it is used?
2. Should the prototype update its gallery **automatically** from these emails, or hold each update for
   approval before it can be used?
3. **Detection:** how do you know an email is a logo update — the subject wording, a specific sender
   (e.g. an agency), or simply “only a logo and no article”?

## 11. Open items

- Confirm the 400-character article threshold against the real BPMB email and one short press release.
- Confirm the auto-active rule C with MSME: they may prefer every update to wait for approval.
- `emailType` values may grow with N-3 (`report`), N-4 (`government_summary`) and N-5 (`contribute`);
  the column is intentionally generic.
