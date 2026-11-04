# Meeting decisions — next MSME call (week of 2026-11-09)

_One page: what MSME must decide, what the system does today, and what changes per answer._
_Built 2026-10-31 from the 21-Sep transcript, the 30-Oct `NEXT_MEETING.md`, the partner
`meeting_notes/AGENDA.md` and the `2026-10-30_MSME_guideline-review.md` brief._

## 0. Sources and one warning

| Source | Date | What it gives |
|---|---|---|
| `MSTeam_transcript_2026_Sept_21.md` (in the zip) | 2026-09-21 | the kickoff principles: 3R, score-then-decide, train on the published site, courtesy reply, start simple |
| `NEXT_MEETING.md` (in the zip) | after 2026-10-30 | the current open list: `AG-09`, `AG-12`…`AG-14`, `AG-16` |
| `AGENDA.md` (partner repo) | 2026-10-24…25 | `AG-01`…`AG-11` rows |
| `2026-10-30_MSME_guideline-review.md` | 2026-10-30 | the measured image/filter/receive brief (decisions 1–13) |

**Warning:** the transcript predates the build — most of what it proposed is now implemented.
`NEXT_MEETING.md` says the 30-Oct call answered `AG-01`…`AG-08` and `AG-15` as `D-024`…`D-029`,
but those answer files are **not in the zip or the repo copy** (the partner repo stops at `D-023`).
Until they arrive, the image/caption/naming items below are marked "answered — detail pending".

## 1. Already settled — do not re-ask

| Topic | Live today |
|---|---|
| 3 hard gates: royalty, religion, race (the 3R) | `royal_respect`, `religious_respect`, `racial_respect` |
| Score each question, then accept/reject | 11 weighted scores + editable threshold |
| Record **why** rejected | reasons in `filter_results`; editor + filter history |
| Links/media kits are valid article sources | Drive, OneDrive, Box, Google Doc, public web (`D6`, `D15`, `D20`, `D23`, `D24`) |
| Extract media embedded in PDF/DOCX | header logos/photos, up to 10 images (`D8`, `D24`) |
| One pipeline on one port | `run.py` → `msme.combined:app` (`D32`) |
| Repurpose on the external engine | `MSME_AI_News` on :8765 (`D35`) |
| "Start simple, upscale the employee" | the link-fetching stage **is** the upscale; needs Wayne's confirmation (`M-1`) |

## 2. Open decisions — MSME (Wayne / Ailee)

| id | Decision (one line) | Today (verified) | What changes per option | Owner | Recommendation | Blocks |
|---|---|---|---|---|---|---|
| **AG-16** | Input channel: email only, or email **and WhatsApp**? Which wins on a duplicate? | Gmail only (poll + webhook) | WhatsApp adapter + identity mapping + duplicate rule; email-only = no change | MSME | **email only** for phase 1 | intake scope |
| **AG-14** | May one release carry **two statuses** (KPMG: REJECT + ACCEPT)? | Version grouping by subject only; no cross-source dedupe; `docs/published-index.json` (100 articles) is unused for dedupe | one current status + history; duplicate check vs the published index (title/body similarity) | MSME | **one current status**, history kept; duplicate = same title/body | filter status, dedupe |
| **AG-12** | What does archive `Original status` record — the guideline's **4 outcomes** or the report's **2**? | internal ACCEPT / EDITOR REVIEW / REJECT + ready/not-ready + ERROR | publish a mapping table (no DB change) or align the vocabulary | MSME | **keep internal, publish mapping** | reports, accuracy claims |
| **AG-13** | Why is **every rejection dated on/before 14 Oct**? | data-provenance question; no code cause | no code change until answered; then re-import/scope evidence | MSME | answer before any accuracy claim | filter evidence |
| **AG-09** | Does Receive extract embedded media from PDF/DOCX? | **Yes, already live** (`D8`, `D24`; 10 images/doc, header logos) | none — the answer is "yes, live"; give the date | EF → MSME | close it with the evidence | receive acceptance |
| **M-1** | Attachment-only vs link fetching (Wayne: "if no attachment, reply asking for one; don't click links") | link fetching is built; **5 of the 7 real examples depend on it** (MATRADE, APAC, JomLokal, BigSeller, Atlas) | reverting disables four fetchers and loses those routes; keeping confirms with Wayne | MSME | **keep link fetching**; the reply covers failures | receive scope |
| **M-2** | Courtesy auto-reply: who receives it, and when? | auto-sent for every `readyToFilter=false`, but to the **fixed test address** (`fhwvdu@gmail.com`); AI-written, threaded | `REPLY_MODE=sender`, approve wording, exclude no-reply addresses, one reply per thread | MSME | approve wording, then **sender mode** | go-live |
| **M-3** | Daily report: email or WhatsApp, to whom, what time, what content? | **not built**; dashboard + weekly report doc only | scheduler job + digest (received, accept %, reasons, failures) | MSME | **daily email** at a fixed time | none |
| **M-4** | Publish: **zero human** (Ailee/Wayne) or an approval step? | **not built**; publish button disabled; no WordPress upload | WP REST uploader + auto-publish **or** approval gate + takedown path for 3R errors | MSME | **configurable gate**: approval for the first N, then zero-touch | stage-3 go-live |
| **M-5** | Historical data vs "start from today" (Wayne) | 241 rows incl. history; archive ≈2.7 GB | evidence scope only: keep history for regression, use post-cutoff rows for accuracy claims | MSME | **history for tests, post-cutoff for evidence** | accuracy claims |
| **M-6** | Sample CC: should CC'd mail be processed as intake or only as ground truth? | no CC rule | a label/filter, or a separate ground-truth store | MSME | **ground truth only** (do not re-process) | evaluation set |

