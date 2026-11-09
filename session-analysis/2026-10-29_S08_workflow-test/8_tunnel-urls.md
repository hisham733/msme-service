# All client links now work through the tunnel (:8899)

**Session:** 2026-10-29 · S08 · reply 8
**State:** URL change live; **Gmail OAuth token expired today** — see §3.

## 1. What changed

The editor/checklist no longer open `localhost:8765`:

- **Editor → Publish Index** now points to **`/repurpose-site/index.html`** (the app on :8899,
  works through `https://hook.empi.site`).
- The editor’s **Engine dashboard** button is removed. That dashboard is the local engine
  operator surface, not a client page; it stays at `:8765` on this laptop.
- **Checklist → Repurpose ↗** and the per-article Repurpose badge now open
  `/repurpose-site/index.html`.
- `REPURPOSE_DASHBOARD` defaults to `/repurpose-site/index.html` in `config.py` and
  `docker-compose.yml`; `/api/repurpose` returns that relative link.
- **Open local draft** was already `/repurpose-site/...`; it works through the tunnel.

✅ nothing to decide.

## 2. Evidence

- **145 tests pass**; live login through `hook.empi.site`.
- `/editor.html`: no `localhost:8765`, no Engine-dashboard link,
  `href="/repurpose-site/index.html"` present.
- `/checklist.html`: no `localhost:8765`; Repurpose link relative.
- `/api/repurpose` → `dashboard: "/repurpose-site/index.html"`.
- `/repurpose-site/index.html`, `/repurpose-site/data/articles.js`, the Tenun article and its
  image all return **200** through the app. The DLW index top is still
  **Tenun Nusantara Collective** (published 07:14:50).

✅ nothing to decide.

## 3. Critical: Gmail OAuth token expired (`invalid_grant`)

The live check returned:

> `invalid_grant: Token has been expired or revoked`

This is the **7-day Testing-mode refresh token** from the 2026-10-22 re-auth (`T-028`). The
existing Tenun article is already processed and safe, but **new inbound mail will not be
fetched**: webhook history replay, polling and watch renewal all call Gmail and now fail.

⭐ **Decision — §3: re-auth before a live new-email demo, or demo the existing article**
- **Blocks:** any *new* email arriving after now. It does **not** block the URL change, login,
  the editor, filter history or the existing Tenun DLW article.
- **A (recommended if the meeting needs a new email):** re-auth now with
  `python3 reauth_google.py`, then publish the OAuth consent screen to **Production** (or accept
  another 7-day expiry). The existing `gmail.json` refresh token is refreshed by that flow.
- **B (recommended if time is short):** demo the existing Tenun article and the rest of the
  workflow; re-auth immediately after the meeting.
- **Effect of not deciding:** the meeting can show the existing data, but a live “send a new
  email” demo will not arrive.
- **Reference:** `todo/✅ T-028.md`, `docs/PRODUCTION-EMAIL-SETUP.md`.

## 4. Meeting demo through the tunnel

- `https://hook.empi.site/login` → admin.
- Checklist → Tenun row; Editor → Tenun item (**Open local draft**,
  **Publish Index** → `/repurpose-site/index.html`).
- Filter history → coloured Jev percentages.
- The DLW index shows **Tenun first**; no `localhost` needed.
- The engine dashboard itself is local-only; use it only if you are on this laptop.

Two content caveats from the test: `hasPic=false` (the photo was not counted; the **logo** was
used as the image), and there is **no live filter-config version yet** (the version card is
empty until the first save).

✅ nothing to decide.

## 5. What I recommend next

For the meeting, use the existing Tenun article and the tunnel URLs. If you need a new inbound
email, re-auth first (§3 A). The auth/UI layer remains uncommitted (profile denies git); not a
meeting topic.

## Recap

| Item | State |
|---|---|
| Editor/checklist links | App-relative, work through the tunnel |
| Engine dashboard link | Removed from editor; engine UI stays local |
| DLW via app | 200; Tenun top (07:14:50) |
| Tests | 145 pass (Gmail-flaky test isolated) |
| Gmail OAuth | **expired/revoked**; no new inbound mail until re-auth |
| Existing Tenun demo | Safe and complete |
