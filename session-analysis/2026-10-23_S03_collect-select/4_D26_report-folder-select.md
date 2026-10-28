# Report folder selector — All / 15+ / 14-

**Session:** 2026-10-23_S03 · **Turn:** 4 · **IDs:** D26
**Page:** `http://localhost:8900/reportmanager.html`

---

## 1. What changed

- New **Archive folder** select on the Report Manager:
  - **All folders (151)**
  - **received-2026-10-15-and-above (40)**
  - **received-2026-10-14-and-below (111)**
- The choice is sent with the run (`/report/run`), carried by the Excel **RUN** link
  (`&folder=…`), stored in `report-runs.jsonl`, and shown in the history table.
- Report file names now include the folder so two runs in the same minute cannot overwrite each
  other: `…-all-…`, `…-10-15-above-…`, `…-10-14-below-…`.
- New endpoint `GET /report/folders` lists the folders + article counts; `/report/duplicates` accepts
  `?folder=` so “Check duplicates” reflects the selected folder.
- The run also reports `folder` and filters **before** version grouping, so a subject that has copies
  in both buckets is judged only from the selected folder.

⭐ **Decision — §1:** ✅ nothing to decide — built as asked.

---

## 2. Measured

| Selection | Articles used |
|---|---:|
| All folders | **151** |
| 15 Oct 2026 and above | **40** |
| 14 Oct 2026 and below | **111** |

Fake-Jev smoke run (no paid calls) confirmed rows **151 / 40 / 111** and the file tags
`base-all`, `base-10-15-above`, `base-10-14-below`. Live `/report/folders` returns the same counts;
`/report/duplicates?folder=received-2026-10-15-and-above` → 40 groups, 0 duplicates.
Tests: `python3 -m unittest discover -s tools -p 'test_*.py'` → **27 pass**.

⭐ **Decision — §2:** ✅ nothing to decide.

---

## 3. One bug caught while building

The report loop reused the name `folder` for the article in the loop, which shadowed the new
selection parameter and produced an invalid path (`…-10-15-above/刊登…`). Renamed the loop variable to
`rel`; the smoke run then wrote the three correct files. No live run was affected.

⭐ **Decision — §3:** ✅ nothing to decide.

---

## 4. How the date range interacts

The **Since** box still applies on top of the folder:

| Folder | Since | Rows |
|---|---|---:|
| All | 2026-10-05 (default) | **114** |
| All | 2026-09-01 | **151** |
| 15-and-above | any date ≤ 15 Oct | **40** |
| 14-and-below | 2026-10-05 (default) | **74** |
| 14-and-below | 2026-09-01 | **111** |

The date range drops rows **after** the Jev calls, so a narrow Since does not reduce the number of
paid calls — the folder selection does.

⭐ **Decision — §4:** keep the default **All + 2026-10-05** (114), or default to **All + 2026-09-01**
(151)? Say which and I will set it.

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | Folder select on the page | **built + live** |
| 2 | `GET /report/folders` | **40 / 111 / 151** |
| 3 | Folder in run, history, file name, Excel RUN link | **done** |
| 4 | Tests | **27 pass** |
| 5 | Default date range | unchanged (114) — awaiting your choice |

## What I recommend next

Run **15-and-above** (40 calls) first — it is the newest batch. Then **14-and-below** (111). If you
want every article in the 14-and-below bucket, set **Since = 2026-09-01**; with the default you get 74
of 111. No DeepSeek calls are involved (`ENABLE_LLM_ASSIST=false`).
