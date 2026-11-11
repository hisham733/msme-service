# N-3 — Report emails are valid articles, and the report link is published

_Status: spec for the 2026-11-11 MSME call · 2026-11-05 · **built 2026-11-07** (`D45`)._
_Built note: the link is stored in the `email_links` table (not archive `meta.json`); the export writes `meta.json` into the engine inbox and the engine appends the line at build (the validator rejects URLs in the draft)._
_Source: 30-Oct 2026 MSME call `[15:42–18:42]`; `docs/meetings/2026-11-09/MEETING-BRIEF-2026-11.md:82`._

## 1. The rule

When an email offers a press release **and a full report**, the report is a valid article source.

- Publish the article.
- **Include a link to the report** so the reader can read more.
- The link belongs in the **published piece**, not only in the email.

Second case, confirmed in the call: when the email only gives a **web link** to the release
(“click here for the full release and photos”), fetch that page, publish from it, and keep the link in
the published piece (`[18:23]`, `[18:42]`).

Example: **Meltwater / We Are Social — 15 years of digital reports** (Thu 22 Oct, thread
`1a162cc0b30af0e7`). The email offered the press release plus the full report; the release DOCX carried
`wearesocial.com/digital-2027` and `meltwater.com/en/global-digital-trends`; the live 27-Oct article has
**neither**.

## 2. What exists today (verified)

- Receive extracts the release text and archives `article.md` + `images/` + `originals/` (`archive.py`).
- The exporter copies `link.md` **if a folder has one**, but nothing writes it — and in the engine
  contract `link.md` means the **published URL**, not the report URL
  (`docs/operations/REPURPOSE-INTEGRATION-2026-10-27.md` §2; T-044).
- The engine reads **one `.md` release text** per folder; two `.md` files ⇒ preflight **FAIL
  (ambiguous)** (`INTEGRATION_CONTRACT.md` rules 1–2). It has **no `reportUrl` concept**.
- **Hyperlinks are not extracted.** `extract_text_from_bytes` (`msme/receive/extract.py:88`) reads DOCX
  paragraphs and PDF text only. The Meltwater DOCX carries both report URLs in
  `word/_rels/document.xml.rels`, not in the paragraph text — so a prompt-only approach cannot see
  them.
- The live Digital 2027 article has **0** report links (verified 2026-11-04;
  `session-analysis/2026-11-04_S12_report-link-check/1_N-3_report-link.md`).
- The existing `linksFound` list (`normalize.py`) covers URLs in the email body, including resolved
  short links, but not links inside attachments.

## 3. Design — receive side

```text
email body links + DOCX rels + PDF /URI annotations
        ↓
report detector + URL scoring
        ↓
meta.json in the archive folder
        ↓
export: repurpose_inbox/<subject>/meta.json + data/repurpose_export.json
        ↓
engine: append "Read the full report: <url>" at publish
```

### 3.1 Hyperlink extractor (deterministic, new)

- **DOCX:** read `word/_rels/document.xml.rels` and collect `Target` values whose `Type` is a
  hyperlink.
- **PDF:** read `/Annots` → `/A` → `/URI` from the first pages.
- **Email body:** reuse `model["linksFound"]`.
- Deduplicate, strip trackers (`utm_*`, redirect wrappers), keep the original order.

### 3.2 Report detector + URL scoring

- `articleType=report` when the subject/body says report/insights (e.g. “full report”, “insights
  report”, “download the report”) **and** a report-like link exists.
- Score links by path/anchor: `report`, `insights`, `trends`, `digital-20xx`, `download`.
- Exclude: social links, publisher/site links, unsubscribe, signature/footer, Drive **folder** links
  unless no public URL exists.
- Store the best public URL and all candidates; a low-confidence case stores candidates with
  `reportUrl=""` for the editor.

### 3.3 Storage — `meta.json`, not a second `.md`

The archive folder gains `meta.json`:

```json
{
  "articleType": "report",
  "reportUrl": "https://wearesocial.com/digital-2027",
  "reportCandidates": [
    "https://wearesocial.com/digital-2027",
    "https://meltwater.com/en/global-digital-trends"
  ],
  "sourceUrl": "",
  "detectedBy": "docx_rels",
  "confidence": 0.9
}
```

- JSON is ignored by the engine’s `find_release_texts` (`*.md`), so the one-release-text preflight still
  passes.
- `sourceUrl` is for the web-link case (the fetched page URL).

### 3.4 Row and UI

