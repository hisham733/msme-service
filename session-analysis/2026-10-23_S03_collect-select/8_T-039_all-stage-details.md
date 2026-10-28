# Details for all stages — walkthrough + diagram

**Session:** 2026-10-23_S03 · **Turn:** 8 · **IDs:** T-039
**Page:** `http://localhost:8899/workflow-lab.html` (`#chart` for the diagram)

---

## 1. What changed

- Every stage now carries a **`Details` section** in two places:
  - the **Walkthrough → Explain** tab (under *What goes in / What comes out*),
  - the **Workflow diagram** detail card (under *Why it matters*).
- The two decision nodes (*Where is the article?*, *Ready to filter?*), the four fetch branches and the
  ready / not-ready outcomes also have their own details.
- The stage list title/summary now stack correctly (no more run-together text).

⭐ **Decision — §1:** ✅ nothing to decide — built as asked.

---

## 2. What each stage now explains

| Stage | Details added |
|---|---|
| **Receive** | query, unread-only, cached list, marks read after success, rate-limit/token stop |
| **Read & clean** | fields parsed, attachment inventory, cover/disclaimer/forward stripping, link collection, up-to-8 redirect resolution, full body vs `cleanBody` |
| **Choose source** | input fields, English preference, image/media-kit flags, link guard, confidence/reason, body fallback |
| **Fetch content** | all attachments, PDF 30 pages/150k, DOCX 10 images/25 examined, Drive/shared drives/Google-native exports, OneDrive/Box/web, body images/asset links, caps, `needs_human` |
| **Extract article** | candidate pool C1..Cn, `chosenCandidate` values, fallback, text-only flag rule, link guard, no-article path |
| **Check media** | four flags, email vs article, PDF/DOCX scanning, 10/25 limit, logo-vs-photo dimensions, in-article never `hasPic` |
| **Decide readiness** | prompt inputs, full output list, D10 subject match, deterministic guard/override, exact `readyToFilter` formula, `needs_human` |
| **Save** | the 14 columns, Sheet + SQLite, archive path/collision rule, reply conditions, run log, `needs_human` |

Diagram-only details:
- **Where is the article?** — attachment / Drive·OneDrive·Box / web / body, collected before the AI.
- **Fetch branches** — attachment, PDF/DOCX caps, Drive, OneDrive/Box/web, body images/assets, caps and
  failures.
- **Collect candidates** — dedupe, C1..Cn labels, body fallback.
- **Ready to filter?** — article + media + subject > 60, deterministic recompute, blocked source.
- **Ready / Not ready / Two outcomes** — filter list vs reply/human review, both rows kept.

⭐ **Decision — §2:** ✅ nothing to decide.

---

## 3. Verified

- Screenshots: **Receive** (walkthrough, Details visible), **Save**, **Where is the article?**,
  **Two outcomes** (diagram, Details visible); **Check media** still shows the media callout + four-flag
  map.
- `/api/workflow/stages` → 8 stages, details counts **5 · 6 · 6 · 7 · 7 · 8 · 7 · 6**.
- Page `GET /workflow-lab.html` → **200**; **38 tests pass**; live DB unchanged
  (**208 checklist · 322 runs · 218 pipeline_results**).

⭐ **Decision — §3:** ✅ nothing to decide.

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | Details on all 8 stages (walkthrough) | **done** |
| 2 | Details on every diagram node | **done** |
| 3 | Decision/branch/outcome details | **done** |
| 4 | Stage-list text spacing | **fixed** |
| 5 | Tests / no writes | **38 pass · DB unchanged** |

## What I recommend next

Open the **Walkthrough**, click each stage and read the **Details** box; then switch to **Workflow
diagram**, press Play, and click any node — the same detail appears under the diagram. The media
section is the richest example.
