# 3 — D38 · media-source decision guide

**Deliverable:** `docs/MEDIA-SOURCE-DECISION.md` (224 lines), linked from `docs/INDEX.md` and the top of
`docs/RECEIVE-WORKFLOW-7-EMAIL-EXAMPLES.md`.

## 1. What the document answers

One question: **who decides where the article is fetched from?** Short answer: not the AI — the
pipeline routes by URL type after a link guard; the decide AI only suggests a link, and the extract AI
only picks the article from the candidate pool.

It contains:

- the decision chain (table + mermaid);
- the five fetch paths with the real code and line references;
- `WEB_FETCH_MODE=off|known|probe` and the link guard;
- **seven real emails, seven different routes**, each in the same order: shape → normalize → decide →
  link guard → what ran → what did not run → candidate pool → result;
- a quick lookup table ("email contains X → this runs");
- why it is deterministic, and what breaks if a fetcher is deleted.

⭐ **Decision — §1:** ✅ nothing to decide; the file is written and linked.

## 2. The seven routes (summary)

| # | Email | Fetchers that ran | Winner |
|---|---|---|---|
| 1 | Kain Fashion | attachments only | PDF attachment |
| 2 | MATRADE | attachments + Drive folder | Drive DOCX release |
| 3 | APAC CEOs | attachments + OneDrive + web page | OneDrive release PDF |
| 4 | #JomLokal | attachments + Box + web (home page rejected) | English DOCX |
| 5 | BigSeller | web probe + body image | vritimes page |
| 6 | Sanct Social | body images only | email body |
| 7 | Atlas Copco | Google Doc export | Google Doc (no media → not ready) |

⭐ **Decision — §2:** ✅ nothing to decide.

## 3. Verification

Every quoted fact was cross-checked against the code or the archived example document:
`pipeline.py` (imports 44–54, `_trusted_links:203`, `_load_attachments:82`, Drive `:543`, Google Doc
`:585–642`, Box `:759`, OneDrive `:785`, web `:815`, body/asset `:860–980`), `web_fetch.py:215`
(`candidate_links`), `config.py` (`WEB_KNOWN_SITES`, `WEB_PROBE_MAX_LINKS=2`,
`COLLECT_MAX_WEB_LINKS=3`), and the seven runs in `RECEIVE-WORKFLOW-7-EMAIL-EXAMPLES.md`.

No code changed, so no test run was needed; the reorg baseline remains 149 tests, ruff clean.

⭐ **Decision — §3:** ✅ nothing to decide.

## 4. What I recommend next

Read `docs/MEDIA-SOURCE-DECISION.md` and tell me if any example needs more detail. Otherwise the next
step is the delete decision (`INDEX.md` §8) or the handover bundle (`todo/T-048.md`). Thinking effort:
**low**.
