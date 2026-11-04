# Receive workflow — seven real emails, stage by stage

**Session:** 2026-10-29 · S08 · reply 11
**Document:** `docs/RECEIVE-WORKFLOW-7-EMAIL-EXAMPLES.md`
**State:** written and linked from the workflow index; no code/data change.

## 1. What was written

A long-form companion to `WORKFLOW-RECEIVE-TO-PUBLISH.md` that takes **seven real archived
emails**, one by one, through all eleven receive stages (Gmail → Normalize → Decide → Fetch →
Collect + select → Extract → Logo scan → Verify → Checklist → Archive → Filter).

| # | Email | Structure | Result |
|---:|---|---|---|
| 1 | Kain Fashion Incubator | PDF + 2 poster PNGs + body photo | ready, ACCEPT 80 |
| 2 | MATRADE–Malaysia Pavilion | logo PNG + Google Drive folder | ready, ACCEPT 91 |
| 3 | APAC CEOs (Egon Zehnder) | inline images + OneDrive + web page | ready, ACCEPT 70 |
| 4 | #JomLokal / TikTok Shop | 6 attachments (EN/BM/ZH) + Box | ready, ACCEPT 84 |
| 5 | BigSeller 11.11 | no attachment; vritimes page + body photo | ready, ACCEPT 88 |
| 6 | Sanct Social | no attachment; full release + 4 inline photos | ready, no current filter row |
| 7 | Contributed Article | Google Docs link, no media | **not ready**, filter skipped |

Each email has an **Email shape** paragraph, an **11-row stage table** with the actual
`pipeline_results` values, the checklist row/filter outcome, and a **“What this teaches”** note.

✅ nothing to decide.

## 2. What it proves

- The source can be a PDF, a Drive/OneDrive folder, a Box kit, a public web page, the email body
  or a Google Doc; **the decide step must choose the release**, not the first/longest text.
- Collect-then-select matters: APAC chose the 9k-char release over a 19k-char CEO report;
  BigSeller chose the 3.3k-char release over a 6.3k-char unrelated page.
- Media is a separate gate: the Contributed Article is complete but stops at `hasPic=false`;
  MATRADE's header logo is found by the deterministic scan even when the extract AI says no.
- Body-only works with inline photos (Sanct Social); a 1×1 tracking pixel does not (Event Me
  Now), so the public-page probe is what adds a real image.
- The current Tenun test is noted: PDF + logo arrived, the photo did not count (`hasPic=false`,
  `T-024`), and the logo kept it ready.

✅ nothing to decide.

## 3. Files

- **New:** `docs/RECEIVE-WORKFLOW-7-EMAIL-EXAMPLES.md`
- **Linked:** `docs/WORKFLOW-RECEIVE-TO-PUBLISH.md` (top-of-page worked-examples link + date)
- **Updated:** `docs/INDEX.md` (workflow group now lists both files)

Data references are real `pipeline_results` run IDs and `checklist` rows; raw email bodies stay
in `all_emails/`/SQLite and are not copied into the doc.

✅ nothing to decide.

## 4. What I recommend next

Use the seven examples in the MSME meeting to show **why the source type is not the problem —
the media and the article-type/relevance rules are**. The historical Ant case (ACCEPT 80,
MSME says not relevant) and the Event Me Now / Mercedes false-reject cases remain the meeting's
calibration discussion.

## Recap

| Item | State |
|---|---|
| Seven-email receive walkthrough | Written |
| Sources covered | PDF, Drive, OneDrive, Box, web, body, Google Doc |
| Stage tables | Real run data |
| Visual/data change | None |
| Docs index/workflow link | Added |