- `emailType=report` — the generic `emailType` column introduced by N-2.
- Add a `reportUrl` extra column (same migration style, not in `_COLUMNS`) so the editor can show and
  override it.
- `readyToFilter` is unchanged: a report is a normal article.

### 3.5 Export and engine handoff

- `repurpose_export.py` copies `meta.json` into `repurpose_inbox/<subject>/` and adds `reportUrl` to
  `data/repurpose_export.json`.
- The vendored engine (`msme/repurpose/engine/`) reads `meta.json` and appends
  `Read the full report: <url>` at the end of the draft/publish.
- This is the **cross-repo** part: receive alone captures the URL but cannot publish it.

## 4. Why not `link.md` or a second `.md`

- `link.md` is the **published URL** in the engine contract — reusing it for the report corrupts that
  field.
- A second `.md` (`report.md`) trips the engine’s ambiguity check. JSON is ignored by the scanner.

## 5. Engine handoff options

| | Approach | Pros | Cons |
|---|---|---|---|
| **A (recommended)** | `meta.json` + engine appends the line | clean separation; link survives receive → draft → publish | one change in the vendored engine |
| **B** | append the line to `article.md` at archive time | no engine change; works today | mutates the verbatim release text; the engine may paraphrase or drop it |
| **C** | receive-only now, engine later | ships the capture + editor display immediately | no published link until the engine task lands |

## 6. Questions for MSME (2026-11-11)

Recorded in `docs/meetings/2026-10-30/NEXT_MEETING.md` §2 (N-3).

1. **Where the report lives — what do we link to?** If the report is an **email attachment**, a
   **Google Drive** file, or another cloud store (OneDrive / Box / Dropbox), what URL goes into the
   published article? If it is only an attachment with no public URL, do we skip the link, upload the
   file, or ask the sender for a link? Please give one real example.
2. **Link or summarise — when?** When do you publish the **link** instead of taking information from
   the report into the repurposed article? Does it depend on the **report size/length**, the type of
   report (insights vs product), or whether the report has an article-worthy story? Please show a
   short-report and a long-report example.
3. **Placement — where does the link sit?** At the **end of the body**, inline next to the relevant
   paragraph, or on a separate line next to the article? Please show the exact wording/format
   (e.g. “Read the full report: <link>”).
4. **File types — what counts as a report?** Only PDF/DOCX, or also **Excel / CSV / PowerPoint** and
   other formats? If the report is a spreadsheet or slide deck, should the pipeline still link it, or
   skip it?
5. **Several links — which one?** When the email offers more than one report URL (e.g. Meltwater and
   We Are Social), publish one, all, or the one the sender calls the full report?

## 7. Decisions before coding

1. **Handoff:** **A** `meta.json` + engine change · **B** append to `article.md` · **C** receive-only now.
2. **Which URL when several:** best public URL (recommended) or publish all candidates.
3. **Placement:** end of body (recommended) vs inline vs both — also question 3 to MSME.
4. **UI:** add the `reportUrl` column (recommended) or keep it in `meta.json` only.

## 8. Tests

| Case | Assertion |
|---|---|
| Meltwater DOCX rels | `reportUrl` captured, `emailType=report`, `meta.json` written, export manifest carries it |
| vritimes web-link email | `sourceUrl` captured; `reportUrl` empty |
| normal release with “report” in text but no link | no `reportUrl` |
| social/publisher links | ignored |
| engine preflight | still **one** release text (no `.md` added) |
| editor | shows the report URL and accepts an override |

Proving run: `python3 -m compileall -q msme run.py tools tests` +
`python3 -m unittest discover -s tests -p 'test_*.py'`.

## 9. Code touchpoints (planned)

| File | Change |
|---|---|
| `msme/receive/report_link.py` (new) | hyperlink extraction, report detection, URL scoring |
| `msme/receive/pipeline.py` | `report` stage after extract; `emailType`/`reportUrl` in the row |
| `msme/receive/archive.py` | write `meta.json` beside `article.md` |
| `msme/repurpose/repurpose_export.py` | copy `meta.json`; add `reportUrl` to the manifest |
| `msme/db.py` | `emailType` + `reportUrl` migrations; write/select them |
| `msme/receive/editor_data.py` · `static/editor.html` | show the report URL |
| `tests/test_report_link.py` (new) | DOCX rels, PDF annotations, URL scoring, export, preflight shape |

## 10. Cross-repo note

The engine change belongs to the vendored engine (`msme/repurpose/engine/`; N-7 is already engine work). Until it lands, **C** is the
honest state: the receive side can capture and display the URL, but the published article will not carry
the link.
