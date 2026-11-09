# CHANGELOG — msme-repurpose

Every edit to `SKILL.md` gets a row here (MG, 2026-10-23): date · what changed · why (the measured
evidence). The engine stamps this skill's hash into each `run.json`, so a draft can always be traced
to the version that wrote it.

## 2026-10-25 — rule 2 (branch selection) tightened, and a false branch signal named

- **What:** rule 2's *Commentary* class now requires the release to **describe itself as opinion**
  (`opinion` · `commentary` · `column` · `viewpoint` · `perspective` · `for your reader`) on top of being
  a statement/response on a policy or decision. The *Signed opinion / byline* bullet now says that
  `By <name>` is a layout signal and must never select the branch on its own.
- **Why (measured, T-020 / G2):** the branch is the decision that sets the whole treatment, and nothing
  measured it — `validate.py` only checks that a branch was *recorded*. New tool
  `tools\repurpose_eval.py` implements D-007's 5-gram metric, and had to compute it in **both**
  directions: raw-contains-in-published (trimming) and published-lifted-from-raw (lifting). The second
  reproduces the hand-recorded `reuse_pct` of all five near-verbatim pairs within ~1 point
  (98.1 · 98.2 · 97.1 · 95.6 · 98.6 vs 95 · 98 · 97 · 96 · 98) — that is what validates the tool.
  - 8 corpus releases are policy statements; only **5** were republished near-verbatim. The other three
    came back at 12 %, 28 % and 41 % body reuse, so "it is a statement on a policy" over-selects.
  - `By <name>` appears in **20 of 22** house-style releases: it cannot discriminate.
  - On the 20 fresh releases the tightened rule fires **2/20** while the publisher rewrote all 20 —
    better, not exact, and recorded so nobody claims a perfect branch rule.
- **Evidence:** `analysis\repurpose\grades\SUMMARY.md` · `analysis\imageeval\receive_feedback.md`.

## 2026-10-23 — rules 6 and 7 added

- **What:** rule 6 (categories reuse the site's vocabulary; short slugs only) and rule 7 (every
  section says something new — no repeated paragraph/heading).
- **Why (measured):** the first live DeepSeek runs (`deepseek-flash`, V4.1-Flash-1017) on N-01/N-02:
  - the model invented categories `aftersales-and-warranty`, `vehicle-financing`, `motorcycling`
    where the cold-run drafts used the site's words (Automotive · Motorcycles · Finance) — evidence
    in the BMW release folder's `draft.prev.md` + `run.json`;
  - the N-01 live draft repeated the *A New Chapter for Selangor's Engineers* section text
    **3 times** in the draft (5 occurrences in the render) — evidence:
    `Files_from_MSME\Email_Articles\PHOTOS - …\draft.md`, captured in reply
    `session_analysis\2026-10-23_S07_engine-use-guide\2_…`;
  - the engine now also rejects repeated content (`REPEATED_PARAGRAPH` / `DUPLICATE_SUBHEADER`
    checks) and fails on untraced numbers — the rules exist so a compliant draft costs zero retries.

## 2026-10-22 — description quoted (strict YAML)

- **What:** `description:` wrapped as a quoted scalar. **Why:** `workflow_lint.py` failed 2/2
  unquoted (a strict harness silently drops such skills); after the fix 2/2 PASS — same F1 class as
  the `project-workflow-setup` v1.1.0 fix. No rule content changed.
