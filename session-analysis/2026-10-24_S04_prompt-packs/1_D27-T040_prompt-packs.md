# Versioned receive prompts — v1 wins on text and tokens

**Session:** 2026-10-24_S04 · **Turn:** 1 · **IDs:** D27 · T-040
**Model:** `deepseek/deepseek-flash` · **Cost of the A/B:** **$0.09** (balance $9.61 → $9.52)

---

## 1. What was built

- **Versioned loader**: `config.load_prompt(name, version=...)`; `PROMPT_VERSION` env selects the
  default; a missing version falls back to the base.
- **v1 packs** for the three row-shaping jobs:
  - `prompts/extract_prompt.v1.txt` — slim 7-key schema, candidate rule, no-article path, examples.
  - `prompts/verify_prompt.v1.txt` — exact headline/label-subject rules, media-flag guard, examples.
  - `prompts/decide_prompt.v1.txt` — English-first, release-vs-report names, link guard, examples.
- **Plumbing**: `prompt_version` flows through `process_email` / `process_model` / `_run_pipeline` →
  decide/extract/verify. The live default is unchanged (v0).
- **A/B harness** `tools/prompt_eval.py`: rebuilds archived emails from `all_emails/` + their checklist
  rows (cover note + originals/images), runs the **real pipeline** in dry-run with a fake Gmail service,
  and compares v0/v1. No archive/Sheet/DB writes.
- **Tests**: `tools/test_prompt_eval.py` — 6 pass; full tools suite **44 pass**.

⭐ **Decision — §1:** ✅ nothing to decide — built as approved.

---

## 2. Measured — 6 archived emails, 36 AI calls

| Version | ready OK | flags | full-text sim | len ratio | tokens | seconds |
|---|---:|---:|---:|---:|---:|---:|
| v0 | 6/6 | 34/36 | 0.969 | 0.972 | 82,868 | 187.9 |
| **v1** | **6/6** | **34/36** | **0.991** | **1.014** | **75,211 (−9.2%)** | **178.2** |

- Winners: **v1 1 · tie 5 · v0 0**.
- v1 returns **more complete article text** (full-text similarity 0.969 → 0.991; length ratio
  0.972 → 1.014) and uses **~9% fewer tokens**.
- The only flag mismatch is **Monash** `hasPic` + `hasLogoInArticle` in **both** versions; it comes from
  the reconstructed archive media, not the prompt. `hasArticle`, `hasLogo`, `hasImageInArticle` and
  `subjectMatch` match 6/6 in both.

Report: `docs/PROMPT-EVAL-20261024-0630.md` + `.json`.

⭐ **Decision — §2:** ✅ nothing to decide.

---

## 3. How to switch / rollback

```bash
# v1 live
#   add PROMPT_VERSION=v1 to docker-compose.yml, then:
docker compose up -d --build

# rollback
#   remove PROMPT_VERSION (or set PROMPT_VERSION=v0), rebuild
```

The base v0 files are untouched, so rollback is one line. Deterministic guards stay active in both:
link-guard, media dimensions, `_finalize`, `readyToFilter`, checklist contract, archive naming.

⭐ **Decision — §3:** ✅ nothing to decide — the switch is §4.

---

## 4. The live switch

v1 is safe on the measured sample: no ready/flag regression, better text, fewer tokens. The sample is
**6 emails**, so a larger 12–20 email run is the cautious option (≈$0.20).

| Option | What it means | Effect |
|---|---|---|
| **A — switch v1 now (recommended)** | set `PROMPT_VERSION=v1`, rebuild, run one real email | Better text + ~9% tokens now; v0 rollback ready |
| B — run 12–20 first | another A/B (~$0.20) before switching | More confidence; delays the switch |

⭐ **Decision — §4:** **A** (switch v1 live now) · **B** (larger evaluation first)?

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | Versioned loader + v1 packs | **built** |
| 2 | A/B harness on `all_emails` | **built + run** |
| 3 | v1 ready/flags | **6/6 · 34/36 (same as v0)** |
| 4 | v1 text / tokens | **0.991 · −9.2%** |
| 5 | Tests | **44 pass** |
| 6 | Live switch | **awaiting your A/B** |

## What I recommend next

**A — switch v1 live now.** Reply “A” and I will set `PROMPT_VERSION=v1`, rebuild, run one real email,
and report the row; v0 stays one line away. If you prefer more evidence first, reply “B” and I will run
12–20 emails for ≈$0.20.
