# Receive modal — reorganized layout

**Session:** 2026-10-26 · S05 · reply 19
**Status:** done.

## New layout

1. Subject + receive status/date/thread/model
2. **Article file** — its own full-width block, monospace, wraps long names
3. **Readiness** — Ready to filter · Article · Subject match
4. **Media** — Picture · Logo · Logo in article · Image in article
5. **Filter & reply** — filter badge + weighted, reply state
6. Error text, if the run had one
7. “Open filter details” button when a verdict exists

The file name is no longer mixed into the table grid; the rest is grouped into
two-column cards, collapsing to one column on narrow screens.

No backend/data change. Rebuilt; 73 tests pass.

✅ nothing to decide
