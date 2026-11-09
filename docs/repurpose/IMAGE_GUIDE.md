# IMAGE_GUIDE — how the image skill is judged, and how to tune it

> **Vendored here (`D40` / `T-050`, 2026-11-06).** This is the upstream engine document.
> In this repository the engine lives in `msme/repurpose/engine/` and runs in-process on :8899;
> `config.local.json`, the `:8765` dashboard and `python -m pipeline.*` commands no longer apply.
> Use `python -m msme.repurpose.engine.<module>` and `/repurpose.html`; paths come from
> `msme/paths.py`.

*Human document (deliverable B): the evaluation rulebook for `msme-image-select`. It mirrors
`pipeline/GUIDE.md` — what a scored article is, every criterion with its threshold, who set it, what
the current measured score is, and what each residual failure means. Machine form:
`pipeline/imgselect.py::RULEBOOK_IMAGE` and `tools/imgeval.py`. Evidence: `analysis/imageeval/`.*

---

## 1. What "the image decision" is

For one release folder the skill must produce, before the article is built:

```
featured  { file | declared asset, renamed, rung, caption, why }
in_body[] { file, renamed, caption }          (0–6)
captions  { renamed: one factual sentence }
```

The article is **held** — not published — when nothing usable exists; but the hold must come with a
named asset to fetch. A HOLD without a name is a failure, not a safety feature.

## 2. Ground truth — how TARGET is established

`tools/imgtruth.py` fingerprints the image MALAYSIA SME actually published (downloaded from the page)
against every file the release folder holds, and answers *which supplied file that was*. It works on
pixels because TARGET renames everything:

- **same picture**: pixel score ≥ 0.90 · **crop/rescale of it** (WordPress `-scaled`, `-1500x500`):
  0.60–0.90 · **a different asset of the same brand**: ≤ 0.31. The gap between 0.31 and 0.60 is wide,
  so the threshold is not delicate. All three bands were verified by eye:
  `analysis/imageeval/_ambiguous_pairs.png`.
