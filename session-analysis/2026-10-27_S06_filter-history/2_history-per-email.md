# Filter history scoped per email; local version numbers

**Session:** 2026-10-27 · S06 · reply 2
**Status:** fixed.

## Change

- History is now queried by **`checklist_id`** (one email row), not `threadId`.
- Two emails in the same thread no longer share versions.
- Versions are numbered **v1..vN per email**:
  - newest = highest version, e.g. **v2**
  - older = **v1** with the black **old** badge
- The left list shows each email separately with `email #<id>`.
- The Filter modal link uses `checklist_id`.
- Legacy `thread_id` links still work as a fallback.

## Verified live

- Checklist **392**: v2 (result 5, ACCEPT 81) → v1 (result 4, ACCEPT 82).
- Checklist **391**: v2 (result 3, ACCEPT 86) → v1 (result 2, ACCEPT 87).
- They no longer appear as global “Version 4/5”.
- Full suite: **79 pass**.

✅ nothing to decide
