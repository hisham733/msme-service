# 12 — N-1 logo gallery: worked examples added

_2026-11-07 (S15) · docs only · no code changed._

## 1. What changed

`docs/new-rules/N-1-logo-gallery.md` grew **240 → 772 lines**; the rule is unchanged, every section now
has concrete examples.

| Section | Examples added |
|---|---|
| §1.1 | three emails: BPMB no image → gallery hit; CIMB no active entry → ask email; AFFIN with a PDF photo → gallery skipped |
| §2.1 | a six-row trigger table with the four flags and the resulting gallery call |
| §3.1 | the BPMB pipeline timeline + the exact `gallery` stage JSON for **hit / miss / error** |
| §4.1.1 | six arithmetic rows (BPMB direct 70, BPMB via Cision 65, AFFIN 100, MATRADE 65, unknown 0) + the CIMB–Maybank false-hit and the undefined all-or-nothing/partial case |
| §4.2.1 | one email per priority tier (domain, subject, display name, file+body, body repeat, fuzzy, ambiguity) + normalisation examples (`BPMB,`, `May Bank`, `B.P.M.B.`, `AB`) |
| §5.1 | one example per method: domain map, two-key, fuzzy, multi-brand, learned cache, alias quality, pHash, TF-IDF |
| §6.1 | five full matches and the exact stage record each would store |
| §7.1 | a five-entry index (BPMB/CIMB/Maybank active, MATRADE pending, AFFIN superseded) + “which entry matches” + path-traversal examples |
| §8 | an “N-1 result” column for the five live posts + a BPMB text-only counter-example |
| §10.1 | what options A/B/C would do on the same BPMB email + demo-seed examples |
| §11.1 | fixture layout, a test `index.json`, seven input→expected rows, and the expected stage JSON |
| §12.1 | the hybrid matcher as pseudocode + two example calls |
| §13 | a one-page cheat sheet: if-this-then-that, four email objects, three stage records, the planned CLI, the smallest useful index |

## 2. Verification

- File length **772 lines**; all **40** code fences balanced.
- 32 headings; no test or runtime code changed (`compileall` not needed for a Markdown-only edit).
- The only semantic clarifications: the BPMB logo-update email is **N-2** (`library_update`), while N-1
  fills a missing image on an article; agency domains are never mapped in the learned cache.

✅ nothing to decide — examples only.

## Recap

| # | Item | State |
|---|---|---|
| 1 | N-1 examples in every section | done |
| 2 | One-page cheat sheet (§13) | done |
| 3 | Rule/code unchanged | yes |

## What I recommend next

**Carry on in this session** (low effort): read §13 first for the quick reference, then §1.1 and §6.1
for the full walk-through. No new session needed.
