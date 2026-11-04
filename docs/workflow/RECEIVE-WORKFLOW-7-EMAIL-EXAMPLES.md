# Receive workflow — seven real email structures, stage by stage

_Last updated 2026-10-29. Companion to `WORKFLOW-RECEIVE-TO-PUBLISH.md`. Source routing (who picks the fetcher) is explained in `MEDIA-SOURCE-DECISION.md`; the stage-first comparison is in `RECEIVE-STAGES-EXPLAINED.md`._

This is the receive stage explained through **seven archived emails**, each with a different
shape. Every email goes through the same eleven stages; what changes is what each stage has to
work with. The examples use the real `pipeline_results` / `checklist` rows and the live archive in
`all_emails/`. Raw email bodies stay in the database/archive; this document only uses the
press-release facts, file names, counts and flags.

## 1. The seven emails at a glance

| # | Email (paraphrased subject) | Shape | The hard part | Receive result |
|---:|---|---|---|---|
| 1 | **Kain Fashion Incubator** open call | PDF attachment + 2 poster PNGs + 1 body photo | Choose the PDF among three files; count the body photo | **ready**; Jev ACCEPT 80 |
| 2 | **MATRADE–Malaysia Pavilion** | 1 logo PNG + a **Google Drive folder** link | Fetch a Drive folder; choose the release among two docs; read the header logo | **ready**; ACCEPT 91 |
| 3 | **APAC CEOs (Egon Zehnder)** | 4 inline images + a **OneDrive folder** + a web page | OneDrive + web fallback; choose the release, not the longer report | **ready**; ACCEPT 70 |
| 4 | **#JomLokal / TikTok Shop** | 6 attachments (EN/BM/ZH DOCX + images) + a **Box** link | Multi-language release picker; Box; duplicate sources | **ready**; ACCEPT 84 |
| 5 | **BigSeller 11.11 checklist** | No attachment; body cover + **vritimes.com** page + body photo | Tracking links; public web page; body image | **ready**; ACCEPT 88 |
| 6 | **Sanct Social** | No attachment; **full release in the email body** + 4 inline photos | Extract the article from the body; use inline images | **ready**; no current filter row |
| 7 | **Contributed Article (Atlas Copco)** | No attachment; **Google Docs** link; only signature icons | Fetch the Google Doc; no usable media | **not ready**; filter skipped |

The spread is deliberate: **attached document → cloud folder → cloud folder + web → box/multi-language
→ public web page → body-only → Google Doc**. It covers every source type the receive stage has to
handle.

## 2. The eleven stages

1. **Gmail** — pick an unread inbox message matching `in:inbox is:unread -category:promotions`
   (push webhook or the 5-minute poll).
2. **Normalize** — read subject, From, date, body text, HTML, attachments and links; resolve
   tracking/redirect links; keep the email model.
3. **Decide** — one AI call chooses the article source: an attachment, a Drive/OneDrive/Box file,
   the email body, or a public web page. It also reports whether images are available.
4. **Fetch** — download the chosen source and the media: attachments, Drive/OneDrive/Box,
   public pages, images inside the email body, direct asset links.
5. **Collect + select** — collect every fetched text as a candidate, score them, and let the
   extract AI choose the real release (not the longest document, not the cover note).
6. **Extract** — produce the verbatim article plus an evidence note; flag document-embedded
   logos/photos.
7. **Logo scan** — deterministic image check inside the document (header/banner/photo) and
   standalone attachment logos; this can override the text-only extract AI.
8. **Verify** — headline, subject match/score, `hasArticle`, `hasPic`, `hasLogo`,
   `hasLogoInArticle`, `hasImageInArticle`, and `readyToFilter`.
9. **Checklist** — the 14-column row is saved to SQLite.
10. **Archive** — `article.md`, `images/` and `originals/` under `all_emails/`.
11. **Filter** — Jev runs only when `readyToFilter=true`; the result is linked to the row.

The stage names below are the pipeline's own names; the **Checklist** row is the SQLite row saved
after verify. All emails were forwarded by **Editor MSME `<editor@malaysiasme.com.my>`**; the
original sender is deeper in the thread.

---

## 3. Walkthroughs

### 3.1 Kain Fashion Incubator — PDF attachment + posters + body photo

