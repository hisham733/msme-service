# How the service decides where to fetch the article

_Companion to_ `RECEIVE-WORKFLOW-7-EMAIL-EXAMPLES.md` _(the full 11-stage walkthroughs).
This page answers one question only: **who decides which source/fetcher is used for an email?_**

## The short answer

The four source fetchers — `drive_fetch`, `onedrive_fetch`, `box_fetch`, `web_fetch` — are **not AI
tools**. The AI never calls them. The pipeline routes by **URL type**, after a **link guard**, and the
AI has only two jobs:

1. **decide** (step 1) *suggests* a link (`linkToFetch`);
2. **extract** (step 2) picks which fetched candidate is the real article.

Everything between those two AI calls is deterministic Python. That is deliberate: a hallucinated URL
must never make the service fetch the wrong thing (`D6`, `D15`, `D20`, `D24`).

```mermaid
flowchart TD
  A[Email] --> B[normalize: linksFound + attachments + body images]
  B --> C{decide AI<br/>suggests linkToFetch}
  C --> D{link guard<br/>is the link in linksFound?}
  D -->|no| E[drop the suggestion]
  D -->|yes| F[classify the URL]
  F -->|drive folder| G[drive_fetch.fetch_media_kit]
  F -->|drive file / Google Doc| H[drive_fetch.fetch_file]
  F -->|box.com/s/| I[box_fetch.fetch_press_kit]
  F -->|1drv.ms / onedrive.live.com| J[onedrive_fetch.fetch_kit]
  F -->|other http(s)| K{WEB_FETCH_MODE != off}
  K -->|yes| L[web_fetch.fetch_article]
  K -->|off| M[skip]
  G & H & I & J & L --> N[candidate pool]
  B -->|attachments| N
  B -->|body images| N
  N --> O{extract AI<br/>picks the article}
  O --> P[verify -> checklist -> archive]
```

### What is the "decide AI"?

It is **one text-only call to the language model** at receive step 1 (`msme/receive/decide.py`).
"Decide" is the stage name you see on the flow page; it means *decide the press source*.

- **What it reads:** the subject, sender, date, cleaned body, the **list** of attachments
(name, MIME type, size) and the links found in the email.
- **What it never does:** it does not open a file, download a link, or call any fetcher.
- **What it answers:** which attachment is the release (English preferred), whether images are
available, and whether there is a media-kit link worth fetching.
- **What it returns:** JSON such as
`{"chosenFileName": "...docx", "chosenDocType": "docx", "imagesAvailable": true, "linkToFetch": "https://drive.google.com/...", "linkIsPressKit": true, "confidence": 0.78, "reason": "..."}`.
- **What happens next:** plain Python acts on that JSON — download attachments, call the matching
fetcher, build the candidate pool.

So "the decide AI suggests, the pipeline acts." The prompt is `prompts/decide_prompt.txt`
(`PROMPT_VERSION=v1` in production); the output keys are consumed by `pipeline.py:436`.

**Example (MATRADE):** the email has one logo PNG and a Drive folder link, no release document.
Decide returns `linkToFetch = https://drive.google.com/drive/folders/...`, confidence 0.78. The
pipeline checks the URL is really in the email, then calls `drive_fetch.fetch_media_kit`.

### What "suggests" means — and what actually acts

The decide answer has eleven fields, but **only two change behaviour**:

| Decide field | Used by the pipeline? | Effect |
|---|---|---|
| `chosenFileName` | **yes** | that attachment's text is preferred as the starting article text; all attachments are still loaded (`D24`) |
| `linkToFetch` | **yes, after the link guard** | that URL is offered first to the URL classifier |
| `chosenAttachmentKey` | recorded only | shown on `/flow.html` |
| `chosenDocType`, `isEnglish` | recorded only | shown on `/flow.html` |
| `imagesAvailable`, `imagesInAttachments`, `imagesViaLink` | recorded only | real images are found by the scanners, not by this flag |
| `linkIsPressKit` | recorded only | the URL pattern decides the fetcher, not this flag |
| `confidence`, `reason` | recorded only | **not a gate** — a low-confidence real link is still used |

**Suggestion is not permission.** The pipeline scans *every* real link in the email; the decide link
only gets priority ordering. That is why #JomLokal's Box still ran even though decide chose the
English DOCX, and why APAC's web page ran even though decide chose OneDrive.

