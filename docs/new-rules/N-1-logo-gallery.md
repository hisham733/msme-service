# N-1 — Logo gallery fallback

_Status: spec for the 2026-11-11 MSME call · 2026-11-05 · **built 2026-11-07** (`msme/receive/gallery.py`, option B)._
_Source: 30-Oct 2026 MSME call `[01:04–06:27]`, `[56:07]`; `docs/meetings/2026-11-09/MEETING-BRIEF-2026-11.md:59`._
_Examples: every rule and method adds a worked example; the one-page cheat sheet is §13._
_Built: hybrid ladder (§6) + option B usable-logo floor (≥200 px or vector) · 259 tests pass · live seed = BPMB + MATRADE logos._

## 1. The rule

An email is usable only when it has **an article and an image**.

The image may be any of:

- a logo attached as a file,
- a logo embedded inside the article PDF/DOCX,
- a photo inside the article PDF/DOCX,
- a body or asset-link image.

**Today:** if no usable image exists, the prototype sends the sender the existing ask email
(“send us a picture/logo”).

**New step:** before that ask email, search the **local gallery for that email's brand**.

- **Found** → use the gallery logo as the article's image; `hasLogo=true`; no ask email.
- **Not found** → send today's ask email, unchanged.

The gallery is **local only**: 10–20 images on the prototype, no WordPress/server access, and no
internet crawl for logos (`[03:55]`, `[04:43]`, `[06:27]`).

### 1.1 Worked example — three emails, three outcomes

**Email A — BPMB release, no image at all (the gallery case).** An agency sends a corporate release;
the release text exists but there is no photo, logo attachment, PDF logo or body image.

```text
From:     Cision <noreply@cision.com>
Subject:  Bank Pembangunan Malaysia Berhad launches RM500m SME fund
Files:    BPMB_SME_Fund_Release.docx      (article text only — no logo/photo inside)
Body:     "...Bank Pembangunan Malaysia Berhad (BPMB) today announced..."
Flags:    has_pic=false  has_logo=false  doc_logo=false  doc_photo=false
Gallery:  index has BPMB with alias "Bank Pembangunan Malaysia Berhad"
          → exact alias in the subject → HIT
Result:   hasLogo=true · readyToFilter=true · no ask email
          image = BPMB_11-November-2026_MALAYSIA-SME.png
```

**Email B — CIMB release, no image, no gallery entry.** Same shape as A, but the index has no CIMB
entry (or only a `pending` one). The gallery is searched and misses; today's ask email is sent
unchanged.

```text
From:     Media OutReach <news@mediaoutreach.com>
Subject:  CIMB launches new SME financing programme
Flags:    has_pic=false  has_logo=false  doc_logo=false  doc_photo=false
Gallery:  the index has no active CIMB entry (only a pending one)
          → nothing to match → MISS
Result:   hasLogo=false · readyToFilter=false · ask email sent
```

**Email C — AFFIN release with a photo inside the PDF (gallery must not run).** Even if the gallery
has an AFFIN logo, the pipeline already has a usable image.

```text
From:     AFFIN Group <news@affin.com>
Subject:  AFFIN SME BizChat 2026 empowers Johor SMEs
Files:    AFFIN_SME_BizChat.pdf            (contains a usable photo)
Flags:    has_pic=true  doc_photo=true
Gallery:  SKIPPED — "has any image" is already true
Result:   uses the supplied photo · no gallery lookup · no ask email
```

**One-line summary:** the gallery is a **last resort before the ask email**, not a replacement for
supplied images.

## 2. Trigger — exactly the ask-email condition

The gallery runs only when the pipeline found **no usable image anywhere**:

```text
not (has_pic or has_logo or doc_logo or doc_photo)
```

This is the same condition behind `msme/receive/reply.py:88` and the pipeline trigger at
`pipeline.py:1234`. It deliberately mirrors today's behaviour, including the current thresholds
(`MIN_IMAGE_BYTES`, `BODY_LOGO_MIN_DIM`).

**Option B — built 2026-11-07.** The trigger uses **`hasUsableLogo`**, not the factual `hasLogo`:
a logo counts only when it is **vector** or its max side is **≥ `BODY_LOGO_MIN_DIM` (200 px)**.
A 40×20 letterhead icon or a `logo.png` under 200 px no longer suppresses the gallery; if the
gallery also misses, the article stays not-ready and the ask email is sent. The factual `hasLogo`
still shows on the checklist, but it does not decide readiness.

| Run state | Gallery |
|---|---|
| article + any image (pic, logo, doc logo/photo, body/asset/web image) | **skipped** |
| article, no image anywhere | **searched** |
| no article | **skipped** — nothing to publish |

### 2.1 Trigger examples (concrete)

“false” below means **no image passed the existing thresholds**, not “no image bytes at all”.

| Email | `has_pic` | `has_logo` | `doc_logo` | `doc_photo` | Gallery? | Why |
|---|---|---|---|---|---|---|
| AFFIN PDF with a 1536×1024 photo | **true** | false | false | true | **skipped** | a supplied photo already exists |
| MATRADE release + `MATRADE-Logo.pdf` attachment | false | **true** | false | false | **skipped** | a logo attachment exists |
| BPMB release, DOCX has a header logo | false | false | **true** | false | **skipped** | the document itself carries a logo |
| BPMB release, text only | false | false | false | false | **searched** | the N-1 case |
| CIMB release, 40×20 tracking pixel in the body | false | false | false | false | **searched** | the pixel is below the image thresholds |
| Email with no article | false | false | false | false | **skipped** | nothing to publish |

