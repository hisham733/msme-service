# Admin login changed to admin / admin

**Session:** 2026-10-29 · S08 · reply 9
**State:** live; old sessions revoked; **temporary weak credential**; Gmail OAuth still expired.

## 1. What changed

- The live `hisham` user was **renamed to `admin`** and its password set to **`admin`**
  (temporary, for the MSME meeting).
- All sessions for that user were deleted, so every device must sign in again as
  `admin / admin`.
- `.env` now has `AUTH_BOOTSTRAP_USERNAME=admin`, `AUTH_BOOTSTRAP_PASSWORD=admin`; the file stays
  600/git-ignored. The container was recreated with the new env.
- `MG123` (editor) and its sessions are unchanged.
- Verified live through `https://hook.empi.site`: **admin/admin → 200**, `/` and `/api/users`
  200; **old hisham / old password → 401**.

✅ nothing to decide.

## 2. Security — this is a temporary hole

`admin` / `admin` on a public tunnel gives **full admin** (users, receive, clear, config) to
anyone who guesses it. It is below the 12-character policy, so it must be temporary.

⭐⭐ **Decision — §2: when to remove the weak credential**
- **Recommended:** use it for the MSME demo, then immediately change it on `/account.html`
  (12+ characters) and remove `AUTH_BOOTSTRAP_USERNAME` / `AUTH_BOOTSTRAP_PASSWORD` from `.env`.
- **If you keep it:** accept that the tunnel is effectively open; not recommended.
- **Fresh-DB caveat:** because `AUTH_BOOTSTRAP_PASSWORD=admin` is below the 12-character policy,
  a **new empty database would refuse to bootstrap** it. Use a 12+ bootstrap password in that
  case, or set the user directly.
- **Reference:** `todo/T-047.md` (2026-10-29 note), `.env`.

## 3. Gmail is still expired

The Gmail refresh token is still **`invalid_grant`** (expired/revoked). The existing Tenun
article is safe and demoable; **new inbound email will not be fetched** until
`python3 reauth_google.py` is run and the consent screen is published to Production. If the
meeting needs a new live email, re-auth first; otherwise demo the existing Tenun article.

✅ nothing to decide.

## 4. Meeting demo, all through the tunnel

- `https://hook.empi.site/login` → **admin / admin**.
- Checklist → Tenun row; Editor → Tenun item → **Open local draft** /
  **Publish Index** (`/repurpose-site/index.html`).
- Filter history → coloured Jev percentages.
- DLW index → **Tenun first** (published 07:14:50); no `localhost`.
- The engine operator dashboard stays local (`:8765`); the client-facing output is on the app.

Caveats to say: the test used the **logo** (`hasPic=false`; the photo was not counted) and the
filter-config version card is empty until the first save.

## 5. What I recommend next

Use `admin/admin` for the demo, then change it immediately. If you need a new inbound email,
re-auth Gmail first. The UI/URL work and **145 tests** remain green.

## Recap

| Item | State |
|---|---|
| Login | **admin / admin** (temporary) |
| Old `hisham` login | 401; sessions revoked |
| `MG123` editor | Unchanged |
| `.env` bootstrap | admin/admin; weak password below policy |
| Gmail | **expired**; no new mail until re-auth |
| Tests | 145 pass |
