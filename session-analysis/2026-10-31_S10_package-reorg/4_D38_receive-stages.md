# 4 — D38 · receive stages + "what suggests means"

## 1. What was added

**`docs/MEDIA-SOURCE-DECISION.md`** — new section **"What 'suggests' means — and what actually acts"**:

- the decide answer has eleven fields but **only two change behaviour** (`chosenFileName`,
  `linkToFetch` after the guard); the rest are recorded for `/flow.html`;
- **suggestion is not permission** — the pipeline scans every real link; the decide link only gets
  priority (proved by #JomLokal's Box and APAC's web page still running);
- a seven-email table of what decide suggested, its confidence, and what still ran;
- two full mini-examples (MATRADE followed, #JomLokal did not exclude the other source);
- four "when the suggestion is ignored" rules (invented URL, tracking URL, low confidence, wrong
  fetcher guess).

**`docs/RECEIVE-STAGES-EXPLAINED.md`** (new, 238 lines) — the receive stage **point by point**:

- all eleven stages in order, each with what it does, its code and its output;
- for every stage, a table of the same stage across the seven emails, showing why the result differs;
- a closing table: **which stage decided each email's result** (Kain → body photo; MATRADE → Drive kit +
  header logo; APAC → collect; JomLokal → decide + collect; BigSeller → normalize + web probe; Sanct →
  body-only; Atlas → verify/media gate).

Links added in `docs/INDEX.md` and at the top of the two companion documents.

⭐ **Decision — §1:** ✅ nothing to decide.

## 2. The one thing that was understated before

The earlier wording could read as if the decide AI "chooses the fetcher". It does not. Only
`chosenFileName` and `linkToFetch` affect behaviour; `confidence`, `linkIsPressKit`, `imagesViaLink`
and the rest are recorded, not gates. The URL type decides the fetcher, and a low-confidence real link
is still used (Atlas Copco, 0.45–0.62).

⭐ **Decision — §2:** ✅ nothing to decide.

## 3. Verification

Every number and flag in both documents was taken from the archived runs in
`RECEIVE-WORKFLOW-7-EMAIL-EXAMPLES.md` and cross-checked against `decide.py:38–82`,
`pipeline.py:436–452`, `pipeline.py:509–520`, `web_fetch.py:215` and `config.py` (`WEB_FETCH_MODE`,
`WEB_PROBE_MAX_LINKS`, `COLLECT_MAX_WEB_LINKS`). No code changed, so no test run was needed.

## 4. What I recommend next

Read `docs/RECEIVE-STAGES-EXPLAINED.md` and tell me if any stage needs more detail. Otherwise the same
treatment can be applied to the **filter stage** (3 gates + 11 scores) or we go back to the delete
decision (`INDEX.md` §8). Thinking effort: **low**.
