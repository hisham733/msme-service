# Weekly report — S01–S04 (21–24 Oct 2026)

_Simple status for the week. Detail lives in `NOW.md`, `decisions/`, `todo/`, and the links below._

## 1. What we did

**Receive**
- Fixed the main intake gaps: Drive file links (view-only → `needs_human`), body images,
  vector/header logos, standalone logo images, Drive/OneDrive/Box/web sources, the
  collect-then-select article flow, and document caps (10 images per PDF/DOCX, first 30 PDF
  pages, 150k chars).
- Final live state: **208 checklist rows · 140 ready · 68 not ready**.
- `all_emails/` sorted by received date: **40** in `15-and-above`, **111** in `14-and-below`;
  **47** older versions in `_duplicates/`, **12** no-article folders in `_no_article/`.

**Filter / reports**
- The Report Manager now reads **`all_emails/`**, one version per subject (**151 groups**),
  and has an **All / 15+ / 14-** folder selector. Default date range (`since=2026-10-05`) →
  **114 rows**.
- Added `/report/duplicates` and a `versions` sheet; ready list opens the kept copy (140/140).

**Prompt v1 (live)**
- Versioned prompts for extract / verify / decide; **`PROMPT_VERSION=v1` is live**, v0 is the rollback.
- Two 6-email A/B runs: **ready 6/6**, flags **34/36** both; v1 tokens **−9% / −12%**; full-text
  similarity 0.97–0.99; cost **$0.10**.
- Live MRCA dry-run: ready, in-article logo + photo, **11,215 tokens**.

**Workflow Lab**
- `/workflow-lab.html` on :8899: 8-stage walkthrough, real code, per-stage details, runnable
  examples, live dry-run, animated workflow diagram, and a purpose map for all **42 `.py`** files.

**Drive folder 4**
- Created `Email_Articles/4` with **20 published articles from `all_emails`**, only
  `readyToFilter=true`; each has `article.md` + `images/` + `originals/` + `link.md`.
- Removed 4 non-ready (Contributed Article, WhatsApp article, SIARAN/Pahang, ConverXion);
  added 4 ready replacements (Baker Tilly, Rolls-Royce, Lion Parcel, SEAM). `1/2/3` untouched.

**Unread refresh (T-042, fixed)**
- Queue queries enforce `is:unread`; single runs mark the email read; the picker refreshes after
  success / `needs_human`. Live Refresh returned **2 unread / 0 read**; cache now 2 entries.

**Tests:** **81 pass** (8 T-042, 7 T-043, 3 D29, 7 D32, 4 D33, 6 D34, 2 auto-repurpose).

## 2. Still an issue

| Issue | Status / impact |
|---|---|
| **T-043 — published-release media** | **Done 2026-10-26**: generic web article probe + `WEB_FETCH_MODE=off|known|probe`; Event Me Now now `hasPic=true`, `hasLogo=false`, `readyToFilter=true` (1536×1024 WebP). Brand logos are publisher logos only. Now runs inside the combined pipeline (D32). |
| **D32 — combined pipeline** | **Done 2026-10-26**: receive + filter on one port (:8899); `filter_results` linked to checklist; combined `/config.html`; live auto-filter ACCEPT 90 on row 390. |
| **D33 — live ACCEPT threshold** | **Done 2026-10-26**: 0–100 editable on the filter Config; live next judgement; verified 60→65→60. |
| **D34 — filter history** | **Done 2026-10-27**: rubric snapshots, article text/hash, `/filter-history.html`, re-run on same checklist row. |
| **T-044 — published links** | **Won't do 2026-10-26** — published links stay in Google Drive; no checklist link column. |
| **T-005 / T-009** | **Won't do 2026-10-26** — no independent report-value check and no variant map (D30). Report figures remain unverified by this project. |
| **T-008 — receive accuracy** | **Won't do 2026-10-26** — no audit/fix; the old 52/55 figures stay the last measure and are unverified (D31). |
| **T-001 / D35 — Repurpose** | **Done 2026-10-27**: external `MSME_AI_News` engine on :8765; auto-export + worker; 3 accepted articles PASS/validated. `T-024` attached-photo rule remains as-is. |
| **D36 — Editor page** | **Done 2026-10-28**: `/editor.html` for MSME editors; every email, stage reason, history, local draft; light desktop-first. |
| **T-038 — DeepSeek 402** | **Resolved**: renewed; AUTH OK, balance **$9.51**; real v1 dry-runs succeeded. |

**Still on you:** send the 11 asks (`T-022`) + MSIA PDF request (`T-011`); rotate/confirm the
six OAuth secrets and decide the first commit (`D3`); publish the consent screen (`T-028`);
check the 20 links in Drive folder 4 (`T-045`).

## 3. Next todo (in order)

1. **T-001 — Repurpose** — the only unbuilt stage.
2. **User actions** — asks, secrets/commit, consent screen, folder-4 link check (`T-045`).
3. **T-043 — done** (generic probe, 3 states); keep `probe` or switch to `known`/`off` on Config.
4. **T-044 / T-005 / T-009 — closed** — links stay in Drive; report verification and variant map won't do.
5. **T-008 — closed** — receive-accuracy audit/fix won't do.

## 4. Numbers

| Item | Value |
|---|---:|
| Checklist rows | **220** |
| Ready / not ready | **140 / 68** |
| Runs · pipeline traces | **322 · 218** |
| Report groups | **151** |
| Report rows (default range) | **114** |
| Drive folder 4 | **20 ready articles** |
| Prompt A/B cost | **$0.10** |
| Tests | **81 pass** · engine three articles PASS |

## 5. Links

- State: `NOW.md` · `decisions/INDEX.md` · `todo/INDEX.md`
- Prompt A/B: `docs/PROMPT-EVAL-20261024-0700.md`
- Drive folder 4: `docs/DRIVE-FOLDER-4-20261024-0808.md` · `docs/DRIVE-FOLDER-4-SELECTION.json`
- Workflow Lab: `http://localhost:8899/workflow-lab.html`
- Drive folder 4: https://drive.google.com/drive/folders/104an8yHRRROgqvIAtebKMd4AhC8SQFbO
