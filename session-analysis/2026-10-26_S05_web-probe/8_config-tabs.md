# Config — one Config tab, two inner tabs

**Session:** 2026-10-26 · S05 · reply 8
**Status:** done. Filter config is now a tab inside the combined Config page; only the config
content is loaded, not the whole filter app.

## 1. Layout

- Top nav has **one Config** tab: `/config.html`.
- Inside it:
  - **Config Receive** — provider, Gmail, web fetch, Sheets/Drive, scheduler, connection test.
  - **Config Filter** — auto-filter toggle, filter settings/rules in an embedded editor.
- Save button stays outside both tabs; one save updates both.

✅ nothing to decide — §1

## 2. Filter tab pulls only the config

- The embedded editor is `filter-config.html?embed=1`.
- In embed mode the filter page hides its title, subtitle and nav; only the Settings, LLM-assist,
  gate and score cards are shown.
- The full standalone rule editor is still available at `/filter-config.html`.

✅ nothing to decide — §2

## 3. Verified

- `/config.html` serves the two tab buttons.
- `/filter-config.html?embed=1` carries the embed mode.
- JS syntax checks pass; the one combined app still serves all pages on :8899.
- No code or data changed.

✅ nothing to decide — §3

## Recap

| Item | State |
|---|---|
| Config nav | one tab |
| Inner tabs | Config Receive · Config Filter |
| Filter content | config only (embed) |
| Standalone rule editor | `/filter-config.html` |

## What I recommend next

Open `/config.html`, switch to **Config Filter**, and confirm the embedded rule cards load.
Then the remaining build todo is **T-001 Repurpose**.
