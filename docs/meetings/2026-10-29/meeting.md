# MSME meeting — 29 Oct 2026, 10:30 MYT, Microsoft Teams

**Audience:** MSME editorial and management
**Goal:** show the flow, explain two disagreements, agree what “relevant” and “publish” mean.

Use simple English. Start with the recording; use the live pages only if needed.

## 1. Open — say this (1 minute)

> “An email arrives. The service reads it, finds the article and the pictures, Jev checks it, and an accepted article becomes a local web page. Today I want to show this, explain two cases you said are not relevant, and agree the rules with you.”

## 2. What to explain (5 minutes)

| Point | Say this |
|---|---|
| Flow | **Receive → Filter → Repurpose → Publish.** Receive finds the article and media. Jev checks it. An accepted article is rewritten and becomes a local page. |
| Receive | The article can come from a PDF, Drive, OneDrive, Box, a public web page, the email body or a Google Doc. |
| Filter | Three safety gates: **royalty, religion, race**. Then a weighted score out of 100. Labels: **fail 3R**, **not relevant**, **needs review**, **accepted**. |
| Live | Webhook, login/roles, editor, filter history, local published page. **149 tests pass.** |
| Not live | WordPress upload. The local page is **staging**, not the MSME site. Old report figures are **not verified**. |
| Numbers | **241** checklist rows, **23** filter results, **19** accepted, **15** local articles. Tenun test: **ACCEPT 78**, validated, first on the local page. |

Seven real email examples (PDF, Drive, OneDrive, Box, web, body, Google Doc) are in
`docs/workflow/RECEIVE-WORKFLOW-7-EMAIL-EXAMPLES.md`.

## 3. Page by page — what to show and what to say (10 minutes)

| Page | What to show | What to say |
|---|---|---|
| **Login** `/login` | Do not show the password. Show the page only if asked. | “Access is local. Admin sees everything; editor sees the editor page and filter config only. Session lasts 7 days.” |
| **Checklist** `/` | The Tenun row and its flags. | “Every email gets one row. The Tenun test is accepted at 78. Article yes, logo yes, ready yes.” |
| **Editor** `/editor.html` | Open the Tenun item. Point at the three chips and **Open local draft**. | “This is the editor view. It says what arrived, what passed, and what is ready. The editor can open the local draft.” |
| **Publish Index** `/repurpose-site/index.html` | The local page; Tenun first. | “This is the local published page. Newest last-publish is first. This is staging; it is not WordPress yet.” |
| **Filter history** `/filter-history.html` | Select Tenun. Show the green/red Jev percentages. | “Each safety gate and each weighted question shows the Jev score. Green is near 100, red is near 0. The result is stored with the exact rubric used.” |
| **Filter config** `/filter-config.html` | The rule editor and the version card. | “Rules are editable. Each save is versioned with who and when. There is no live version yet; the card will fill after the first save.” |
| **Users** `/users.html` | Admin and editor accounts; the audit table. | “Admin manages users. Editor can change filter config only. Every change is logged.” |

**Skip if short:** Users and Config. Do not open `localhost:8765`; the engine dashboard is local only.

## 4. What to mention (8 minutes)

### Two confirmed cases: we accepted, MSME says not relevant

| Case | Our result | Why it passed | Say this |
|---|---|---|---|
| **Ant CEO speech** | ACCEPT **80**; SME 0.86, SME voice 0.74, overall 0.67 | Broad SME question + one Malaysia example + high substance/source. No article-type rule and no minimum SME-relevance floor. | “Same company has a product article you published. The speech is global thought-leadership, not a Malaysian SME development.” |
| **BWH Hotels** | ACCEPT **68**; SME 0.45, SME voice 0.45, overall 0.57 | One Malaysia hotel lifted geography; high substance/source; no SME floor. | “A global hotel brand and loyalty change, not a Malaysian SME story.” |

### The opposite direction — ask them to confirm

> “You also said some articles we rejected should be published. Please name them. Our candidates are these two.”

- **Event Me Now** — filter test **REJECT 79**, commercial intent; it is on the MSME published site.
- **Mercedes-AMG GT Coupés** — filter test **REJECT 59–60**, not SME-relevant / commercial; it is on the MSME published site.

The 5–13 Oct weekly had 7 AI rejects, all editor rejects; the 20-article test has these two published
cases. We need one **gold set** of labelled articles.

### Media — short version

- 20-folder audit: **9 missing the published image**, **7 with no picture**, **5 HEIC files**.
- **11 sender asks** are drafted; not sent.
- **Tenun**: photo did not count (under 1 MB); the logo saved it.
- **Event Me Now**: only a 1×1 tracking pixel in the body; the public page supplied the image.
- **Contributed Article**: Google Doc gave text, no photo/logo → stopped.
- **MSIA**: Drive PDF with download disabled.
- Ask senders for: high-res photo/logo, Drive download on, no tracking pixels, one release per email, exact subject.

