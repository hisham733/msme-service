# v1 is live — verified on a real email

**Session:** 2026-10-24_S04 · **Turn:** 2 · **IDs:** D27 · T-040
**Model:** `deepseek/deepseek-flash` · **Total A/B + live cost:** **$0.10** (balance $9.61 → $9.51)

---

## 1. What changed

- `docker-compose.yml` now sets **`PROMPT_VERSION=v1`**; the container was rebuilt.
- Live check: `config.PROMPT_VERSION == "v1"`; extract/verify/decide prompt lengths are the v1 packs.
- Rollback: set `PROMPT_VERSION=v0` (or remove it) and rebuild. The v0 files are untouched.

⭐ **Decision — §1:** ✅ nothing to decide — switched as requested.

---

## 2. Live verification — one real email, dry-run

`1a1662ce839b0678` — **MRCA Retail Tech Summit 2026**, 42.6 s, **11,215 tokens**, no writes.

| Field | Value |
|---|---|
| `hasArticle` | **true** |
| `hasPic` / `hasLogo` | false / false |
| `hasLogoInArticle` / `hasImageInArticle` | **true / true** |
| `subjectMatch` / `subjectScore` | true / **100** |
| `readyToFilter` | **true** |

The reason is consistent: *“The subject matches the article headline and first paragraph exactly,
and the document contains an embedded logo and photo.”*

**Issue found and fixed:** the first live run returned `readyToFilter=true` but a reason saying
“no media” while `docLogo`/`docPhoto` were true. `verify_prompt.v1.txt` now maps
`docLogo → hasLogoInArticle=true`, `docPhoto → hasImageInArticle=true`, and requires the reason to
agree with the flags. The re-run above is the fixed result.

⭐ **Decision — §2:** ✅ nothing to decide.

---

## 3. Final A/B — two 6-email runs

| Run | v0 ready / flags | v1 ready / flags | v0 text / tokens | v1 text / tokens |
|---|---|---|---|---|
| post-fix | 6/6 · 34/36 | **6/6 · 34/36** | 0.987 · 76,555 | **0.970 · 67,099 (−12.4%)** |
| first | 6/6 · 34/36 | **6/6 · 34/36** | 0.969 · 82,868 | **0.991 · 75,211 (−9.2%)** |

- **No ready/flag regression** in either run; text similarity 0.97–0.99 for both (the order flips
  between runs — normal model variance). **Token saving is consistent: 9–12%.**
- The only flag mismatch is one case's `hasPic` + `hasLogoInArticle` in both versions; it comes from
  the reconstructed archive media, not the prompt.
- Reports: `docs/PROMPT-EVAL-20261024-0700.md` (final) and `...-0630.md` (first).

⭐ **Decision — §3:** ✅ nothing to decide.

---

## 4. State and rollback

- Live DB unchanged after the dry-runs: **208 checklist · 322 runs · 218 pipeline_results**.
- Tests: **44 pass**.
- Rollback is one line: `PROMPT_VERSION=v0` + rebuild.
- v1 applies only to the receive AI (extract/verify/decide); the filter/Jev and reply prompts are
  unaffected (no v1 files, so they use their base prompts).

⭐ **Decision — §4:** ✅ nothing to decide.

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | `PROMPT_VERSION=v1` | **live** |
| 2 | Real-email dry-run | **ready · in-article logo/photo · 11.2k tokens** |
| 3 | Reason/flags contradiction | **fixed in v1 verify prompt** |
| 4 | A/B (2 × 6 emails) | **ready 6/6 · flags 34/36 both · tokens −9/−12%** |
| 5 | No writes / tests | **DB unchanged · 44 pass** |

## What I recommend next

Process the next real batch normally; v1 is live and writes will use it. Watch the first 3–5 rows for
the `readyToFilter` and media flags. If anything looks worse, reply **“rollback v0”** and rebuild — one
line.
