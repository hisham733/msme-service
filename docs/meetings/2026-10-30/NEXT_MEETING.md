# NEXT MEETING — the single file for the next MSME meeting

*Status: staging file. When the date is fixed, rename this file to `YYYY-MM-DD_<subject>.md` (then it
becomes that meeting's brief) and add a row to `INDEX.md`. Until then, this is the one place where both
MG and the partner merge **issues** and **MSME design decisions** for the next conversation.*

**Status 2026-10-31 — after the 30-Oct call:** that call answered `AG-01`…`AG-08` and `AG-15` (the answers
are `D-024`…`D-029`, see `AGENDA.md`), so the three-decision table below is stale and has been replaced with
the four items that were **never reached**. This file is reused for the next session (≈ week of 2026-11-09,
`T-037`); rename it to `2026-11-09_<subject>.md` once the date is fixed.

**Why one file:** the 30-Oct brief showed that issues raised from two sides (MG's pipeline measurements,
the partner's Receive/Filter findings) arrive as two documents and get reconciled by hand. One staging
file, appended by both, is the reconciliation. The append-only decision list stays in `AGENDA.md`; this
file is the running order and the narrative.

## How to use it

1. **Append, don't rewrite.** Add under the right heading, with your initials and the date:
   `[MG 2026-10-26] …`, `[HS 2026-10-27] …`. Never delete someone else's line; strike it with
   `~~…~~` and say why.
2. **An issue is one line + evidence.** Link the file or quote the measurement; "the images are bad" is
   not an issue, "9 of 20 published pictures were never delivered (receive_feedback.md)" is.
3. **A design decision needs an answer shape** (`D1 = A`) and an owner, like `AGENDA.md`.
4. **After the meeting:** answers that settle a rule go to `decisions\`; work goes to `todo\`; this file
   keeps the narrative and is renamed to the meeting date.

## 1. Running order (draft — confirm with MSME)

| # | subject | who leads | time |
|---|---|---|---|
| 1 | Image rule: people-first and its two exceptions (`AG-01`, `AG-02`) | MG | 15 min |
| 2 | Captions, file naming, max images (`AG-04`…`AG-06`) | MG | 15 min |
| 3 | AI-generated images (`AG-07`) | MG | 10 min |
| 4 | Receive: embedded media + missing assets (`AG-08`…`AG-10`) | partner | 20 min |
| 5 | Filter stage: cut 62, determinism, `c10` (`T-024`, `T-023`) | MG | 10 min |
| 6 | Next batch and who sends what | both | 10 min |

## 2. Issues to raise (append)

- `[MG 2026-10-26]` **9 of 20 published pictures were never delivered** — not loose, not inside the
  attachment, not a letterhead render; 4 could not be named from the release text. Evidence:
  `../analysis/imageeval/receive_feedback.md`, `KNOWN_ISSUES.md` R2.
  **Ask:** who sends the fallback when the sender's featured image is a logo that never arrived?
- `[MG 2026-10-26]` **PDF/DOCX extraction is still not done in Receive** — 7 of 20 folders arrived with
  no picture; 115 images were mined downstream. Evidence: `KNOWN_ISSUES.md` R1.
  **Ask:** is extraction in the Receive scope, and by when?
- `[HS 2026-11-04]` **N-3 — long report: rule says link it, publish has no link.**
  **Email example:** "Fwd: Fifteen years of Digital reports: Meltwater & We Are Social's 2027 edition
  shows 6.15 billion online and 1 in 3 people using generative AI" (Thu 22 Oct, thread
  `1a162cc0b30af0e7`). It offered the press release plus a Drive folder with the full report.
  **Rule (30-Oct call):** if the report is too long, add the link to the report in the published article.
  **Gap:** the live article has **no** report link (0 `wearesocial`/`meltwater` URLs in the page HTML;
  published 27 Oct), while the release DOCX carries `wearesocial.com/digital-2027` and
  `meltwater.com/en/global-digital-trends`. Live URL:
  `https://www.malaysiasme.com.my/digital-2027-report-one-in-three-people-globally-use-genai-as-social-media-users-hit-5-8-billion/`.
  **Ask:** who adds it — editor or system — and where?
- *(partner — add yours here)*

## 3. MSME design decisions (append; one row per decision)

| id | decision | where it stands | what the next call needs |
|---|---|---|---|
| `AG-12` | what the archive's `Original status` actually records (two outcomes vs the guideline's four) | **open** — the brief's A2 was never presented | an answer; the three columns that would let us diagnose are in the A2 appendix |
| `AG-13` | why every rejection is dated on or before 14 October | **open** | an answer; the 40 releases after that date cannot be used as evidence until it comes |
| `AG-14` | one release carrying both `REJECT` and `ACCEPT` (KPMG, received 7 Oct) | **open** | a ruling on whether a duplicate may carry two statuses |
| `AG-16` | the input channel — email, WhatsApp, or both | **open** — never reached in October | the system of record, and which wins on a duplicate |
| `AG-09` | does the Receive stage extract embedded media from `.pdf`/`.docx`? | **open** — the partner's item | scope and a date |
| `N-3` | long reports: publish the link to the report | **verified gap** — live Digital 2027 article has no report link; the release DOCX has two | ruling + owner (editor or system), and where the link sits |

*The guideline decisions (`AG-01`…`AG-08`, `AG-15`) are answered — do not re-ask them; read `AGENDA.md` and
`decisions\D-024`…`D-029` first.*

## 4. Notes during the meeting (append, timestamped)

- `[HH:MM]` …

## 5. After the meeting

- answers → `decisions\D-xxx.md` + the `AGENDA.md` row's status;
- work → `todo\T-xxx.md`;
- rename this file to `YYYY-MM-DD_<subject>.md`, update `INDEX.md`, and start a fresh `NEXT_MEETING.md`
  from this shape when the following meeting is scheduled.
