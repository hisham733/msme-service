# Editor / filter-history / account cleanup

**Session:** 2026-10-29 · S08 · reply 4
**State:** live; 145 tests pass; the Tenun Nusantara test package is ready to send.

## 1. What changed

- **Filter history** now shows the Jev value next to **weighted criteria** as well as the
  hard gates:
  - gates: `YES 0.990 · defect 0.010 · pass/fired`
  - weighted: `YES 0.250` (the `norm` value from the stored result)
- **`/editor.html`**: the **Operations** link is removed.
- **`/editor.html`**: **Publish Index** replaces **WordPress Publish / Send**; it still opens
  `http://localhost:8765/dlw/index.html`. The note now says “Publish Index opens the local DLW
  index”.
- **`/editor.html`**: the **Drafting** and **WordPress Publish** KPI cards and filter tabs are
  removed. The remaining cards/tabs are **Received emails**, **Needs attention** and
  **Published Locally**; the grid is now 3 columns. Draft/published items still appear under
  **All**, with their `Publish:` chip.
- **`/account.html`**: the **Operations** link is removed. **Filter config** now points to
  **`/config.html`** (not `/filter-config.html`).

✅ nothing to decide.

## 2. Evidence

- **145 tests pass** (`python3 -m unittest discover -s tools -p 'test_*.py'`).
- Live as admin through `https://hook.empi.site`:
  - `/editor.html`: no Operations, no `kDraft`/`kPublished`, no Drafting/WordPress tabs,
    contains **Publish Index** and the DLW URL.
  - `/filter-history.html`: **2 × “Jev result”** headers (gates + weighted criteria).
  - `/account.html`: no Operations, `href="/config.html"`.
  - `/api/filter-result` returns the score `norm` values the new column reads
    (e.g. `sme_relevance {raw:0.25, norm:0.25}`).
  - `/config.html` is reachable as admin.

✅ nothing to decide.

## 3. One caveat

`/config.html` is **admin-only**. An editor clicking **Filter config** on the account page
will get 403; their own page remains `/filter-config.html`. This follows the instruction to
point the link at `config.html`; say if you want the editor link to stay on
`/filter-config.html` instead.

✅ nothing to decide.

## 4. What I recommend next

Send the prepared Tenun Nusantara email (folder `data/test_email_tenun_nusantara/`) and tell me
**“sent”**; I will verify receive → filter → repurpose → editor → DLW. The UI changes are
already deployed. The auth/UI layer is still uncommitted (the profile denies git).

## Recap

| Task | State |
|---|---|
| Jev value for gates **and** weighted criteria | Done |
| Remove Operations from `/editor.html` | Done |
| WordPress Publish / Send → **Publish Index** | Done |
| Remove Drafting / WordPress Publish cards + tabs | Done |
| Account: remove Operations; Filter config → `/config.html` | Done |
| Tests / live checks | 145 pass; live verified |
