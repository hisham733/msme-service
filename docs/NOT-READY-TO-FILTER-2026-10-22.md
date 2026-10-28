# Not ready to filter — updated after the recommended actions

**Generated:** 2026-10-22 · **Updated:** 2026-10-23 (D24: Finnfund body logo + web photo — 17 remain)
**Source:** latest `checklist` row per email with `readyToFilter=false`; latest `pipeline_results` stage.
**Batch image:** `msme-service:batch-3-20261022` · **Asks:** `docs/SENDER-ASKS-2026-10-22.md`

> **OAuth:** re-authed 2026-10-22 (`T-028` done); new receives work. Publish the consent screen to Production
> (or re-auth every 7 days) to avoid another expiry.

## Summary

| State | Count |
|---|--:|
| Originally not ready | 26 |
| **Resolved by the recommended re-runs** | **9** |
| Still not ready — no qualifying media | 8 |
| Still not ready — not a press release | 4 |
| Still not ready — source not retrievable | 1 |
| **Remaining from the original set** | **13** |
| Newly received backlog (46) — not ready | **4** (the other 42 are ready) |
| **Remaining total** | **17** |

The 9 resolved rows were all **re-run live**; the other 17 were not changed. Every remaining reason was
re-checked against the latest run + source (archived article, Gmail HTML images, Drive docs).

**Re-run of the 22 remaining (2026-10-22):** all were re-run; **EAP** (short-link), **World Bank speech** (web fetch), **Jobstreet** (attachment logo) and **i-City** (shared drive) became ready; **18 remain**. **Finnfund** (2026-10-23, D24) is now ready too — its body logo (250×87) and the 800×440 photo on its Cision release page are counted, so **17 remain**.
Subject matching improved (many now 80-100%), but the gate is the **media asset**: 11 have article +
subject and **no photo/logo**; 5 lack an article (non-releases, MSIA view-only);
1 is asset-only (BPMB: photos/logo but no release). **149 total · 132 ready · 17 not**.

## Chronological view — 17 remaining (date ascending)

Groups: **A** no media · **B** not a release · **C** source access · **D** 46-email backlog.

| Date | Email (id) | Group | Action |
|---|---|---|---|
| 28 Sep | BPMB Group Logo and Building Photographs (`1a0e70ae4af4d80b`) | D | Ignore (asset-only) |
| 28 Sep | AICPA & CIMA opinion piece (`1a0e709a638ce51a`) | D | Ask for media |
| 29 Sep | ConverXion KL 2026 (`1a0ea6d2dad4b996`) | D | Ask for media |
| 2 Oct | Contributed Article — SE Asian industrial talent (`1a0fbe5251974652`) | D | Ask for the article |
| 5 Oct | WhatsApp article (`1a109730d87ee5f0`) | A | Ask for media |
| 5 Oct | Anak Sulung Najib (`1a1096d3edc1e0fc`) | A | Ask for media |
| 5 Oct | MSIA Budget 2027 (`1a1096dc8c3e8df1`) | C | `T-011` re-share |
| 6 Oct | IMAGO PaperSmart (`1a10ec75d1312a46`) | A | Ask for media |
| 7 Oct | Event Me Now (`1a1160f03ca04ae4`) | A | Ask for media |
| 8 Oct | Google Account data-sharing (`1a11a62acef15a38`) | B | Ignore |
| 9 Oct | ICW & BuildXpo (`1a11fbd83326fc6a`) | A | Ask for media |
| 9 Oct | EnerGex 2026 invite (`1a11fbc3755e3888`) | B | Ignore |
| 12 Oct | Google Workspace MCP (`1a13230a98b80be1`) | B | Ignore |
| 14 Oct | Trainocate (`1a13a4d65f12b570`) | A | Ask for media |
| 14 Oct | Budget 2027 POV (`1a13a48d7c963f16`) | B | Ignore |
| 16 Oct | Research pitch (`1a14271db2ec2474`) | A | Ask for media |
| 17 Oct | Mimecast (`1a147166f5a3c1d0`) | A | Ask for media |

## Resolved — 9 re-run, now `readyToFilter=true`

