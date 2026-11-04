# Follow-up — Jev vs just prompting an LLM with the same fuzzy question

**Project:** Malaysia SME / AI_News · **Date:** 29 Sep 2026 · **Replies to:** MG's quick question (`JEV` message 2 of the day).

---

## 1. Answer

You *can* send the identical question (state + instructions + criteria) to an LLM. For a gating decision, the differences are:

| Axis | Jev | LLM (GPT/Claude-class) |
|---|---|---|
| **Cost** | ~$0.00015/article; input $0.042 per 1M tokens, output free | Output/reasoning tokens are billed; 17 structured answers/article typically costs tens of times more, plus parsing/retry overhead |
| **Speed** | Snap judgment; all questions in one call, in parallel | Must generate/reason before answering — seconds to tens of seconds; slower at batch scale |
| **Accuracy** | Calibrated probability (0–100 *means* something), per the docs; not yet measured on our filters | Can be strong on world knowledge/multi-hop reasoning, but its self-reported "confidence 93%" is **not** a real probability — known to be overconfident |
| **Shape** | Fixed options/criteria; no prose to parse; cannot drift | Can ramble, ignore the schema, refuse; needs validation + retries |
| **Consistency** | Very stable across runs (docs) | Varies run-to-run and when the model is updated |

**Bottom line:** an LLM gives a reasoned but uncalibrated opinion in prose; Jev gives a calibrated, parseable number built for routing — at a fraction of cost and time. Accuracy on *our* 17 filters is settled only by measurement, so the pilot can A/B the LLM baseline on the same samples.

✅ nothing to decide — explanation only; D-1/D-2 (previous reply §2–§3) are unchanged.

---

## 2. What I recommend next

- If you want the **LLM baseline** added to the pilot (same samples, one LLM prompt per article, compare separation numbers side-by-side), just say so — I'll build it into `probe.py` when the pilot runs. Otherwise we run Jev-only first.
- Otherwise: same as reply §6 — **D-1 = A · D-2 = A + API key**, and I carry on here.
