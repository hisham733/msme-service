# 14 — N-1 tier 5 amended (A) + Xendit logo live

_2026-11-07 (S15) · "go with A" · the Xendit 6-market email now resolves to ready._

## 1. What changed

| Part | Before | After |
|---|---|---|
| **Tier 5 rule** | alias ≥2× in body **and** known agency sender | exact alias in the first `GALLERY_BODY_LEAD_CHARS` (600) chars **and** ≥2× in body, **any sender** (`msme/receive/gallery.py`, `msme/config.py`) |
| **Xendit logo** | SVG content saved as `.png` (121×37, `_image_dims` = 0×0) | real 600×183 PNG (50 KB), same gallery name |
| **Registration** | file dropped in `data/gallery/` only — invisible to the matcher | `gallery_admin add` wrote the `index.json` entry (brand Xendit, aliases Xendit, domains xendit.com/xendit.co, active) |
| **Docs/tests** | §6 tier 5 = agency gate | §6 + §4.2 aligned; `D43` amended; `tests/test_gallery.py` tier-5 test rewritten + a negative (no-lead → miss) added |

Why A: the agency gate missed forwarded editor emails (`editor@malaysiasme.com.my`) whose release text
names the brand. The 600-char lead keeps it strict — a brand only in the body tail still misses.

## 2. Verification (measured)

| Check | Result |
|---|---|
| Full suite | **260 tests OK** (8 skipped; +1 new negative tier-5 test) |
| `tests.test_gallery` | 19 tests OK |
| `compileall msme run.py tools tests` | OK |
| Matcher on the real email (host + container) | `hit` brand **Xendit**, **tier 5**, field `body`, score 80 |
| Image rebuilt + restarted | `/api/health` `{"status":"ok", …}`; container sees `GALLERY_BODY_LEAD_CHARS=600` and index `[BPMB, MATRADE, Xendit]` |
| Live re-run (`POST /api/run`, id `1a162cb47c8e3493`) | run `success`; checklist **hasLogo=true, readyToFilter=true** (subjectScore 86) |
| Archive | `all_emails/…_3/images/xendit_07-November-2026_MALAYSIA-SME.png` = real PNG 600×183 |

`pipeline_results` gallery stage: `{"status":"hit","brand":"Xendit","tier":5,"field":"body", …}`.

## 3. Notes

- The re-run created a fourth archive folder (`…_3`) for this subject — re-runs append a new folder
  rather than overwrite (pre-existing behaviour).
- `data/gallery/` is gitignored live data; the code/decision changes are staged only by you (profile
  denies `git commit`).
- **N-2** (`library_update`) is still spec-only and untouched this turn — a different path (emails with
  no article at all), not the xendit case.

✅ nothing to decide — A is built, deployed and the email is ready.

## Recap

| # | Item | State |
|---|---|---|
| 1 | Tier 5 = first-600-chars + ≥2× body, any sender | done |
| 2 | Xendit SVG → real 600×183 PNG | done |
| 3 | Xendit registered in `index.json` | done |
| 4 | Docs (§6/§4.2, D43), tests | done; 260 pass |
| 5 | Deploy + live re-run | readyToFilter=true |

## What I recommend next

Carry on in this session (low effort): add the remaining logos with `gallery_admin add` as MSME sends
them, and re-run the N-2 build decision at the 2026-11-11 call (N-2 is still unbuilt).
