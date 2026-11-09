> **Superseded 2026-11-06 by `D40` / `T-050`:** the engine is now vendored under
> `msme/repurpose/engine/` and runs in-process on :8899; `:8765` and the host worker are retired.
> This file is kept as the D35 record.

# Repurpose integration — 2026-10-27

**Decision:** `D35` · **Engine:** `/home/hisham/Desktop/new_div/MSME_AI_News` · **Dashboard:** http://localhost:8765/

## 1. Inventory

| Item | Result |
|---|---|
| Engine | `MSME_AI_News`, branch `main`, clean |
| Engine demo | `preflight` 2 PASS |
| Engine key | created local `.env` from the current DeepSeek key (not shown) |
| Engine paths | local `config.local.json`: inbox + `repurpose_site` |
| Receive/filter | one app on :8899, SQLite |
| Filter output | SQLite `filter_results`; adapter required |
| Accepted | 3 unique articles (391, 392, 394); 390 deduped into 391 |
| Archive | `all_emails/<subject>/` with article md + images + originals |
| Site | `msme-service/repurpose_site/` |
| Link files | absent; preflight WARN only (optional) |

## 2. Mapping

| Engine contract | Our source |
|---|---|
| `email_articles_root` | `/home/hisham/Desktop/new_div/msme-service/repurpose_inbox` |
| release text | archive `articleFile` |
| images | archive `images/` |
| originals | archive `originals/` |
| `link.md` | absent (T-044: links stay in Drive) |
| `dlw_root` | `/home/hisham/Desktop/new_div/msme-service/repurpose_site` |

## 3. Changes made

| File | Why |
|---|---|
| `repurpose_export.py` | latest ACCEPT → one-folder-per-article export; dedupe and manifest |
| `repurpose_worker.py` | watches inbox and runs one engine article at a time |
| `.gitignore` | ignore `repurpose_inbox/` and `repurpose_site/` |
| `static/checklist.html` | **Repurpose ↗** link to :8765 |
| `D35`, `T-001`, `NOW`, this report | record the integration |

Engine code unchanged. Its `.env` and `config.local.json` are gitignored.

## 4. Evidence

- Exporter: **3 accepted articles** (1, 6 and 9 images), all with originals.
- Preflight: `3 folders · 0 fail · 3 warn` (no `link.md`).
- Key: `model=deepseek-flash version=DeepSeek-V4.1-Flash-1017 reply='OK'`.
- Run 1 — Setia Awan Land: **PASS / validated** (signed opinion, 1 image).
- Run 2 — MPUPK Turun Padang: **PASS / validated** (news, 6 images).
- Run 3 — Labuan IBFC: **PASS / validated** (news, 9 images).
- `repurpose_site/index.html` lists all three; article pages exist.
- Dashboard :8765 and the inbox worker are running.

## 5. Risks / limitations

- `link.md` is missing; the engine warns but does not fail. T-044 decided links stay in Drive.
- One e-mail is assumed to hold one article; the exporter does not split multiple releases.
- The engine runs on the host, not inside the :8899 container; :8765 is a second port by decision.
- Generated drafts/pages are local; nothing is sent to MSME.
- Our repo still has no commits (D3), so this is local-only, no PR.