**Example of the boundary:** a 250×87 Finnfund logo counted as an image under D24; a 40×20 tracking
pixel did not. The gallery follows whatever the existing thresholds decided — it does not re-judge
images.

## 3. Where it runs

Between the logo scan and Verify in `msme/receive/pipeline.py`:

- after `has_logo` is computed (`pipeline.py:1213`),
- before `verify.verify(...)` (`:1290`),
- before the archive dicts (`:1421`, `:1451`) so the gallery logo is archived with the article,
- before the ready/reply decision (`:1320` readiness, `:1577` reply).

A gallery hit adds the file as `gallery_logos[...]`, sets `has_logo = True`, and records a
`stages["gallery"]` entry. The existing ready→filter→reply logic then needs no special case.

Gallery failures (missing index, unreadable file, bad JSON) must never fail the run; they record
`gallery: error` and the pipeline continues to the ask email.

### 3.1 Worked pipeline order — the BPMB email

```text
decide → collect → extract → logo_scan → [GALLERY] → verify → archive → ready/reply
                                      has_logo=false   hit BPMB   hasLogo=true
```

| Stage | Before the gallery | After the gallery |
|---|---|---|
| `logo_scan` | `has_logo=false` (no logo found in the email/document) | unchanged |
| `gallery` | not run | `has_logo=true`; `gallery_logos=["BPMB_11-November-2026_MALAYSIA-SME.png"]` |
| `verify` | would see no logo | sees the deterministic `has_logo=true` evidence |
| `archive` | would archive only the article | also archives the gallery file |
| `ready/reply` | would send the ask email | `readyToFilter=true`; **no ask email** |

**The three `stages["gallery"]` shapes:**

```text
// hit
"gallery": {"status": "hit", "detail": {
  "brand": "BPMB", "tier": 1, "field": "sender_domain",
  "alias": "bpmb.com.my", "score": 100,
  "file": "BPMB_11-November-2026_MALAYSIA-SME.png"}}

// miss (searched, no confident match → ask email continues)
"gallery": {"status": "miss", "detail": {
  "reason": "no alias matched", "best_score": 45,
  "candidates": ["CIMB", "Maybank"]}}

// error (never fails the run)
"gallery": {"status": "error", "detail": {"error": "index.json not found"}}
```

**Counter-example — an error must not send a false “ready”:** if `index.json` is unreadable, the
pipeline records `gallery: error`, keeps `hasLogo=false`, and reaches the normal ask-email branch.
It must **not** crash and must **not** pretend a logo was found.

## 4. Match criteria — the two proposals

### 4.1 Weighted signals

| Signal | Weight |
|---|---|
| subject / headline | 35 |
| sender name + email domain | 35 |
| attachment filenames | 20 |
| first ~600 chars of body | 10 |
| **threshold** | **70** |

**What this means arithmetically:** only **subject + sender** reach 70.

| Fields matched | Total | Hit? |
|---|---|---|
| subject + sender | 70 | yes |
| subject + attachments + body | 65 | no |
| sender + attachments + body | 65 | no |
| subject + attachments | 55 | no |
| subject + body | 45 | no |

#### 4.1.1 Worked arithmetic — six real shapes

| Email | Subject 35 | Sender 35 | Files 20 | Body 10 | Total | Hit? |
|---|---:|---:|---:|---:|---:|---|
| BPMB direct: subject “Bank Pembangunan Malaysia…”, from `@bpmb.com.my` | 35 | 35 | 0 | 0 | **70** | **yes** |
| BPMB via Cision: subject has the alias, file `BPMB_Release.docx`, body has BPMB | 35 | 0 | 20 | 10 | **65** | **no** |
| BPMB via Cision: subject alias + one body mention | 35 | 0 | 0 | 10 | **45** | **no** |
| AFFIN direct: subject + `@affin.com` + `AFFIN_Release.pdf` + body | 35 | 35 | 20 | 10 | **100** | **yes** |
| MATRADE via agency: subject + `MATRADE_Release.pdf` + body | 35 | 0 | 20 | 10 | **65** | **no** |
| Unknown brand: no signal | 0 | 0 | 0 | 0 | **0** | **no** |

**The agency trap in one line:** an exact brand in the subject is only **35**, and the sender domain is
the agency, so the two strongest fields do **not** add up to 70.

**The CIMB–Maybank trap:** a joint release from CIMB whose subject names both “CIMB” and “Maybank”
scores **35 (subject) + 35 (CIMB sender) = 70 → hit CIMB**, even though Maybank is equally named. This
method has **no ambiguity guard**, so it can return the wrong brand.

**Undefined case:** if the subject contains both “CIMB” and “Maybank”, does the subject score 35 once
(all-or-nothing) or 35 for each brand (partial)? The spec does not say. Example:

```text
all-or-nothing: subject=35 (one signal) + sender=35 → 70 → CIMB hit
partial:        subject=35 for CIMB and 35 for Maybank + sender=35 for CIMB
                → CIMB 70, Maybank 35 → still CIMB, but the numbers no longer mean one thing
```