| Email | Actual result after re-run |
|---|---|
| Sanct Social | `hasPic=true` (4 inline photos 544–768–1366 px) |
| PIKOM | `subjectMatch=true` 90; embedded logo |
| ICAEW | `subjectMatch=true` 89; embedded logo |
| AiSEM | `D12` selected the **Media Statement**; subject 80; 8 photos; `hasPic=true` |
| Hotcoin | `hasPic=true` (4 inline photos 512 px) |
| redBus | `subjectMatch=true` 95; **fixed a new bug** — the Drive image `redBus - Krishnan.jpg` (8.7 MB) was treated as an article source and marked `needs_human`; now treated as media → `hasPic=true`, `hasArticle=true`, ready (`D13`/`T-023`) |
| Data centers | `subjectMatch=true` 75 (new prompt); embedded logo |
| MICSEA | `subjectMatch=true` 88 (new prompt); logo + image |
| EY | `subjectMatch=true` 85 (new prompt); photo + image |

## Remaining 17 (13 original + 4 from the backlog)

### A. No qualifying media — 8 (ask the sender; drafts ready)

| Email (id) | Why it is still false |
|---|---|
| WhatsApp article (`1a109730d87ee5f0`) | Article true, subject 80; no photo/logo in the DOCX or body |
| IMAGO (`1a10ec75d1312a46`) | Article true, subject 100; no attachment and no media |
| Event Me Now (`1a1160f03ca04ae4`) | Article true, subject 100; the only inline image is a **1×1 tracking pixel** |
| ICW & BuildXpo (`1a11fbd83326fc6a`) | Article true, subject 100; no media |
| Trainocate (`1a13a4d65f12b570`) | Article true, subject 100; no media |
| Anak Sulung Najib (`1a1096d3edc1e0fc`) | Article true, but the subject is a different Malay angle; no media |
| Research pitch (`1a14271db2ec2474`) | Article true, but the subject is a pitch title; no media |
| Mimecast (`1a147166f5a3c1d0`) | Subject now matches (coverage 0.64) but there is **still no photo/logo** |

### B. Not a press release — 4 (ignore for filtering)

Google Account data-sharing (`1a11a62acef15a38`) · EnerGex media invitation
(`1a11fbc3755e3888`) · Google Workspace MCP announcement (`1a13230a98b80be1`) · Budget 2027 POV pitch
(`1a13a48d7c963f16`).

### C. Source not retrievable — 1

| Email (id) | Why | Action |
|---|---|---|
| MSIA (`1a1096dc8c3e8df1`) | Re-run after D6; Drive PDF view-only (`cannotDownloadFile`, owner `dayana.arif@msia.org.my`) | `T-011` re-share message |

### D. Newly received backlog — 4 not ready

| Date | Email (id) | Why it is false | Action |
|---|---|---|---|
| 28 Sep | BPMB logo + building photos (`1a0e70ae4af4d80b`) | **Asset-only email** (logo/building photos, no release) | Ignore for filtering |
| 28 Sep | AICPA & CIMA opinion piece (`1a0e709a638ce51a`) | Article true, subject 100; **no media** | Ask sender for media |
| 29 Sep | ConverXion KL 2026 (`1a0ea6d2dad4b996`) | Article true, subject 100; **no media** | Ask sender for media |
| 2 Oct | Contributed Article — SE Asian industrial talent (`1a0fbe5251974652`) | Article **fetched from the Google Doc** (7.3k chars, subject 100); no Atlas Copco **photo/logo** | Ask for a photo/logo |

## What is left to do

1. **Send the 11 asks** in `docs/SENDER-ASKS-2026-10-22.md` (8 previous + 3 remaining).
2. **Send the MSIA re-share request** (`T-011`).
3. **Ignore the 6 non-releases** for filtering purposes.
4. When a sender replies, re-run that email; no code change is expected.

*MATRADE resolved 2026-10-22: a `/file/d/` link was a folder; handled by D18/T-029.*
*Finnfund resolved 2026-10-23: D24 collects the body logo and the Cision release photo; no ask needed. Report reflects live rows.*