**Email shape:** open-call release forwarded by the editor; **three attachments** — the PDF
`[PRESS RELEASE] Kain Fashion Incubator - Open Call.pdf`, `MainCampaignPoster_RGB_1080x1350.png`
and `KFI_OpenCall_1080X1350.png` — plus one photo embedded in the HTML body. The only links are
Mediaportal “update my details”/opt-out links, not articles.

| Stage | What happened |
|---|---|
| **Gmail** | Unread forwarded open call; subject begins `Fwd: OPEN CALL - …`; no sender-side filtering needed. |
| **Normalize** | 3 attachments, HTML body with 1 image (`bodyphoto-1.png`), two non-article Mediaportal links. |
| **Decide** | Chose **attachment 2**, the PDF: “the substantive English release, while the two PNGs are campaign artwork”; no press-kit URL. |
| **Fetch** | `load_attachments` downloaded all 3 (PDF 47,883 B; posters 1.46 MB / 1.70 MB); extracted **5,229 chars** from the PDF; body image extraction found **1 photo**. |
| **Collect + select** | **1 candidate**: `attachment_pdf`, 5,228 chars, score 12.6 → selected. |
| **Extract** | `attachment_pdf`; body 5,135 chars; confidence 0.95; PDF contains headline, dateline, body, quotes and boilerplate. |
| **Logo scan** | No document logo/photo; `hasLogoFile=false`; the body photo is not a document logo. |
| **Verify** | Headline “Kain Fashion Incubator Seeks 10 …”; subject match **true / 98**; `hasArticle=true`, `hasPic=true`, `hasLogo=false`, `hasLogoInArticle=false`, `hasImageInArticle=false`; **ready**. |
| **Checklist** | Row **407**: article/picture yes, logos no, subject 98, ready yes. |
| **Archive** | `all_emails/OPEN CALL - Kain Fashion Incubator …`; **3 images**, **1 original** (the PDF). |
| **Filter** | **ACCEPT, 80** (3R gates 0.01–0.02). |

**What it teaches:** the common, clean case — one PDF plus artwork. The **body photo** is what
 satisfies `hasPic`; the PDF being small is irrelevant. If the sender had sent only the PDF, the
row would have `hasPic=false` and would not reach the filter.

### 3.2 MATRADE — logo attachment + Google Drive folder

**Email shape:** a logo PNG is attached, but the release itself is in a **Google Drive folder**
linked in the body (`drive.google.com/open?id=…`). The body is a cover note.

| Stage | What happened |
|---|---|
| **Gmail** | Unread forwarded release; subject `Fwd: [PRESS RELEASE] MATRADE-LED …`. |
| **Normalize** | 1 attachment (`Logo-MATRADE_Color.png`), one Drive folder link; no release document in the email. |
| **Decide** | No document attachment; chose the **Drive link** as the release/media kit; confidence 0.78. |
| **Fetch** | Logo downloaded (14 KB); `drive_fetch` read **2 DOCX docs** — the full release (4,268 chars) and a short report (1,196 chars) — plus **4 images**; the DOCX header has a **200×52 logo**. |
| **Collect + select** | **2 candidates**; the release doc (score 13.0) beat the short report (7.6) → selected. |
| **Extract** | `drive_link`; 4,134 chars; confidence 0.95; the release text came from the Drive DOCX. |
| **Logo scan** | `docLogo=true`; the DOCX header logo is classified as a logo; `attachmentLogos` also sees the attached logo; `hasLogoFile=true`. **Deterministic evidence overrides** the extract AI's “no logo”. |
| **Verify** | Subject **100**; `hasArticle=true`, `hasPic=true`, `hasLogo=true`, `hasLogoInArticle=true`, `hasImageInArticle=false`; **ready**. |
| **Checklist** | Row **397**: article/picture/logo/logo-in-article yes, subject 100, ready yes. |
| **Archive** | `all_emails/MATRADE-LED MALAYSIA PAVILION …`; **6 images**, **2 originals**; release `.md` + logo + photos + DOCX. |
| **Filter** | **ACCEPT, 91**. |

**What it teaches:** a **Drive folder is a media kit**; the release is chosen by name/content, not
by being the longest. The logo can be a header image inside the document — the deterministic scan
catches it even when the extract AI says otherwise.

### 3.3 APAC CEOs (Egon Zehnder) — OneDrive folder + web fallback + inline images

**Email shape:** four inline images, a **OneDrive folder** link, and a public Egon Zehnder page;
the body also carries the full release. No release document is attached.

