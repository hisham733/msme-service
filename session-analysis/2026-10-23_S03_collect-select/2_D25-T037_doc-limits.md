# Document caps: 10 images, first 30 PDF pages — Meltwater 15 min → 115 s

**Session:** 2026-10-23_S03 · **Turn:** 2 · **Image:** `msme-service:doc-limits-20261023`
**IDs:** D25 · T-037 · T-038

---

## 1. What changed

- **10 images per PDF/DOCX** (saved and classified); at most **25 examined** to find them.
- **PDF text: first 30 pages**, any document capped at **150,000 chars**, with a visible truncation marker.
- **No 10 MB hard ignore** — dropped as requested.
- Caps apply to every source: attachments, Drive, OneDrive, Box, Google-native PDF exports.
- `truncated` is recorded in the doc-image stages.

⭐ **Decision — §1:** ✅ nothing to decide — built as confirmed.

---

## 2. Measured on the 38.7 MB / 906-page Meltwater PDF

| Step | Before | After |
|---|---:|---:|
| Text extraction | all 906 pages, >240 s | 30 pages, 29,564 chars, **25.4 s** |
| Image classification | 25 images, 15.6 s | 10 images, **8.2 s** |
| Photo extraction | all images, 29.7 s | ≤25 examined / 10 saved, 27.5 s |
| **End-to-end (fake AI, real Gmail/Drive)** | **~15 min** | **114.9 s** |

The text cap is the real fix; images were only ~46 s of the old run.

⭐ **Decision — §2:** ✅ nothing to decide.

---

## 3. Verified

**Unit:** `python3 -m unittest tools.test_collect_select -v` → **15 pass** (limits, 30-page stop, 10-image cap, truncation).

**Fake-AI end-to-end** (temp DB/archive, real Gmail/Drive — production data untouched):

| Email | Time | Ready | Media |
|---|--:|:--:|---|
| Meltwater | **114.9 s** | ✅ | `hasImageInArticle` + `hasLogoInArticle` |
| Workplace (21 MB DOCX) | **47.6 s** | ✅ | `hasPic` + `hasLogo` |
| Pink October (190 MB extra PDF) | **150 s** | ✅ | `hasPic` + in-article image/logo |
| MRCA (13 MB captions DOCX) | **7.7 s** | ✅ | in-article image/logo |

**Live AI re-run:** blocked by **DeepSeek 402 Insufficient Balance**, **after** every document stage
completed (`drive_fetch` textLen 29,564, images truncated). This is not a code failure. The previous
Meltwater row **378** remains ready.

⭐ **Decision — §3:** the live AI step needs `T-038` (below).

---

## 4. Live state and records

- Live totals moved to **153 emails · 135 ready · 18 not ready** while this session ran: four newer
  emails were processed after the 149 snapshot. Trainocate is now **ready**; “Sustainable Action
  Conference” (image-only attachments, no release text) and “31% cart abandonment” (article, no media)
  are new not-ready rows.
- `docs/NOT-READY-TO-FILTER-2026-10-22.md` and `docs/SENDER-ASKS-2026-10-22.md` still describe the
  **149 snapshot** (17 not ready / 11 asks). Refresh them before sending: Remove Trainocate, add the
  cart-abandonment media ask and the Sustainable Action Conference text ask.
- `D25` + `T-037` recorded, indexes regenerated; `NOW.md` updated.

⭐ **Decision — §4:** ✅ nothing to decide — but the asks docs need a refresh before sending.

---

## 5. The AI balance blocker

`T-038` is the only thing between the verified document caps and a live successful re-run.

| Option | What it means | Effect |
|---|---|---|
| **A — top up DeepSeek** | Keep the same model/quality; add credit | Live runs work again; no prompt/behaviour change |
| **B — switch to Gemini** | Set `LLM_PROVIDER=gemini` in Config (key already present) | Unblocks immediately, free tier; re-test one email for extraction quality |

**Not decided:** every new receive currently fails at the AI step with 402; existing rows are safe.
Decision needed before the next live run.

⭐ **Decision — §5:** **A** (top up, recommended for continuity) · **B** (switch to Gemini now)?

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | 10 images per PDF/DOCX | **built + tested** |
| 2 | 30 PDF pages / 150k chars | **built + tested** |
| 3 | 10 MB hard ignore | **dropped** |
| 4 | Meltwater speed | **~15 min → 115 s** |
| 5 | Live AI re-run | **blocked: DeepSeek 402** (`T-038`) |
| 6 | Live totals | **153 · 135 ready · 18 not** (docs stale) |

## What I recommend next

Top up DeepSeek (**A**) and say **“re-run Meltwater and Workplace”** — both should finish in ~2 minutes
and stay ready. If you prefer to unblock without paying now, choose **B** (Gemini), then I will re-run
one email first to check extraction quality before touching the batch.
