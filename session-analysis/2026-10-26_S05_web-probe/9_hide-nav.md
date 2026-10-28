# Hide Workflow, Workflow Lab and Logs from the nav

**Session:** 2026-10-26 · S05 · reply 9
**Status:** done. Links removed; pages remain reachable by URL.

## 1. What changed

Removed the nav links for:

- `flow.html` (Workflow)
- `workflow-lab.html` (Workflow Lab)
- `receive-logs.html` (receive Logs)
- `/workflow.html` (filter Workflow)
- `/logs.html` (filter Logs)

Across the receive, filter, lab, test, verdicts and config pages. No route was deleted.

✅ nothing to decide — §1

## 2. Nav now

- Receive: **Checklist · Config**
- Filter: **Filter · Verdicts · Config · Jev Lab**
- Config: **one Config tab** → **Config Receive / Config Filter**

✅ nothing to decide — §2

## 3. Verified

- Rebuilt the combined :8899 app.
- `checklist.html` and `config.html` contain 0 Workflow/Logs nav links.
- Filter pages contain 0 Workflow/Logs nav links.
- Full suite: **69 pass**.

✅ nothing to decide — §3

## Recap

| Item | State |
|---|---|
| Workflow links | hidden |
| Workflow Lab links | hidden |
| Logs links | hidden |
| Routes | still available |
| Config tabs | intact |

## What I recommend next

Open `/checklist.html` and `/config.html` to confirm the smaller nav; then **T-001 Repurpose** is
the only open build todo.
