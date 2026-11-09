# N-4 — Government budget/speech emails: use the summary, link the speech

_Status: spec for the 2026-11-11 MSME call · 2026-11-05 · no code written yet._
_Source: 30-Oct 2026 MSME call `[31:19–38:35]`; `docs/meetings/2026-11-09/MEETING-BRIEF-2026-11.md:93`._

## 1. The rule

For budget/government emails:

1. The **email summary is enough** — publish it **as written**, do not paraphrase (avoid misquoting).
2. Keep a **link to the minister's speech** in the published piece.
3. If the summary is **too skeletal**, open the linked speech and process the article from the speech.

The call's words: “if the summary is good enough, we will publish as per what we see… we don't want to
misquote them or paraphrase it” (`[32:44]`, `[33:22]`); “if the information is too skeletal from the
introduction on the email… we will open this particular speech and then we will kind of like process
from this particular speech” (`[38:09]`).

## 2. What the Madani case shows (verified)

The real email is **“Fwd: Budget 2027 POV: Where should SMEs start with MADANI's AI funding?”**
(checklist rows 204 and 347).

| Check | Result |
|---|---|
| Decide | “a media pitch/interview offer from Ellerton & Co. with only signature, tracking, map and a **government speech link**, none of which is a press release or press kit.” |
| Extract | `bodyTextLen=0`, `needsHumanFetch=true`, “no press-release article is present” |
| Row | `hasArticle=false`, `readyToFilter=false` |
| Archive folder | `all_emails/_no_article/Budget 2027 POV …/` contains only empty `images/` and `originals/` |

So today the pipeline sends this to the **needs-human/ask path**, although the call says the summary
plus the speech link is publishable. The raw body is not in the saved trace, so the exact summary length
must be measured on a dry-run of the Gmail thread before the threshold is fixed.

## 3. Design — receive side

```text
email (budget/government markers + speech link)
        ↓
summary substantive? ── yes ──► article = email body verbatim
        │ no
        ▼
fetch the speech link ──► article = speech text
        │ cannot fetch (video / blocked)
        ▼
article = email summary + speech link (link-only)
        ↓
meta.json: articleType=government_summary, speechUrl, source
```

### 3.1 Detect the type (deterministic)

- Subject/body markers: `budget`, `belanjawan`, `madani`, `speech`, `ucapan`, `minister`, `menteri`,
  `kementerian`, `government`, `POV`.
- Sender domain: `gov.my` or a known ministry/agency domain.
- A **speech-like link**: URL path/anchor contains `speech`, `ucapan`, `text-of-speech`, `minister`,
  `kementerian`, `pm`, or anchor text “speech”/“ucapan”.

A hit needs a government marker **and** either a substantive summary or a speech-like link. A normal
press release that merely mentions the word “budget” does not qualify.

### 3.2 Summary vs speech — left to MSME (decision B, 2026-11-05)

The call gives no threshold, and the raw Madani body is not in the saved trace. **No summary-length
threshold is coded until MSME answers question 1.**

Until then, the receive side may:

- detect the government/budget type and capture the speech link;
- but must **not** auto-publish the email summary as the article, and must **not** fetch the speech on a
  guessed rule. The case stays on today's path (needs-human/editor) with the speech URL recorded.

When the answer arrives, the rule is recorded here and implemented:

- **Summary is enough:** `<MSME's condition>` → use the body verbatim; `source=email_summary`.
- **Too skeletal:** `<MSME's condition>` → fetch the speech; `source=speech_page|speech_pdf`.
- **Cannot fetch** (YouTube/video, login wall): keep the summary, record the URL; `source=link_only`.

### 3.3 Fetch the speech

- **HTML page:** reuse `web_fetch.fetch_article` — it already treats `/speech/` as a content path and
  probes public pages (no AI).
- **PDF speech:** not fetchable today — `web_fetch._is_blocked` rejects `.pdf`
  (`msme/receive/web_fetch.py:50`). Add a public-document fetch: `is_public_http` (SSRF guard) →
  download with a size cap → `extract_text_from_bytes` (the existing PDF/DOCX reader). This helper is
  reusable by N-3 for report PDFs.
- **YouTube/video:** detect and **do not fetch**; use the summary and keep the video link.
- Fetch **only a trusted link**: one literally present in `linksFound` or the email body, never a link
  the AI invented.

### 3.4 Store and hand off the link

`meta.json` in the archive folder (the N-3 plumbing):

