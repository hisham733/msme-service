# D32 — receive + filter on one port, one pipeline

**Session:** 2026-10-26 · S05 · reply 7
**Status:** implemented and verified. One port, separate linked filter storage, all archives kept.

## 1. One app / one port

- `combined.py` is the single ASGI entrypoint on **:8899**.
- Receive paths → `dashboard.app`; filter paths → `filter_service.app`.
- Legacy `/run`, `/run-all`, `/emails`, `/logs`, `/config` are rewritten to `/api/*`.
- `run.py` starts one uvicorn worker; `docker-compose.yml` exposes **8899 only**;
  healthcheck is `/api/health`.
- `/` is the checklist; `/filter.html` is the filter home.

✅ nothing to decide — §1

## 2. One pipeline

```text
Gmail → normalize → decide → extract → verify
  ├─ readyToFilter=false → skip filter
  └─ true → filter.judge (in-process) → filter_results
→ archive all → checklist row → SQLite
```

- `ENABLE_AUTO_FILTER=true`; setting is live (no rebuild to turn off).
- Dry-run skips the filter.
- Filter error is non-fatal; row keeps `filterStatus=error`.
- Filter outcome is separate from `readyToFilter`; every ready article is archived.

✅ nothing to decide — §2

## 3. Separate but linked storage

`filter_results` is a separate table linked by `checklist_id`:

`status, outcome, weighted, gate, confidence, gates, scores, verdict, model, error, created_at`

- 14-column `checklist` contract unchanged.
- `db.list_checklist()` returns the latest filter summary + full verdict.
- `data/filter_verdicts.jsonl` still records every verdict (`source=receive` for auto).

✅ nothing to decide — §3

## 4. UI / config

- Checklist: **Filter** column, outcome KPIs, outcome filter, click → gate/score modal.
- Flow page: filter stage after verify.
- Workflow Lab: 9 stages.
- `/config.html`: combined receive settings + auto-filter toggle + embedded filter rule editor.
- `/filter-config.html`: full filter rule editor.

✅ nothing to decide — §4

## 5. Verified live

- One port: `:8898` and `:8900` are closed; all pages on `:8899` return 200.
- Ready email `1a175ac2c4797d1c` auto-filtered in the same run:
  checklist row **390**, `filter_results` linked, **ACCEPT**, weighted **90**,
  model `jev-1.14.0`, archive done, JSONL `source=receive`.
- `/checklist.json` row 390 returns `filterStatus=ok`, `filterOutcome=ACCEPT`,
  `filterWeighted=90`, 3 gates + 11 scores.
- Full suite: **69 pass**.

Note: Event Me Now is not ready with your current `WEB_FETCH_MODE=off`; the live filter proof
used a ready email. The mode is unchanged.

✅ nothing to decide — §5

## Recap

| Item | State |
|---|---|
| External port | **8899 only** |
| Pipeline | receive → filter |
| Storage | separate `filter_results`, linked |
| Archive | all ready articles kept |
| Config | `/config.html` combined |
| Tests | 69 pass |
| Live proof | row 390 — ACCEPT 90 |

## What I recommend next

Review the new checklist filter modal and `/config.html` in the browser. Then **T-001
Repurpose** is the only open build todo; high effort.