| Stage | What happened |
|---|---|
| **Gmail** | Unread forwarded release; subject `Fwd: [PRESS RELEASE] APAC CEOs …`. |
| **Normalize** | 4 image attachments (`image001.jpg` etc.), a `1drv.ms` OneDrive link and an Egon Zehnder page; body contains the release text. |
| **Decide** | No document; chose the **OneDrive folder**; confidence 0.85–0.90. |
| **Fetch** | `onedrive_fetch` read the folder: the APAC press-release PDF, a longer CEO report and images; `web_fetch` also fetched the public page (5 images); the 4 inline images were loaded. |
| **Collect + select** | **3 candidates**: OneDrive release PDF 9,072 chars (score 9.0), CEO report 19,116 chars (6.85), web page 4,995 (5.54). The **release** won, not the longest report. |
| **Extract** | `onedrive_link`; 8,968 chars; the release PDF has the headline, dateline, findings, quotes and media contacts. |
| **Logo scan** | Document images: a 506×87 **logo**, plus 1664×1174 **photos**; `docLogo=true`, `docPhoto=true`; no standalone logo file. |
| **Verify** | Subject **98**; `hasArticle=true`, `hasPic=true`, `hasLogo=true`, `hasLogoInArticle=true`, `hasImageInArticle=true`; **ready**. |
| **Checklist** | Row **395**: all media flags true, subject 98, ready yes. |
| **Archive** | `all_emails/APAC CEOs …`; **10 images**, **2 originals**. |
| **Filter** | **ACCEPT, 70** — a lower score; the meeting may challenge its relevance. |

**What it teaches:** the same release can arrive from **three places** (OneDrive, the public web
page, inline images). The collect-then-select step is what stops the longer CEO report or the
web-page copy from winning. The document's header logo and photos are media.

### 3.4 #JomLokal / TikTok Shop — Box + three-language release picker

**Email shape:** six attachments — the English, Malay and Chinese DOCX releases plus three image
files — and a **Box shared link** to the digital press kit. The body is a pitch/cover note.

| Stage | What happened |
|---|---|
| **Gmail** | Unread forwarded release; subject `Fwd: [Press Release] #JomLokal …`. |
| **Normalize** | 6 attachments (3 DOCX + 3 images); a `voxeureka.box.com` link; body cover note. |
| **Decide** | Chose the **English DOCX** by name; also noted the Box link as supporting material. |
| **Fetch** | All 6 attachments; `box_fetch` read **2 folders / 3 files / 3 originals**, with no images; `web_fetch` found the agency home page, not a release. |
| **Collect + select** | **6 candidates**: English DOCX (14.0), the same release from Box (13.0), Malay DOCX (11.45), the web home page (7.73), and more. The **English DOCX** won — the same release appeared through two sources. |
| **Extract** | `attachment_docx`; 6,335 chars; English release chosen over the BM/ZH versions and the Box duplicate. |
| **Logo scan** | English DOCX contains a **1920×356 header logo** and a **542×305 body photo**; `docLogo=true`, `docPhoto=true`; an attachment logo is also present. |
| **Verify** | Subject **100**; all four media flags true; **ready**. |
| **Checklist** | Row **405**: article/picture/logo/logo-in-article/image-in-article all yes, subject 100, ready yes. |
| **Archive** | `all_emails/JomLokal MSMEs Record 140 Sales Growth …`; **9 images**, **6 originals**. |
| **Filter** | **ACCEPT, 84**. |

**What it teaches:** **multiple languages and duplicate sources are normal**. The picker uses the
name and content, not the first attachment; Box can supply the same release again; the body’s
agency home page is not the article. Embedded logo + photo are enough media.

### 3.5 BigSeller — public web page + body photo, no attachment

**Email shape:** no attachments. The email carries a short cover note, a **vritimes.com** link to
the full release and photos, SendGrid tracking links, and one image in the body.

