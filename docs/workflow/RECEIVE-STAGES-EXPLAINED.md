# The receive stage, point by point — and how seven emails differ at each point

_Stage-first companion to `RECEIVE-WORKFLOW-7-EMAIL-EXAMPLES.md` (email-first) and
`MEDIA-SOURCE-DECISION.md` (who picks the source)._

Every email runs the **same eleven stages**. Nothing is configured per email. What changes is the
**shape of the email** — what is attached, what is linked, what is in the body — and each stage reacts
to that shape. This page shows each stage once, then the same stage across the seven archived emails,
so you can see exactly **which step produces which different result**.

## The eleven stages at a glance

| # | Stage | What it does | Code | Output |
|---:|---|---|---|---|
| 1 | **Gmail** | picks an unread inbox message | `receive/gmail.py` | the message id |
| 2 | **Normalize** | reads subject/from/date/body, attachments, links; resolves tracking | `receive/normalize.py` | the email model |
| 3 | **Decide** (AI) | suggests the release attachment and any media-kit link | `receive/decide.py` | `chosenFileName`, `linkToFetch`, confidence |
| 4 | **Fetch** | downloads attachments + Drive/OneDrive/Box/web + body images | `receive/pipeline.py`, the four fetchers | source texts + media |
| 5 | **Collect + select** | puts every fetched text in a pool and ranks it | `pipeline.py` (`_rank_candidates`) | one chosen candidate |
| 6 | **Extract** (AI) | returns the article verbatim + evidence | `receive/extract.py` | `bodyText`, source, confidence |
| 7 | **Logo scan** | finds logos/photos inside the document | `receive/extract.py`, `pipeline.py` | `docLogo`, `docPhoto` |
| 8 | **Verify** (AI) | headline, subject match, media flags, ready | `receive/verify.py` | the 14 flags |
| 9 | **Checklist** | saves the row to SQLite | `receive/checklist.py` | row id |
| 10 | **Archive** | writes `article.md`, `images/`, `originals/` | `receive/archive.py` | folder |
| 11 | **Filter** | Jev runs only when `readyToFilter=true` | `filtering/filter.py` | verdict |

---

## 1. Gmail — pick the message

**What it does:** takes the next unread message matching `in:inbox is:unread -category:promotions`
(push webhook or the 5-minute poll).

**Across the seven:** identical. All seven are unread forwarded emails from
`Editor MSME <editor@malaysiasme.com.my>`. This stage never explains a difference in the results.

**What it teaches:** the pipeline does not pre-sort by sender or subject; every forwarded email is
processed the same way.

## 2. Normalize — read the envelope

**What it does:** parses subject, From, date, body, HTML, attachments (name/type/size), every link,
and inline body-image URLs; resolves short/tracking links (bit.ly, mjt.lu, sendgrid.net).

| Email | What normalize saw | Why it differs |
|---|---|---|
| Kain | 3 attachments, 1 body image, 2 non-article links | release is attached |
| MATRADE | 1 logo attachment, 1 Drive folder link | release is in the cloud |
| APAC | 4 inline images, 1 OneDrive link, 1 web page | three possible sources |
| JomLokal | 6 attachments, 1 Box link | multi-language + duplicate kit |
| BigSeller | 0 attachments, vritimes URL, SendGrid tracking, 1 body image | web-only |
| Sanct | 0 attachments, full release in body, tracking link, 4 inline images | body-only |
| Atlas | 0 attachments, Google Docs link, two 32×32 icons | document link, no media |

**What it teaches:** **this is where the difference is created.** Every later stage only reacts to
what normalize recorded.

## 3. Decide — choose the source (AI)

**What it does:** one text-only AI call reads the email + attachment **names** + links and suggests the
release and any media-kit link. It never opens a file.

| Email | Decide suggested | Confidence |
|---|---|---|
| Kain | the PDF attachment; no link | — |
| MATRADE | the Drive folder link | 0.78 |
| APAC | the OneDrive folder | 0.85–0.90 |
| JomLokal | the English DOCX; Box as supporting | — |
| BigSeller | the vritimes page; tracking ignored | — |
| Sanct | the body is the article; tracking is not a kit | — |
| Atlas | the Google Docs link | 0.45–0.62 |