**Problem:** PR agencies send on behalf of brands. For an agency-sent release (Cision, Media OutReach,
vritimes), the subject may name the brand but the sender domain is the agency → 45 → **miss**, even
with an exact brand in the subject. That is one of N-1's main cases.

Also undefined: whether each field scores all-or-nothing or partially, and whether the 35 for
“sender name + domain” is split between display name and domain.

### 4.2 Priority — direct match

Use the first rule that matches; a direct match is used immediately.

1. Sender domain is registered to a brand → use it.
2. Exact alias in subject/headline → use it.
3. Exact alias in the sender display name → use it.
4. Exact alias in an attachment filename **and** in the body → use it.
5. Exact alias in the first 600 chars **and** at least twice in the body → use it.
6. Otherwise → miss.
7. Two different brands at the same tier → **miss** (ambiguous → ask the sender).

“Exact” = case/punctuation-normalised, whole-word, alias ≥ 3 characters.

#### 4.2.1 Worked examples — one email per tier

| Tier | Example email | What matched | Result |
|---:|---|---|---|
| 1 | `news@bpmb.com.my` → “BPMB…”; index `domains:["bpmb.com.my"]` | sender domain | **BPMB hit** |
| 2 | Cision sender, subject “Bank Pembangunan Malaysia Berhad launches…” | exact alias in subject | **BPMB hit** |
| 3 | “Maybank Newsroom `<news@agency.com>`”, subject generic | exact alias in display name | **Maybank hit** |
| 4 | `CIMB_SME_Release.pdf` + body “CIMB today…” | attachment filename **and** body | **CIMB hit** |
| 5 | sender generic, body “AFFIN” in the first 600 chars and 3× total | alias in first 600 chars + ≥2× in body | **AFFIN hit** |
| 6 | subject “May Bank announces…”, index alias “Maybank”, single top | fuzzy 0.95 | **Maybank hit** |
| 7 | subject “CIMB and Maybank launch…”, sender CIMB, both aliases exact | two brands at the same tier | **miss** (ask sender) |

**Normalisation examples:**

| Text | Alias | Exact? | Why |
|---|---|---|---|
| `BPMB,` | `BPMB` | **yes** | trailing punctuation is normalised away |
| `CIMB Bank` | `CIMB` | **yes** | `CIMB` is a whole word inside the phrase |
| `May Bank` | `Maybank` | **no** (fuzzy 0.95) | a space is not punctuation; this is a fuzzy case |
| `B.P.M.B.` | `BPMB` | **yes** under punctuation-normalisation | dots are removed; confirm in the matcher |
| `AB` | `AB` | **no** | alias shorter than 3 characters |
| `CIMB` | `CIMB Bank` | **no** | the alias is longer than the text (no partial credit here) |

**Ambiguity example:** a joint CIMB–Maybank release from CIMB reaches tier 2 for “CIMB” and tier 2 for
“Maybank”; both are exact, so tier 7 fires → **miss**, even though CIMB is the sender. The ask email is
safer than publishing either logo.

## 5. Other matching methods considered

| Method | Value | Cost / risk |
|---|---|---|
| **Domain map** (`domains` in the index) | strongest, cheapest: `bpmb.com.my → BPMB` | agency domains must never be mapped |
| **Two-key rule** | one strong signal + one corroborating signal | slightly stricter than a ladder |
| **Fuzzy match** (`difflib.SequenceMatcher`, stdlib) | “May Bank” vs “Maybank”, “CIMB” vs “CIMB Bank” | secondary only; never enough alone |
| **Multi-brand guard** | if 2+ brands score closely, no hit | avoids Maybank in a CIMB–Maybank article |
| **Learned sender cache** | after a hit, store domain → gallery file; next time direct | small store, improves repeat senders |
| **Alias quality score** | longer/specific aliases outrank short/generic ones | replaces arbitrary fixed weights |
| **Image pHash** | compare a supplied logo to gallery images | needs Pillow; the no-image case has nothing to compare → not v1 |
| **Token overlap / TF-IDF** | brand + event/date tags together | heavier; unnecessary for 10–20 images |

### 5.1 Examples in practice

- **Domain map.** `news@bpmb.com.my` → `bpmb.com.my → BPMB` → direct hit. `noreply@cision.com` is an
  agency: it is **never** mapped (it would make every Cision email look like one brand).
- **Two-key rule.** Cision sender + subject “BPMB launches…” + body “BPMB” → subject alias **and** body
  alias → hit. Same email with the brand only in the subject, never in the body → **miss**.
- **Fuzzy match.** “May Bank” vs “Maybank” ≈ **0.95** → can hit when it is the single top candidate.
  “CIMB” vs “CIMB Bank” may score lower (≈0.82) → **not enough alone**.
- **Multi-brand guard.** A joint CIMB–Maybank release: both brands score closely → **no hit** (ask the
  sender). A CIMB-only release: CIMB far ahead → **CIMB hit**.
- **Learned sender cache.** First Cision AFFIN email hits → store **`(cision.com, "AFFIN") → AFFIN`**,
  never `cision.com → AFFIN` alone; the next Cision email about MATRADE must not reuse AFFIN.
