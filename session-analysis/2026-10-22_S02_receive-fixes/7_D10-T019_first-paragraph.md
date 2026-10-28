# Subject match — headline **+ first paragraph** (your suggestion, measured)

**Session:** 2026-10-22_S02 · **Turn:** 7 · **IDs:** D10 · T-019 · T-018

---

## 1. Yes — and the data supports it

I updated `D10` / `T-019`: the subject is compared with the **headline**, the **first paragraph after the
headline**, and the chosen **attachment filename** — not the headline alone.

| Signal | Rule |
|---|---|
| Exact label | normalised subject appears verbatim in the headline / first paragraph / filename |
| Key-token coverage | ≥ **60 %** of the subject's key tokens (≥ 2) appear in headline + first paragraph; generic label words (`press, statement, release, news, media, advisory, commentary…`) and stopwords are removed |
| Score | exact → max(AI, 85); coverage → max(AI, 70 + 25 × coverage), cap 95 |

**Measured on the 13 current `subjectMatch=false` rows:** coverage ≥ 0.60 flags **5**, all inspected and
correct:

| Row | Coverage | Article is correct? |
|---|--:|---|
| ACCCIM Budget 2027 | 1.00 | yes (label is line 1 of the PDF) |
| OCBC Perspectives | 0.83 | yes (headline is "MEDIA STATEMENT", first paragraph names OCBC) |
| PIKOM Reaction | 0.80 | yes |
| redBus commentary | 1.00 | yes |
| Mimecast data residency | 0.64 | yes |

An unrelated subject/article pair scores ~0, so the 0.60 bar does not open the door to any match.

⭐ **Decision — §1:** ✅ nothing to decide (rule updated, logged).

---

## 2. Logged — no code changed

- `decisions/D10.md` — the refined rule (headline + first paragraph + filename; exact or ≥60 % coverage).
- `todo/T-019.md` — build item, **`decided-unbuilt`**: deterministic override **and** a
  `verify_prompt.txt` change so the AI itself compares subject vs headline + first paragraph and accepts
  label subjects.
- `todo/T-018.md` — ACCCIM row updated; OCBC/PIKOM/redBus/Mimecast noted as extra rows covered by the same fix.

No code change, no deploy.

⭐ **Decision — §2:** ✅ nothing to decide.

---

## 3. Queue

| Case | Missed | Fix | State |
|---|---|---|---|
| MSIA | article | D6 · T-010 | fixed + live |
| IRGCE | picture | D7 · T-012 | fixed + live |
| ACCA | logo | D8 · T-016 | fixed + live |
| Aventra | picture/logo | D9 · T-017 | logged |
| ACCCIM | subject match | D10 · T-019 (**now headline + first paragraph**) | logged |
| ACCCIM banner | image in article | D11 · T-020 | logged |

⭐ **Decision — §3:** ✅ nothing to decide.

---

## Recap

| # | Item | State |
|---|---|---|
| 1 | Subject vs first paragraph | rule updated, measured on 13 rows |
| 2 | 5 correct label/paraphrase articles | would match, no false pair found |
| 3 | Code | not changed (batch protocol) |

## What I recommend next

Send the remaining cases, then say **"list complete"** — the batch will implement `T-017`, `T-019` and
`T-020` together in one deploy. **Medium** effort.

> Ready-to-paste when done: `list complete — build every logged row in T-018 in one batch.`
