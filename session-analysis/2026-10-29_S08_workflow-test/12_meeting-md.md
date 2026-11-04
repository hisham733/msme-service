# MSME meeting runbook — written

**Session:** 2026-10-29 · S08 · reply 12
**File:** `docs/meeting-2026-10-29/meeting.md`
**Meeting:** today, 10:30 MYT, Microsoft Teams — MSME editorial and management.

## 1. What is in the runbook

The file is written in simple English and follows the order you asked for:

1. **What to explain** — the four stages, the live numbers, what is live and what is not, the
   Tenun test, the seven email structures.
2. **What to mention** — the two confirmed “accepted but not relevant” cases (**Ant CEO speech**,
   **BWH Hotels**), why our filter passed them, and the contrast with the Ant product article
   MSME published.
3. **What to ask** — relevance definition, SME relevance floor, article type, commercial intent,
   consumer/luxury, media standard, feedback loop, WordPress access, production setup.
4. **Live demo** — the exact Teams screen-share steps.
5. **If they ask** — short answers for the likely questions.
6. **Close and next** — the decisions and what happens after.
7. **Presenter only — do not show** — marked clearly at the bottom.
8. **Links and evidence** — the filter result IDs, local pages and published URLs.

✅ nothing to decide.

## 2. The two confirmed cases

| Case | Our result | Why it passed | What to say |
|---|---|---|---|
| **Ant International CEO speech** | ACCEPT 80; SME 0.86, SME voice 0.74, overall 0.67 | broad SME question + one Malaysia example + high substance/source; `SME voice` rewards opinion; no article-type or local-development rule | same company has a **product article** MSME published; the speech is thought-leadership |
| **BWH Hotels / WorldHotels** | ACCEPT 68; SME 0.45, SME voice 0.45, overall 0.57 | one Malaysia hotel lifted geography; high substance/source; no minimum SME-relevance floor | global hotel brand/loyalty story, not a Malaysian SME development |

The **opposite direction** (we rejected but MSME published) is still a question for them. The
runbook lists our two candidates — **Event Me Now** and **Mercedes-AMG** — and asks MSME to name
the exact articles they meant. The 5–13 Oct weekly and the 20-article test disagree, so the meeting
asks for one labelled gold set.

✅ nothing to decide.

## 3. Presenter-only reminders

- Login is temporary **admin / admin**; change it after the meeting.
- **Gmail OAuth is expired**; the demo uses the existing Tenun article — do not try a live new
  email unless you re-authenticate first.
- The engine dashboard `:8765` is local; use the app pages in Teams.
- The Tenun test is **synthetic**; the local page is **staging, not WordPress**.
- The old report figures are **unverified**; do not present them as audited.
- If the recording shows the login/password, cut or blur it.

✅ nothing to decide.

## 4. Files

- **New:** `docs/meeting-2026-10-29/meeting.md`
- **Linked:** `docs/INDEX.md`
- **Supporting:** `docs/RECEIVE-WORKFLOW-7-EMAIL-EXAMPLES.md`
- No code change; the last run remains **146 tests pass**.

## 5. What I recommend next

Open the runbook before the call and keep it on a second screen. Start with the recording, then
follow §1 → §2 → §3. After the meeting, send me the names MSME gives for the rejected-but-
published cases and their three “relevant/not relevant” examples; I will update the calibration
and the versioned filter config.

## Recap

| Item | State |
|---|---|
| Runbook | `docs/meeting-2026-10-29/meeting.md` |
| Meeting | Today 10:30 MYT, Teams |
| Confirmed not-relevant | Ant speech, BWH |
| Rejected-but-published | Candidates only; ask MSME |
| Presenter-only notes | Inside the file, marked “do not show” |
| Code/data change | None |
