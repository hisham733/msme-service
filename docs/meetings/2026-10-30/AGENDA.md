# AGENDA — the shared MSME decision list

*This file is the durable agenda for the AI_News project. Both MG and the partner append to it; it is in
git so that neither laptop holds a private version. It is append-only by design (see the rules below).*

## Why this file exists

Many rules in this project are not ours to invent: image choice, captions, file naming, what may be
published, and what the Receive stage must deliver are all agreed with **MSME** in conversation. A
decision that lives only in a chat or a meeting recording is lost at the next handover. So the questions
we must put to MSME live here, one row each, until they are answered — then the answer goes to
`decisions\` and the row says so.

**This file holds the decision rows; the running order and the narrative for the next meeting live in
`NEXT_MEETING.md`.** Append issues and design items there; add an `AG-` row here only when it is a
decision you need answered.

## Rules for appending

1. **Append only.** Add a row with the next free `AG-<n>`; never renumber, reorder or delete another
   person's row. To change state, edit the `status` cell and add a dated note in the meeting log.
2. **One row = one decision MSME can answer.** If a row needs two answers, split it.
3. **Write the answer shape** in the row (`AG-07 = A`), so MG can answer from this file alone.
4. **A row is not a task.** Work that we do goes to `todo\`; a row here is a question that needs a
   human's ruling, usually MSME's.
5. **When it is answered:** change `status` to `answered: <what>`, add a `decisions\D-xxx` file if it
   changes a rule, and link both here.
6. **A new meeting** gets one file `YYYY-MM-DD_<subject>.md` and a row in the meeting log below; its
   open questions are copied here as `AG-` rows (the file keeps the conversation, this table keeps the
   state).

Status vocabulary: `open` · `asked` (put to MSME, no answer) · `answered: <one line>` · `parked`
(deliberately not now) · `superseded by AG-xx`.

## The decision list

| id | raised | subject | what MSME must decide | owner | status |
|---|---|---|---|---|---|
| AG-01 | 2026-10-24 | Featured image — "people first" and its exceptions | When a supplied portrait and a brand logo are both present, which wins? The guideline's order says people; the site's practice is not consistent. Rule or exception? | MG + MSME | open |
| AG-02 | 2026-10-24 | A logo as the masthead | Confirm that a logo may be the featured image when no suitable people photo exists (the guideline's own fallback). | MG + MSME | open |
| AG-03 | 2026-10-24 | Graphs and charts | Confirm a graph/chart is **never** the featured image, and send one real example the AI may be scored against. | MG + MSME | open |
| AG-04 | 2026-10-24 | Captions | Enable captions on the site, or accept metadata-only images? The guideline requires captions; the live example article renders `alt=""` on every image. | MG + MSME | open |
| AG-05 | 2026-10-24 | File naming | Fix the guideline's example so it matches the site (`Subject_Month_Year_MALAYSIA-SME.ext`), including the site token. | MG + MSME | open |
| AG-06 | 2026-10-24 | "Use the maximum number of images" vs featured-only | Which is the rule: many images, or one featured image? 25 of 30 published articles are featured-only. | MG + MSME | open |
| AG-07 | 2026-10-24 | AI-generated images | May a generated image ever be published? Current conservative default: no (Sept-2026 guideline). | MG + MSME | open |
| AG-08 | 2026-10-24 | Assets inside PDF/DOCX + never-received pictures | Who is responsible for extracting embedded media, and who asks the sender when a brand/event logo is missing? | MG + partner + MSME | open |
| AG-09 | 2026-10-25 | Receive stage: embedded media | Will the Receive stage extract pictures from `.pdf`/`.docx` itself? Today a release sent as one PDF arrives with no picture. | partner | open |
| AG-10 | 2026-10-25 | Missing brand/event logo | When the published logo was never supplied: (a) ask the sender, (b) crop from the letterhead, or (c) publish the logo we do hold? Decides 9 of 20 rows in the October batch. | MG + MSME | open |
| AG-11 | 2026-10-25 | Filter (Stage One) — decisions 9–11 | The three filter questions are in the 30-Oct brief's A2 appendix; copy them here as separate rows before the meeting, so each gets its own answer. | MG | open |

*Rows AG-01…AG-08 are the 30 October 2026 guideline review (`guideline-review.md`).
AG-09…AG-11 come from the measured filter/receive appendices of the same brief.*

## Meeting log

| date | file | what it produced |
|---|---|---|
| 2026-09-21 | [`../2026-09-21/meeting-report.md`](../2026-09-21/meeting-report.md) | workflow agreements + open image conflict F2 |
| 2026-10-30 | [`guideline-review.md`](guideline-review.md) | the guideline-review brief; 8 guideline decisions + receive/filter appendices |

## How to append (git)

```powershell
git switch -c docs/agenda-add-<topic>
# edit this file: add ONE row with the next free AG-id, and a note in the meeting log if it is new
git add meeting_notes/AGENDA.md
git commit -m "agenda: add AG-12 <subject>"
git push -u origin docs/agenda-add-<topic>
# open a PR; the other person merges it
```

Do not edit another person's row and do not resolve an agenda conflict by deleting a row — keep both,
renumber nothing, and note the overlap in the new row.
