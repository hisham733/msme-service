# Repurpose integration — engine on :8765

**Session:** 2026-10-27 · S06 · reply 3
**Status:** done; two accepted articles passed end to end.

## 1. What runs where

- **Engine:** `/home/hisham/Desktop/new_div/MSME_AI_News` — unchanged.
- **Dashboard:** http://localhost:8765/ — queue, Run/Validate, rules, DLW.
- **Input:** `msme-service/repurpose_inbox/` — exported latest ACCEPT folders.
- **Output:** `msme-service/repurpose_site/` — index + article pages + images.
- **Key:** engine `.env`, gitignored; taken from the current DeepSeek setting.
- **Link:** Checklist → **Repurpose ↗**.

## 2. Export

`repurpose_export.py` selects the **latest ACCEPT** filter result per article and copies one
`.md` + `images/` + `originals/`.

- 5 filter verdicts → **2 unique articles** (390 deduped into 391; plus 392).
- `preflight`: **2 folders · 0 fail · 2 warn** — only optional `link.md` is absent.

## 3. Engine evidence

- Key check: `model=deepseek-flash version=DeepSeek-V4.1-Flash-1017 reply='OK'`.
- **Setia Awan Land** — signed opinion, 1 image → **PASS / validated**.
- **MPUPK Turun Padang** — news, 6 images → **PASS / validated**.
- Pages exist in `repurpose_site/articles/`; `index.html` lists both.
- Dashboard :8765 returns 200; no PR/commit per your choice.

## 4. Records

- `D35`, `T-001` closed, `NOW`, `README`, weekly report.
- Integration report: `docs/REPURPOSE-INTEGRATION-2026-10-27.md`.
- Tests: **79 pass**.

## 5. Limitations

- `link.md` is missing because links stay in Google Drive (T-044); engine warns only.
- One email is assumed to hold one article.
- Engine runs on the host; :8765 is a second port by decision.

✅ nothing to decide