```json
{
  "articleType": "government_summary",
  "speechUrl": "https://www.kabinet.gov.my/ucapan/...",
  "source": "speech_page",
  "summaryLen": 620,
  "detectedBy": "budget_markers+speech_link",
  "requestedBranch": "commentary"
}
```

- `emailType=government_summary` in the checklist row; `speechUrl` extra column for the editor.
- `repurpose_export.py` copies `meta.json` into `repurpose_inbox/<subject>/` and adds `speechUrl` to
  `data/repurpose_export.json`.
- The engine appends the speech line — the same cross-repo handoff as N-3.

### 3.5 “As written” — the engine's commentary branch

The engine already has a **near-verbatim commentary branch** for statements on a policy
(`docs/repurpose/decisions/D-004.md`: commentary published at 95–98% reuse). A government budget summary
belongs there. The receive side passes `requestedBranch: "commentary"` in `meta.json`; the engine change
reads it and confirms/forces the branch.

## 4. Questions for MSME (2026-11-11)

Recorded in `docs/meetings/2026-10-30/NEXT_MEETING.md` §2 (N-4).

1. **Summary or speech — when?** When is the email summary “good enough”, and when do you open the
   minister's speech? Is it length, the facts it contains, or the sender's instruction? Please give one
   example of each.
2. **As written — how exact?** Publish the summary word-for-word, or the normal near-verbatim
   commentary treatment (house formatting, headline/excerpt)? Anything we must never change?
3. **Placement — where does the speech link go?** End of the body, inline, or a separate line? Please
   show the exact wording (e.g. “Read the minister's speech: <link>”).
4. **Speech source — what formats?** Web page, PDF, YouTube/video? What should the pipeline do when the
   speech is only a video with no text?
5. **Scope — which emails?** Budget speeches only, or every ministry/government statement?

## 5. Decisions before coding

1. **Summary threshold:** **B — decided 2026-11-05: leave it to MSME.** No threshold is coded until the
   answer to question 1 arrives; the N-4 build waits on it.
2. **Speech fetch scope:** HTML + PDF (recommended) vs HTML only; video = link-only.
3. **Branch:** rely on the engine's commentary branch with a `requestedBranch` hint (recommended) vs add
   a new forced-verbatim mode.
4. **Link handoff:** depends on the N-3 choice (A `meta.json` + engine · B append to `article.md` ·
   C receive-only now).

## 6. Tests

| Case | Assertion |
|---|---|
| Madani-style substantive summary + speech link | `emailType=government_summary`, summary used verbatim, `speechUrl` stored |
| skeletal summary + fetchable speech page | speech text becomes the article; URL stored |
| speech is a PDF | PDF text extracted; URL stored |
| speech is YouTube | no fetch; summary + video link stored |
| normal press release with “budget” in the text | stays a normal article |
| link not in the email | never fetched |
| engine preflight | still one release text (only `meta.json` added) |

Proving run: `python3 -m compileall -q msme run.py tools tests` +
`python3 -m unittest discover -s tests -p 'test_*.py'`.

## 7. Code touchpoints (planned)

| File | Change |
|---|---|
| `msme/receive/gov_summary.py` (new) | detection, summary-vs-speech decision, speech fetch routing |
| `msme/receive/report_link.py` (N-3) | shared hyperlink extraction for the speech URL |
| `msme/receive/web_fetch.py` | public PDF/document fetch for a speech PDF |
| `msme/receive/pipeline.py` | `government` stage after extract; override `needs_human` when the summary/speech is usable |
| `msme/receive/archive.py` | write `meta.json` |
| `msme/repurpose/repurpose_export.py` | copy `meta.json`; add `speechUrl` to the manifest |
| `msme/db.py` | `emailType` + `speechUrl`; write/select |
| `msme/receive/editor_data.py` · `static/editor.html` | show the speech URL |
| `tests/test_gov_summary.py` (new) | summary/speech branches, fetch guards, row/meta |

## 8. Dependencies and sequence

- **N-3** provides the `meta.json` handoff and the hyperlink extractor.
- **The vendored engine** (`msme/repurpose/engine/`) must read `meta.json`, keep the commentary branch and append the speech
  line. Bundle with the N-3 engine change.
- Build after N-1/N-2/N-3; ≈1 working day for the receive side plus the engine change.
- **The N-4 build is blocked on MSME's answer to question 1** (decision B, 2026-11-05): no
  summary-length threshold is coded until the “good enough” rule arrives.
- Until the engine change lands, the honest state is **C**: the summary and URL are captured, but the
  published draft does not carry the line.