- **Alias quality.** “Bank Pembangunan Malaysia Berhad” is a stronger alias than “BPMB”; both point to
  the same file, but the long one is less likely to collide with another brand. A short generic alias
  such as “SME” must not be an alias at all.
- **Image pHash.** A supplied CIMB logo can be compared to the gallery CIMB logo; it is useful for
  **verifying a supplied image**, not for N-1 (the N-1 email has no image to compare).
- **Token overlap / TF-IDF.** “BPMB” + “SME fund” + “November 2026” together can separate a BPMB
  release from a generic SME story; for 10–20 images the simpler signals above are enough.

## 6. Recommended matching — hybrid priority ladder

A **miss** only sends the ask email (safe). A **false hit** publishes the wrong logo (bad). Bias
conservative.

Index entries gain a `domains` list:

```json
"brand": "BPMB",
"aliases": ["Bank Pembangunan Malaysia", "Bank Pembangunan Malaysia Berhad"],
"domains": ["bpmb.com.my"]
```

Match order:

1. sender domain in `domains` → hit,
2. exact alias in subject/headline → hit,
3. exact alias in sender display name → hit,
4. exact alias in an attachment filename **and** the body → hit,
5. exact alias in the first 600 chars **and** ≥ 2× in the body → hit,
6. fuzzy match ≥ 0.88 in subject/sender → hit only if it is the single top candidate,
7. ambiguity (2 brands within 10 points) → **miss**.

The `gallery` stage records `alias`, `field`, `tier`, `score`, `file`, so the call can review a match
without guessing, and the weights can be tuned later from real runs.

### 6.1 Full worked match — five emails

| # | Email | Walk down the ladder | Result |
|---:|---|---|---|
| 1 | `news@bpmb.com.my`, subject “BPMB SME fund” | tier 1: `bpmb.com.my` in `domains` | **hit, tier 1** |
| 2 | Cision, subject “Bank Pembangunan Malaysia Berhad launches…” | tier 1 no; tier 2: exact alias in subject | **hit, tier 2** |
| 3 | sender generic, body “AFFIN” in the first 600 chars and 3× total | tiers 1–4 no; tier 5: alias in first 600 chars + ≥2× body | **hit, tier 5** |
| 4 | subject “May Bank announces…”, alias “Maybank”, single top | tiers 1–5 no; tier 6: fuzzy 0.95 | **hit, tier 6** |
| 5 | subject “CIMB and Maybank launch…”, sender CIMB | tier 2 for both brands; scores within 10 → tier 7 | **miss (ambiguous)** |

**The exact records the page would store:**

```text
// 1 — direct domain
"gallery": {"status": "hit", "detail": {
  "brand": "BPMB", "tier": 1, "field": "sender_domain",
  "alias": "bpmb.com.my", "score": 100,
  "file": "BPMB_11-November-2026_MALAYSIA-SME.png"}}

// 2 — exact alias in the subject (agency sender)
"gallery": {"status": "hit", "detail": {
  "brand": "BPMB", "tier": 2, "field": "subject",
  "alias": "Bank Pembangunan Malaysia Berhad", "score": 100,
  "file": "BPMB_11-November-2026_MALAYSIA-SME.png"}}

// 3 — alias in the first 600 chars + body repetition
"gallery": {"status": "hit", "detail": {
  "brand": "AFFIN", "tier": 5, "field": "body",
  "alias": "AFFIN", "lead_chars": 600, "occurrences": 3,
  "score": 80, "file": "AFFIN-Group_November_2026_MALAYSIA-SME.jpg"}}

// 4 — fuzzy
"gallery": {"status": "hit", "detail": {
  "brand": "Maybank", "tier": 6, "field": "subject",
  "alias": "Maybank", "matched_text": "May Bank", "score": 0.95,
  "file": "Maybank_2026_MALAYSIA-SME.png"}}

// 5 — ambiguity: no logo is published
"gallery": {"status": "miss", "detail": {
  "reason": "ambiguous", "tier": 7,
  "brands": ["CIMB", "Maybank"], "scores": [100, 100]}}
```

**Known agencies:** `cision.com`, `mediaoutreach.com`, `vritimes.com`. These are **never** in a brand's
`domains` list (an agency domain must never map to a brand). Tier 5 no longer requires an agency sender
— an exact alias in the first 600 chars plus two body mentions is enough (§4.2), so a forwarded editor
email whose release text names the brand also matches.

### 6.2 Built implementation (2026-11-07)

| Part | Code | Notes |
|---|---|---|
| Matcher | `msme/receive/gallery.py` | `load_index`, `match`, `pick`; no AI, no network |
| Pipeline stage | `msme/receive/pipeline.py` | after `logo_scan`, before `verify`; `stages["gallery"]` |
| Path | `msme/paths.py` | `paths.GALLERY = data/gallery` |
| Config | `msme/config.py` | `GALLERY_ENABLED`, `GALLERY_DIR`, `GALLERY_INDEX`, `GALLERY_MAX_FILE_BYTES`, `GALLERY_FUZZY_MIN`, `GALLERY_AGENCY_DOMAINS` |
| Admin CLI | `tools/gallery_admin.py` | `check` (dry-run) and `add` (copy + index) |
| Tests | `tests/test_gallery.py` | 18 tests: every tier, ambiguity, pending/superseded, path traversal, option B |

