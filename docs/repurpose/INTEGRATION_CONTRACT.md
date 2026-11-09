# INTEGRATION CONTRACT — the boundary between your pipeline and ours

> **Vendored here (`D40` / `T-050`, 2026-11-06).** This is the upstream engine document.
> In this repository the engine lives in `msme/repurpose/engine/` and runs in-process on :8899;
> `config.local.json`, the `:8765` dashboard and `python -m pipeline.*` commands no longer apply.
> Use `python -m msme.repurpose.engine.<module>` and `/repurpose.html`; paths come from
> `msme/paths.py`.

*Reference for the partner's engineer **and** their LLM. It describes what the exported engine reads,
what it writes, and where your existing pipeline stops. Read `README.md` first for the human view; read
`LLM_INTEGRATION_PROMPT.md` for the copy-paste brief.*

---

## 1. Where the boundary is

```
YOUR PIPELINE                                  THIS EXPORT
Receive  ─────────────►  Filter (gate)  ─────►  Repurpose ─► validate ─► .html ─► DLW index
(e-mail → files)         (accept / reject)      (this engine starts here)
```

**We do not receive e-mail and we do not decide accept/reject.** The first thing this engine needs is a
folder that already passed your filter. Everything before that folder is yours; everything from the
folder onward is ours.

The two stages meet at **one filesystem contract**: *one folder per article*. If your filter output is a
database row, a JSON file, or one folder per e-mail, a thin adapter on **your** side writes the contract
folder. Do not change the engine to read your internal format — keep the seam in one place (D-016).

The measured issues on your side of the seam are in `KNOWN_ISSUES.md`. They do not change this contract;
they explain why some folders arrive with no picture, and which filter settings are decided (cut 62) and
which are still open (`c10`, determinism).

## 2. Input contract — one folder per article

```
<email_articles_root>\
  <release folder>\                     # ONE article; the folder name is the article id
    <release text>.md                   # the press release, plain text or markdown, UTF-8
    link.md                             # the published URL, optional but recommended
    images\                             # supplied pictures, original names
    originals\                          # optional: source files / attachments
```

Rules, in the order they bite:

