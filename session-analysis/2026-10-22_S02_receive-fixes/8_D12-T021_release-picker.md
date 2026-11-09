# HARI EKSPORT PERAK — the release was in the Drive folder, but a **speech** was picked

**Session:** 2026-10-22_S02 · **Turn:** 8 · **IDs:** D12 · T-021 · T-018

---

## 1. Why it said "no article"

The Drive media kit held **three** documents:

| Doc | Length | What it is |
|---|--:|---|
| `[SIARAN AKHBAR] HARI EKSPORT PERAK 2026 …docx` | 6,150 | **the press release** — headline is exactly the email subject |
| `Ucapan Aluan MATRADE - Export Day Perak 2026.pdf` | 11,022 | welcome speech |
| `TEKS UCAPAN PERASMIAN EN.KUMARESAN EXPORTDAY.pdf` | 10,350 | opening speech |

`pipeline.py` took the **longest** doc for the article text → the welcome speech. Verify then correctly
said "TEKS UCAPAN ALUAN … rather than a press release" → `hasArticle=false`, subject score 10. The release
was present; the **doc picker** failed.

Confirmed: the release DOCX starts with `NOTA KEPADA EDITOR: HEBAHAN SERTA-MERTA` and its first line is
the email subject verbatim.

⭐ **Decision — §1:** ✅ nothing to decide (defect found, logged).

---

## 2. Logged — no code changed

| Register | Content |
|---|---|
| `decisions/D12.md` | pick the **release-named** doc (siaran akhbar / press release / kenyataan media / nota kepada editor …), deprioritise speeches (`ucapan`, `speech`, `remarks`, `perasmian`); English then length only as tie-breaks |
| `todo/✅ T-021.md` | build item (`decided-unbuilt`): multilingual picker used by both `attachment_text` and the extract prompt |
| `todo/✅ T-018.md` | HARI EKSPORT PERAK row added to the batch queue |

Current queue:

| Case | Missed | Cause | State |
|---|---|---|---|
| MSIA | article | Drive file view-only | fixed + live |
| IRGCE | picture | inline body photos | fixed + live |
| ACCA | logo | vector PDF header | fixed + live |
| Aventra | picture/logo | body logo + download link | logged |
| ACCCIM | subject match | label vs headline | logged |
| ACCCIM banner | image in article | header/footer strips called photos | logged |
| **HARI EKSPORT PERAK** | **article** | **longest doc = speech, release ignored** | **logged** |

⭐ **Decision — §2:** ✅ nothing to decide.

---

## 3. Protocol

Keep sending the cases; I append one row each and change no code. When you say **"list complete"**, I
build `T-017`, `T-019`, `T-020`, `T-021` in one batch, deploy once, and write one verification reply.

⭐ **Decision — §3:** ✅ nothing to decide.

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | Release present in Drive | yes — 6,150-char DOCX |
| 2 | What was extracted | welcome speech (longest text) |
| 3 | Fix | release-name picker — `D12` / `T-021`, logged |

## What I recommend next

Send the remaining cases, then **"list complete"** — batch build, one deploy, one reply. **Medium** effort.
