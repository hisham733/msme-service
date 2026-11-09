# Not-ready list — 26 emails, verified reasons, 25 not re-run

**Session:** 2026-10-22_S02 · **Turn:** 10 · **Report:** `docs/NOT-READY-TO-FILTER-2026-10-22.md`
**Register:** `todo/⏳ T-022.md`

---

## 1. What the report contains

Every latest checklist row with `readyToFilter=false` (26 emails). For each row: the last measured stage
reason, the archived article text, Gmail HTML image count/pixel size, and Drive document names.
**25 of 26 were not re-run** after the batch fixes; **MSIA is the only re-run** (after D6) and is still
blocked by the sender. No code was changed for this report.

| Group | Count |
|---|--:|
| A. Likely ready on re-run | **5** |
| B. Subject fixes, media still missing | 1 |
| C. Media present, subject needs prompt/editor | 3 |
| D. Correct article, no qualifying media | 8 |
| E. Not a press release | 6 |
| F. Source not retrievable | 2 |
| G. Subject fixed, media uncertain | 1 |

⭐ **Decision — §1:** ✅ nothing to decide.

---

## 2. The likely-ready six (re-run)

| Email | Basis |
|---|---|
| Sanct Social | 4 inline photos 544–1366 px → D7 counts them |
| PIKOM | subject coverage 0.60 + embedded logo → D10 |
| ICAEW | subject coverage 0.75 + embedded logo → D10 |
| AiSEM | D12 selects the **Media Statement** (7,858 chars) over the 12,861-char speech; 8 photos |
| Hotcoin | 4 inline photos 512 px → D7 counts them |
| redBus | subject coverage 1.00 → D10; media depends on the Drive profile image (may be < 1 MB) |

**Not expected to change:** 8 rows with no photo/logo at all; 3 rows (Data centers, MICSEA, EY) where the
subject is a different angle (editor/prompt may help); 6 non-releases; MSIA + i-City access.

⭐ **Decision — §2:** re-run these 6 now (A) · leave them for you to run later (B)?

---

## 3. Still open elsewhere

- **T-011** — MSIA re-share message (blocks the MSIA article).
- **T-022** — the actionable not-ready list (re-run 6 · ask senders 8 · editor 3 · i-City access).
- **D3** — secret rotation + first commit.
- **T-001** — repurpose stage.

⭐ **Decision — §3:** ✅ nothing to decide.

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | Report of 26 not-ready rows | `docs/NOT-READY-TO-FILTER-2026-10-22.md` |
| 2 | 25 not re-run identified | measured from the latest runs |
| 3 | 5 likely ready + redBus uncertain | listed with causes |
| 4 | Action register | `T-022` open |

## What I recommend next

Answer §2: if **A**, I re-run the six in this session (some AI cost, ~6 checklist rows) and update the
report; if **B**, the list stands as-is and `T-022` tracks it.
