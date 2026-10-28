# Filter criteria — save / rollback fix

**Session:** 2026-10-26 · S05 · reply 12
**Status:** fixed.

## Cause

The criteria parser accepted only one-line `TRUE: …` / `FALSE: …` entries. A multi-line
example lost its continuation lines; if the text no longer parsed, the empty criteria was sent,
and the Jev Lab wording (higher precedence) made the card look reverted.

## Fix

- `parseCriteria()` now keeps continuation lines under the previous `TRUE:` / `FALSE:` key.
- An empty/unparseable criteria block is rejected with a visible error instead of saving `{}`.
- The rule card’s editable body still stops click propagation, so clicking a textarea/Save no
  longer closes the card.
- The combined Config page now says: use the card’s **Save** for filter rules; the outer
  **Save settings** only saves receive fields.

## Verified

- JS syntax check passes.
- API round-trip of a changed gate instruction/criteria reads back the new value.
- Container rebuilt; filter config and combined config serve the new code.

✅ nothing to decide