| # | Email | Decide suggested | Confidence | Used as suggested? | Other real links that still ran | Outcome |
|---|---|---|---|---|---|---|
| 1 | Kain Fashion | the PDF attachment, no link | — | yes | none (only opt-out links) | PDF used |
| 2 | MATRADE | Drive folder link | 0.78 | yes | none | Drive fetched |
| 3 | APAC CEOs | OneDrive folder | 0.85–0.90 | yes | **the Egon Zehnder web page** | OneDrive + web candidates |
| 4 | #JomLokal | English DOCX; Box noted as "supporting" | — | attachment yes | **the Box link** | English DOCX beat the Box copy |
| 5 | BigSeller | vritimes web link | — | yes | none (SendGrid tracking dropped) | vritimes used |
| 6 | Sanct Social | body is the article, no link | — | yes | none (SendGrid is not a press kit) | body used |
| 7 | Atlas Copco | Google Docs link | 0.45–0.62 | yes, despite low confidence | none (32×32 icons skipped) | Google Doc used, no media |

**Two mini-examples**

*MATRADE — suggestion followed.* Decide saw `Logo-MATRADE_Color.png` and one Drive folder link; it
returned `linkToFetch` = the folder, `linkIsPressKit=true`, confidence 0.78. The guard found the URL
in `linksFound`, so `drive_fetch.fetch_media_kit` ran and produced 2 DOCX + 4 images.

*#JomLokal — suggestion did not exclude the other source.* Decide chose the **English DOCX**
attachment and treated the Box link as supporting material. The pipeline still saw the Box URL in
the email, so `box_fetch` ran too. The candidate pool held both copies; the English DOCX (14.0) beat
the Box duplicate (13.0).

**When the suggestion is ignored**

- **Invented URL** → `_trusted_links` drops it; the run continues with the real links.
- **Tracking/opt-out URL** → the AI itself marks it "not a press kit" (BigSeller, Sanct Social).
- **Low confidence** → still followed if the URL is real (Atlas Copco, 0.45–0.62); confidence is
recorded, not a gate.
- **Wrong fetcher guess** → the URL type wins: a Drive URL always goes to `drive_fetch`, a
`1drv.ms` URL always to `onedrive_fetch`, whatever the AI called it.

Code: `msme/receive/decide.py:38–82` (input), `pipeline.py:436–452` (what is recorded),
`pipeline.py:509–520` (the guard + priority).

## Who decides what

| Question | Decided by | Rule |
|---|---|---|
| Is there a media-kit link? | **decide AI** (step 1) | returns `linkToFetch`, `imagesViaLink`, confidence |
| Is that link real? | **pipeline** (`_trusted_links`, `msme/receive/pipeline.py:203`) | only links `normalize` saw in the email; a decide-only URL is dropped |
| Which fetcher runs? | **pipeline**, by URL pattern | Drive folder/file, Google Doc, Box, OneDrive, else web |
| Does web fetching happen? | **config**, not AI | `WEB_FETCH_MODE=off\|known\|probe` (default `probe`), `WEB_KNOWN_SITES`, `WEB_PROBE_MAX_LINKS` |
| Which text is the article? | **extract AI** (step 2) | every fetched source becomes a candidate; the AI selects (`D24`) |

**Drive/Box/OneDrive have no on/off switch** — the presence of that link type is the switch. Several
fetchers can run for the same email; the candidate pool then holds all of them.

## The fetch paths

| Path | Trigger in the email | Code | What comes back |
|---|---|---|---|
| **Attachments** | files on the email | `_load_attachments` (`pipeline.py:82`) | every file is downloaded; text/images extracted |
| **Drive folder** | `drive.google.com/.../folders/<id>` | `drive_fetch.fetch_media_kit` (`pipeline.py:543`) | docs, images, header logo/photo flags |
| **Drive file / Google Doc** | `/file/d/<id>/` or `docs.google.com/document/d/<id>` | `drive_fetch.fetch_file` (`pipeline.py:585–642`) | one document's bytes/text |
| **OneDrive** | `1drv.ms`, `onedrive.live.com` | `onedrive_fetch.fetch_kit` (`pipeline.py:785`) | same kit shape as Drive |
| **Box** | `*.box.com/s/...` | `box_fetch.fetch_press_kit` (`pipeline.py:759`) | docs, images, originals |
| **Web page** | any other public `http(s)` | `web_fetch.fetch_article` (`pipeline.py:815`) | title, text, images, publisher logos |
| **Body images / asset links** | `<img src>` in the body; "download" links | body-image scan + `asset_link` (`pipeline.py:860–980`) | photos and logos, by dimensions |

### `WEB_FETCH_MODE`

| Mode | Effect |
|---|---|
| `off` | no web page, **no body images**, no asset links; only attachments + cloud kits |
| `known` | only hosts in `WEB_KNOWN_SITES` (pitchmystory, cision, mynewsdesk) |
| `probe` (default) | known sites + up to `WEB_PROBE_MAX_LINKS` (2) unknown links, capped by `COLLECT_MAX_WEB_LINKS` (3) |

### The link guard

1. `normalize` records every link it actually sees (`linksFound`) and resolves short/tracking links

   (`bit.ly`, `mjt.lu`, `sendgrid.net`) to their final URL.
