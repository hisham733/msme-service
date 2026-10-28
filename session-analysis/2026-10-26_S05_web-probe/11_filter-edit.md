# Filter config edit — card closing / apparent rollback

**Session:** 2026-10-26 · S05 · reply 11
**Status:** fixed.

## Cause

The whole rule card had `onclick="toggleRule(...)"`. Clicking a textarea or the Save button
inside it bubbled to the card, which immediately closed it. Unsaved edits then looked as if
they had rolled back when the card was reopened.

## Fix

- `static/config.html`: the card’s editable body now stops click propagation
  (`onclick="event.stopPropagation()"`), so textareas and Save do not close the card.
- `load()` now preserves the currently open card across a save/reload.

## Verified

- Filter rule page served on :8899; config tabs still work.
- A no-op PUT to `/config.json` returned `ok`, and the gate instruction/threshold read back
  unchanged.
- Rebuilt the app.

✅ nothing to decide