**Scores and ambiguity:** tier 1=100, 2=95, 3=90, 4=85, 5=80, 6=fuzzy×100. If the top two **brands**
are within **10 points**, the result is a **miss** (e.g. CIMB sender domain 100 vs Maybank subject 95
→ miss). This is deliberately conservative: a miss only asks the sender, a false hit publishes the
wrong logo.

**Option B in code:** the trigger is `hasUsableLogo` = vector or max side ≥ 200 px. A tiny
`logo.png` or a 40×20 DOCX icon is still `hasLogo=true` on the checklist but no longer counts as a
usable image; the gallery runs, and if it misses the article is not ready.

**Live seed:** `data/gallery/` has **BPMB** (`BPMB_11-November-2026_MALAYSIA-SME.png`) and
**MATRADE** (`MATRADE_07-November-2026_MALAYSIA-SME.png`), both `active`, with their aliases and
domains. Add the rest with:
`python3 tools/gallery_admin.py add --file … --brand … --aliases … --domain …`.

## 7. Gallery store

- Path: `data/gallery/` (gitignored live data; already mounted into Docker as `./data`).
- Index: `data/gallery/index.json`.
- Files: the images themselves, named per **AG-05**.

```json
{
  "version": 1,
  "updated": "2026-11-05",
  "images": [
    {
      "id": "bpmb-logo-2026-11",
      "brand": "BPMB",
      "aliases": ["Bank Pembangunan Malaysia", "Bank Pembangunan Malaysia Berhad"],
      "domains": ["bpmb.com.my"],
      "type": "logo",
      "file": "BPMB_11-November-2026_MALAYSIA-SME.png",
      "updated": "2026-11-11",
      "status": "active",
      "source": "MSME gallery"
    }
  ]
}
```

- `type`: `logo` (used by N-1) or `photo` (schema ready; not used by the fallback).
- `status`: `active` (usable), `pending` (captured by N-2, not used), `superseded` (replaced by a newer
  logo). N-1 matches **only** `active` entries.
- Logo filenames carry the date so a newer logo supersedes an older one (`[76:01]`, AG-05).
- Path resolution stays inside `data/gallery/`; `..` and absolute paths are rejected.
- Any error → no hit, run continues.

### 7.1 A five-entry index and which entry matches

```json
{
  "version": 1,
  "updated": "2026-11-07",
  "images": [
    {
      "id": "bpmb-logo-2026-11", "brand": "BPMB",
      "aliases": ["Bank Pembangunan Malaysia", "Bank Pembangunan Malaysia Berhad", "BPMB"],
      "domains": ["bpmb.com.my"], "type": "logo",
      "file": "BPMB_11-November-2026_MALAYSIA-SME.png",
      "updated": "2026-11-11", "status": "active"
    },
    {
      "id": "cimb-logo-2026-05", "brand": "CIMB",
      "aliases": ["CIMB Bank", "CIMB Group"],
      "domains": ["cimb.com"], "type": "logo",
      "file": "CIMB-Logo_May_2026_MALAYSIA-SME.jpg",
      "updated": "2026-05-01", "status": "active"
    },
    {
      "id": "maybank-logo-2026", "brand": "Maybank",
      "aliases": ["Malayan Banking", "Maybank Berhad"],
      "domains": ["maybank.com"], "type": "logo",
      "file": "Maybank_2026_MALAYSIA-SME.png",
      "updated": "2026-06-01", "status": "active"
    },
    {
      "id": "matrade-logo-2026-11", "brand": "MATRADE",
      "aliases": ["Malaysia External Trade Development Corporation"],
      "domains": ["matrade.gov.my"], "type": "logo",
      "file": "MATRADE-in-orange_November_2026_MALAYSIA-SME.png",
      "updated": "2026-11-07", "status": "pending"
    },
    {
      "id": "affin-logo-2025", "brand": "AFFIN",
      "aliases": ["Affin Bank", "AFFIN Group"],
      "domains": ["affin.com"], "type": "logo",
      "file": "AFFIN_2025_MALAYSIA-SME.png",
      "updated": "2025-12-01", "status": "superseded"
    }
  ]
}
```

| Email | Entry that matches | Status | N-1 result |
|---|---|---|---|
| `news@bpmb.com.my` | BPMB | `active` | **hit** — `BPMB_11-November-2026…` |
| Cision + “CIMB Bank launches…” | CIMB | `active` | **hit** — `CIMB-Logo_May_2026…` |
| Cision + “MATRADE at FoodExpo…” | MATRADE | `pending` | **miss** — N-1 uses `active` only; N-2 captures the update |
| Cision + “AFFIN Group…” | AFFIN | `superseded` | **miss** — the old logo is not used; ask for/await the new one |
| “CIMB and Maybank launch…” | CIMB **and** Maybank | both `active` | **miss** — ambiguous (tier 7) |

**Path examples (all resolved under `data/gallery/`):**

| `file` value | Result | Why |
|---|---|---|
| `BPMB_11-November-2026_MALAYSIA-SME.png` | **allowed** | a plain filename |
| `logos/BPMB_2026.png` | **allowed** | a subfolder still inside the gallery |
| `../creds/gmail.json` | **rejected** | `..` escapes the gallery |
| `/etc/passwd` | **rejected** | absolute path |
| `C:\logos\bpmb.png` | **rejected** | absolute Windows path |

