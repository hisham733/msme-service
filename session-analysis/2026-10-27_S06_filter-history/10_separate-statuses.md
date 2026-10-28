# Editor — receive, filter and draft results separated

**Session:** 2026-10-27 · S06 · reply 10

## Change

Each editor card now shows three independent chips:

- **Receive:** Received · Not ready to filter · Receive issue · Receive error · Receiving
- **Filter:** Accepted · Not accepted · Needs editor review · Filter error · Not filtered
- **Draft:** Not started · Drafting · Ready to publish · Draft needs attention · Published locally

The detail panel has separate sections:

1. **Receive result** — status, ready flag, article, picture/logo, why it stopped.
2. **Filter result** — status, weighted score, gate, filter error, why it stopped.
3. **Draft result** — status, engine status, failing rules.
4. **Article flags**.

“No image” now reads **Draft image pending** when the article has a picture but no draft
page yet, so it is not confused with the receive result.

Rebuilt and verified on `/editor.html`. No data/API change.

✅ nothing to decide
