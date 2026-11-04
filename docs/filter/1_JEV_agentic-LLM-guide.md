# Jev as the fuzzy classifier for AI_News Stage 1 — feasibility answered, pilot designed

**Project:** Malaysia SME / AI_News (MSME × EmpiFlow) · **Date:** 29 Sep 2026 · **Session:** first reply folder for this project (`S01` — rename the folder if you count working days differently).
**Deliverable (the thing to read):** `Malaysia SME/Jev/Agentic LLM using JEV.md`
**Also:** this replies to the research brief in `Malaysia SME/MG_LLM_AInews.md` (`JEV` section + `Deliverable`).

---

## 1. What was done

- Read the updated MSME guideline .docx (extracted from the file itself today — all 17 filters + the 4 outcomes confirmed, same as `analysis/State1_filter.md`), plus the 21 Sep meeting report for agreed scope.
- Read the official TypeSafe/Jev documentation (10 pages, listed in the deliverable §11) — **all Jev facts below are from those docs read today; nothing has been run against the live API yet** (no API key).
- Wrote the deliverable: direct answers to the three questions, the recommended architecture, a draft 17-question battery mapped to the 17 filters, and a step-by-step pilot test with a ready `probe.py` script.

The answer in one breath: **feasible, and it is exactly what Jev is for.** To "how confident is this article SME-Relevant (0–100)": you ask a **Noul** question ("Is this article SME-relevant…?") and Jev returns `noul` = probability 0.0–1.0 → ×100. Confidence is an *output* property (0–1) for Choice/Score answers, not a question you ask. Jev is a **stateless HTTP API** (`POST api.typesafe.ai/v1/systemone`) + Python/JS SDKs — not a chatbot and not an agent brain. Its "knowledge" of SME Relevance lives entirely in what we send: the article as `state`, the definition written into `instructions`, and the boundary cases in `criteria`. To let an LLM call it, we wrap it as a function tool (`ask_jev`) executed by our harness — but the recommended shape for Stage 1 is **not** an LLM loop: code calls Jev once per article with all ~17 questions, and code applies the thresholds to produce ACCEPT / HOLD / EDITOR REVIEW / REJECT + reason code (the guidelines' own outcomes). LLM stays for what only it can do: turning email/WhatsApp/links into clean text.

✅ nothing to decide — findings only.

---

## 2. ⭐ D-1 — Stage-1 architecture: adopt the hybrid (Jev as judgment layer)?

**What it means operationally.** For each incoming submission: LLM extracts clean text/fields → deterministic code checks run first (image count, dates, country, regex, WordPress index) → **one Jev request per article** with the battery (SME relevance, commercial intent, safety flags, etc.) → code routes on the returned `noul`/`confidence` with thresholds → **ACCEPT** to repurpose, **HOLD** (missing materials), **EDITOR REVIEW** (low confidence, safety, political), **REJECT** with reason code.

**A real example.** A bank's loan-programme PR: `sme_relevance` = 0.91, `commercial_intent` = 0.72 → above auto-reject? No — the doc's own rule: mid-band → **EDITOR REVIEW – COMMERCIAL_CONTENT**, the "hard case" from the 21 Sep meeting, now routed with numbers instead of a coin toss. A B2C discount blast: `sme_relevance` = 0.08 → **REJECT – NO_SME_RELEVANCE**.

**Measured effect.** Jev pricing $0.042 per 1M input tokens → ≈ US$0.45/month at 100 articles/day (deliverable §8.7). Latency per article to be measured in the pilot. One call per article, not 17 — the docs benchmark 12.2× cheaper / 10.0× faster than per-question calls.

**Effect of NOT deciding.** Stage 1 stays "rules only", which `State1_filter.md` already showed cannot cover the filters that matter most (#2 SME Relevance, #4 commercial intent, #6 substance, #12 significance, #14 safety) — those stay 100% manual.

**Options.** A) Hybrid pipeline — Jev called by code (recommended). B) Full agent loop — an LLM orchestrator calls the `ask_jev` tool per judgment (more moving parts, slower, nondeterministic; keep only if MSME wants an interactive reviewer console). C) Skip Jev; keep rules-only.