## 8. Evidence from the live website (2026-11-05)

The five newest posts on `malaysiasme.com.my` use a **photo or screenshot** as masthead, not a brand
logo:

| Post | Masthead | Brand logo | N-1 result |
|---|---|---|---|
| “Toifie Queen” Crystal Lim | `image-23-1024x500.jpeg` | none | **skipped** — a photo exists |
| Puteri Irene / TalentCorp WIN | `image-3-1500x500.png` | none | **skipped** — a photo exists |
| Chloe’s Theory 13 | `image-2-613x500.png` | none | **skipped** — a photo exists |
| AiSED Conference 2026 | `Screenshot-2026-11-03-at-6.39.55-PM…png` | only inside screenshots | **skipped** — the screenshot is the image |
| MECA IR Convention 2026 | `Convention_DharmenS-scaled…jpg` | none | **skipped** — a photo exists |

**Counter-example from the same site:** a corporate release with **no masthead image at all** (e.g. a
BPMB text-only release) has `has_pic=false`, `has_logo=false`, `doc_logo=false`, `doc_photo=false` →
the gallery **is** searched; the BPMB gallery file is used and the article is published with the logo
as its image.

The **logo-as-masthead** pattern appears on corporate releases lower on the same page, and those files
follow AG-05: `CIMB-Logo_May_2026_MALAYSIA-SME.jpg`, `Red-Hat-logo_SEPTEMBER_2026_MALAYSIA-SME.png`,
`SME-Bank-Subsidiary-Logo-ENG`, `world-bank-group-logo`, `Capbay_OCTOBER_2026_MALAYSIA-SME`,
`INNOTRANS_MALAYSIA-SME_OCTOBER_2026`.

So the 5 newest posts would never trigger the gallery (they already have a photo); the gallery's real
case is a corporate release with no image. The BPMB **logo-update** email is N-2's `library_update`
case, not N-1: it brings a new asset, while N-1 fills a missing image on an article.

## 9. Questions for MSME (2026-11-11)

Recorded in `docs/meetings/2026-10-30/NEXT_MEETING.md` §2.

1. **How do you match a logo to an article on your side?** What signals do you use — brand tag, event
   name, date, sender, something else? Who does the matching?
2. **What naming convention do you use for gallery files?** Does it follow brand + month + year +
   `MALAYSIA-SME`, with the date only for logos (`[75:32]`, `[76:28]`)?
3. **What does the library look like?** Structure, fields/tags, file types, how many images, and
   whether logos and photos are in the same library (`[08:18]`, `[06:58]`).
4. **Can we take a copy of it, or do we get access to it?** A zip export, a read-only API, or
   WordPress access? How often would it need refreshing?

## 10. Open decisions before coding

1. Match scheme: **A** weighted 35/35/20/10 at 70 · **B** priority ladder ·
   **C (recommended)** priority ladder + domain map + ambiguity guard.
2. May each entry carry a `domains` list?
3. Demo seed source: **A** 3–5 real logos already in `all_emails/` · **B** wait for MSME's pack ·
   **C** random placeholders.

### 10.1 What each option would do on the same BPMB email

Input: Cision sender, subject “Bank Pembangunan Malaysia Berhad launches…”, file
`BPMB_Release.docx`, body mentions BPMB twice, no image.

| Option | Walk | Result |
|---|---|---|
| **A** weighted 35/35/20/10 | subject 35 + sender 0 + files 20 + body 10 = **65** | **miss** → ask email |
| **B** priority ladder | tier 2: exact alias in subject | **hit** → BPMB logo |
| **C** hybrid (recommended) | tier 2 hit; domain map and ambiguity guard still apply | **hit** → BPMB logo |

**Demo seed examples:**

- **A — 3–5 real logos from `all_emails/`.** Use BPMB, CIMB, Maybank, MATRADE, AFFIN (the files already
  exist in the archive). Example: seed BPMB and CIMB, then run the BPMB email → hit; run a DHL email →
  miss.
- **B — wait for MSME's pack.** No demo hit until the pack arrives; the N-1 test uses a synthetic
  `index.json` with a test logo.
- **C — random placeholders.** A placeholder called “logo-1.png” with alias “BPMB” still works for the
  mechanics, but it can create a **false hit** if the alias is real and the image is not; label it
  clearly as a placeholder.

## 11. Test plan (when built)

| Branch | Assertion |
|---|---|
| image present | gallery **skipped** |
| no image + brand match | `hasLogo=true`, `readyToFilter=true`, gallery logged, **no ask email** |
| no image + no match | `hasLogo=false`, ask email unchanged |
| ambiguous brands | no hit |
| missing/corrupt index | no hit, no exception |
| path traversal | rejected |

### 11.1 Fixtures and expected values

```text
tests/repurpose/fixtures/gallery/
  index.json                 # BPMB (active), CIMB (active), Maybank (active), MATRADE (pending)
  BPMB_test.png
  CIMB_test.png
  Maybank_test.png
```

Example `index.json`:

