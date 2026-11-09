# GUIDE — the AI_News repurpose→upload engine, by hand

> **Vendored here (`D40` / `T-050`, 2026-11-06).** This is the upstream engine document.
> In this repository the engine lives in `msme/repurpose/engine/` and runs in-process on :8899;
> `config.local.json`, the `:8765` dashboard and `python -m pipeline.*` commands no longer apply.
> Use `python -m msme.repurpose.engine.<module>` and `/repurpose.html`; paths come from
> `msme/paths.py`.

*Rewritten 2026-10-23 (S07). Human document: what the engine does, every control, every rule and its
threshold, what each status means, and who fixes what. Machine contract: `pipeline\INDEX.md`.
Decisions behind the rules: `decisions\D-002` (no added facts), `D-003` (image ladder), `D-007`
(acceptance), `D-008` (graph never key visual), `D-009` (site paths).*

---

## 0. What one "run" means

For ONE release folder under `Files_from_MSME\Email_Articles\`:

1. **draft** — the two `SKILL.md` files drive DeepSeek to write the article;
2. **validate** — 18 mechanical checks (below). Any fail-level failure triggers up to `retry_limit`
   re-prompts that carry the failure list; still failing → **HOLD**;
3. **build** — render `DLW\articles\<slug>.html`, copy its images to `DLW\images\`, regenerate
   `DLW\index.html` + `data\articles.js`.

One article at a time; nothing is sent to MSME.

---

## 1. First-time setup (5 minutes)

1. **Python 3.10+** (this laptop: 3.12). No pip packages.
2. **API key** — one of:
   - the dashboard: **Settings → API key → Save** (writes `.env`, masked forever after), or
   - a text file `.env` in the project root: `DEEPSEEK_API_KEY=sk-…` (copy `.env.example`).
   **Never put the key in `config.json`** — that file is committed to git.
3. **Prove key + model in one tiny call:** `python -m pipeline.run check`
   → `model=deepseek-flash version=DeepSeek-V4.1-Flash-1017 reply='OK'`.
4. **Start the dashboard** — double-click **`pipeline\start_dashboard.cmd`** (or
   `python -m pipeline.dashboard`) → open **http://127.0.0.1:8765**.

`config.json` holds the **shared defaults** (committed: model id, base URL, retry limit, intake rules).
`config.local.json` holds **this machine's** overrides (gitignored: the two roots, a local model or port)
and is written by the dashboard's Settings page — so an edit can never dirty the repo or arrive in a pull
as a conflict. Effective config = shared, with local on top; the Settings page says whether a local layer
exists.

---

## 2. The folder — before and after

```
Email_Articles\<release folder>\
  <release title>.md   press release text                 (input, never edited)
  link.md / Link.md    published-link note                (input, optional)
  images\ originals\   supplied images / source files     (input)
  draft.md             the article draft                  (written by the model)
  draft.prev.md        the previous draft                 (auto-archive before each re-draft)
  run.json             status · model · skill hashes · validator results   (the record)
