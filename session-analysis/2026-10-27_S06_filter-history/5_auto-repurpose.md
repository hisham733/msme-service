# Automatic Repurpose after ACCEPT

**Session:** 2026-10-27 · S06 · reply 5
**Status:** auto-export + inbox worker running.

## Flow

```text
Receive → Filter ACCEPT
  → checklist.save_checklist()
  → repurpose_export.py (auto, if ENABLE_AUTO_REPURPOSE)
  → all_emails source → repurpose_inbox/<subject>/
  → repurpose_worker.py (host, one at a time)
  → engine :8765 → repurpose_site/
  → checklist Repurpose column updates
```

- Source remains **`all_emails/`**; the exporter uses `articleFile` and prefers the kept date bucket.
- Existing engine work is never overwritten.
- `ENABLE_AUTO_REPURPOSE=true` in Config **Filter**; off means manual export only.
- `repurpose_worker.py` skips folders that already have `draft.md`/`run.json`.
- Repurpose column: `queued` → `validated` / `HOLD` / error; click opens :8765.

## Live state

- **3** exported articles: 391, 392, 394.
- All three engine runs: **PASS / validated**.
- `repurpose_site/` has 3 article pages + index.
- Engine dashboard :8765 and worker are running.
- Exporter/inbox mount verified writable from the app container.
- Full suite: **81 pass**.

## Restart commands

```bash
cd /home/hisham/Desktop/new_div/MSME_AI_News
nohup python3 -m pipeline.dashboard > /tmp/opencode/msme_repurpose_dashboard.log 2>&1 &
cd /home/hisham/Desktop/new_div/msme-service
nohup python3 repurpose_worker.py > /tmp/opencode/msme_repurpose_worker.log 2>&1 &
```

✅ nothing to decide