```json
{
  "version": 1,
  "images": [
    {"id": "bpmb-test", "brand": "BPMB",
     "aliases": ["Bank Pembangunan Malaysia", "Bank Pembangunan Malaysia Berhad", "BPMB"],
     "domains": ["bpmb.com.my"], "type": "logo", "file": "BPMB_test.png", "status": "active"},
    {"id": "cimb-test", "brand": "CIMB", "aliases": ["CIMB Bank", "CIMB"],
     "domains": ["cimb.com"], "type": "logo", "file": "CIMB_test.png", "status": "active"},
    {"id": "maybank-test", "brand": "Maybank", "aliases": ["Maybank", "Malayan Banking"],
     "domains": ["maybank.com"], "type": "logo", "file": "Maybank_test.png", "status": "active"},
    {"id": "matrade-test", "brand": "MATRADE",
     "aliases": ["Malaysia External Trade Development Corporation"],
     "domains": ["matrade.gov.my"], "type": "logo", "file": "MATRADE_test.png", "status": "pending"}
  ]
}
```

| # | Email input | Expected |
|---:|---|---|
| 1 | AFFIN PDF with a photo | `gallery` **not called**; `hasLogo` from the supplied photo |
| 2 | Cision, subject “Bank Pembangunan Malaysia Berhad launches…” | `hit` tier 2 · `hasLogo=true` · **no reply** |
| 3 | `news@bpmb.com.my`, generic subject | `hit` tier 1 · file `BPMB_test.png` |
| 4 | Cision, subject “CIMB and Maybank launch…” | `miss` (tier 7) · `hasLogo=false` · reply sent |
| 5 | Cision, subject “MATRADE at FoodExpo…” | `miss` (MATRADE is `pending`) · reply sent |
| 6 | `file` set to `../creds/gmail.json` | path rejected · `miss`/`error` · no exception |
| 7 | `index.json` deleted | `error` · `hasLogo=false` · reply sent · no exception |

Expected stage for case 2:

```json
"gallery": {"status": "hit", "detail": {
  "brand": "BPMB", "tier": 2, "field": "subject",
  "alias": "Bank Pembangunan Malaysia Berhad", "score": 100,
  "file": "BPMB_test.png"}}
```

Proving run: `python3 -m compileall -q msme run.py tools tests` +
`python3 -m unittest discover -s tests -p 'test_*.py'` → **259 tests pass** (8 skipped).

## 12. Code touchpoints (built 2026-11-07)

| File | Change | State |
|---|---|---|
| `msme/receive/gallery.py` | index load, hybrid matcher, safe file read; no AI, no network | **built** |
| `msme/receive/pipeline.py` | `gallery` stage, `gallery_logos`, archive inclusion, option B trigger | **built** |
| `msme/paths.py` | `GALLERY` directory | **built** |
| `msme/config.py` | `GALLERY_ENABLED`, `GALLERY_DIR`, `GALLERY_INDEX`, `GALLERY_MAX_FILE_BYTES`, `GALLERY_FUZZY_MIN`, `GALLERY_AGENCY_DOMAINS` | **built** |
| `msme/receive/reply.py` | asks for an image when `hasUsableLogo=false` | **built** |
| `tools/gallery_admin.py` | `check` and `add` | **built** |
| `tests/test_gallery.py` | 18 matcher/option-B tests | **built** |

### 12.1 Example matcher (pseudocode, not built)

```python
def match_email(email, index):
    """email: {subject, from_name, from_email, filenames: [...], body}
       index: {"images": [{brand, aliases: [...], domains: [...], file, status}]}
    """
    entries = [e for e in index["images"] if e.get("status") == "active"]
    domain = email["from_email"].split("@")[-1].lower()

    # 1. sender domain is registered to a brand
    for e in entries:
        if domain in [d.lower() for d in e.get("domains", [])]:
            return hit(e, tier=1, field="sender_domain", alias=domain)

    # 2. exact alias in the subject/headline
    for e in entries:
        for alias in e.get("aliases", []):
            if whole_word(email["subject"], alias):
                return hit(e, tier=2, field="subject", alias=alias)

    # 3. exact alias in the sender display name
    for e in entries:
        for alias in e.get("aliases", []):
            if whole_word(email["from_name"], alias):
                return hit(e, tier=3, field="sender_name", alias=alias)

    # 4. exact alias in a filename AND in the body
    for e in entries:
        for alias in e.get("aliases", []):
            if any(whole_word(f, alias) for f in email["filenames"]) and whole_word(email["body"], alias):
                return hit(e, tier=4, field="filename+body", alias=alias)

    # 5. exact alias in the first 600 chars AND >=2x in the body (any sender)
    lead = email["body"][:600]
    for e in entries:
        for alias in e.get("aliases", []):
            if whole_word(lead, alias) and count_whole_word(email["body"], alias) >= 2:
                return hit(e, tier=5, field="body", alias=alias)

    # 6. fuzzy >=0.88 in the subject/display name, single top candidate only
    candidates = fuzzy_candidates(email, entries, cutoff=0.88)
    if len(candidates) == 1:
        return hit(candidates[0].entry, tier=6, field=candidates[0].field,
                   alias=candidates[0].alias, score=candidates[0].score)

    # 7. two brands within 10 points -> ambiguous -> miss
    if ambiguous(candidates, window=10):
        return {"status": "miss", "detail": {"reason": "ambiguous",
                                             "brands": [c.entry["brand"] for c in candidates]}}

    return {"status": "miss", "detail": {"reason": "no confident match"}}


def hit(entry, **detail):
    return {"status": "hit", "detail": {**detail, "brand": entry["brand"],
                                        "file": entry["file"]}}
```

