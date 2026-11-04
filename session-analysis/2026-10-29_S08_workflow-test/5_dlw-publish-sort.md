# DLW index sorted by last publish

**Session:** 2026-10-29 · S08 · reply 5
**Scope:** `MSME_AI_News` (engine) + the generated `repurpose_site/`
**State:** live at `http://localhost:8765/dlw/index.html`; the test article will be first.

## 1. What changed

The DLW builder used to sort entries by the **article dateline** (`entries.sort(key=date)`).
It now records each release's **last publish** as the engine run time (`run.json updated`) and
sorts by that, newest first, with the dateline only as a fallback:

```python
entries.append({..., "published": run.get("updated") or ""})
entries.sort(key=lambda e: (e.get("published") or "", e.get("date") or ""), reverse=True)
```

`repurpose_site` was regenerated: **14 articles** built. Current top of the served
`dlw/data/articles.js`:

| # | Last publish | Article |
|---:|---|---|
| 0 | 2026-10-29 05:23 | Ant International CEO … |
| 1 | 2026-10-29 05:17 | BWH Hotels … |
| 2 | 2026-10-29 05:16 | Kain Fashion Incubator … |
| 3 | 2026-10-29 05:14 | Banking Industry … |
| 4 | 2026-10-29 05:13 | TikTok Shop #JomLokal … |

✅ nothing to decide.

## 2. Evidence

- `build_site.build_all(load_config())` → `{'built': 14}`.
- `articles.js` order verified: every `published` is ≥ the next; the live HTTP response from
  `http://localhost:8765/dlw/data/articles.js` shows the same top entry.
- `http://localhost:8765/dlw/index.html` → **200**.
- Engine `build_site.py` compiles; the engine's `TestBuild` is **skipped** on this host
  (“client release text/images not present”) — the real 14-article rebuild is the proof.
- msme-service side unchanged; its **145 tests** remain green.

✅ nothing to decide.

## 3. One caveat

The **already-running** engine dashboard (`python -m pipeline.dashboard`, PID 2189399) loaded
the old `build_site` module at start. Its manual **“Regenerate DLW index”** button will sort by
date until that process is restarted. The normal **auto worker** path uses a fresh
`pipeline.run` subprocess, so the test article will be sorted correctly without a restart.
Restart the engine dashboard if you want the manual button to use the new sort too.

✅ nothing to decide.

## 4. What I recommend next

Send the prepared Tenun Nusantara email. After the worker publishes it, the new article will be
**first** on `http://localhost:8765/dlw/index.html`, then tell me **“sent”** and I will verify
the whole chain. Restart the engine dashboard only if you rely on its manual rebuild button.

## Recap

| Item | State |
|---|---|
| DLW sort key | Last publish (`run.json updated`), newest first |
| Current order | Ant → BWH → Kain → Banking → TikTok … |
| Page | `:8765/dlw/index.html` 200 |
| Test article | Will be first after the worker run |
| Engine test | Skipped (client fixtures absent); real rebuild verified |
| msme-service tests | 145 pass |
