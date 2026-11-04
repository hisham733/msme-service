# Login now lands on /editor.html

**Session:** 2026-10-29 · S08 · reply 10
**State:** live; 146 tests pass.

## 1. What changed

- **`/login` success** (both roles) → **`/editor.html`**; the old `admin → /` branch is gone.
- Visiting **`/login` with an active session** → **302 `/editor.html`**.
- **Account → change password** now continues to **`/editor.html`** after 800 ms.
- **Forced password change** still goes to `/account.html` first; after the change it lands on the
  editor. `AUTH_BOOTSTRAP_*`/admin and `MG123` behave the same.
- The admin can still open the operations pages directly (`/checklist.html`, `/flow.html`, …);
  there is no Operations link on the editor.

✅ nothing to decide.

## 2. Evidence

- **146 tests pass** (one new: both roles redirect to `/editor.html`).
- Live: `admin/admin` login **200**; `/editor.html` **200**; `/login` with the session →
  **302 `/editor.html`**; the anonymous login page contains `location.href='/editor.html'` and no
  role branch; account page contains the post-change redirect.
- `https://hook.empi.site` health OK.

✅ nothing to decide.

## 3. Unchanged reminders

- The login is **admin/admin** (temporary weak, public tunnel): change it immediately after the
  MSME demo and remove the two bootstrap vars from `.env`.
- **Gmail OAuth is still expired** (`invalid_grant`): the existing Tenun article is demoable; a new
  inbound email needs `python3 reauth_google.py` first.
- The test article used the **logo** (`hasPic=false`), and the filter-config version card is empty
  until the first save.

✅ nothing to decide.

## 4. What I recommend next

Log in once as **admin/admin** to confirm the editor landing, run the demo from the editor, then
change the password. If a new email demo is needed, re-auth Gmail first.

## Recap

| Item | State |
|---|---|
| Login success | `/editor.html` for admin and editor |
| `/login` with session | 302 `/editor.html` |
| Account password change | Continues to editor |
| Tests | 146 pass |
| Admin | Temporary admin/admin; change after demo |
| Gmail | Expired; re-auth before a new email |