Example calls:

```python
match_email({"subject": "Bank Pembangunan Malaysia Berhad launches...",
             "from_email": "noreply@cision.com", "from_name": "Cision",
             "filenames": ["BPMB_Release.docx"], "body": "... BPMB ..."},
            index)
# -> {"status":"hit","detail":{"brand":"BPMB","tier":2,"field":"subject",
#                              "alias":"Bank Pembangunan Malaysia Berhad",
#                              "file":"BPMB_11-November-2026_MALAYSIA-SME.png"}}

match_email({"subject": "CIMB and Maybank launch...",
             "from_email": "news@cimb.com", "from_name": "CIMB",
             "filenames": [], "body": "CIMB and Maybank ..."}, index)
# -> {"status":"miss","detail":{"reason":"ambiguous","brands":["CIMB","Maybank"]}}
```

## 13. Quick reference — copy/paste examples

### 13.1 If this, then that

| Email looks like | Index has | N-1 does |
|---|---|---|
| `news@bpmb.com.my` + BPMB release | BPMB `active` | **hit** (tier 1) |
| Cision + subject “Bank Pembangunan Malaysia Berhad…” | BPMB `active` | **hit** (tier 2) |
| Cision + subject “MATRADE at FoodExpo…” | MATRADE `pending` | **miss** → ask email |
| Cision + subject “AFFIN Group…” | AFFIN `superseded` | **miss** → ask email |
| Cision + subject “CIMB and Maybank…” | both `active` | **miss** (ambiguous) |
| “May Bank” + index alias “Maybank” | Maybank `active` | **hit** (tier 6, fuzzy 0.95) |
| PDF already contains a photo | any | **skipped** — gallery not called |
| No article | any | **skipped** — nothing to publish |
| `index.json` missing | — | `gallery: error` → ask email; no crash |

### 13.2 Four example emails and their expected result

```text
// 1 — direct domain
{"from_email":"news@bpmb.com.my","from_name":"BPMB","subject":"BPMB SME fund",
 "filenames":[],"body":"..."}
// expected: hit tier 1, BPMB_11-November-2026_MALAYSIA-SME.png

// 2 — agency + subject alias
{"from_email":"noreply@cision.com","from_name":"Cision",
 "subject":"Bank Pembangunan Malaysia Berhad launches RM500m SME fund",
 "filenames":["BPMB_Release.docx"],"body":"... BPMB ..."}
// expected: hit tier 2, BPMB_11-November-2026_MALAYSIA-SME.png

// 3 — ambiguity
{"from_email":"news@cimb.com","from_name":"CIMB",
 "subject":"CIMB and Maybank launch a joint SME programme",
 "filenames":[],"body":"CIMB and Maybank ..."}
// expected: miss (tier 7: CIMB and Maybank both exact)

// 4 — pending entry
{"from_email":"noreply@mediaoutreach.com","from_name":"Media OutReach",
 "subject":"MATRADE debuts at FoodExpo Qazaqstan 2026",
 "filenames":["MATRADE_Release.pdf"],"body":"... MATRADE ..."}
// expected: miss (MATRADE is pending; N-1 matches active only)
```

### 13.3 The `gallery` stage — three copy/paste records

```text
{"status":"hit","detail":{"brand":"BPMB","tier":1,"field":"sender_domain",
 "alias":"bpmb.com.my","score":100,
 "file":"BPMB_11-November-2026_MALAYSIA-SME.png"}}

{"status":"miss","detail":{"reason":"ambiguous","tier":7,
 "brands":["CIMB","Maybank"],"scores":[100,100]}}

{"status":"error","detail":{"error":"index.json not found"}}
```

### 13.4 Planned CLI (`tools/gallery_admin.py`)

```bash
# dry-run a match without writing anything
python3 tools/gallery_admin.py check \
  --from "noreply@cision.com" \
  --subject "Bank Pembangunan Malaysia Berhad launches RM500m SME fund" \
  --body "Bank Pembangunan Malaysia Berhad (BPMB) today announced..."

# expected
# {"hit": true, "brand": "BPMB", "tier": 2, "field": "subject",
#  "file": "BPMB_11-November-2026_MALAYSIA-SME.png"}

# add a new logo to the index (N-2 will do this automatically later)
python3 tools/gallery_admin.py add \
  --file BPMB_11-November-2026_MALAYSIA-SME.png \
  --brand BPMB \
  --aliases "BPMB,Bank Pembangunan Malaysia,Bank Pembangunan Malaysia Berhad" \
  --domain bpmb.com.my \
  --type logo
```

### 13.5 The smallest useful gallery index

```json
{
  "version": 1,
  "images": [
    {"id": "bpmb-1", "brand": "BPMB", "aliases": ["Bank Pembangunan Malaysia", "BPMB"],
     "domains": ["bpmb.com.my"], "type": "logo", "file": "BPMB_11-November-2026_MALAYSIA-SME.png",
     "status": "active"}
  ]
}
```

With only this entry: the BPMB direct email and the Cision BPMB email **hit**; the CIMB, MATRADE and
AFFIN emails **miss** and continue to the ask email.
