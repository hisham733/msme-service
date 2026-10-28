# World Bank speech — web fetch built, row ready

**Session:** 2026-10-22_S02 · **Turn:** 29 · **Image:** `msme-service:web-fetch-20261022`
**IDs:** D20 · T-032 · T-013

## 1. What was built

`web_fetch.py` (stdlib HTML parser) fetches a public article/speech page **only as a fallback**:

- no attachment / Drive / OneDrive / Box article;
- clean email body < 2,500 chars with no release/dateline marker;
- one article-like URL from `linkToFetch`/`linksFound` (`/news/`, `/speech/`, `/article/`…).

It extracts the title + paragraphs (nav dropped), publisher logo (JSON-LD `publisher.logo` or
`og:image`) and content images. `logo|share-logo|default-meta-image` → `hasLogo`; content photos →
`hasPic`. HTML only, 5 MB/20 s caps; failures are recorded, never fatal.

## 2. The speech page

- Page 200; title exact; **13.6k chars** of speech text.
- `og:image` (`default-meta-image.png`) is **404**; the valid media is the JSON-LD publisher logo
  `share-logo/social-share.jpg` (780×439) → counted as **logo**.
- No news photo exists; `hasPic=false`, `hasLogo=true`.

## 3. Live result

Run `16a1ed34-…` → row 364: `hasArticle=true`, `hasLogo=true`, subject **100**,
**`readyToFilter=true`**; article `.md` + logo archived.

## 4. Totals

**149 emails · 129 ready · 20 not ready**; asks unchanged at 14. `T-013` closed by `D20`/`T-032`.
The Jev filter may still reject the speech editorially; receive has now supplied the article and a media
asset (publisher logo, not a news photo).
