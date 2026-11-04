# Meeting runbook shortened + page-by-page script

**Session:** 2026-10-29 · S08 · reply 13
**File:** `docs/meeting-2026-10-29/meeting.md` (now 119 lines)

## 1. What changed in the runbook

- **Short format:** open (1 min) → what to explain (5) → **page by page** (10) → what to mention
  (8) → what to ask (10) → if they ask → close → presenter-only → links.
- **New page-by-page table:** for each page it says **what to show** and **exactly what to say**:
  Login, Checklist, Editor, Publish Index, Filter history, Filter config, Users.
- Simple English throughout; the video comes first; the live pages are optional.
- The two confirmed cases are still **Ant CEO speech** and **BWH Hotels**, with the scores, the
  reason they passed and the sentence to say.
- The opposite direction (**Event Me Now / Mercedes**) is still a question for MSME, not a
  confirmed case.
- The presenter-only section remains inside the file, marked **“DO NOT SHOW”**.

✅ nothing to decide.

## 2. Password bug — fixed and live-verified

- Cause: the session carried `user_id`, but `/api/auth/password` read `user.id`; it was always
  null → “Current password is incorrect.”
- Fix: `db.get_session` now selects `u.id AS id`; tests added for a **real session** password
  change, wrong current password, and self-deactivation.
- **149 tests pass.**
- Live check on `http://localhost:8899` (the public hostname is not resolving right now):
  - admin/admin login **200**
  - change to a temporary strong password **200**
  - new password login **200**; old admin login **401**
  - restored **admin/admin** for the meeting; all sessions revoked
  - audit row: `password.change`, actor_id **1**
- You can now change the password from `/account.html`. Do it **after** the meeting if you want
  `admin/admin` for the demo; the runbook says so.

✅ nothing to decide.

## 3. Public URL status

- `http://localhost:8899/api/health` → **200**.
- `https://hook.empi.site/api/health` → **000 / DNS no result** from this machine.
- For the Teams meeting, **share the local app** in screen share:
  `http://localhost:8899/login`, then the pages in the runbook. The client does not need the
  public URL.
- The public tunnel/Gmail token is separate: Gmail OAuth is still expired, so no new mail; the
  demo uses the existing Tenun article.

✅ nothing to decide.

## 4. What I recommend next

Open `docs/meeting-2026-10-29/meeting.md`, keep it on a second screen, and follow the page table.
After the meeting: change the admin password, send me MSME’s relevance examples + the exact
rejected-but-published articles, and then we update the versioned filter config.

## Recap

| Item | State |
|---|---|
| Meeting runbook | Short, page-by-page, `docs/meeting-2026-10-29/meeting.md` |
| Confirmed not-relevant | Ant speech, BWH |
| Rejected-but-published | Candidates; ask MSME |
| Password change | Fixed; 149 tests; verified on localhost |
| Public URL | DNS down; use localhost screen share |
| Admin for meeting | admin/admin (restored) |
