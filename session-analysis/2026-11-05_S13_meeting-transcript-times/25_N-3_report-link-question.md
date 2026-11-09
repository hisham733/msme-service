# 25 — N-3 spec written; five MSME questions added

_2026-11-05 (S13) · docs only · no code touched._

## 1. What changed

| File | Change |
|---|---|
| `docs/new-rules/N-3-report-link.md` (new, 168 lines) | N-3 spec: report rule, hyperlink capture, `meta.json`, engine handoff, tests, touchpoints |
| `docs/meetings/2026-10-30/NEXT_MEETING.md:96` | five **Questions for MSME** under N-3 |
| `docs/meetings/2026-10-30/NEXT_MEETING.md:48` | at-a-glance N-3 row now says “owner, placement, source format” |
| `docs/INDEX.md` | `new-rules/` description + N-3 file row |

**The five questions** (also in the spec §6):

1. **Where the report lives** — attachment, Google Drive, or another cloud store: what URL do we
   publish? If there is no public URL, skip, upload, or ask the sender? One real example.
2. **Link or summarise** — when do you publish the link instead of taking the report's content into
   the repurposed article? Does it depend on size, report type, or story value? Short and long example.
3. **Placement** — end of body, inline, or a separate line next to the article? Exact wording/format.
4. **File types** — PDF/DOCX only, or also Excel/CSV/PowerPoint? What should the pipeline do with a
   spreadsheet or slide deck?
5. **Several links** — when the email offers more than one report URL (Meltwater + We Are Social),
   publish one, all, or the one the sender calls the full report?

✅ nothing to decide — the questions are recorded exactly as asked.

## 2. Verification

| Check | Result |
|---|---|
| Meeting file | N-3 questions at `NEXT_MEETING.md:96-114` (5 numbered items) |
| Spec file | same five at `N-3-report-link.md:123-143` |
| `docs/INDEX.md` | folder row line 15; N-3 row line 67 |
| Code changed | **0** — docs only |
| Compile/tests | not run — no `.py` touched |

✅ nothing to decide — measured.

## 3. The one N-3 decision that blocks publishing

The spec can capture the report URL in this repo, but the **external engine** turns it into the
published line.

**What it means operationally:** the reader either gets “Read the full report: <url>” at the end of the
article, or the link stays in `meta.json` and the live page still has none.

**Real example:** the Meltwater Digital 2027 release. The DOCX carries `wearesocial.com/digital-2027`
and `meltwater.com/en/global-digital-trends`; the live 27-Oct page has neither.

**Options:**
- **A (recommended)** — receive writes `meta.json`; the engine (`MSME_AI_News`) reads it and appends the
  line at publish. Clean, survives every stage; needs one external-engine change.
- **B** — append the line to `article.md` at archive time; no engine change, but it mutates the verbatim
  release text and the engine may paraphrase or drop it.
- **C** — receive-only now: capture and show the URL in the editor; publish later.

**Effect of not deciding:** N-3 can be partly built, but the reported gap — zero report links on the
live article — stays open.

**Blocks:** N-3 code and the 11-Nov demo of the published link. Needed before coding N-3.

**Register:** `docs/new-rules/N-3-report-link.md` §5, §7 · `todo/🟢 T-049.md` (N-3 row).

⭐ Decision — §3: **A / B / C** for the report-link handoff.

## 4. What I recommend next

**Carry on in this session** (low effort): write the **N-4** government-summary spec, then N-5.
Reason: the remaining rule docs are short and complete the 11-Nov answer sheet; the build session comes
after the choices are locked.

| # | Item | State |
|---|---|---|
| 1 | N-3 spec | done |
| 2 | Five MSME questions in `NEXT_MEETING.md` | done |
| 3 | `docs/INDEX.md` updated | done |
| 4 | Report-link handoff A/B/C | **open — §3** |
| 5 | N-4 / N-5 specs | next |
| 6 | N-1 + N-2 + N-3 build | after the specs |