## 5. Suggested fixes — for their decision

These are small rule changes in the versioned filter config. **They send the case to editor review; they do not auto-reject.** The editor makes the final call.

| Problem | Suggested fix | Expected effect |
|---|---|---|
| Ant CEO speech was accepted | **Article type:** a speech, op-ed or global thought-leadership piece goes to **editor review**; product/news releases stay as they are. | The Ant speech goes to review; the **Ant product** article stays accepted. |
| BWH was accepted | **SME relevance floor:** `sme_relevance < 0.50` → **editor review**, not a hard reject. | BWH (0.45), AI Muda (0.41) and Egon (0.43) go to review; every current relevant ACCEPT is above 0.50. |
| Global brand / consumer / luxury | **Site-fit review:** global brand, loyalty, consumer or luxury stories → **editor review**; do not hard-reject. | BWH and Mercedes can be judged by the editor; no silent false reject. |
| Event Me Now was rejected in the **older 6-gate test** | **Commercial review band:** a product launch with high source/substance → **editor review**. Do **not** restore the old hard commercial gate. | The published product launch can be reviewed; a hard sell can still be rejected. |
| One Malaysia example made a global story look local | **Local-development check:** one local mention is a **review signal**, not an auto-accept or auto-reject. | Ant/BWH reviewed; a real Malaysia development still accepted. |
| No labels yet | **Feedback loop + gold set:** editor buttons **Relevant / Not relevant / Should publish**; 20–50 labelled emails; every filter change versioned. | We tune from MSME’s own decisions, not guesses. |
| Media gaps | **Media standard:** high-res photo/logo, Drive download on, no tracking pixels, one release; count attached photos by dimensions (T-024), support HEIC. | Fewer “accepted but no image” and no-media stops; the 11 sender asks. |

**The simple message:** “We suggest these small changes: article-type review, an SME
relevance review floor, a site-fit review, a commercial review band, and a feedback loop. None of
these new rules auto-reject; the editor decides. The 3R safety gates still reject.”

## 6. Which rule to improve — and what not to touch

The **live battery is 3 hard gates + 11 weighted scores** (weight sums to 100; accept at 62).
The old 6-gate test (commercial, not-SME, etc.) is **not** the live battery. The 3R gates are
safety and should stay.

| Rule | Weight / type | Problem today | Improve | Evidence |
|---|---:|---|---|---|
| **3R gates** (royalty, religion, race) | 3 hard gates | none | **Keep.** Do not weaken. | Ant and BWH passed them; they are not the false-accept cause. |
| **sme_relevance** | 26 | too broad; BWH 0.45 still accepts | Rewrite the criteria around a **Malaysian SME development/need**, and add a **review floor 0.50** | BWH 0.45, AI Muda 0.41, Egon 0.43; every current relevant ACCEPT is above 0.50 |
| **sme_voice_business_updates** | 7 | rewards “insight or opinion”; a global CEO speech scores 0.74 | Rewrite to **“Malaysian SME business update”**, not opinion. **Do not raise the weight now** | Ant 0.74, BWH 0.45; historical mean 46 |
| **geographic_relevance** | 7 | one Malaysia mention lifts a global story | Require a **real local development/impact**, not a mention; use as a review signal | BWH 0.96, Ant 0.91 |
| **overall_editorial_test** | 12 | low for valid articles too (Setia 0.60, Tenun 0.64, MPUPK 0.62) | **Do not use a hard floor.** Improve the examples and use it with article type as a review signal | A hard floor would review valid articles |
| **commercial_intent** | 10 | the old test hard-rejected Event Me Now | Keep it as a **score**; product launch → review; **no old hard gate** | Event Me Now is on the MSME site |
| **safety_reputation** / **claims_statistics** | 10 / 6 | noisy; Ant safety 0.44 but BWH 0.80 | **No hard gate.** Consider lower weight only after labels | Historical signal was noise (−0.3 / −0.8) |
| **political_advocacy** | 6 | inverted/noise in the old run | **No hard gate.** Review with MSME | Historical −26 separation |
| **New: article type + local development** | review flag | missing | Add a **review flag** for speech/op-ed/global thought leadership and one-example local stories; no auto-reject | Ant speech, BWH; the Ant product stays accepted |

### Improve in this order
1. **Article type + local-development review** — catches Ant/BWH without hurting the Ant product.
2. **`sme_relevance` criteria + 0.50 review floor** — catches BWH and other low-SME items; valid accepts stay above 0.50.
3. **`sme_voice_business_updates` rewrite** — stop rewarding global opinion; keep weight 7 for now.
4. **`geographic_relevance` criteria** — a mention is not a local development.
5. **Feedback loop + gold set** — measure on MSME’s labels before changing any more weights.