**Recommendation:** **A · D-1 = A** — and prove it on the pilot before wiring the engine.

**Blocking?** Blocks the Stage-1 engine build (not the pilot). Needed before the next MSME meeting (EF-9: ~1–1.5 weeks from 21 Sep) so EF returns with measured filter behaviour, not theory.
Reference only: `Malaysia SME/Jev/Agentic LLM using JEV.md` §5–§6.

⭐ Decision — §2

---

## 3. ⭐ D-2 — Run the pilot now? (I need two things from you)

**What it means.** Before touching the Stage-1 engine, run the deliverable's §7 test: Playground smoke test (10 min), then `probe.py` over 10 published articles (positive set — the crawler from **EF-7**, the "train on the published website" idea) + ~10 hard negatives from the inbox MSME forwards (**EF-2**). Output: a separation table (does `sme_relevance` split positives from negatives?) + the thresholds + a stability check. This is also the first proof for Wayne's daily-report review (**EF-6**).

**What I need:** 1) a **Typesafe API key** (`https://console.typesafe.ai/keys`) — without it nothing can run; 2) **negatives**: as soon as MSME starts CC-ing `ainews.msme@gmail.com`, 10+ obvious-reject emails; until then I can construct temporary negatives, clearly labelled.

**Effect of NOT deciding / not providing the key.** The deliverable stays theory; the "prove it" slide for the next MSME meeting doesn't exist.

**Options.** A) Go now — I build the pilot folder + crawler sample + `probe.py`, run 4 samples, then the full pilot, and report numbers (recommended). B) Later — when negatives accumulate; D-1 stays pending until then.

**Recommendation:** **D-2 = A**, even with constructed negatives first.

**Role note:** this is also the gateway for Ailee/Wayne's calibration input — the deliverable (§6 battery wording + §7.6 acceptance criteria) is written to be REVIEWED by MSME, not just run.

⭐ Decision — §3

---

## 4. Parked this turn (per the parking rule)

- **Duplication filter (#9)** needs the WordPress index — that is **EF-11** and stays parked until we get site access; Jev can only judge candidate pairs later.
- **Malay-only submissions** — Jev is English-first by the docs; untested, route to human until measured.
- **Adversarial PRs** ("this is highly relevant…") can nudge Jev's reading — mitigation written in the deliverable §9; add 2–3 such samples to the pilot.

✅ nothing to decide — parked items have owners/triggers.

---

## 5. Recap

| # | Item | Status |
|---|------|--------|
| 1 | Jev feasibility + how-to (API, tool exposure, context, confidence) | Answered; deliverable written: `Jev/Agentic LLM using JEV.md` |
| 2 | 17-filter → Jev battery + provisional routing | Drafted in deliverable §6 |
| 3 | Pilot test guide + `probe.py` | Ready in deliverable §7–§8 |
| 4 | Architecture choice | ⭐ awaiting D-1 |
| 5 | API key + negatives | ⭐ awaiting D-2 |

---

## 6. What I recommend next

1. **Answer D-1 = A · D-2 = A (+ API key)**, then **carry on in this session** to build the pilot folder, fetch the 10 positive samples, wire `probe.py`, and run the 4-sample smoke (medium thinking effort — mechanical build + first read of the numbers).
2. If the key comes later and you'd rather start fresh: **new session**, paste: *"Read `Malaysia SME/Jev/Agentic LLM using JEV.md` and `Malaysia SME/session_analysis/2026-09-29_S01_jev-tool-research/1_JEV_agentic-LLM-guide.md`. Build the Jev pilot per deliverable §7 and §8.5: crawl 10 positive articles from malaysiasme.com.my/category/feature/, use 10 negatives per D-2, run `probe.py --dry` then the full pilot, and report the separation table + proposed thresholds. Install the TypeSafe agent skill first."* Thinking effort: medium (script + measurement; high only if question wording needs rework).
3. **Send Ailee/Wayne deliverable §6 + §7.6** for review — their sign-off on the battery wording and acceptance criteria is what makes this "modelled after MSME", not after one person (Wayne's point, 21 Sep).

No `/compact` needed for option 1 — this session still has room; compact only if you want the pilot build in a clean context.
