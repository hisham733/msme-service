# New end-user editor page

**Session:** 2026-10-27 · S06 · reply 8
**Status:** built and live.

## Page

**http://localhost:8899/editor.html**

- Light desktop-first theme; link added to the operations checklist nav.
- Shows **every received email**, one current item per email/thread.
- Search + tabs: All, Needs attention, Drafting, Ready, Published locally.
- Cards show article title, date, stage, score, reason, version count.
- Cover image and **Open local draft** when Repurpose built a page.

## Detail panel

- Stage timeline: Receive → Ready check → Editorial check → Draft → Publish.
- The first failed stage is red with the reason, e.g.:
  - view-only Drive file
  - no media / subject match too low
  - gate fired / weighted score below threshold
  - draft rule failures (`FEATURED_EXISTS`, `EXCERPT_WORDS`, …)
- Article flags, filter outcome/score, draft status, previous versions.
- Links: local draft, Filter history, engine dashboard :8765.
- **Publish / Send** is visible but disabled until an uploader is configured.

## APIs / files

- `/api/editor/articles` — every email + current stage/reason.
- `/api/editor/article?thread_id=…` — timeline detail + version history.
- `/repurpose-site/…` — serves the local built site safely.
- `editor_data.py`, `static/editor.html`, `static/INDEX.md`, `decisions/D36.md`.

## Live check

- **155** editor items; **6** Ready to publish; **16** need attention.
- Editor, engine, and local draft pages return 200.
- Full suite: **81 pass**.

✅ nothing to decide
