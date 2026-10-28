# Config label — Probe → Auto

**Session:** 2026-10-26 · S05 · reply 2
**Status:** done; no data or code behaviour changed.

## 1. Change

`static/receive-config.html` now shows:

`Auto — known + up to 2 unknown links (recommended)`

The option value stays `probe`, and `WEB_FETCH_MODE` / the saved setting / API remain
`probe`. No migration. `decisions/D28.md` notes that **Auto** is the UI label for `probe`.

✅ nothing to decide — §1

## 2. Verified

- Built/restarted the container.
- `receive-config.html` serves the **Auto** label.
- `/api/config` still returns `WEB_FETCH_MODE = "probe"`.
- Full suite: **59 pass**.

✅ nothing to decide — §2

## Recap

| Item | State |
|---|---|
| UI label | **Auto** |
| Stored/API value | `probe` |
| Tests | 59 pass |

## What I recommend next

Carry on with **T-044** (published links in the checklist) in this session. It still needs the
**A/B** choice from the previous reply: **A** = SQLite now, Sheet later (recommended).
