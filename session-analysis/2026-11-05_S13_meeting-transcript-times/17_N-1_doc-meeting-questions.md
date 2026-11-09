# 17 — N-1 spec written; MSME questions added to the next-meeting file

_2026-11-05 (S13) · docs only · no code touched._

## 1. What changed

| File | Change |
|---|---|
| `docs/new-rules/N-1-logo-gallery.md` (new, 237 lines) | the N-1 spec: rule, trigger, matching criteria, other methods, recommended hybrid, gallery index, website evidence, test plan, code touchpoints |
| `docs/meetings/2026-10-30/NEXT_MEETING.md:67` | `[HS 2026-11-05]` issue with the **four MSME questions** (matching, naming, library shape, access/copy) |
| `docs/INDEX.md:15,61` | new `new-rules/` folder row + its file table |

The four questions, as they now read in `NEXT_MEETING.md` §2:

1. How do you match a logo to an article on your side — brand tag, event name, date, sender, other? Who matches?
2. What naming convention do you use for gallery files (brand + month + year + `MALAYSIA-SME`; date only for logos)?
3. What does the library look like — structure, tags/fields, file types, how many images, logos and photos together?
4. Can we take a copy (zip export) or get access (read-only API / WordPress)? How often refreshed?

✅ nothing to decide — the doc and questions are exactly what was asked.

## 2. Verification

| Check | Result |
|---|---|
| New folder + spec | `docs/new-rules/N-1-logo-gallery.md` — 237 lines |
| Questions in the meeting file | 4 numbered items at `NEXT_MEETING.md:67-78` |
| `docs/INDEX.md` links | folder row line 15, file row line 65 |
| Code changed | **0** — `git status` shows docs only (plus the earlier transcript-time edit) |
| Compile/tests | not run — no `.py` touched |

✅ nothing to decide — measured.

## 3. The match rule to choose (blocks the N-1 build)

The spec records both of your proposals and a third. The choice changes **which emails the gallery can rescue**.

**What it means operationally:** the matcher decides whether a no-image email gets a gallery logo or goes to the sender ask-email.

**Real example:** a Meltwater-style release sent through Cision/Media OutReach. The subject names the brand; the sender domain is the agency.

- **A (weights 35/35/20/10, threshold 70):** only subject + sender reaches 70 → this email scores 45 → **miss**, even though the subject is exact. Agency-sent releases are locked out.
- **B (priority ladder):** subject exact → **hit**, even when the sender is an agency.
- **C (recommended: priority ladder + domain map + ambiguity guard):** subject exact → **hit**; `bpmb.com.my → BPMB` gives BPMB a direct hit; two competing brands → **miss**.

**Effect of not deciding:** N-1 cannot be coded past the matcher, so the 11-Nov call gets the spec but no working library-first demo.

**Decision needed:** by **2026-11-08**, to leave time for build + tests before the 11-Nov call.

**Register:** `docs/new-rules/N-1-logo-gallery.md` §4–§6 · `todo/🟢 T-049.md` (N-1 row).

⭐ Decision — §3: **A / B / C**, and may each gallery entry carry a `domains` list? (C needs it.)

## 4. What I recommend next

**Start a NEW session** (medium thinking effort): the decision above plus the build is a clean unit, and this session’s context is long. Reason: the spec is finished, so the next session can go straight to code.

Ready-to-paste prompt:

```text
Load the project rules. Read docs/new-rules/N-1-logo-gallery.md and build N-1 using decision C
(priority ladder + domain map + ambiguity guard) and seed A (3-5 real logos from all_emails/).
Trigger only when the email has no usable image anywhere, i.e.
not (has_pic or has_logo or doc_logo or doc_photo), which is the same condition as the ask email.
Add msme/receive/gallery.py, the gallery stage in pipeline.py before verify, data/gallery/index.json,
config/paths entries, tools/gallery_admin.py, tests/test_gallery.py, and the doc update.
On a hit set hasLogo=true, archive the gallery logo, send no ask email; on a miss leave today's reply
unchanged. Run compileall and the full unittest suite, then report with the proving run.
```

| # | Item | State |
|---|---|---|
| 1 | `docs/new-rules/` + N-1 spec | done |
| 2 | Four MSME questions in `NEXT_MEETING.md` | done |
| 3 | `docs/INDEX.md` updated | done |
| 4 | Match scheme A/B/C + `domains` | **open — §3** |
| 5 | N-1 code + tests | next session |
| 6 | Gallery seed source (A/B/C) | open — spec §10 |
