# Report reads all_emails — newest version kept, archive split 15+ / 14-

**Session:** 2026-10-23_S03 · **Turn:** 3 · **Image:** `msme-service` rebuilt 2026-10-23 15:47
**IDs:** D26 · T-015 · T-038

---

## 1. What changed

- **Report input** moved from `emails/` to **`all_emails/`** (`config.REPORT_ARCHIVE_DIR`,
  `/app/all_emails` in Docker). The old store held only 24 live articles + 43 test/published
  subfolders; only **28 of 141** ready rows were visible.
- **One version per subject**: new `archive_layout.py` groups folders that differ only by `_1`,
  `_2`, ` 3`… and picks the keep-map entry (`docs/archive-versions.json`) or the **newest folder
  with an article**.
- **Archive split** (cutoff 2026-10-15):
  `all_emails/received-2026-10-15-and-above/` (**40**) and
  `all_emails/received-2026-10-14-and-below/` (**111**).
- **Older copies** → `all_emails/_duplicates/` (**47 folders**, 31 groups). **No hard delete**; every
  move is in `/tmp/opencode/reorganize_archive.json`.
- **No-article folders** → `all_emails/_no_article/` (**12** folders: BPMB, MADANI POV, Sustainable
  Action, EnerGex, typesafe notice, OAuth notice).
- **Report Manager**: `/report/duplicates` endpoint, a `versions` sheet in the Excel, and the page
  now shows the archive + duplicate counts.
- **Ready list** (`/archived`) also skips `_duplicates/` and prefers the live archive, so it opens the
  kept copy (previously 12 of 141 rows opened an older version).

⭐ **Decision — §1:** ✅ nothing to decide — built as asked.

---

## 2. Measured after the sort

| Check | Before | After |
|---|---:|---:|
| Report rows (one per subject) | 113 from `emails/` | **151 from `all_emails/`** |
| Duplicate versions in a run | yes | **0** |
| Ready rows with an openable article | 140/141 | **140/140** |
| Default report range (`since=2026-10-05`) | — | **114 rows** |
| Buckets | flat | **40 above · 111 below** |
| Duplicate folders moved | — | **47** (31 groups) |
| No-article folders moved | — | **12** (6 groups) |

Kept copies for the groups whose article file changed: redBus `_1`, HARI EKSPORT `_1`, World Bank
`_4`, PHOTOS-semiconductor `_1`, MALAYSIA’S EXPORTS `_1`, SIARAN MEDIA `_2`. All other groups kept
their newest copy. The full map is `docs/archive-versions.json` (151 entries).

⭐ **Decision — §2:** ✅ nothing to decide.

---

## 3. Verified

- **Live endpoints:** `:8900/health` ok; `/report/duplicates` → root `/app/all_emails`, **151 groups,
  0 duplicate groups**; `/archived` → **140 ready rows, 140 with a path, 0 missing**.
- **Tests:** `python3 -m unittest tools.test_report_versions -v` → **10 pass**;
  `tools.test_collect_select` → **15 pass**; `python3 -m compileall -q *.py tools/*.py` → OK.
- **Fake-Jev smoke run** of `_do_report` (no paid calls): **151 groups · 114 dated rows · 0
  duplicates**, `versions` sheet present, Excel/CSV/TSV written and removed afterwards. `report-runs`
  restored to its pre-smoke state.
- **Your 15:25 run** (`gates-def-my-deepseek-nocriteria`, 109 Jev calls, 287,696 tokens, 140.6 s,
  rows=2) ran on the old `emails/` input; its report is untouched. The new code is live since the
  15:47 rebuild.

⭐ **Decision — §3:** ✅ nothing to decide.

---

## 4. One data change to know about

The Malay copy of **MALAYSIA’S EXPORTS TO 40 COUNTRIES** (checklist id **338**) pointed at
`EKSPORT-MALAYSIA…md`, which is now in `_duplicates/`. I set that row to `readyToFilter=false`; the
kept English copy is id **371**. That is the only ready row affected — it is reversible with one
`UPDATE`.

⭐ **Decision — §4:** ✅ nothing to decide — say if you want the Malay copy kept instead.

---

## 5. What the report will show now

The page’s **Since** box still defaults to **2026-10-05**, which gives **114** of the 151 groups.
The 37 earlier articles (22 Sep – 4 Oct) are in the **14-and-below** bucket. Set **Since = 2026-09-01**
to judge all 151.

⭐ **Decision — §5:** change the default Since to **2026-09-01** (all 151) or keep **2026-10-05** (114)?

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | Report input → `all_emails/` | **built + live** |
| 2 | Newest version kept, 47 duplicates isolated | **done** |
| 3 | Buckets 15+ (40) / 14- (111) | **done** |
| 4 | `/report/duplicates` + `versions` sheet | **built + tested** |
| 5 | Ready list opens kept copies | **140/140** |
| 6 | Default date range | **114 of 151** — awaiting your 2026-09-01 / 2026-10-05 choice |

## What I recommend next

Open **`http://localhost:8900/reportmanager.html`**, press **Check duplicates** (should say 0), set
**Since = 2026-09-01**, and run the report once — that is the first full filter pass on the cleaned
archive. After that, `T-005` (recompute one report’s values) is the natural check. Say the word and I
can run it, but it spends Jev calls (~151); no DeepSeek calls are needed (`ENABLE_LLM_ASSIST=false`).