### Do not do yet
- Do **not** hard-floor `overall_editorial_test` — too many valid articles are below 0.70.
- Do **not** hard-gate `safety_reputation`, `claims_statistics` or `political_advocacy` — they are noisy in the historical data.
- Do **not** restore the old hard commercial/not-SME gates; use **review** instead.
- Do **not** raise the `sme_voice` weight before the gold set; Kain 0.26 and Tenun 0.27 are valid but low on that question.
- Do **not** change the 3R safety gates.

## 7. What to ask (10 minutes)

> First ask: “We suggest the fixes above. Do you agree with the direction? We can set the thresholds together.”

1. **What does “relevant” mean?** Give us 3 publish and 3 do-not-publish examples; start with Ant and BWH.
2. **SME relevance floor:** below **0.50**, should it go to editor review instead of ACCEPT?
3. **Article type:** should speeches/op-eds/global thought-leadership go to editor review?
4. **Commercial intent:** is a product launch (Event Me Now) acceptable business news?
5. **Consumer/luxury:** is Mercedes-AMG in scope for Malaysia SME?
6. **Media standard:** who sends the 11 asks? Can senders attach a high-res photo/logo and enable Drive download?
7. **Feedback loop:** who marks each article **Relevant / Not relevant / Should publish**, and how often?
8. **WordPress:** site/API, credentials, draft or publish, categories, featured image, author.
9. **Staging:** do you accept the local page as staging until WordPress is connected?

## 8. If they ask

| Question | Answer |
|---|---|
| Why did you accept Ant/BWH? | “The SME question is broad and both mention SMEs or a Malaysia hotel. There is no minimum SME-relevance rule and no article-type rule. That is what we want to fix with you.” |
| Why did you reject Event Me Now / Mercedes? | “In the **older 6-gate test**, the commercial/relevance gate fired first. The **current live battery has only the 3R hard gates**, so these may now be accepted or sent to review. The published site shows some product/consumer stories are in scope; we need your labels.” |
| Is this live on our website? | “No. This is the local staging page. WordPress is the next build; we need your access and target.” |
| Can the system learn? | “Yes — add a simple Relevant / Not relevant / Should publish mark in the editor. Every filter change is versioned.” |
| How accurate is it? | “In the 5–13 Oct test, 13 of 20 editor rejects were accepted; the 20-article test had two published articles rejected. We need a fixed labelled set, not a final accuracy claim.” |

## 9. Close

- Agree the definition of relevant/publish.
- Agree the SME floor and article-type rule; we update the filter as a versioned config.
- Agree the media standard and who sends the asks.
- Agree the feedback loop and a gold set of 20–50 emails.
- MSME provides WordPress access; we build the upload stage.
- Keep the local page as staging.

## 10. PRESENTER ONLY — DO NOT SHOW

- Login is temporary **admin / admin**; change it after the meeting.
- Gmail OAuth is **expired**; the demo uses the existing Tenun article. Do not try a new live email unless you re-authenticate.
- The engine dashboard `:8765` is local; use the app pages. If public DNS is down, use `http://localhost:8899` in screen share.
- Tenun is a **synthetic test**; the local page is **staging**, not WordPress.
- The old report figures are **unverified**.
- The config version card is empty; the first save creates version #1.
- If the recording shows a password, cut or blur it.

## 11. Links

- Seven receive examples: `docs/workflow/RECEIVE-WORKFLOW-7-EMAIL-EXAMPLES.md`
- Workflow: `docs/workflow/WORKFLOW-RECEIVE-TO-PUBLISH.md`
- Historical test: `docs/operations/AI-NEWS-WEEKLY-5-13-OCT.md` · `docs/filter/filter-test-report-20.md`
- Media: `docs/receive/receive_feedback.md` · `docs/operations/NOT-READY-TO-FILTER-2026-10-22.md` · `docs/operations/SENDER-ASKS-2026-10-22.md`
- Ant: filter result **21**, checklist row **411**; BWH: filter result **20**, row **410**
- Ant product (MSME published): `https://www.malaysiasme.com.my/ant-international-unveils-full-stack-ai-native-financial-solutions-for-global-businesses/`
- Event Me Now (MSME published): `https://www.malaysiasme.com.my/malaysian-startup-event-me-now-launches-digital-marketplace-with-zero-booking-commission/`
- Mercedes (MSME published): `https://www.malaysiasme.com.my/mercedes-amg-gt-coupes-bring-v8-power-and-electric-performance-to-malaysia/`