- `.heif` is opened (that is how CAEXPO's featured image was found), `.pdf/.docx` media are mined.
- The **rung of TARGET's own image** is not hand-labelled: the published picture is read by the same
  vision model (`dataset.md`). This caught a real error inherited from the corpus — *Event Me Now* was
  recorded as `logo` but TARGET published a 13-person stage photograph.

Result: **30 articles · 13 featured images traced to a supplied file · 17 to an outside asset** (12
logos, 2 event visuals, 3 photographs). The 17 are why the skill must *declare* assets, not only pick
files.

## 3. The criteria — what, threshold, who set it

Canonical list: `pipeline/imgselect.py::RULEBOOK_IMAGE` (codes) + the scoring table below (rates).
The scorer is `tools/imgeval.py`; it writes `analysis/imageeval/eval_report.md`.

| # | criterion | pass when | threshold / how measured | set by |
|---|---|---|---|---|
| **C1** | `RUNG` | the kind of visual matches TARGET's | rung ∈ people / logo / event-visual / product / none, compared with the pixel-verified rung | measured 30 pairs (D-003) |
| **C2** | `ASSET` | the same picture was chosen, **or** — when TARGET used an outside asset — the same asset identity was declared | same file, or a ≥0.97 near-duplicate of it; otherwise the rename/declaration must carry TARGET's own subject token | measured 30 pairs · T-018 |
| **C3** | `RENAME` | `Subject_Month_Year_MALAYSIA-SME.ext` | regex on the emitted name; **not applicable** when the decision is a declaration (nothing on disk to rename) | site practice |
| **C4** | `INBODY` | 0–6 in-body images, none invented | count only | published practice |
| **C5** | `CAPTION` | one factual sentence per used image, no invented identity, no editorial note | needs `--caption` (API calls); a name is allowed only if the release names it | MSME guideline · MSME question 4 |
| **MATCH** | headline | **C1 and C2 together** | the number to move | — |

`MATCH` is deliberately conjunctive: being right about *what kind* of image while naming the wrong
brand is not a match.

## 4. Current score — two sets, and why the split matters

The skill was tuned on one set and tested on another; mixing them is how a 70 % number gets quoted as if
it were the honest one.

| set | what it is | n | MATCH |
|---|---|---|---|
| **CAL** — calibration | every release the skill had already been tuned against (the original 30 + BMW + the semiconductor PHOTOS release, both of which the scraper had silently been missing) | 32 | **84.4 %** (27/32) |
| **B3** — the fresh batch | the 20 folders the partner delivered from the rebuilt receive stage (T-020) | 20 | **70.0 %** (14/20) |

**The honest out-of-sample number is turn 0, not the last row.** The frozen v4 skill scored **55.0 %** on
B3 before any rule changed (C1 75.0 · C2 70.0 · C3 100 · C4 100; SKILL_RIGHT 7 · SKILL_WRONG 4 ·
RECEIVE_GAP 9). Every later turn was chosen by looking at B3's failures, so 70.0 % is a *fitted* number
and the next delivered batch is the only clean test.

| criterion | CAL (32) | B3 (20) |
|---|---|---|
| C1 RUNG | 96.9 % | 90.0 % |
| C2 ASSET | 87.5 % | 75.0 % |
| C3 RENAME | 100 % | 100 % |
| C4 INBODY | 100 % | 100 % |
| **MATCH (C1 ∧ C2)** | **84.4 %** | **70.0 %** |

Tuning history to 2026-10-23 — every step measured, never assumed:

| turn | change | MATCH (CAL-30) |
|---|---|---|
| 0 | v3 rules run as code (no pixels) | 43.3% |
| 1 | vision tags + story-gated ladder + origin tracking | 50.0% |
| 2 | attach: mine the `.pdf`/`.docx`; header band only for logos | 70.0% |
| 3 | org ranking (folder/file-name evidence, acronyms, generic-word guard) | 73.3% |
| 4 | commentary detected from the pack's labels, not a stray body word | 76.7% |
| 5 | commentary takes the hero portrait; product rung restricted to vehicles/devices | 80.0% |
| 6 | LLM context pass (issuer + story type) | 83.3% |
| 7 | strict product cue + first-signatory + expo naming | 80.0% |
| 8 | **junk gate fixed**: a byte-size gate is unsafe (the smallest published logo is 2,423 B) — degenerate dimensions only, the model calls junk | 76.7% |
| 9 | holding-the-product = people-first; an expo banner is decided by the expo; prefer the logo of the story's organisation | **83.3%** |

Turns 6–7 traded wins for losses: **the rule set had reached its ceiling**. Further gains needed a
different mechanism, not another keyword (see §6).

T-020 round, 2026-10-25 — the live ledger is `analysis\imageeval\tuning_ledger.md`, generated by
`tools\tune_ledger.py`, so this table and that file cannot drift apart:

| turn | change | CAL | B3 | TUNE | HOLD |
|---|---|---|---|---|---|
| 0 | **the frozen v4 skill, first contact with B3** | 78.1 % | **55.0 %** | — | — |
| 1 | a declaration may ask for an event photograph only when the pack holds one; otherwise declare the issuer's logo | 78.1 % | 60.0 % | 70 % | 50 % |
| 2 | the release's own `Long Form (ACRONYM)` becomes the declared subject (rename tokens untouched) | 81.2 % | 60.0 % | 70 % | 50 % |
| 3 | the model's fallback label `news` may not override a specific keyword story type; product-launch cues widened to *coachbuild / prototype / motor car* | 81.2 % | 65.0 % | 70 % | 60 % |
| 4 | a photograph whose *vision subject* names a player in this story scores +3.0 | 84.4 % | 65.0 % | 70 % | 60 % |
| 5 | …the same evidence in the supplied *file name* scores +3.0 too | **84.4 %** | **70.0 %** | **80 %** | **60 %** |

Two turns were **rejected on measurement**, and both are worth remembering:
* pushing the acronym into `ctx["orgs"]` — so it also rewrote the rename token — gave CAL 75.0 / B3 55.0.
  The rename was already carrying TARGET's tokens, so widening the alias broke C2 elsewhere;
* a permissive acronym extractor "found" `MOU`, `MITI` and `AIMS` and declared those as the asset.

Turn 3 also exposed a **silent no-op**: `analysis\imageeval\ctx_cache.json` pins the LLM's story answer per
folder, so a change to `STORY_RULES` did nothing until the *override rule* changed instead. Any future
rule turn on the story type must invalidate that cache first, or it will measure nothing.

## 5. The residuals — what each one actually is

As at 2026-10-25: **11 failures of 52** (CAL 5 · B3 6). The triage is mechanical — `python
tools\imgeval.py --errors` prints `residual_kind` and `picked_sim` per row:

| kind (mechanical label) | CAL | B3 | can a rule fix it? |
|---|---|---|---|
| `published asset not in the pack` | 3 | 5 | **no** — a receive-stage fix, named in `receive_feedback.md` |
| `same scene` / `crop of the same picture` | 2 | 0 | **no** — nothing in the pack separates two press photos of one ceremony |
| `different subject` | 0 | 1 | no verdict needed — see the note below |

The single `different subject` row is the **SEAM cohort**: MSME's own file (`Group Photo of IKEA Thought
Partners … and Biji-biji Initiative Team.jpg`) *was* in the pack and a different group photo of the same event
was chosen; the pixel band scores the two as different subjects (0.31) because they are different frames, so
this is a same-event choice wearing the wrong label. No evidence in the pack separates them.

On the fresh batch **every remaining failure is either upstream or unseparable**. That is the plateau, and it
is a property of the data rather than of the rule set — the same conclusion the 2026-10-23 round reached by a
different route ("turns 6–7 show the variance is ±3 points").

Continuity with the earlier five residuals:

| article | residual | classification |
|---|---|---|
| AFFIN commentary | TARGET published **no** featured image | **not a defect.** A recorded deviation (C-018); the skill correctly declares a logo |
| Sun Life (Legacy Planning) | picked the *agency's* wordmark (`image001.png`, Sandpiper) over declaring the Sun Life logo | **still open** — T-019 |
| MICSEA | declaration subject `Malaysian Industrial…` instead of `MICSEA` | **fixed 2026-10-25, turn 2** |
| TP-Link | picked the *same event*, a different frame, from the .docx | **correct behaviour**, scored fail because it is not the identical file; TARGET's exact frame was not supplied |
| MYHK | two photographs of the same ceremony; picked the landscape, TARGET the portrait | 50/50 coin flip, no rule can separate them |
| Mercedes-AMG | picked the 8-person composite where TARGET used the 2-person car frame | product-hero scoring ties on `people` count |
| BMW Motorrad | picked a handshake; TARGET used a rider on the marque in dust | **fixed 2026-10-25, turn 4** |
| Rolls-Royce Nightingale | offered the wordmark; TARGET used the prototype | **fixed 2026-10-25, turn 3** |
| Lion Parcel | another frame of the same event (ribbon-cutting vs the lion-dance pose) | **fixed 2026-10-25, turn 5** |
| SEAM cohort | another frame of the same event | not separable |

**The model behind the tags is specified in `pipeline/VISION_MODEL.md`** — including the measured
reason a byte-size junk filter is unsafe (this skill had that bug until turn 8) and why no local vision
model is needed.

## 6. How to tune (and what not to repeat)

- Run `python tools/imgeval.py --detail` after **every** rule change. It prints one line per article:
  verdict · story · picked rung vs TARGET rung · the reason. Change one rule, re-run, keep the number.
- Never tune against a criterion you cannot measure. "It looks better" is not a measurement; the score
  or the residual table is.
- **Do not add another keyword to chase one article.** Turns 6–7 show the variance is ±3 points; a
  keyword that fixes MYHK breaks something else with the same words in it.
- The next real step is not a keyword: it is a **brand/event alias table** (MICSEA, MIHAS) plus letting
  the LLM name the *event* as well as the *issuer*. That is T-019.
- New evidence: add the article to `corpus/`, re-run `tools/imgtruth.py`, `tools/imgtag.py`,
  `tools/imgdata.py`, then `tools/imgeval.py`. Four commands, no manual bookkeeping.

## 7. Engine wiring

- `pipeline/vision.py` — the eyes. One call per folder, every answer cached by file sha in
  `analysis/imageeval/vision_cache.json` (a re-run is free and the cache is audit evidence).
- `pipeline/harvest.py` — mines `.pdf`/`.docx` into `Files_from_MSME/_harvest/<slug>/` (a short path on
  purpose: a 100-character release folder plus a file name passes the Windows 260 limit — D-009).
- `pipeline/imgselect.py` — the decision, and `to_draft_block()` renders the `## Images` section.
- `pipeline/llm_step.py` — the draft's Images section is **replaced** by the code's decision, so the
  model writes prose and the skill owns the pictures.
- `pipeline/validate.py` — the existing mechanical checks still run on the rendered section
  (`FEATURED_EXISTS`, `FEATURED_RENAME_TOKEN`, `FEATURED_CAPTION`, `CAPTION_CLEAN`,
  `FEATURED_RUNG_D008`, `IN_BODY_COUNT`) plus `FEATURED_DECLARED_ASSET`.

**Cost of a folder**: 1 vision call + 1 context call + 1 caption call per used image. Cached after the
first run; only new files cost anything.

## 8. Rules that must not slip

- The skill **looks at the pixels**; a filename is never evidence (§0 of the SKILL).
- The **attachment is part of the release** — mine it before declaring an asset missing.
- A **graph is never the featured image** (D-008).
- A **lone spokesperson portrait does not beat the logo** in a statement or survey.
- Every used image gets **one factual caption**; a name appears only if the release supplies it.
- Nothing usable → **declare** the asset with a specific subject; do not publish, do not guess.
