# 2 — Website admin password changed

_2026-11-04 (S12) · live auth operation · `T-047` follow-up._

## 1. What changed

- Replaced the weak 5-character bootstrap password on the `admin` account with a generated
  24-character password (scrypt hash stored in `data/msme.sqlite3`).
- Revoked **4** existing sessions for `admin`.
- Removed `AUTH_BOOTSTRAP_USERNAME` and `AUTH_BOOTSTRAP_PASSWORD` from `.env`.
- The new password is **not in chat and not in git**; it is in
  `/tmp/opencode/msme-admin-pw.txt` (mode `600`).

Accounts now: `admin` (admin), `MG123` (editor), `user1` (admin).

✅ nothing to decide — the change is done.

## 2. Verification

| Check | Result |
|---|---|
| Hash verifies | `verify_password` → **True** |
| `must_change_password` | **0** |
| Live login `POST /api/auth/login` | **200** (`ok`, username `admin`) |
| Auth test suite | `python3 -m unittest tests.test_auth -q` → **37 tests, OK** |
| Bootstrap lines left in `.env` | **0** |
| Password file | `/tmp/opencode/msme-admin-pw.txt`, mode `600` |

Note: `/health` still returns **200**; no restart was needed.

✅ nothing to decide — measured, not assumed.

## 3. What you must do

1. Read `/tmp/opencode/msme-admin-pw.txt` and save the password in your password manager.
2. Delete that file once saved.
3. Still owed from `T-047`: create the real editor accounts on `/users.html`.

⭐ Decision — §3: save the password and delete `/tmp/opencode/msme-admin-pw.txt` now, or keep it until after the next login?

## 4. What I recommend next

**Carry on in this session** (low effort): log in once with the new password, then create the editor
accounts on `/users.html`.

Reason: proves the new credential works from a browser, not only from the API.

| # | Item | State |
|---|---|---|
| 1 | `admin` password replaced | done |
| 2 | 4 sessions revoked | done |
| 3 | Bootstrap vars removed from `.env` | done |
| 4 | Live login 200 + 37 auth tests | verified |
| 5 | Password saved by the user | user action |
| 6 | Editor accounts on `/users.html` | still owed |
