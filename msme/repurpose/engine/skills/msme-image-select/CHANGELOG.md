# CHANGELOG — msme-image-select

Every edit to `SKILL.md` gets a row here (MG, 2026-10-23): date · what changed · why (the measured
evidence). The engine stamps this skill's hash into each `run.json`, so an image decision can always
be traced to the version that made it.

## 2026-10-23 — v4: the skill reads pixels, and the ladder is gated by story type

Rewritten against **30 published pairs whose featured image was traced back to the released files by
pixel matching** (`analysis/imageeval/`, `pipeline/IMAGE_GUIDE.md`). Measured effect: TARGET-match
**43.3% → 80.0%** (C1 rung 90%, C2 asset 83.3%, C3 rename 100%, C4 in-body 100%).

- **New §0 — you must LOOK at the pictures.** Gathering was extended to the supplied `.pdf`/`.docx`
  (`pipeline/harvest.py`), and every candidate is now read by a vision model (`pipeline/vision.py`).
  **Why (measured):** of the 17 articles whose published featured image matched no loose file, **10 had
  that picture — or the same logo artwork — inside the attachment**: the ACCCIM, SME Malaysia, MICSEA,
  PIKOM, Sun Life and Securities Commission logos are crops of the supplied PDF header, and TP-Link's
  MoU photograph is `word/media/image2.png`. The v3 wording ("the skill never sees pixels") was the
  direct cause of the 2026-10-23 live failure where the people rung was claimed for `1.jpg`.
- **The ladder is now gated by story type** instead of being a flat people→logo→event→product chain.
  New order: product hero (manufactured goods) · event scene · author portrait · event poster · brand
  logo · declared asset. **Why (measured):** a supplied spokesperson portrait loses to the logo in a
  statement or survey (MICSEA, Sun Life/Legacy Planning) but wins in a commentary or appointment (IKEA,
  Boehringer, MDEC); food/drink launches are people-first (Tealive, Wagyu) while only vehicles/devices
  produced a product-hero featured image.
- **A HOLD must name its asset.** New §3 `asset {kind, subject, fetch}`. **Why:** 17 of 30 published
  featured images were outside the folder; the skill's job in that case is to say *which* asset to
  fetch, not to stop silently (T-018).
- **Captions: describe the frame.** §5 now says to caption what the image actually shows (because §0
  makes that knowable) and to name a person only when the release names them.
- **Rename**: the token order `<Subject>_<Month>_<Year>` is stated as the one to emit; the corpus shows
  the site's month casing varies, and 100% of the 22 file-based decisions are expressible in this form.
- Unchanged: D-008 (a graph is never the key visual), supplied-material-only, `-2`/`-3` suffixes,
  0–6 in-body.

## 2026-10-23 — rule 1: people rung ordered by story type

- **What:** the people rung now splits by story type — event story → group photograph of the event;
  person-centred non-event story → supplied single-person portrait. Defines "verified identity" as
  supplied caption/credit/filename-metadata/event description (the skill never sees pixels, so pixel
  matching is not a method); unverifiable → drop a rung + `[FLAG]`.
- **Why (measured):** MG's instruction 2026-10-23 (reply 3 of S07) after the strict wording made
  N-01's ceremony photo fall to *event-visual* while the cold-run draft (and the published article)
  used the group frame as **people**. The live BMW run showed the other side: no verifiable person →
  product hero with a flag. Both behaviours are now rule-driven instead of judgement calls.
- **Superseded in v4:** "the skill never sees pixels" is no longer true — see v4 §0.

## 2026-10-23 — rule 1: a filename is not identity evidence

- **What:** rule 1 gains the explicit sentence that a camera-numbered file, a model series name or a
  guessed scene never earns the people rung; unverifiable identity falls to a lower rung with a
  `[FLAG]`.
- **Why (measured):** in the first live DeepSeek run on N-02 (BMW), one attempt claimed
  **people** for `1.jpg` — a camera-numbered photo whose content cannot be verified from the release
  — while the pre-registered cold-run draft explicitly refused it. Evidence: the BMW release
  folder's `draft.prev.md` (rung: people) and
  `session_analysis\2026-10-23_S07_engine-use-guide\1_T-010_T-011_T-014_run-guide.md` §3.
- **Related:** D-008 (a graph image is never the key visual) — unchanged, still enforced by the
  engine's validator.

## 2026-10-22 — description quoted (strict YAML)

- **What:** `description:` wrapped as a quoted scalar. **Why:** `workflow_lint.py` failed 2/2
  unquoted; after the fix 2/2 PASS. No rule content changed.
