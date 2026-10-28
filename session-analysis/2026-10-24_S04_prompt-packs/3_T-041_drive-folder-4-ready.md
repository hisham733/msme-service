# Folder 4 — now 20 ready-to-filter articles only

**Session:** 2026-10-24_S04 · **Turn:** 3 · **IDs:** T-041
**Drive:** https://drive.google.com/drive/folders/104an8yHRRROgqvIAtebKMd4AhC8SQFbO

---

## 1. What was wrong

The first upload had **4 articles that did not pass receive** (`readyToFilter=false`):

| Removed (trashed, recoverable) | Why |
|---|---|
| `Contributed Article What the next generation…_3` | no media → not ready (your example) |
| `Article proposal why Malaysian SMEs lose WhatsApp leads…_1` | no media → not ready |
| `SIARAN MEDIA Anak Sulung Najib…_2` | no media → not ready |
| `ConverXion KL 2026 Returns…_1` | no media → not ready |

**Finnfund `_2` stays** — its latest receive row is ready (`hasPic=true`, `hasLogo=true`). The earlier
flag was from an older duplicate row, not the latest run.

⭐ **Decision — §1:** ✅ nothing to decide — removed as asked.

---

## 2. What was added

Four ready replacements, each with `article.md` + `images/` + `originals/` + `link.md`:

| Added | MSME link | Ready | Media |
|---|---|:--:|---|
| Baker Tilly – IPO director | /baker-tilly-appoints-capital-markets-veteran-lee-kuan-teck… | ✅ | 11 images + 1 original |
| Rolls-Royce – Project Nightingale | /rolls-royce-begins-global-testing-of-100-unit-project-nightingale/ | ✅ | 3 images + 1 original |
| Lion Parcel – Malaysia | /lion-parcel-opens-first-international-office-in-malaysia… | ✅ | 7 images + 4 originals |
| SEAM Cohort 2 | /seam-cohort-2-backs-nine-malaysian-social-enterprises… | ✅ | 8 images + 2 originals |

All four URLs return **200**.

⭐ **Decision — §2:** ✅ nothing to decide.

---

## 3. Final state

| Check | Result |
|---|---|
| `Email_Articles/4` | **20 folders + `_LINKS.md`** |
| Final 20 `readyToFilter` | **20/20 true** (latest checklist row) |
| `4/_LINKS.md` | **20 links** (the removed 4 are gone) |
| Each folder | `article.md` + `images/` + `originals/` + `link.md` |
| Removed 4 | **in Drive trash** (recoverable) |
| `Email_Articles/1/2/3` | **untouched** — 17 / 13 / 2 folders |

Full list: `docs/DRIVE-FOLDER-4-20261024-0808.md` (with the removed section) and `.json`.
Selection: `docs/DRIVE-FOLDER-4-SELECTION.json` (final 20 ready).

⭐ **Decision — §3:** ✅ nothing to decide.

---

## 4. Tool change

`tools/drive_folder4.py` now:

- selects only local articles whose **latest** checklist row has `readyToFilter=true`;
- `--sync` uploads the new selection, **trashes old children of 4** not in it, and rewrites
  `_LINKS.md`;
- **never touches 1/2/3**.

⭐ **Decision — §4:** ✅ nothing to decide.

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | Non-ready articles removed | **4 trashed** |
| 2 | Ready replacements | **4 uploaded** |
| 3 | Final 20 ready | **20/20 true** |
| 4 | Links | **20 in `_LINKS.md`** |
| 5 | 1/2/3 | **untouched** |
| 6 | Tool | **ready-only + `--sync`** |

## What I recommend next

Open **`docs/DRIVE-FOLDER-4-20261024-0808.md`** and check the 20 links against the local folders.
If any replacement is the wrong article, tell me the folder name and I will trash it and pick the next
ready published article.