**What it teaches:** the suggestion changes the **priority**, not the permission. Real links still run
even when not suggested (#JomLokal's Box), and a low-confidence real link still runs (Atlas).

## 4. Fetch — collect the sources

**What it does:** downloads attachments, then routes each real URL by type to Drive / OneDrive / Box /
web; also scans body images and asset links. `WEB_FETCH_MODE` gates web, body and asset fetching.

| Email | Fetchers that ran | What came back |
|---|---|---|
| Kain | attachments | PDF 47,883 B → 5,229 chars; 1 body photo |
| MATRADE | attachments + **Drive** | 2 DOCX (4,268 / 1,196 chars) + 4 images; 200×52 header logo |
| APAC | attachments + **OneDrive + web** | release PDF + longer report + images; web page 5 images |
| JomLokal | attachments + **Box + web** | 6 attachments; Box 3 files; web home page (not an article) |
| BigSeller | **web** + body images | vritimes 3,261 chars + 4 images; 1 body photo |
| Sanct | body images only | 4 inline photos; no attachment |
| Atlas | **Drive (Google Doc)** | doc exported as 7,302 chars; 32×32 icons skipped |

**What it teaches:** the **URL type** decides the fetcher, not the AI. Several fetchers can run for one
email; failures are isolated per source.

## 5. Collect + select — build the candidate pool

**What it does:** every fetched text becomes a candidate, scored against the subject; the best one is
chosen. The AI does not see only one source.

| Email | Candidates | Winner (score) | Loser |
|---|---|---|---|
| Kain | 1 | PDF (12.6) | — |
| MATRADE | 2 | release DOCX (13.0) | short report (7.6) |
| APAC | 3 | OneDrive release (9.0) | 19k-char CEO report (6.85), web page (5.54) |
| JomLokal | 6 | English DOCX (14.0) | Box duplicate (13.0), Malay DOCX (11.45), home page (7.73) |
| BigSeller | 2 | vritimes (10.63) | longer Shopee page (4.0) |
| Sanct | 1 | the body | — |
| Atlas | 1 | the Google Doc | — |

**What it teaches:** **the longest text never wins by default.** Subject match decides — that is what
stops a CEO report or an unrelated page from becoming the article.

## 6. Extract — write the article

**What it does:** returns the chosen candidate verbatim plus an evidence note and a confidence.

| Email | Source | Length | Confidence |
|---|---|---|---|
| Kain | attachment PDF | 5,135 chars | 0.95 |
| MATRADE | Drive DOCX | 4,134 chars | 0.95 |
| APAC | OneDrive PDF | 8,968 chars | 0.95 |
| JomLokal | English DOCX | 6,335 chars | — |
| BigSeller | web page | 3,261 chars | — |
| Sanct | email body | 4,679 chars | 0.86 |
| Atlas | Google Doc | 7,229 chars | — |

**What it teaches:** extract never fetches anything; it only writes the article from the candidate that
collect chose.

## 7. Logo scan — find media inside the document

**What it does:** checks the document's embedded images by dimensions and classifies logo vs photo;
standalone attachment logos are counted too. Deterministic evidence can override the text AI.

| Email | Found in the document | Flags |
|---|---|---|
| Kain | no document logo/photo; body photo is not a document logo | none |
| MATRADE | 200×52 header logo | `docLogo=true` |
| APAC | 506×87 logo + 1664×1174 photos | `docLogo`, `docPhoto` |
| JomLokal | 1920×356 header logo + 542×305 photo | `docLogo`, `docPhoto` |
| BigSeller | none; the publisher logo is **not** the brand logo | none |
| Sanct | none; 4 inline photos | none |
| Atlas | none; 32×32 icons skipped | none |

**What it teaches:** media is judged by **dimensions**, not file size. A small logo counts; a 1×1
tracking pixel does not; a publisher's site logo never becomes the brand's logo.

## 8. Verify — the checklist flags

**What it does:** compares the email subject to the extracted headline, sets the media flags and
`readyToFilter`.

| Email | Article | Pic | Logo | Logo in article | Image in article | Subject | Ready |
|---|---|:---:|:---:|:---:|:---:|---:|:---:|
| Kain | ✓ | ✓ | — | — | — | 98 | ✓ |
| MATRADE | ✓ | ✓ | ✓ | ✓ | — | 100 | ✓ |
| APAC | ✓ | ✓ | ✓ | ✓ | ✓ | 98 | ✓ |
| JomLokal | ✓ | ✓ | ✓ | ✓ | ✓ | 100 | ✓ |
| BigSeller | ✓ | ✓ | — | — | — | 100 | ✓ |
| Sanct | ✓ | ✓ | — | — | ✓ | 100 | ✓ |
| Atlas | ✓ | — | — | — | — | 100 | **✗** |

**What it teaches:** the readiness rule is simple: **article + subject match + at least one media
signal**. Atlas has a complete article and a perfect subject match, and still stops — no media.

## 9. Checklist — save the row

**What it does:** writes the 14-column row to SQLite (the source of truth).

| Email | Row |
|---|---|
| Kain | 407 |
| MATRADE | 397 |
| APAC | 395 |
| JomLokal | 405 |
| BigSeller | 400 |
| Sanct | 281 |
| Atlas | 385 (not ready) |

**What it teaches:** the row is frozen at this point; every later page reads it.

## 10. Archive — write the files

**What it does:** writes `all_emails/<Subject>/article.md`, `images/` and `originals/`.

| Email | Images | Originals |
|---|---:|---:|
| Kain | 3 | 1 (the PDF) |
| MATRADE | 6 | 2 |
| APAC | 10 | 2 |
| JomLokal | 9 | 6 |
| BigSeller | 6 | 0 |
| Sanct | 4 | 0 |
| Atlas | 0 | 0 |

**What it teaches:** the archive mirrors the media decision — a row with `hasPic=false` archives no
images (Atlas), and a Drive kit brings more images than the email itself.

## 11. Filter — Jev

**What it does:** runs the 3 hard gates + 11 weighted scores, only for `readyToFilter=true`, and stores
the verdict linked to the checklist row.

| Email | Filter |
|---|---|
| Kain | ACCEPT 80 |
| MATRADE | ACCEPT 91 |
| APAC | ACCEPT 70 |
| JomLokal | ACCEPT 84 |
| BigSeller | ACCEPT 88 |
| Sanct | no current result row (older batch) |
| Atlas | **skipped** — not ready |

**What it teaches:** filter is a separate stage. A complete article can be accepted or rejected on
editorial grounds; a not-ready row never reaches it.

---

## Which stage decided each email's result

| Email | Decisive stage | Why the result differs |
|---|---|---|
| Kain | **Normalize / Fetch** | only attachments; the body photo is what makes `hasPic=true` |
| MATRADE | **Fetch + Logo scan** | the Drive kit supplies the release; the DOCX header logo supplies `hasLogoInArticle` |
| APAC | **Collect + select** | three sources; the 9k release beats the 19k report |
| JomLokal | **Decide + Collect** | English DOCX chosen; the Box duplicate loses in the pool |
| BigSeller | **Normalize + Fetch** | tracking links dropped; the web probe finds the release; body photo saves `hasPic` |
| Sanct | **Normalize + Decide** | no usable link; the body is the only source |
| Atlas | **Verify** | complete article, but no media → `readyToFilter=false` |

**The one-line summary:** the email shape (stage 2) creates the possibilities; decide and the URL type
(stages 3–4) choose the sources; collect (stage 5) picks the article; verify (stage 8) decides whether
it is usable. A different result almost always traces back to one of those four stages.

## See also

- `docs/workflow/RECEIVE-WORKFLOW-7-EMAIL-EXAMPLES.md` — the same seven emails, full walkthroughs.
- `docs/workflow/MEDIA-SOURCE-DECISION.md` — who picks the fetcher, with the decide-suggestion detail.
- `docs/workflow/CODE-MAP.md` — where every module lives.