## 3. Technical decisions / fixes — EF

| id | Decision | Today (verified) | Change |
|---|---|---|---|
| **B-1** | ACCEPT threshold **60 or 62**? | our default is **60** (`D33`); the partner's `D-014`/`D-019` say **62** (measured: 4 false accepts disappear, agreement unchanged) | align the live default to 62 and record it |
| **B-2** | Is `political_advocacy` **inverted**? | the partner measured an inversion; our battery scores it positively (high = good) | verify with a known political article; fix wording/scoring if inverted |
| **B-3** | Add the missing filter questions | no dedicated **Events/Awards/Appointments** question (the partner's largest false-accept source); no dedicated sponsored/advertorial or duplication | add `events_awards` first; `sponsored_advertorial` next; duplication waits on `AG-14` |
| **B-4** | A failed evaluation must never read as REJECT | pipeline records **ERROR**; manual filter endpoints return ERROR (verified) | add a regression test; keep failures out of accept/reject counts |
| **B-5** | Use the published website as the gold set | 100 crawled articles with body text in `docs/published-*.json`, used only by the Drive tool | a read-only refresh + accuracy report; no training loop yet |
| **B-6** | SEO image naming | archive keeps original names (`DSC1456.jpg`) | rename at draft/upload to `Subject_Month_Year_MALAYSIA-SME` (needs the `AG-05` answer) |

## 4. Recommended meeting order

1. **AG-09** (answer: already built) + **M-1** (keep link fetching) — receive scope.
2. **M-2** (reply go-live) + **B-1** (threshold 62) — two one-line answers that change live behaviour.
3. **AG-14 / AG-12 / AG-13** — needed before any filter accuracy claim.
4. **M-4** (publish gate) — the last big scope decision.
5. **AG-16** (channel) + **M-3** (daily report) — next phase.

## 5. Where each change lands

| Decision | Repo / owner | Concrete change |
|---|---|---|
| `B-1` | msme-service | `msme/config.py` `ACCEPT_THRESHOLD` default + settings |
| `B-2`, `B-3` | msme-service | `msme/filtering/filter.py` battery (`GATES`/`SCORES`) |
| `B-4` | msme-service | regression test in `tests/` |
| `M-2` | msme-service | `REPLY_MODE=sender`, reply wording |
| `M-3` | msme-service | scheduler + digest job |
| `M-4` | msme-service + `MSME_AI_News` | WordPress uploader / approval gate |
| `AG-14`, `B-5` | msme-service | dedupe vs `docs/published-index.json` |
| `B-6` | msme-service + engine | image rename at draft/upload |
| `AG-01`…`AG-08`, `AG-15` | `MSME_AI_News` | image skill, captions, naming (answers `D-024`…`D-029`) |
| `AG-16`, `M-1`, `M-3`, `M-5`, `M-6` | MSME ruling | no code until answered |

## 6. Answer sheet (copy-paste for the call)

```text
AG-16 = email only
AG-14 = one current status, history kept
AG-12 = keep internal, publish mapping
AG-13 = <answer>
AG-09 = already built (D8/D24) — confirm
M-1  = keep link fetching
M-2  = sender mode, wording approved
M-3  = daily email, <time>, <recipients>
M-4  = approval for first N, then zero-touch
M-5  = history for tests, post-cutoff for evidence
M-6  = ground truth only
B-1  = 62
B-2  = <verify/fix>
B-3  = add events/awards
B-4  = test
B-5  = build eval
B-6  = rename at upload
```

## 7. Evidence

- `docs/workflow/MEDIA-SOURCE-DECISION.md` — who picks the source/fetcher, with the seven real emails.
- `docs/workflow/RECEIVE-STAGES-EXPLAINED.md` — the eleven receive stages, compared across the seven emails.
- `docs/workflow/RECEIVE-WORKFLOW-7-EMAIL-EXAMPLES.md` — the full walkthroughs.
- `INDEX.md` — every `.py` file, purpose and delete impact.
- Partner: `meeting_notes/AGENDA.md`, `2026-10-30_MSME_guideline-review.md`.

## 8. Open data request

Send the **`D-024`…`D-029`** answer files (or the updated `AGENDA.md`). They close `AG-01`…`AG-08`
and `AG-15`; without them the image, caption, naming and AI-image decisions look open when MSME has
already answered them.
