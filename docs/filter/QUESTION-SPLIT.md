# Question Split — what was added, what was separated, and why

**Date:** 2026-10-12 · **Status:** **APPLIED** (re-applied on request; see §5)

This explains the “split the compound questions” experiment: which **new (extra) questions**
were created, which **existing questions** were separated, and **why**.

---

## 1. Why (the rule we were following)

From *“Writing a good Noul question”*:

> **Ask one thing.** “Is the customer angry **and** asking for a refund?” makes the model
> judge two conditions at once and the number means less. **Ask two Nouls and combine them
> in code.**

A “Noul” question is a yes/no question where a **high value = yes = the defect is present**.
Three of our scored criteria asked **several things at once** (their `true` side was an
“ANY of …” list). Those were the ones we **separated** into single-condition Nouls.

---

## 2. What was separated (3 compound questions → 9 single questions)

### 2.1 `not_sme_relevant` (weight 18) → **5 questions**
Its `true` side was one big “ANY of …” list (consumer/lifestyle **or** single-company news
**or** education PR **or** event previews **or** foreign delegations …). Split into:

| new question | asks (one thing) | weight |
|---|---|---|
| `nsr_consumer` | Is this general consumer or lifestyle content (not about businesses)? | 4 |
| `nsr_single_company` | Is this a single company’s own news (a product launch, rebrand, appointment or award) with no wider business development? | 6 |
| `nsr_event` | Is this a preview or announcement of an event, exhibition or conference? | 3 |
| `nsr_education` | Is this education or edtech promotion (a course, university or training sign-up)? | 2 |
| `nsr_foreign_delegation` | Is this a foreign trade-delegation or mission-visit report with no SME development? | 3 |

(4 + 6 + 3 + 2 + 3 = **18**, same total weight as the original.)

### 2.2 `defamatory` (weight 10) → **2 questions**
Its `true` side was “false, **or** discriminatory, **or** unsubstantiated”.

| new question | asks (one thing) | weight |
|---|---|---|
| `disc_content` | Does the article disparage or discriminate against a person or group? | 5 |
| `unsubst_claims` | Does the article make damaging claims about an identifiable person or company that are not substantiated? | 5 |

(5 + 5 = **10**.)

### 2.3 `political` (weight 6) → **2 questions**
Its `true` side was “(a) party campaign … **or** (b) advocacy that attacks/blames …”.

| new question | asks (one thing) | weight |
|---|---|---|
| `partisan_campaign` | Does the article campaign for or against a party, leader or the government? | 3 |
| `attacks_government` | Does the article attack or blame the government or a leader, rather than report policy factually? | 3 |

(3 + 3 = **6**.)

**Total:** 3 compound questions → **9 single-condition questions**, weights preserved (18 + 10 + 6),
so the overall weighted score (still out of 100) was unchanged.

---

## 2.5 How each question was a problem *before* we split it

All three broke the “**ask one thing**” rule — each was a single Noul whose `true` side was a
bundle of unrelated conditions (“… **OR** … **OR** …”). That caused the same kinds of trouble:

### `not_sme_relevant` (weight 18)
- **Too many conditions in one number.** It asked the model to judge ~8 unrelated things at once
  (consumer/lifestyle **or** single-company news **or** education **or** event previews **or**
  foreign delegations **or** consumer money-advice **or** overseas op-ed …). A high value could be
  triggered by *any* of them, and you could not tell **which**.
- **Blurred meaning.** An article that was, say, both a single-company launch *and* an event preview
  produced one opaque mid number (e.g. `0.5`), instead of two clear answers.
- **One noisy number carried 18 points.** The biggest weight in the whole battery rode on that
  one muddy judgement, so it dominated the weighted score and swung the verdict.
- **Untunable.** You could not turn one trigger up or down (e.g. “event previews matter less than
  consumer content”) without moving all of them together.
- **Overlap / double-counting.** It mixed “topical relevance” with “no wider value” and
  “commercial intent”, which are separate criteria — the same article got scored for the same thing
  in more than one place.
- **Middle-ground problem.** Because it was so broad, answers clustered around the middle instead
  of being decisively low/high, so a threshold was hard to set.

### `defamatory` (weight 10)
- **Three defects in one question:** its `true` side was “**false, OR discriminatory, OR
  unsubstantiated**”. Those are different problems needing different editorial action
  (legal: false claims; editorial sensitivity: discriminatory content; sourcing: unattributed claims).
- **Ambiguous high value.** A high number did not say *why* — false? discriminatory? just
  unattributed? — yet all three looked identical in the score.
- **Couldn’t weight them separately.** One 10-point block meant you couldn’t say false claims matter
  more than missing attribution.
