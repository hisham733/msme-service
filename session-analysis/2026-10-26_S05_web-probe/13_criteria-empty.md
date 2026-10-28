# Criteria can be empty

**Session:** 2026-10-26 · S05 · reply 13
**Status:** fixed.

## Change

- Removed the `TRUE:/FALSE:` requirement from the rule editor.
- An empty criteria box now saves as `{}` instead of showing an error.
- `filter.py` now treats an explicit empty criteria as valid and mirrors it to
  `docs/jev-variants.json`, so the Jev Lab source cannot silently restore the old text.
- The hint now says criteria are optional.

## Verified

- Live API round-trip: `criteria:{}` saved and read back as `{}`; original restored.
- Full suite: **69 pass**; container rebuilt.

✅ nothing to decide
