# ACCA op-ed — the logo is vector, so the AI never saw it; the code now does

**Session:** 2026-10-22_S02 · **Turn:** 4 · **IDs:** D8 · T-016 · T-013 · T-015

---

## 1. Could the code or AI see it? — measured answer

| Check | Result |
|---|---|
| Attachment | 1 PDF, `ACCA_Pre-Budget Commentary_…pdf`, 126,615 bytes, 4 pages |
| `page.images` (pypdf) | **0 on every page** — there is no raster image anywhere |
| The logo | drawn as **vector paths** in a PDF header artifact: red fill `0.929 0.11 0.141`, a 55.9×55.9 block, **155 path ops**, repeated on all 4 pages |
| The **AI** | **cannot see it** — extract/verify are text-only; the prompt carries only text + image *names* |
| The old classifier | only read `/Subtype /Image` (PDF) and `word/media` (DOCX) → missed vector artwork |
| Old checklist | `hasLogoInArticle=false`, `readyToFilter=false` |

So: **the AI cannot see a logo, ever.** The fix has to be deterministic code, not a prompt.

⭐ **Decision — §1:** ✅ nothing to decide.

---

## 2. What was built and verified live

| Change | Effect |
|---|---|
| `extract._pdf_header_vector_logo()` | reads `/Artifact … /Subtype /Header`; a shape with ≥20 path ops + non-white fill, or a painted 20–400 pt top block, is a **logo** |
| `classify_doc_images` hook | adds a synthetic `pdf-header-vector` entry (`kind=logo`, `location=header`) |
| `pipeline` override | deterministic `docLogo` / `docPhoto` now **set** `hasLogoInArticle` / `hasImageInArticle` true even when the text-only AI says false |
| corpus check | across **85 archived PDFs** the rule flags only the ACCA file; full-bleed backgrounds and `W*` clip boxes are ignored |

**Live re-run `39b13e27-…`:**

- `hasLogoInArticle=true`, `readyToFilter=true`, subjectScore **98**
- `logo_scan.docLogo=true`; detail: `pdf-header-vector`, page 1, `reason=vector_paths`, `paths=155`
- `/archived` now lists it with a real path; the original PDF (which holds the vector logo) is archived
- Deployed as `msme-service:vector-logo-20261022`; `:8898`/`:8900` health OK, compile/import OK

**Note:** no logo image file is produced — the logo is vector, not a picture. It is counted as in-article
branding; the PDF keeps it visually. Extracting a PNG would need a render step (parked).

⭐ **Decision — §2:** ✅ nothing to decide.

---

## 3. Limits and still-open items

- **Text-only wordmarks** (a logo typed as letters, no vector shape) are still not detected; `D8` records
  this limit.
- **T-013** — fetching a linked public web article (vritimes) — parked by your earlier choice.
- **T-015** — report runner still reads only `emails/` (54 of 71 articles are in `all_emails/`) — parked.
- **T-011** — MSIA re-share message — awaiting you.
- **D3** — secret rotation + first commit — still unanswered.

⭐ **Decision — §3:** ✅ nothing new to decide.

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | Why the logo was missed | vector artwork, AI is text-only |
| 2 | Vector header-logo detection | **done, live, verified** |
| 3 | Deterministic evidence overrides AI flags | done |
| 4 | ACCA row | `hasLogoInArticle=true`, `readyToFilter=true` |
| 5 | Text-only wordmark limit | recorded in `D8` |

## What I recommend next

Start a **new session at medium effort** on **T-001 (repurpose)** — the only unbuilt stage. Send the T-011
message in parallel.

> Ready-to-paste prompt: Read `README.md`, `NOW.md`, `todo/INDEX.md` and today's replies. Start `T-001`:
> propose the repurpose output (format + inputs from an ACCEPTed article), ask me one decision, then build.