- **Signal overlap.** The “discriminatory” branch overlaps the separate `race`/`religion` gates, so
  the model was partly re-judging content already handled elsewhere.

### `political` (weight 6)
- **Two different behaviours in one question:** “(a) party campaign **OR** (b) advocacy that
  attacks/blames the government”. Active partisanship and mere criticism are not the same thing.
- **Conflated criticism with campaigning.** A factual policy critique (“the Budget is moving too
  slowly”) and an electoral campaign both raised the same number, so the model could not tell the
  editorially-important case (campaigning) from the noise (opinion).
- **Re-introduced the isolated topics.** It explicitly carried a note about **religion, race and the
  royal institution** — which are now their own gates — so it invited the model to reconsider
  content that was supposed to be handled separately.
- **Undifferentiated weight.** One 6-point number couldn’t reflect that partisan campaigning is a
  stronger concern than a critical op-ed.

### Net effect
Each question was **multi-topic**, **middle-ground**, and **carried its whole weight on one blurry
number** — so the score meant less, couldn’t be tuned per trigger, and partly double-counted other
criteria. Splitting gives each defect its **own high=yes Noul and its own weight**; the “OR”
logic then lives in **code** (where it belongs), which is exactly rule 1: *ask one thing, combine
in code.*

---

## 3. The “extra” questions added (the 9 new Nouls)

```text
nsr_consumer            Is this general consumer or lifestyle content (not about businesses)?
nsr_single_company      Is this a single company's own news (a product launch, rebrand,
                        appointment or award) with no wider business development?
nsr_event               Is this a preview or announcement of an event, exhibition or conference?
nsr_education           Is this education or edtech promotion (a course, university or
                        training sign-up)?
nsr_foreign_delegation  Is this a foreign trade-delegation or mission-visit report with no
                        SME development?
disc_content            Does the article disparage or discriminate against a person or group?
unsubst_claims          Does the article make damaging claims about an identifiable person or
                        company that are not substantiated?
partisan_campaign       Does the article campaign for or against a party, leader or the government?
attacks_government      Does the article attack or blame the government or a leader, rather than
                        report policy factually?
```

Each was also given **4–5 candidate wordings** in the Lab
(`<q>`, `<q>_1` … `<q>_4`) to test phrasing (question form / statement form / no criteria /
short criteria / short criteria-with-examples).

---

## 4. Why we did NOT keep it (the result)

We tested all candidates on the 120-item labelled set (100 published positives + 20 editor
“Not relevant” negatives). Splitting made it **worse**, not better:

| configuration | in-sample reject-F1 | 5-fold CV reject-F1 |
|---|---|---|
| pre-split (compound, learned wordings) — **kept** | 0.68 | **0.53** |
| split, separate weighted scores (diluted) | 0.17 | 0.00 |
| split, re-combined in code with `max()` | 0.30 | 0.21 |
| split, `max()` + per-part wording learn | 0.30 | 0.21 |

**Why it failed:** Jev under-fires on short single-condition questions — it needs the
explicit example lists (the “ANY of …” text) to raise the number for off-topic/commercial
items. Splitting also **diluted** the signal: the 18-point weight was spread across five
weak nouls, so no single part moved the decision much, even after re-combining with `max()`.

So the rubric is correct in general, but for **this model/task** the compound criteria
currently answer better (rule 4: “try both ways and keep whichever answers better”).

---

## 5. Current state

- **Live filter = the SPLIT config (re-applied on request):** 3 hard gates + **20** scored
  criteria (weights sum 100). The 3 compound questions (`not_sme_relevant`, `defamatory`,
  `political`) are replaced by the 9 single-condition Nouls above, so all 9 now appear on
  `config.html` and in the Lab (each with wording candidates `_1.._4` + `_jev_best_qu` +
  `_jev_learn`).
- Frozen version: **`9a50a4671fca655e`**. Records/Reports regenerated.
- Accuracy note: this is the lower-scoring configuration (see §4). The pre-split config
  (3 compound criteria) was the better performer; it can be restored from `filter.py`
  history / the earlier frozen sha `76087c1077add97f`.
- Artifacts: `docs/filter/experiments/refactor-matrix.json`, `docs/filter/experiments/refactor-validation.json`,
  `docs/filter/experiments/refactor-maxcombine.json`, and §9 of `docs/filter/LEARNING-RUN.md`.

## 6. One-line summary
We **separated 3 compound questions** (`not_sme_relevant`, `defamatory`, `political`) into
**9 single-condition Nouls** (the extra questions above) to follow “ask one thing”, and
**applied** them on request (accepting the accuracy drop).
