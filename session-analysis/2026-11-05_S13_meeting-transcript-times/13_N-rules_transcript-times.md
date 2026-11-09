# 13 — N-rules: transcript times added to the brief headings

_2026-11-05 (S13) · doc-only change · no code touched._

## 1. What changed

Each `### N-*` heading in `docs/meetings/2026-11-09/MEETING-BRIEF-2026-11.md` now carries its
transcript time range, appended after the title. No quotes and no body text were added.

| Rule | Heading now ends with |
|---|---|
| N-1 logo gallery | `· 01:04–06:27; 56:07` |
| N-2 library update | `· 26:45–28:12` |
| N-3 report + link | `· 15:42–18:42` |
| N-4 government summary | `· 31:19–38:35` |
| N-5 contribute/byline | `· 39:16–46:12` |
| N-6 email link | `· 14:33–15:01; 39:49` |
| N-7 chunk/image rules | `· 57:24–63:31; 77:32–78:26` |
| N-8 agent name | `· 03:19, 23:35` |
| N-9 cost/credit | `· 19:55–23:07` |

✅ nothing to decide — the edit is exactly what was asked.

## 2. Verification

| Check | Result |
|---|---|
| `rg -n "^### N-"` | **9 headings**, lines 59 · 71 · 82 · 93 · 104 · 116 · 125 · 135 · 140 |
| `git diff --numstat` | **9 insertions, 9 deletions** — headings only |
| Body text / quote lines added | **0** |
| Code touched | **0** |

✅ nothing to decide — measured, not assumed.

## 3. The N-1 build question that blocks the 11-Nov call

N-1 is the only rule whose demo needs data we do not have yet: a gallery to search.

**What it means operationally:** on 11 Nov we can show the code path only if `data/gallery/` has at
least one brand that also appears in a test email. With an empty gallery, every run is a miss and the
demo shows only today's ask-email — not the new library-first step.

**Real example:** BPMB sent a logo + building photo (`all_emails/_no_article/BPMB Group Logo and
Building Photographs/`). If a BPMB logo is in the gallery, a later BPMB release reuses it and no ask
email is sent.

**Effect of not deciding:** N-1 can be built and tested on a synthetic fixture, but the 11-Nov call
cannot see a real hit; the rule stays unproven against live data.

**Options:**
- **A (recommended)** — seed `data/gallery/` with 3–5 logos already in `all_emails/` (BPMB and other
  ready brands); replace them with MSME's 10–20 images when Ailee sends the pack.
- **B** — wait for MSME's pack; build N-1 now but demo it on a synthetic fixture only.
- **C** — seed with random placeholder images (Wayne's `[04:43]` suggestion); proves matching mechanics
  but not a real brand hit.

**Recommendation:** **A** — real data proves the full library-first → publish path, and the seed files
are already on disk.

**Blocks:** the N-1 demo on 2026-11-11. Needed before the seed step, not before writing the matcher.

**Register:** `todo/🟢 T-049.md` (N-1 row) · `docs/meetings/2026-11-09/MEETING-BRIEF-2026-11.md:59`.

⭐ Decision — §3: **A / B / C** for the gallery seed.

## 4. What I recommend next

**Start a NEW session** (medium-high thinking effort): the N-1 build needs fresh room for the
matcher, pipeline hook and tests. Reason: this session’s context is already large and mostly
meeting analysis.

Ready-to-paste prompt for that session:

```text
Load the project rules, then build N-1 (logo gallery fallback) exactly as planned.
Read docs/meetings/2026-11-09/MEETING-BRIEF-2026-11.md:59 and
session-analysis/2026-11-05_S13_meeting-transcript-times/13_N-rules_transcript-times.md.
Trigger: only when the email has no usable image anywhere (same condition as the ask-email).
Search data/gallery/index.json for the email's brand (alias/name only, no Pillow), and on a hit
add the gallery logo to the media so readyToFilter=true and no ask email is sent. On a miss,
leave the current reply unchanged. Seed the gallery from 3-5 real logos in all_emails/
(decision A). Add tests for image-present/miss, no-image/hit, no-image/miss. Run compileall and
the full unittest suite, then report with the proving run.
```

| # | Item | State |
|---|---|---|
| 1 | Nine N headings carry transcript times | done |
| 2 | No quotes or body text added | verified |
| 3 | `git diff` = 9 lines changed | verified |
| 4 | Gallery seed choice | open — §3 |
| 5 | N-1 build and tests | next session |
