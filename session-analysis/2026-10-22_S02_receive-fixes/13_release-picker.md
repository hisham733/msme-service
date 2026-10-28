# Release selection strengthened — Malay fix + content-aware picker

**Session:** 2026-10-22_S02 · **Turn:** 13 · **Image:** `msme-service:picker-20261022`
**IDs:** D16 · T-026

---

## 1. What changed

| Change | Effect |
|---|---|
| `prompts/decide_prompt.txt` | `siaran akhbar` / `siaran media` now means **press release**; `laporan` (Malay report) is what to ignore. The old prompt wrongly told the AI to ignore "siaran". |
| `drive_fetch.pick_release_doc` | chooses by **name score + first ~1,200 chars**: release markers (`for immediate release`, `nota kepada editor`, `siaran akhbar`, `kenyataan media`, dateline, `About …`) add points; speeches (`teks ucapan`, `opening address`, `remarks`) and reports (`executive summary`, `methodology`, `appendix`) subtract. English then longest text only as a fallback. |

## 2. How the decision works now (the answer to your question)

- **Attachment:** the AI decider (`decide.py`) sees subject/body + attachment **names/types/sizes** — never file contents — and picks one; the prompt rules now handle Malay correctly.
- **Drive/OneDrive/Box kit:** **code**, not the AI, ranks the documents by name + first paragraph (`D12` + `D16`); only the chosen release is sent to Extract.
- **Body-only release:** the Extract AI uses the email body; Verify finds the headline and subject match.
- **After selection:** Extract reads the chosen text; Verify + deterministic guards (`D8`/`D10`) decide the final flags.

## 3. Tests — measured

| Test | Result |
|---|---|
| HARI EKSPORT actual kit (release 6,150 vs speeches 11,023 / 10,350) | **release DOCX** |
| APAC OneDrive actual kit (press release vs CEO report) | **`Egon Zehnder APAC_Press Release…pdf`** |
| Generic `document.pdf` ("FOR IMMEDIATE RELEASE" + dateline) vs `report.pdf` ("Executive Summary") | **document.pdf** |
| `Siaran Akhbar - Program PMKS.docx` vs `Laporan Tahunan 2026.pdf` | **Siaran Akhbar** |

Deployed in `msme-service:picker-20261022`; health OK on `:8898`/`:8899`/`:8900`. No re-run was needed —
the APAC and HARI rows already used the correct file, and the picker was tested on their real kits.

⭐ **Decision — §1:** ✅ nothing to decide.

---

## 4. Still open

- **`D14` / `T-024`** — attached photos <1 MB still `hasPic=false` (APAC ready via the OneDrive PDF).
- **`T-022`** — send the 10 drafted asks (`docs/SENDER-ASKS-2026-10-22.md`).
- **`T-011`** — MSIA re-share.
- **`T-001`** — repurpose.

⭐ **Decision — §2:** ✅ nothing new to decide.

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | Malay "siaran" prompt bug | fixed |
| 2 | Content-aware release picker | done, tested on real kits |
| 3 | Deployed | `picker-20261022`, health OK |

## What I recommend next

Send the T-022 asks + T-011. The next build remains **T-001 (repurpose)** — new session, medium effort.