| Stage | What happened |
|---|---|
| **Gmail** | Unread forwarded release; subject `Fwd: [PRESS RELEASE] BigSeller Shares …`. |
| **Normalize** | No attachments; a vritimes article URL, SendGrid tracking links, 1 body image. |
| **Decide** | Chose the **vritimes link** as the only substantive release; explicitly ignored the SendGrid tracking redirects. |
| **Fetch** | `web_fetch` (probe) fetched the vritimes release (3,261 chars, **4 images**) and an unrelated Shopee ads page; body image extraction found **1 photo**. |
| **Collect + select** | **2 web candidates**: vritimes (3,261 chars, 10.63) and the longer Shopee page (6,297, 4.0). The **shorter, subject-matching vritimes release** won. |
| **Extract** | `web_link`; 3,261 chars; the web page is the complete four-point checklist; the email body is a truncated cover note. |
| **Logo scan** | No document; no document logo/photo; the publisher logo on the page is **not** a brand logo. |
| **Verify** | Subject **100**; `hasArticle=true`, `hasPic=true` (body image), `hasLogo=false`, `hasLogoInArticle=false`, `hasImageInArticle=false`; **ready**. |
| **Checklist** | Row **400**: article/picture yes, logos no, subject 100, ready yes. |
| **Archive** | `all_emails/BigSeller Shares Four-Point Inventory Checklist …`; **6 images**, **0 originals**. |
| **Filter** | **ACCEPT, 88**. |

**What it teaches:** a **public web page is a valid article source**, but the system must not pick
the longest page or a tracking link. The body photo saved `hasPic`; if the sender had omitted it,
the web page's images would be the fallback. Publisher logos are deliberately **not** counted as
the brand's logo.

### 3.6 Sanct Social — body-only release + four inline photos

**Email shape:** no attachments and no usable press-kit link (a SendGrid tracking URL). The full
press release is in the email body, with **four inline photos** and no logo.

| Stage | What happened |
|---|---|
| **Gmail** | Unread forwarded release; subject `Fwd: [PRESS RELEASE] Sanct Social …`. |
| **Normalize** | No attachments; full release in the body; a SendGrid tracking link; 4 inline images. |
| **Decide** | No attachment; the body is the article; the tracking link is not a press kit, so nothing is fetched from it. |
| **Fetch** | `load_attachments` found 0 files; `body_images` found **4 photos** (`bodyphoto-1.jpg` … `bodyphoto-4.jpg`). |
| **Collect + select** | This archive predates the explicit collect stage (D24); today the body would be the single candidate. The body was the only article source. |
| **Extract** | `email_body`; 4,679 chars; confidence 0.86; the distributor cover note was stripped; the release runs headline → dateline → quotes → contact. |
| **Logo scan** | No document and no logo; `hasLogoFile=false`; the four inline images are photos. |
| **Verify** | Subject **100**; `hasArticle=true`, `hasPic=true` (inline photos), `hasLogo=false`, `hasLogoInArticle=false`, `hasImageInArticle=true`; **ready**. |
| **Checklist** | Row **281**: article/picture/image-in-article yes, logos no, subject 100, ready yes. |
| **Archive** | `all_emails/Sanct Social …`; **4 images**, **0 originals**. |
| **Filter** | No stored filter result in the current 23 (an older batch row); the receive row is ready. |

**What it teaches:** **body-only works** if the release and its photos are genuinely in the body.
The four inline photos are what save the media check; a SendGrid tracking link is not a press kit.
Compare **Event Me Now**, whose only inline image is a **1×1 tracking pixel** — without the web
probe it stays `readyToFilter=false`.

### 3.7 Contributed Article (Atlas Copco) — Google Docs link, no media

**Email shape:** no attachments. The article is a **Google Docs** link; the only images in the
body are 32×32 Facebook/LinkedIn icons. It is a contributed article/op-ed, not a release with a
media kit.

| Stage | What happened |
|---|---|
| **Gmail** | Unread forwarded article; subject `Fwd: Contributed Article: What the next generation …`. |
| **Normalize** | No attachments; a `docs.google.com/document/d/…` link; two 32×32 social icons in the signature. |
| **Decide** | No attachment; chose the **Google Docs link**; confidence 0.45–0.62; no images indicated. |
| **Fetch** | `google_doc_fetch` exported the doc as text: **7,302 chars**; body-image scan found only the two 32×32 social icons and skipped them as logos/too small. |
| **Collect + select** | **1 candidate**: the Google Doc, 7,302 chars → selected. |
| **Extract** | `drive_link`; 7,229 chars; complete contributed article with headline, sections and body; the email body is only the cover note and signature. |
| **Logo scan** | No document logo/photo; no usable attachment; `hasLogoFile=false`. |
| **Verify** | Subject **100**; `hasArticle=true`, `hasPic=false`, `hasLogo=false`, `hasLogoInArticle=false`, `hasImageInArticle=false`; **readyToFilter=false** — “no photo, logo, or in-article image assets”. |
| **Checklist** | Row **385**: article yes, all media no, subject 100, **not ready**. |
| **Archive** | `all_emails/Contributed Article …`; **0 images**, **0 originals**; only the article `.md`. |
| **Filter** | **Skipped** — “not ready to filter”. |

