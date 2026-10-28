# Receive status is clickable

**Session:** 2026-10-26 · S05 · reply 17
**Status:** done.

## Change

- Dashboard column **Status → Receive**.
- Labels:
  - success → **received**
  - needs_human → **receive issue**
  - error → **error**
  - running → **processing…**
- The badge is clickable → receive detail modal:
  - article file, article/picture/logo/image flags, subject score/match, ready state, reply
  - filter outcome/weighted
  - run model and error text
  - **Open filter details** button when a filter verdict exists
- Added receive-state filters: received / issue / error.

## Verified

- JS syntax check passes; rebuilt on :8899.
- Full suite: **73 pass**.

✅ nothing to decide