```

**One folder = one article.** The names are configurable (`config.json` → `intake`), because the folder
shape is produced by the receive stage and must not be guessed: `release_text_glob`, `image_dirs`,
`link_names` and friends. `python -m pipeline.preflight --root <tree>` measures a real tree against that
contract, folder by folder, before any model call (D-016).

**Status vocabulary** (`run.json` → also shown in the dashboard):

| status | meaning | on the DLW index? |
|---|---|---|
| `pending` | no draft yet | no |
| `drafted` | a draft exists, not yet validated | no |
| `validated` | every fail-level check passed | **yes** (after a build) |
| `validate-failed` | checks failed, retries were used, not yet HOLD | no |
| `HOLD` | retries exhausted — a human must decide | no |
| `rendered` | the page exists in `DLW\articles\` | yes |

So an article can be `drafted` yet absent from the site — the site only publishes **validated** drafts.
That is the answer to "why is this article not on index.html".

---

## 3. The dashboard — every control

| control | what it does | costs an API call? |
|---|---|---|
| **queue table** | one row per release folder: name · status · the last check results (green/red per rule) | no |
| **Run** (per row) | full pass: draft → validate (+retries) → build | **yes** (1 + retries) |
| **Validate** (per row) | re-run the checks on the CURRENT `draft.md`; updates `run.json` | no |
| **Regenerate DLW index** (right column) | rebuild every validated page + the index, no model | no |
| **Open DLW** | serves the demo site at `/dlw/index.html` (relative assets kept) | no |
| **Validation rules** | the 18-rule table with threshold + who set it | no |
| **Settings** | model id · base URL · retry limit · both paths · API key (write-only, masked) | no |
| **Open settings** | saves to `config.json` (+ key to `.env`) | no |

**Why Validate exists:** a draft can change without a new model call — you edited it by hand, or you
changed a skill and want the *existing* draft re-judged. Run would overwrite it with a new draft.

**Why "Run always drafts first":** Run means "produce a fresh article". The existing draft is copied
to `draft.prev.md` first, so nothing is lost — but if you only want to check, use Validate.

---

## 4. The rules — what, threshold, who set it

Canonical table: **dashboard → Validation rules** (generated from `pipeline\validate.py` → `RULEBOOK`,
so code and document cannot drift).

| rule | what it checks | threshold | set by |
|---|---|---|---|
| `DRAFT_PARSE` | the draft has the contract sections | Branch, Title, Excerpt, Body, Categories, Images, Flags parse | engine contract — it is the skills' output shape |
| `BRANCH_RECORDED` | article type is explicit | Branch names news / commentary / byline | skill Step 3 · D-006 |
| `TITLE_PRESENT` | a title exists | non-empty | skill Step 4 |
| `EXCERPT_WORDS` | news excerpt length | 25–42 words | measured corpus · skill Step 5 |
| `SUBHEADERS_3_8` | section count | 3–8 H2s (news) | published practice · skill Step 7 |
| `QUOTES_SENTENCE_BOUNDARY` | quotes end cleanly | each blockquote ends `. ! ?` | skill rule 4 |
| `DUPLICATE_SUBHEADER` | no repeated heading | each heading once | MG 2026-10-23 · skill rule 7 |
| `REPEATED_PARAGRAPH` | no repeated paragraph | no identical paragraph (8+ words) twice | MG 2026-10-23 · skill rule 7 |
| `CATEGORIES_1_4` | category count | 1–4 | skill Step 3/11 |
| `CATEGORIES_BANNED` | reserved names | never PILLARS / COLUMN | site taxonomy |
| `NO_CONTACTS_BOILERPLATE` | clean body | no URLs/emails/phones/"FOR IMMEDIATE RELEASE"/`###` | skill Step 9 |
| `NUMBERS_TRACE` | **no added facts (D-002)** | every number in the draft appears in the release | D-002 · engine (fail since 2026-10-23) |
| `FEATURED_EXISTS` | the featured file exists | found in `images\` or `originals\` | D-003 · image skill |
| `FEATURED_RENAME_TOKEN` | rename convention | `renamed` contains `_MALAYSIA-SME.` | image skill Step 4 |
| `FEATURED_CAPTION` | caption present | non-empty | image skill Step 5 |
| `CAPTION_CLEAN` | caption is publishable | no `*(`, `[FLAG]`, "confirm"/"unverified" inside it | MG 2026-10-23 live-run finding |
| `FEATURED_RUNG_D008` | ladder rung valid | people / logo / event key-visual / product; **a GRAPH always fails** | D-003 · D-008 |
| `IN_BODY_COUNT` | in-body cap | 0–6 | image skill Step 3 |

**`FEATURED_EXISTS — <file>` means:** the draft named a featured image that is **not on disk** — the
build cannot show it. Common causes: a rename typo, or the draft used D-003's *library* fallback but
nobody downloaded the library asset (see the Event Me Now case, §10).

---

## 5. Failure, retries and HOLD — the exact semantics

- A draft **fails** when **any** rule at fail-level fails. One failing rule is enough; others may pass.
- `retry_limit` (default **2**) = how many **re-prompts** happen after a failed validation. Each
  re-prompt sends the model the list of failed rules and asks it to fix exactly those.
- After `retry_limit` failed attempts → status **HOLD**. Nothing is published; `run.json` keeps every
  attempt's results and `draft.prev.md` keeps the previous draft.
- **`retry_limit = 0`** → one draft only; if it fails, the article goes straight to HOLD. It does
  **not** mean "publish anyway" — there is no auto-publish path.
- Setting it: dashboard → Settings, or `config.json` → `llm.retry_limit`.

---

## 6. The demo site (DLW) — how it is laid out

- Pages: `DLW\articles\<slug>.html`; images: `DLW\images\<Subject>_<Month>_<Year>_MALAYSIA-SME.ext`;
  index: `DLW\index.html` + `DLW\data\articles.js`; styles + vendored fonts under `DLW\assets\`.
- **Why the pages are here and not beside the release (D-009):** Windows browsers refuse file paths
  over ~260 characters — the BMW release folder alone is 113 characters; a page built inside it
  measured **272** and Edge returned `ERR_FILE_NOT_FOUND`, while the same page here is **158** and
  loads. The release folder keeps the *record*; the site keeps the *output*.
- Open it **through the dashboard** ("Open DLW") or by double-clicking `DLW\index.html`. Both work.
- Deliberately absent (per MG's spec, refs in `analysis\upload\dlw_refs\`): site header, category
  labels on cards, the article side panel. 8 cards + **Load more**; clicking image or title opens the
  article.

---

## 7. Fine-tuning the two skills — who does what

| step | who |
|---|---|
| Notice a mismatch against the live MSME article | **MG** (read the rendered page; the dashboard shows the checks) |
| Decide the intended behaviour | **MG** |
| Edit `SKILL.md` + log `CHANGELOG.md` + update `GUIDE.md` | **the LLM session** (three files, always) |
| Run goldens + devtests, re-run affected folders, compare again | **the LLM session** (or you: §8) |

There is no "tune" button: tuning is a text edit to a skill file followed by re-runs. `run.json`
records each draft's skill hashes, so the engine can tell you a draft predates a skill edit
(`devtests` → `skills` check).

---

## 8. Command line (same code path as the dashboard)

```powershell
python -m pipeline.run check                            # prove key + model (1 tiny call)
python -m pipeline.preflight [--root <tree>] [--strict] # read-only intake check, no model call
python -m pipeline.run scan [--all]                     # the queue
python -m pipeline.run run --folder "<EXACT NAME>"      # draft -> validate -> build
python -m pipeline.run draft   --folder "<name>"        # model only
python -m pipeline.run validate --folder "<name>"       # checks only (free)
python -m pipeline.run build                            # re-render every validated page + index
python -m unittest discover pipeline\tests              # 38 golden tests (8 skip where client data is absent)
python -m pipeline.devtests [--update]                  # dev suite: links · drafts · skills · dash · config · paths · intake · handoff
```

**"The goldens show exactly which rule moved":** each rule has a test with a known input and an
expected answer — e.g. a 9-word excerpt *must* fail `EXCERPT_WORDS`, N-01's real 30-word excerpt
*must* pass. After any change, the suite re-runs them all and names the rule that changed behaviour,
before a wrong article can be built.

---

## 9. Sending it to your partner

**Do not hand-copy folders — build the handoff.** The old instruction ("copy `pipeline\` minus
`devtests\`, `DLW\`, the two skill folders …") rots: a new file is not added to a hand copy, and a
client folder or `.env` is one drag away from leaving.

```powershell
python tools\build_export.py --check     # asserts: required files present, no secret, no client folder
python tools\build_export.py --zip       # writes export\MSME_AI_News_handoff\ + a dated .zip
```

The export is the **whole repository minus** `.env`, `config.local.json`, `Files_from_MSME\`, `corpus\`,
`analysis\` (except the cold-run drafts the goldens parse — three files), `todo\`, `session_analysis\`,
`tools\` (except the four workflow tools), `pipeline\devtests\`, `DLW\images\` and `DLW\articles\`. It includes `partner_handoff\` (human guide + LLM
prompt + contract + synthetic demo), `meeting_notes\` (including `AGENDA.md`), `COLLABORATION.md`, the
hooks and the CI workflow, and `EXPORT_SOURCE.txt` — which states how many files were **uncommitted** at
build time. If that number is not zero, the partner must not pull GitHub as if it were the same tree.

On the partner's machine: `python -m pipeline.run check`, then set the two roots in
`config.local.json` (never `config.json`), then `python -m pipeline.preflight --root <their tree>` before
the first model call. Full instructions: `partner_handoff\README.md`.

---

## 10. Troubleshooting

| symptom | cause / fix |
|---|---|
| `no API key in .env` | Settings → API key, or the `.env` line |
| `401` | key wrong/rotated → replace it |
| `400` model error | `llm.model` must be `deepseek-flash` |
| `no release text .md in <folder>` | the folder has no release text (link/draft ignored). Run `python -m pipeline.preflight --root <tree>` to see what the scanner actually found |
| `preflight` says "ambiguous" | one folder holds two release texts — the contract is one folder per article; split it |
| the build points at the wrong folder | the path is in `config.local.json` (this machine), not `config.json` (shared) |
| `FEATURED_EXISTS — <file>` | the named image is not in `images\`/`originals\`. Either put it there, or (library fallback) download the logo first — naming a library asset does not create it. Live case: *Malaysias Event Industry…* (no images supplied; draft chose the library logo) |
| article **HOLD** | read the red rules in the queue column; fix the skill or the folder, then re-run |
| `draft.md` keeps changing on Run | by design: Run always drafts. Use **Validate** to check without a model call |
| card without image | featured file missing (same as `FEATURED_EXISTS`) |
| DLW looks stale | **Regenerate DLW index**, or any validated Run |
| port 8765 busy / old page shows | an older dashboard is still running: close it (or change `dashboard.port`) |
| dashboard error banner | shows the error + short traceback; fix and retry |

---

## 11. Rules that must not slip

- **The key lives in `.env` only** — never `config.json`, never a commit, never a chat log.
- **Shared defaults vs machine overrides** — team settings go in `config.json`; paths and local
  overrides go in `config.local.json` (gitignored), which the dashboard writes (D-015).
- **A session may commit/push when MG requests or approves it** (D-022); absent that, leave the tree and
  report what changed. Destructive history operations still need an explicit request.
- **MSME is the client** — drafts only; nothing is sent from here.
- **No added facts (D-002)** — an untraced number fails the build; the model is re-prompted, then the
  article HOLDs rather than publishing an invention.
- **Every skill edit logs three files** — `SKILL.md` · `CHANGELOG.md` · `GUIDE.md`.
