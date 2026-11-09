# 13 — N-1 gallery built (option B + hybrid priority ladder)

_2026-11-07 (S15) · code + tests + container rebuilt._

## 1. What was built

| Part | Result |
|---|---|
| **Option B** | The N-1 trigger now uses `hasUsableLogo` = **vector or max side ≥ 200 px**. A 40×20 icon or a `logo.png` under 200 px no longer suppresses the gallery; if the gallery misses, the article is not ready and the ask email is sent. `hasLogo` stays factual on the checklist. |
| **Matcher (§6)** | `msme/receive/gallery.py`: domain → subject → display name → filename+body → agency body repeat → fuzzy → ambiguity. Scores 100/95/90/85/80/fuzzy×100; two brands within **10 points → miss**. Active `logo` entries only; known agencies `cision.com`, `mediaoutreach.com`, `vritimes.com`. |
| **Pipeline stage** | between `logo_scan` and `verify`; a hit adds `gallery_logos[...]`, sets `hasLogo` + `hasUsableLogo`, archives the file and records `stages["gallery"]`. A miss/error never fails the run. |
| **Readiness/reply** | `_media_asset` uses `hasUsableLogo`; `reply.py` asks for an image when `hasUsableLogo=false`. |
| **Store** | `data/gallery/index.json` + images; safe path resolution (`..`/absolute rejected); max file size. |
| **CLI** | `tools/gallery_admin.py check` (dry-run) and `add` (copy + index, older active logo superseded). |
| **Live seed** | **BPMB** (`BPMB_11-November-2026_MALAYSIA-SME.png`) and **MATRADE** (`MATRADE_07-November-2026_MALAYSIA-SME.png`), both `active`. |

## 2. Verification

| Check | Result |
|---|---|
| Full suite | **259 tests, OK** (8 skipped) |
| New gallery tests | **18**: every tier, ambiguity, pending/superseded, normalisation, path traversal, option B |
| Live matcher (container) | Cision + “Bank Pembangunan Malaysia Berhad…” → **hit tier 2**, file `BPMB_11-November-2026_MALAYSIA-SME.png`, 56,122 bytes |
| Other live checks | BPMB direct → tier 1; MATRADE via agency → tier 2; unknown brand → miss |
| Compile | OK |
| Container | rebuilt, `/api/health` **200**, `{"webhook": true, "auto": false}` |

## 3. What remains

- MSME’s **10–20 gallery images** are still to add; the two real seeds prove the mechanics.
  Add each with:
  `python3 tools/gallery_admin.py add --file … --brand … --aliases … --domain …`
- The 2026-11-11 call still needs the four gallery questions in N-1 §9 answered.
- `data/gallery/` is live data (gitignored), not committed.

✅ nothing to decide — option B and the §6 ladder are built and proven.

## Recap

| # | Item | State |
|---|---|---|
| 1 | Option B usable-logo floor | done |
| 2 | Hybrid priority ladder (§6) | done |
| 3 | Pipeline stage + archive | done |
| 4 | Reply/readiness use the usable flag | done |
| 5 | CLI + live seed (BPMB/MATRADE) | done |
| 6 | Tests + container | 259 pass; healthy |
| 7 | MSME’s 10–20 images | pending their pack |

## What I recommend next

**Carry on in this session** (low effort): add the rest of the logos with `gallery_admin.py add`
when MSME sends the pack; no new session is needed.
