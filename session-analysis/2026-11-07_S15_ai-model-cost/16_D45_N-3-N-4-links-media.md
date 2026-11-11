# 16 — Repurpose image/link discovery: N-3 report link + N-4 capture + email_media/email_links

_2026-11-07 (S15) · "recommended defaults", "ok go"._

## 1. What was built (D45)

The received email is the root; two child tables carry what repurpose needs.

| Table | Purpose |
|---|---|
| **`email_links`** | report/speech/source link per email (`link_type`, `url`, `source`, `anchor`, `confidence`, `is_primary`, `candidates_json`) |
| **`email_media`** | one row per collected image/logo (`name`, `kind`, `source`, `role`, `width`, `height`, `bytes`, `sha1`, `usable`, `chosen`); `source='gallery'` = the N-1 fallback |

**N-3 (built):** `report_link.py` reads DOCX `document.xml.rels` hyperlinks + PDF `/URI` + body links,
scores by path/anchor; a hit needs a report phrase **and** a scored link → `emailType=report`,
`email_links(link_type='report')`. `repurpose_export` writes `meta.json`; the engine appends
**"Read the full report: <url>"** at build (the validator forbids URLs in `draft.md`).

**N-4 (capture-only):** `gov_summary.py` detects budget/government markers + a speech-like link →
`email_links(link_type='speech')`, `emailType=government_summary`. It never fetches the speech and
never turns a no-article email into a published one — the summary/branch + fetch wait for MSME Q1.

Also: `media_index.py` indexes the collected media (incl. the gallery fallback); the editor shows the
report/speech link + "gallery fallback"; `DATABASE-FLOW.md` and the schema graph were updated.

## 2. Verification (measured)

| Check | Result |
|---|---|
| Full suite | **291 tests OK** (8 skipped) · `compileall` OK |
| Live Meltwater re-run (`1a162cc0b30af0e7`) | `emailType=report`, `hasArticle=true`, `readyToFilter=true` |
| `email_links` | `report` → `https://wearesocial.com/digital-2027`, source `docx_rels`, confidence 0.9 |
| `email_media` | 0 rows (no image attachments — correct; a re-run with no media now clears stale rows) |
| Export | wrote `meta.json` (`articleType=report`, `reportUrl=…`) into the inbox folder — even though a 30-Oct draft already existed (draft untouched) |
| Engine append | real Meltwater draft + `meta.json` → HTML contains "Read the full report" + the URL |

## 3. Notes

- The link is appended **at build**, never in `draft.md`/`article.md` (`NO_CONTACTS_BOILERPLATE` rejects
  URLs in the draft).
- The export keeps existing engine work and only drops `meta.json`; the next engine `build` adds the line.
- Fixed mid-build: `email_media` now skips non-image attachments (a DOCX was being indexed), and a
  re-run with no media clears stale rows.
- N-4 branch/fetch remain parked pending MSME Q1 (summary-vs-speech threshold).

✅ nothing to decide — N-3 is live; N-4 capture is live (publish branch parked for MSME).

## Recap

| # | Item | State |
|---|---|---|
| 1 | `email_links` + `email_media` tables | done |
| 2 | N-3 report link (capture → meta.json → build append) | done |
| 3 | N-4 speech link capture-only | done |
| 4 | Media index incl. gallery fallback + editor display | done |
| 5 | Tests + live Meltwater proof | 291 pass |
| 6 | N-4 summary/branch + speech fetch | parked (MSME Q1) |

## What I recommend next

Carry on in this session (low effort): refresh the Meltwater page with the engine `build` so the link
appears on the live local site; then move to **N-5 (contribute/byline)** — the last unblocked N-rule in
`T-049`. N-4 publish work waits for the 2026-11-11 call.
