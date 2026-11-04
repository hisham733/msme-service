# Gate/rule improvements added to the runbook

**Session:** 2026-10-29 · S08 · reply 15
**File:** `docs/meeting-2026-10-29/meeting.md` (171 lines)

## 1. What was added

A new **§6 Which rule to improve — and what not to touch**, plus a correction: the **live battery is
3 hard gates + 11 weighted scores**. The old 6-gate test (commercial, not-SME, etc.) is historical,
not the live filter.

| Rule | Weight/type | Improve | Why |
|---|---:|---|---|
| 3R gates | 3 hard gates | **Keep unchanged** | Ant/BWH passed; not the false-accept cause |
| `sme_relevance` | 26 | Rewrite criteria around a Malaysian SME development; add **review floor 0.50** | BWH .45, AI Muda .41, Egon .43; valid accepts above .50 |
| `sme_voice_business_updates` | 7 | Rewrite as **Malaysian SME business update**, not opinion; **do not raise weight yet** | Ant .74 (speech), BWH .45; Kain .26/Tenun .27 are valid but low |
| `geographic_relevance` | 7 | Require a real local development/impact, not one mention | BWH .96, Ant .91 from one example |
| `overall_editorial_test` | 12 | **No hard floor**; use with article type as a review signal | Setia .60, Tenun .64, MPUPK .62 are valid but low |
| `commercial_intent` | 10 | Keep as a score; product launch → review; **no old hard gate** | Event Me Now is on the MSME site |
| `safety_reputation` / `claims_statistics` | 10 / 6 | **No hard gate**; consider lower weight after labels | Historical signal was noise |
| `political_advocacy` | 6 | **No hard gate**; review with MSME | Historical separation −26 (inverted) |
| New: article type + local development | review flag | Add a **review flag** for speech/op-ed/global thought leadership and one-example local stories | Ant/BWH caught; Ant product stays accepted |

**Improve in this order:** article-type/local-development review → `sme_relevance` criteria + 0.50
review → `sme_voice` rewrite → `geographic` criteria → feedback loop/gold set.

**Do not do yet:** hard-floor `overall`; hard-gate safety/claims/political; restore the old hard
commercial/not-SME gates; raise the `sme_voice` weight before labels; change the 3R gates.

✅ nothing to decide.

## 2. Why this is the right direction

- **Ant**: its SME relevance is high (0.86) but it is a global CEO speech; the **article-type
  review** catches it, while the Ant **product** article stays news/product.
- **BWH**: SME relevance 0.45 and overall 0.57; the **0.50 review floor** catches it without
  touching the valid accepts.
- **Event Me Now / Mercedes**: the old 6-gate test rejected them; the current live battery has only
  3R hard gates, so they may now be accepted or reviewed. The runbook corrects this and asks MSME
  for the exact rejected-but-published articles.
- The **gold set + feedback loop** is the only reliable way to set the final thresholds; every
  filter change is versioned.

✅ nothing to decide.

## 3. Unchanged

- **149 tests pass**; no code change in this turn.
- The page-by-page meeting script, the Ant/BWH cases, the asks, the presenter-only notes and the
  localhost fallback remain.
- Gmail OAuth is still expired; use the existing Tenun article.
- `hook.empi.site` is not resolving from this machine; use `http://localhost:8899` in Teams.

✅ nothing to decide.

## 4. What I recommend next

Show §5 (suggested fixes) and §6 (which rule to improve) in this order. Ask MSME to agree with the
direction and give the labels. After the meeting, send me the labels and the exact opposite cases;
I will implement the approved rules as versioned filter-config changes.

## Recap

| Item | State |
|---|---|
| Rule-by-rule section | Added |
| 3R gates | Keep |
| Main improvements | Article type + local development, SME floor 0.50, SME voice rewrite, geography |
| No hard floors | overall / safety / claims / political |
| Old commercial hard gate | Not restored |
| Tests | 149 pass |
| Meeting | Use localhost screen share |