2. The decide AI's `linkToFetch` is trusted only if it matches (or contains / is contained in) a

   `linksFound` entry (`pipeline.py:203`).
3. If not, it is dropped — the run continues with the links the email really has.

---

## Seven real emails, seven different routes

Each block follows the same order: **shape → normalize → decide → link guard → what ran → what did
not → candidate pool → result**. The facts come from the archived runs in
`RECEIVE-WORKFLOW-7-EMAIL-EXAMPLES.md`; the routing rules come from `msme/receive/pipeline.py`.

### 1. Kain Fashion Incubator — attachment only

- **Shape:** PDF `[PRESS RELEASE] Kain Fashion Incubator - Open Call.pdf`, two poster PNGs, one photo
in the HTML body. The only links are Mediaportal “update my details”/opt-out links.
- **Normalize:** 3 attachments, 1 body image (`bodyphoto-1.png`), 2 non-article links.
- **Decide:** chose attachment 2 (the PDF) — “the substantive English release, while the two PNGs are
campaign artwork”; no press-kit URL.
- **Link guard:** nothing to trust — the Mediaportal links are not a media kit.
- **Ran:** attachments only (`load_attachments`).
- **Did not run:** Drive / OneDrive / Box (no matching link). No web candidate contributed — the
Mediaportal links are opt-out/update links, not articles.
- **Candidate pool:** 1 — `attachment_pdf`, 5,228 chars, score 12.6.
- **Result:** ready; `hasPic=true` from the body photo; **ACCEPT 80**.

### 2. MATRADE–Malaysia Pavilion — Drive folder

- **Shape:** one logo PNG attached; the release itself is in a **Google Drive folder** link; the body
is a cover note.
- **Normalize:** 1 attachment (`Logo-MATRADE_Color.png`), 1 Drive folder link, no release document.
- **Decide:** no document attachment; chose the Drive link as the release/media kit (confidence 0.78).
- **Link guard:** the Drive URL is in `linksFound` → trusted.
- **Ran:** `drive_fetch.fetch_media_kit(folder_id)` → 2 DOCX (4,268 and 1,196 chars) + 4 images;
`pick_release_doc` selected the release by name/content.
- **Did not run:** OneDrive / Box (no such link); web (no other article link).
- **Candidate pool:** 2 — release doc score 13.0 vs short report 7.6 → **release wins**.
- **Result:** ready; the DOCX header logo is caught deterministically (`hasLogoInArticle=true`);
**ACCEPT 91**.

### 3. APAC CEOs (Egon Zehnder) — OneDrive + web page + inline images

- **Shape:** 4 inline images, a **OneDrive folder** link, a public Egon Zehnder page; the release text
is also in the body.
- **Normalize:** 4 image attachments, a `1drv.ms` link, a web page link.
- **Decide:** no document; chose the **OneDrive folder** (confidence 0.85–0.90).
- **Link guard:** both the OneDrive and web links are in `linksFound` → trusted.
- **Ran:** `onedrive_fetch.fetch_kit` (release PDF, a longer CEO report, images) **and**
`web_fetch.fetch_article` (5 images); the 4 inline images were loaded too.
- **Did not run:** Drive / Box (no such links).
- **Candidate pool:** 3 — OneDrive release 9,072 chars (9.0), CEO report 19,116 (6.85), web page 4,995
(5.54) → **the release wins, not the longest document**.
- **Result:** ready; header logo + photos found in the document; **ACCEPT 70**.

### 4. #JomLokal / TikTok Shop — attachments + Box duplicate + web home page

- **Shape:** 6 attachments (English/Malay/Chinese DOCX + 3 images) and a **Box** shared link.
- **Normalize:** 6 attachments, a `voxeureka.box.com` link, body cover note.
- **Decide:** chose the **English DOCX** by name; also noted the Box link as supporting material.
- **Link guard:** the Box link is in `linksFound` → trusted.
- **Ran:** all attachments; `box_fetch.fetch_press_kit` (2 folders / 3 files / 3 originals, no
images); `web_fetch` fetched the agency home page.
- **Did not run:** Drive / OneDrive (no such links).
- **Candidate pool:** 6 — English DOCX 14.0, the same release from Box 13.0, Malay DOCX 11.45, the
agency home page 7.73, and more → **English DOCX wins**; the home page is not an article.
- **Result:** ready; header logo + body photo in the DOCX; **ACCEPT 84**.

### 5. BigSeller 11.11 checklist — public web page + body photo

