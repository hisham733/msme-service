# Weekly report — done, issues, next

**Session:** 2026-10-24_S04 · **Turn:** 4 · **IDs:** T-038 · T-042 · T-043 · T-044 · T-045
**Report:** [`docs/WEEKLY-REPORT-2026-10-24.md`](../../docs/operations/WEEKLY-REPORT-2026-10-24.md)

---

## 1. What we did (S01–S04, 21–24 Oct)

- **Receive**: Drive file links, body images, vector/header logos, standalone logos,
  Drive/OneDrive/Box/web sources, collect-then-select, and document caps. Live state
  **208 rows · 140 ready · 68 not ready**.
- **Archive**: sorted `all_emails/` into **40** (15+) and **111** (14-); **47** older versions
  in `_duplicates/`, **12** no-article in `_no_article/`.
- **Reports**: reads `all_emails/`, **151 groups**, **114 rows** in the default range, folder
  selector All/15+/14-, versions sheet + `/report/duplicates`.
- **Prompt v1 live**: A/B on 6 emails → **ready 6/6**, flags **34/36**, tokens **−9% / −12%**,
  text 0.97–0.99, **$0.10**; live MRCA ready, 11,215 tokens.
- **Workflow Lab**: 8-stage walkthrough, real code, details, examples, animated diagram,
  **42 `.py`** map.
- **Drive folder 4**: **20 ready published articles**; 4 non-ready removed, 4 ready
  replacements; `1/2/3` untouched.
- **Tests**: **44 pass**.

⭐ **Decision — §1:** ✅ nothing to decide — report only.

---

## 2. Still an issue

| ID | Issue | Impact |
|---|---|---|
| **T-042** | Refresh returns **read + unread** (query lacks `is:unread`) | `/run-all` and scheduler can re-process read mail |
| **T-043** | Event Me Now says **not ready**; PitchMyStory page has a 1536×1024 photo but the URL is rejected and WebP dims are unsupported | A published article stays not ready |
| **T-044** | `folderId`/`folderUrl` empty for **208** rows; **Sheet 403** for `ainews.msme@gmail.com` | Dashboard “open” link blank; Sheet is not writable |
| **T-005 / T-009** | Report values not independently verified; variant map stale | Filter confidence |
| **T-001 / T-008 / T-024** | Repurpose not built; image accuracy <100%; <1 MB photos still `hasPic=false` | Pipeline completeness |
| **T-038** | DeepSeek 402 | **Resolved** — renewed, $9.51 |

**Still on you:** T-022 asks + T-011 MSIA PDF; D3 secrets/commit; T-028 consent screen;
T-045 check the 20 folder-4 links.

⭐ **Decision — §2:** ✅ nothing to decide — report only.

---

## 3. Next todo (in order)

1. **T-042 — unread-only Refresh** (small, high impact; also stops re-processing).
2. **T-043 — published-release featured image** (PitchMyStory + WebP); re-run Event Me Now.
3. **T-044 — published links in the checklist** (and Sheet 403).
4. **T-005 + T-009** — verify a report; map the variants.
5. **T-001 — Repurpose.**
6. **User actions** — asks, secrets/commit, consent screen, folder-4 check.

⭐ **Decision — §3:** start **T-042** next (recommended), or T-043 first?

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | Receive + archive | **208 · 140 ready · 68 not** |
| 2 | Reports | **151 groups · 114 rows** |
| 3 | Prompt v1 | **live · −9/−12% tokens** |
| 4 | Workflow Lab | **built · 42 files** |
| 5 | Drive folder 4 | **20 ready · 1/2/3 untouched** |
| 6 | Tests | **44 pass** |
| 7 | Open | **T-042 · T-043 · T-044 · T-005/T-009 · T-001** |

## What I recommend next

Continue in this session at **low effort** with **T-042** (unread-only Refresh) — it is a small
server-side query fix plus a test, and it also stops the scheduler re-processing read mail.
Then T-043 (published-release media) and T-044 (checklist links).
