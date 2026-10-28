# Repurpose column on the checklist

**Session:** 2026-10-27 · S06 · reply 4
**Status:** done.

## Change

- Added **Repurpose** column after **Filter**.
- Status is read from the engine’s `run.json` via the exported manifest:
  - `validated` / `rendered` → green
  - `HOLD` → red
  - `drafted` / `validate-failed` → amber
  - no export → `—`
- Clicking the badge opens the engine dashboard **http://localhost:8765/**.
- Container mounts `repurpose_inbox` and `repurpose_site` read-only.

## Verified

- `/api/repurpose` returns:
  - checklist **392** → `validated` (Setia Awan)
  - checklist **391** → `validated` (MPUPK)
- Engine dashboard :8765 still returns 200.
- Full suite: **79 pass**.

✅ nothing to decide
