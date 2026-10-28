# “Simple chart” tab — animated 8-step receive workflow

**Session:** 2026-10-23_S03 · **Turn:** 6 · **IDs:** T-039
**Page:** `http://localhost:8899/workflow-lab.html#chart`

---

## 1. What changed

- New **Simple chart** tab next to **Walkthrough** (same page, no new backend).
- **Auto-playing animation** of the 8 receive steps: each card lights up, the connector fills,
  the progress bar advances and a one-line narration says what is happening.
- **Play / Pause / Play again / Reset**, a step counter (`4 / 8`), and a smooth scroll to the active card.
- **Click any card** for a plain-English detail card: *what goes in · what comes out · why it matters*,
  plus an **Open in walkthrough →** button.
- **Readiness equation**:
  `article found + photo or logo + subject match > 60 = readyToFilter`.
- **What happens next** panel: ready rows go to the filter (:8900); not-ready rows stay for a reply or
  a human check.
- Deep link: `#chart` opens the chart directly; the walkthrough and code map stay unchanged.
- Respects `prefers-reduced-motion`: shows the complete flow without animation.

⭐ **Decision — §1:** ✅ nothing to decide — built as asked.

---

## 2. Verified

- Page `GET /workflow-lab.html` → **200**; chart markup present.
- Browser check (Playwright, 1500×1200): at 6 s stage **4/8 “Fetch content”** is active with its detail
  card; at 15 s the run completes **8/8** with “▶ Play again” and the ready equation visible.
- `node --check` on the inline JS → **OK**.
- No backend change in this turn: tests remain **38 pass**; live DB counts unchanged
  (**208 checklist · 322 runs · 218 pipeline_results**).

⭐ **Decision — §2:** ✅ nothing to decide.

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | “Simple chart” tab | **built + live** |
| 2 | Auto-play + Play/Pause/Replay | **done** |
| 3 | Clickable plain-English detail | **done** |
| 4 | Readiness equation + next step | **done** |
| 5 | Deep link `#chart` | **done** |

## What I recommend next

Open **`http://localhost:8899/workflow-lab.html#chart`** and let it play once — it is the fastest way
for a normal user to understand the workflow. The **Walkthrough** tab stays for the code and the
runnable examples.