| # | rule | checked by | consequence |
|---|---|---|---|
| 1 | **one release text per folder** | `preflight` | two `.md` files ⇒ **FAIL** (ambiguous), not "pick the first" |
| 2 | release text is UTF-8 and ≥ 200 characters | `preflight` | not UTF-8 ⇒ FAIL; short ⇒ warning |
| 3 | `link.md` (or `Link.md`) is present | `preflight` | warning; the corpus needs the URL later |
| 4 | at least one picture in `images\` or `originals\` | `preflight` | warning; the image stage then has to declare a library asset |
| 5 | the folder has **not** been processed before | `preflight` | `draft.md`/`run.json` present ⇒ warning: use a fresh folder for the test |
| 6 | the root holds folders, not loose `.md` files | `preflight` | loose release texts ⇒ FAIL (flat layout) |

The names are **configurable**, not hard-coded, because your receive stage already exists. In
`config.json` → `intake` (or `config.local.json` on your machine):

| key | default | set it when |
|---|---|---|
| `layout` | `folder_per_release` | keep this; the engine assumes it |
| `release_text_glob` | `*.md` | your releases are `.txt` |
| `release_text_exclude` | `link.md`, `draft.md`, `draft.prev.md`, `index.md`, `run.md`, `summary.md`, `notes.md` | your filter writes a `summary.md` beside the release |
| `link_names` | `Link.md`, `link.md`, `LINK.md` | your URL file has another name |
| `image_dirs` | `images`, `originals` | your pictures land in `photos\` |
| `extra_image_dirs` | `[]` | pictures are also in another folder |
| `require_link` | `false` | a missing URL must be a hard failure |

`python -m pipeline.preflight --root <your filter output>` is the tool that proves the mapping before
any model call. It writes nothing and costs nothing.

## 3. Output contract — what the engine writes

Inside each release folder:

| file | meaning |
|---|---|
| `draft.md` | the article draft, in the section contract the skills produce |
| `draft.prev.md` | the draft before the last re-draft (never silently overwritten) |
| `run.json` | status · model · skill hashes · validator results — the record of what happened |
| `site\*.html` | legacy per-folder render, kept for compatibility; the live demo is DLW |

In the demo-site root (`dlw_root`, default `DLW\`):

| path | meaning |
|---|---|
| `articles\<slug>.html` | one rendered page per validated article |
| `index.html` | the listing page (no server needed; open the file) |
| `data\articles.js` | the list the page reads (`var DLW_ARTICLES = [...]`) |
| `images\` | copies of the images the pages use |

Status vocabulary (`run.json`, also shown in the dashboard):

| status | meaning | on the index? |
|---|---|---|
| `pending` | no draft yet | no |
| `drafted` | a draft exists, not validated | no |
| `validated` | every fail-level check passed | **yes**, after a build |
| `validate-failed` | checks failed, retries remain | no |
| `HOLD` | retries exhausted — a human must decide | no |
| `rendered` | a page exists | yes |

## 4. Commands

```powershell
python -m pipeline.run check                            # prove key + model (one tiny API call)
python -m pipeline.preflight --root <tree>              # read-only intake check (no API call)
python -m pipeline.run scan [--all]                     # the queue, one article at a time
python -m pipeline.run run --folder "<EXACT NAME>"      # draft -> validate (+retries) -> build
python -m pipeline.run validate --folder "<name>"       # re-check the current draft, no model call
python -m pipeline.run build                            # re-render every validated page + index
python -m pipeline.dashboard                            # http://127.0.0.1:8765 (queue + rules)
python -m unittest discover pipeline\tests              # the golden tests
```

The dashboard is the operator surface: the queue with per-rule pass/fail, a **Validate** button that
does not spend an API call, and a **Validation rules** page that carries the draft rules, the image
rulebook, the image scoring criteria, and the repurpose playbook (D-007). It is part of the export on
purpose: a human must be able to see the evaluation criteria, not just a percentage.

## 5. Failure semantics

- One failing fail-level rule fails the draft. The failure list is sent back to the model, at most
  `llm.retry_limit` times (default 2). Still failing ⇒ `HOLD`.
- **`HOLD` publishes nothing.** There is no auto-publish path and no "best effort" page.
- `FEATURED_EXISTS — <file>` means the draft named an image that is not on disk. Naming a library asset
  does not download it; put the file in the folder first.
- `retry_limit = 0` means one draft, then `HOLD` if it fails — not "publish anyway".

## 6. What this export does not do

- **No e-mail ingestion, no filter gate.** Those are yours.
- **No send to MSME.** Drafts and local pages only; the client is never contacted from a session.
- **No WordPress upload.** `build_site.WordPressUploader` is an interface stub that raises
  `NotImplementedError`; the upload stage is replaced when MSME credentials exist.
- **No AI-generated images.** Supplied pictures, or a declared library asset, per the client guideline.

## 7. Unknowns to resolve during integration

These are the things this side cannot know. The LLM prompt makes filling them in the first deliverable.

| unknown | why it matters | where to record it |
|---|---|---|
| your filter's output path and format | the adapter, or just `email_articles_root` | the mapping table in `INTEGRATION_REPORT.md` |
| whether one e-mail can hold two releases | the contract is one folder per article | same |
| your Python version (needs 3.10+) | the engine is stdlib-only, no packages | `INTEGRATION_REPORT.md` |
| your LLM provider and key | the engine calls DeepSeek's API directly | `config.local.json` + `.env` |
| whether your orchestrator calls a CLI or a Python function | both work; the CLI is the stable seam | `INTEGRATION_REPORT.md` |
| max path length on your OS | Windows browsers fail over ~260 characters (D-009) | `INTEGRATION_REPORT.md` |

## 8. Changing this contract

The contract is versioned with the repository. If your integration needs a different input shape,
**change `intake` first**; if that is not enough, open a PR against `pipeline/preflight.py` and
`pipeline/scan.py` with a test. Do not fork the engine into your repo — a fork is how the two sides stop
being one project (D-017).

## 9. The two human gates — what the partner does manually

The integration is not "run a script". Two moments need the **human**, and both are easy to skip:

| gate | when | who | what must happen |
|---|---|---|---|
| **G-A · inventory approval** | before any code change | **the partner** | the LLM sends the Phase-0 table (where your filter writes, folder shape, Python, key, OS); the partner reads it and says **go / no-go**. Nothing is installed or mapped before this. |
| **G-B · final report** | after the two-article test | **the partner**, then **MG** | the LLM writes `INTEGRATION_REPORT.md`; the partner reads it, then it comes back **as a PR** to this repository. MG reviews it item by item (**T-031**) and decides what our side adopts. |

An LLM may not self-approve either gate. If the partner is unavailable, the integration stops at the gate
— a paused integration is recoverable; a silently changed pipeline is not.

## 10. The Filter measurement kit (optional)

`filter_stage/` in this export is a **read-only measurement kit** for the stage that precedes this engine.
It is not required to integrate repurpose → `.html`. It exists so the Filter issues in `KNOWN_ISSUES.md`
are inspectable rather than asserted.

- **What it is:** `parse` (needs `openpyxl`), `report`, `fit`, `selftest`; `FORMULATION.md` is the
  measured rule; `ROUND-2.md` is the next-batch protocol; `results/*.txt` are the recorded outputs.
- **What it is not:** a configuration for your Filter engine. The gate weights and the accept cut are
  **tunables of your engine**; where they live and what they are set to is your decision (D-023). The
  `CUT = 62` in the kit is only the value used to reproduce the 2026-10 measurement; `report --cut N`
  measures any other.
- **Your decision:** integrate the rule, defer it, or ignore it — and record which in
  `INTEGRATION_REPORT.md` §5–§7. The repurpose chain works regardless.