**What it teaches:** a **Google Doc can supply the text but not the media**. The article is
complete and the subject matches, yet the row stops at the media gate. The sender must provide an
Atlas Copco photo/logo (the 11 sender asks include this case).

---

## 4. Summary matrix

| # | Source chosen | Article | Pic | Logo | Logo in article | Image in article | Subject | Ready | Filter |
|---:|---|---:|:---:|:---:|:---:|:---:|---:|:---:|---|
| 1 Kain | PDF attachment | ✓ | ✓ | — | — | — | 98 | ✓ | ACCEPT 80 |
| 2 MATRADE | Drive folder DOCX | ✓ | ✓ | ✓ | ✓ | — | 100 | ✓ | ACCEPT 91 |
| 3 APAC | OneDrive release PDF | ✓ | ✓ | ✓ | ✓ | ✓ | 98 | ✓ | ACCEPT 70 |
| 4 JomLokal | English DOCX attachment | ✓ | ✓ | ✓ | ✓ | ✓ | 100 | ✓ | ACCEPT 84 |
| 5 BigSeller | Public web page | ✓ | ✓ | — | — | — | 100 | ✓ | ACCEPT 88 |
| 6 Sanct | Email body | ✓ | ✓ | — | — | ✓ | 100 | ✓ | —* |
| 7 Contributed | Google Doc | ✓ | — | — | — | — | 100 | **✗** | skipped |

\* Sanct row 281 is ready; no current filter result row (older batch).

## 5. What the seven examples prove

1. **The source type is not the article.** A PDF, a Drive folder, a OneDrive folder, a Box kit, a
   public page, the email body and a Google Doc can all carry the release. The decide step must
   choose the **release**, not the first file or the longest text.
2. **Collect-then-select matters.** APAC had a 19k-char CEO report and a 9k-char release; BigSeller
   had a 6.3k-char unrelated Shopee page and a 3.3k-char release. The subject-matching release
   wins.
3. **Media is a separate gate.** An article can be complete and still stop at
   `readyToFilter=false` (Contributed). A **photo**, a **logo**, a **document header logo** or an
   **in-body image** is required.
4. **Deterministic checks beat the text AI for media.** The extract AI said “no logo” for MATRADE,
   but the header scan found the 200×52 logo; the logo scan set `hasLogo`/`hasLogoInArticle`.
5. **Body-only is real.** Sanct Social proves a release in the body + inline photos works.
   The opposite failure is Event Me Now, whose only inline image is a 1×1 tracking pixel — the
   public-page probe is what gives it a real image.
6. **A Google Doc is text-only unless a media asset comes with it.** The Contributed Article is
   the clean example of a complete article blocked only by media.
7. **The threshold for “ready” is simple:** article + subject match + at least one media signal
   (`hasPic`, `hasLogo`, `hasLogoInArticle` or `hasImageInArticle`).

**Current live note (29 Oct 2026):** the synthetic **Tenun Nusantara** test has the same shape as
Kain (PDF + logo, one photo) but the photo did not count (`hasPic=false`; it arrived under the
1 MB attachment floor after mail-client compression). `hasLogo=true` kept it ready, and the
engine published the draft using the logo as the featured image. This is the `T-024`
attached-photo gap, not a failure of the PDF/Drive/Box route.

## 6. Reproduce a case

The live rows are queryable; the raw data stays in the DB/archive:

```bash
python3 - <<'PY'
import db, json
email_id = "1a15c5a14ead29e2"       # MATRADE
for r in [x for x in db.list_pipeline_results(limit=1000) if x["email_id"] == email_id][:1]:
    print(r["subject"])
    for stage, data in (r["stages"] or {}).items():
        print(stage, data.get("status"), json.dumps(data.get("detail"))[:300])
PY
```

The archived folder is under `all_emails/<subject>/`; the checklist row is in `data/msme.sqlite3`
(`checklist`) and the filter result in `filter_results`. The `filter-history.html` page shows the
Jev gates/scores for a row that reached the filter.
