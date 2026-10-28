# static/ — INDEX

_Hand-maintained. All pages are served from this flat folder by one combined app on :8899; no build step._

## Pages by app

| Page | URL | Served by | Shows |
|---|---|---|---|
| `editor.html` | `/editor.html` on :8899 | `dashboard.py` | end-user editor: every received email, stage/rejection reason, local draft; light theme |
| `checklist.html` | `/` and `/checklist.html` on :8899 | `dashboard.py` | operations: 14-col flags, KPIs, email dropdown, Run/Refresh/CSV/Clear |
| `flow.html` | `/flow.html` on :8899 | `dashboard.py` | animated receive pipeline + per-stage detail, tokens, model |
| `workflow-lab.html` | `/workflow-lab.html` on :8899 | `dashboard.py` + `workflow_lab.py` | interactive 9-stage walkthrough (code, input/output, per-stage details, runnable examples) + animated workflow diagram (`#chart`) + .py purpose map |
| `receive-logs.html` | `/receive-logs.html` on :8899 | `dashboard.py` | receive run history (`/api/logs`, `/api/clear`) |
| `config.html` | `/config.html` on :8899 | `dashboard.py` | **combined receive + filter config**; filter rules in an embedded editor |
| `receive-config.html` | `/receive-config.html` on :8899 | `dashboard.py` | legacy receive-only config |
| `filter.html` | `/filter.html` on :8899 | `filter_service.py` | pick an archived article, run Jev, see the verdict |
| `verdicts.html` | `/verdicts.html` on :8899 | `filter_service.py` | recent verdicts (`/verdicts`, `/clear`) |
| `workflow.html` | `/workflow.html` on :8899 | `filter_service.py` | filter battery/routing explanation (`/workflow.json`) |
| `logs.html` | `/logs.html` on :8899 | `filter_service.py` | filter error/verdict log (`/logs.json`) |
| `filter-history.html` | `/filter-history.html` on :8899 | `dashboard.py` | Filter versions, rubric used, diff and re-run |
| `filter-config.html` | `/filter-config.html` on :8899 | `dashboard.py` (filter page) | gate thresholds + score weights (`/config.json`); also embedded in `/config.html` |
| `lab.html` | `/lab.html` on :8899 | `filter_service.py` | Jev Lab: edit question wording, ask Jev (`/lab/*`) |
| `testfilter.html` | `/testfilter.html` on :8899 | `filter_service.py` | test-article runner, learn/promote/sync/rollback |
| `report.html` | `/reportmanager.html` on :8899 | `filter_service.py` | pick a variant Excel, run the battery, download the report |

## Notes

- One port: `combined.py` routes receive paths to `dashboard.app` and filter paths to
  `filter_service.app`. `/` is the checklist; the filter home is `/filter.html`.
- Receive logs are `receive-logs.html`; filter logs are `logs.html`.
- `/config.html` is the combined pipeline config; `/filter-config.html` is the full filter rule editor.
- **Hidden from the nav (still reachable by URL):** `flow.html`, `workflow-lab.html`, `receive-logs.html`, `/workflow.html`, `/logs.html`.
- Pages fetch **relative** URLs so each app is same-origin (no CORS).
- Adding a page: put it here, add the route in the owning app, and add a row above.