- **Shape:** no attachments; a **vritimes.com** article link, SendGrid tracking links, one body image.
- **Normalize:** no attachments; a vritimes URL, SendGrid tracking links, 1 body image.
- **Decide:** chose the **vritimes link** as the only substantive release; explicitly ignored the
SendGrid tracking redirects.
- **Link guard:** the tracking links are resolved/ignored; the vritimes URL is trusted.
- **Ran:** `web_fetch` in `probe` mode (vritimes + an unrelated Shopee ads page); body-image scan found
**1 photo**.
- **Did not run:** Drive / OneDrive / Box (no such links).
- **Candidate pool:** 2 web candidates — vritimes 3,261 chars (10.63) vs the longer Shopee page 6,297
(4.0) → **the shorter, subject-matching vritimes release wins**.
- **Result:** ready; the body photo saves `hasPic`; the publisher logo is **not** counted as the brand
logo; **ACCEPT 88**.

### 6. Sanct Social — body-only release

- **Shape:** no attachments, no usable press-kit link (only a SendGrid tracking URL); the full release
and 4 inline photos are in the email body.
- **Normalize:** no attachments; full release in the body; a tracking link; 4 inline images.
- **Decide:** no attachment; the body is the article; the tracking link is not a press kit, so nothing
is fetched from it.
- **Link guard:** the SendGrid URL is not a press kit → no cloud fetcher is selected.
- **Ran:** body-image scan → **4 photos** (`bodyphoto-1.jpg` … `bodyphoto-4.jpg`); 0 attachments.
- **Did not run:** Drive / OneDrive / Box / web (no eligible link).
- **Candidate pool:** the body (this archive predates `D24`; today the body would be the single
candidate).
- **Result:** ready; `hasPic=true` and `hasImageInArticle=true` from the inline photos; no stored
filter result in the current batch.

### 7. Contributed Article (Atlas Copco) — Google Docs link, no media

- **Shape:** no attachments; the article is a **Google Docs** link; the only images are 32×32
Facebook/LinkedIn icons in the signature.
- **Normalize:** no attachments; a `docs.google.com/document/d/…` link; two 32×32 social icons.
- **Decide:** no attachment; chose the Google Docs link (confidence 0.45–0.62); no images indicated.
- **Link guard:** the Google Docs URL is in `linksFound` → trusted.
- **Ran:** `drive_fetch.doc_id_from_link` → `fetch_file` exported the document as text (7,302 chars).
- **Did not run:** OneDrive / Box (no links); the body-image scan skipped the 32×32 icons as
logos/too small; no web article.
- **Candidate pool:** 1 — the Google Doc, 7,302 chars → selected.
- **Result:** article yes, **all media no** → `readyToFilter=false`; the filter is skipped. The sender
must supply an Atlas Copco photo/logo.

---

## Quick lookup

| The email contains… | What runs |
|---|---|
| A document/image attached | attachments (`load_attachments`) — always |
| `drive.google.com/.../folders/` | `drive_fetch.fetch_media_kit` |
| `/file/d/<id>/` or `docs.google.com/document/d/<id>` | `drive_fetch.fetch_file` |
| `1drv.ms` / `onedrive.live.com` | `onedrive_fetch.fetch_kit` |
| `*.box.com/s/...` | `box_fetch.fetch_press_kit` |
| Any other public article URL | `web_fetch` if `WEB_FETCH_MODE` is `known`/`probe` |
| `<img src>` photos/logos in the body | body-image scan (also gated by `WEB_FETCH_MODE`) |
| A “download”/press-kit asset URL | `asset_link` (also gated by `WEB_FETCH_MODE`) |
| Only tracking/opt-out links | nothing is fetched from them |

## Why it is built this way

- **No AI tool-calling:** the AI cannot choose a fetcher, so it cannot fetch an invented URL.
- **Multiple sources are normal:** the same release often arrives twice (attachment + Box, OneDrive +
web). All are collected; the extract AI picks (`D24`). A Drive folder kit is merged even when an
attachment article already exists, because the kit may hold higher-res photos.
- **Media is judged by dimensions, never bytes:** an 8.6 KB 250×87 logo is media; a 1×1 tracking
pixel is not (`D7`, `D24`).
- **Publisher logos are not the brand's logo** — `web_fetch` returns them separately.
- **A fetcher failure does not abort the run:** each block is wrapped in `try/except` and records a
stage error; the run continues with whatever else was collected.

## If a fetcher is deleted

All four are imported at the top of `msme/receive/pipeline.py` (lines 44–54), so deleting one stops
the app from starting — even for emails that would never use it. See `INDEX.md` §8 for the full
delete guide.

## See also

- `docs/workflow/RECEIVE-WORKFLOW-7-EMAIL-EXAMPLES.md` — the same seven emails, all 11 stages each.
- `docs/workflow/RECEIVE-STAGES-EXPLAINED.md` — the eleven stages point by point, with the seven emails compared at each stage.
- `docs/workflow/CODE-MAP.md` — where every module lives.
- `decisions/D24.md` — collect every source first, then let the extract AI select.
