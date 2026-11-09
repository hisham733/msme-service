# 70 — N-8 applied: the editor is now AIN

_2026-11-06 (S14) · code + docs · live container rebuilt._

## 1. What changed

| File | Change |
|---|---|
| `static/editor.html:7` | title: **AIN — Articles** |
| `static/editor.html:84` | header: **AIN** |
| `docs/new-rules/N-8-agent-name.md` (new) | decision: the agent is **AIN**; IAN/IAM rejected; where it is applied |
| `docs/meetings/2026-10-30/NEXT_MEETING.md` | `### 10. N-8` (no question) + at-a-glance row 10 |
| `docs/INDEX.md` | N-8 row + `new-rules/` description |
| `todo/🟢 T-049.md` | N-8 ticked: **AIN** chosen; applied |
| `todo/INDEX.md` + `decisions/INDEX.md` | regenerated (`build_register_indexes.py`) |

✅ nothing to decide — **AIN** is recorded and applied.

## 2. Live verification

| Check | Result |
|---|---|
| `docker compose up -d --build` | image rebuilt, container recreated |
| `/health` | **200** |
| Container `editor.html` title | `AIN — Articles` |
| Container header | `<h1>AIN</h1>` |
| “MSME Editor” left in the file | **0** |
| Code changed | `editor.html` + docs |

Open **http://localhost:8899/editor.html** and hard-refresh (`Ctrl+Shift+R`).

## 3. One operational note

Docker Desktop was **stopped** when I started the deploy (the desktop socket was missing, and the app was
down). I started `docker-desktop`, rebuilt, and the app is back on :8899.

The Gmail token is still `invalid_grant` (T-028) — re-authentication is still owed; it does not affect
this UI change.

## 4. What I recommend next

**Carry on** (low effort): the **N-9** cost/credit note, then stop for the 11-Nov call.
Reason: N-1…N-8 are done; N-9 is the last note.

| # | Item | State |
|---|---|---|
| 1 | N-8 = AIN, UI + docs | done |
| 2 | Live container rebuilt, `/health` 200 | verified |
| 3 | Docker Desktop was down | restarted |
| 4 | Gmail token (`T-028`) | **open — user action** |
| 5 | N-9 cost/credit | next |
