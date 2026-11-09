# Partner handoff — read this first

> **Vendored here (`D40` / `T-050`, 2026-11-06).** This is the upstream engine document.
> In this repository the engine lives in `msme/repurpose/engine/` and runs in-process on :8899;
> `config.local.json`, the `:8765` dashboard and `python -m pipeline.*` commands no longer apply.
> Use `python -m msme.repurpose.engine.<module>` and `/repurpose.html`; paths come from
> `msme/paths.py`.

*For the partner (human). Your LLM's copy-paste brief is `LLM_INTEGRATION_PROMPT.md`; the technical
boundary is `INTEGRATION_CONTRACT.md`. This file tells you what you received, what the LLM will do, and
what only you can decide.*

---

## 1. What you received

| path | what it is | read it? |
|---|---|---|
| `partner_handoff/README.md` | this file | **yes, now** |
| `partner_handoff/LLM_INTEGRATION_PROMPT.md` | paste this into your LLM session | yes, skim |
| `partner_handoff/INTEGRATION_CONTRACT.md` | the folder/status/CLI contract | when integrating |
| `partner_handoff/KNOWN_ISSUES.md` | the measured Receive/Filter issues (R1–R3 · F1–F3), their status, and what **not** to patch | **yes** |
| `partner_handoff/FILTER_KIT.md` | the optional Filter measurement kit (`filter_stage/`): what it measures, what it does not decide, how to run it on your own report | if you touch the filter |
| `pipeline/` | the engine: scan → draft → validate → build | `pipeline/GUIDE.md` |
| `pipeline/IMAGE_GUIDE.md` | the image rulebook and how it is scored | when tuning images |
| `.claude/skills/msme-repurpose/`, `…msme-image-select/` | the two skills (prompt text + human guide) | yes |
| `DLW/` | the local demo site shell: `index.html`, styles, fonts | open `index.html` after a build |
| `meeting_notes/` | MSME meeting notes + `AGENDA.md` (the shared, append-only agenda) | yes |
| `decisions/`, `roadmap/` | why the rules are what they are | reference |
| `COLLABORATION.md` | how we work on this repository together | **yes, before your first commit** |
| `tools/` | the four workflow tools: install the hooks · regenerate the registers · lint a reply · rebuild this handoff | run once |
| `partner_handoff/demo_releases/` | **synthetic** demo folders for a free end-to-end check | run them |
| `config.json` | shared defaults (committed) | do not put paths here |
| `.env.example` | the API-key template | copy to `.env` |

**Not included, on purpose:** the existing `.html` pages, the article folders, the client raw material,
the measured corpus, the images of the demo site, and `.env`. None of them are needed to integrate, and
they are either client-owned or regenerable. The first build on your machine produces the demo site from
**your** folders — which is a better proof than inheriting ours.

## 2. Read this before you pull

**On Windows, enable long paths first:** `git config --global core.longpaths true`. The repository
versions some analysis evidence whose paths exceed 260 characters; without that setting the clone fails
with `Filename too long` (measured in CI, run 40264167485). macOS/Linux need nothing.

If you received a zip, open `EXPORT_SOURCE.txt`. If it says *"N uncommitted change(s)"* with N > 0, the
GitHub repository is **older than this snapshot**. Ask MG to commit and push before you pull, or the two
sides will diverge on day one. This is the one blocking item in the handoff, and it is deliberate that
the export states it instead of hiding it.

## 3. The boundary in one picture

```
your pipeline                          this export
Receive ─► Filter (accept/reject) ─►  Repurpose ─► validate ─► .html ─► DLW index
```

Your filter is the last thing you own. What the engine needs from you is **one folder per article** —
release text, `images\`, optional `link.md`, optional `originals\`. If your filter writes something else,
your LLM writes a small adapter on your side. We do not ask you to change how you receive mail, and we
will not change the engine to read your database.

The one rule worth repeating: **one folder = one article.** If one e-mail holds two releases, split them
before the engine sees them. `preflight` deliberately fails a folder with two release texts instead of
picking one silently.

## 4. What your LLM will do — in plain language

The prompt is written as five phases with a **stop-and-report gate** at the start:

1. **Inventory, then stop.** It writes down where your filter output lands, what your folder shape is,
   which Python and which key you have, and sends you that table before changing anything. You approve.
2. **Install.** Clone (or copy) the repository, install the git hooks, put the key in `.env`, run one
   tiny API call to prove key + model, and run the engine on the synthetic demo. No client data, no
   spend beyond one short call.
3. **Map.** Either point `email_articles_root` at your filter output (if it already matches), or add a
   ≤100-line exporter that writes the contract folder. Then run `preflight` — free, read-only — on real
   output until it passes.
4. **Test one article, twice.** One fresh e-mail through Receive → Filter → Repurpose → `.html` →
   `DLW\index.html`, then a second one. It records the command and the output for each; a `HOLD` is
   reported honestly with the failing rules, never forced.
5. **Commit, PR, report, and append the agenda.** Branch, PR (CI must be green), a written
   `INTEGRATION_REPORT.md` with the mapping, the changes, the evidence, the risks, and what **our** side
   should change — plus any MSME question added as one new `AG-` row.

The report is the answer to "do we need a .md that guides reorganisation here?" — **yes, but as
evidence-backed recommendations, not a reorganisation done from your branch.** One of us applies it here,
with a test, and it lands as a normal PR.

## 5. What only you can decide

1. **Access** — your GitHub account must be a collaborator on `EmpiFlow/MSME_AI_News`, and the repository
   must be **private** (the meeting transcripts are client material).
2. **The key** — whose DeepSeek key the repurpose stage uses, and its spend limit.
3. **The adapter** — exporter on your side (recommended) versus pointing the root at existing output.
4. **The branch** — the PR target and who reviews it.
5. **The go/no-go** on the two acceptance articles.

## 6. How you check the work yourself

You do not have to trust a percentage. Three things are visible:

- **`python -m pipeline.preflight --root "<filter output>"`** — per folder: release text, link, images,
  and exactly why a folder fails. Free and read-only.
- **The dashboard** (`python -m pipeline.dashboard`, then `http://127.0.0.1:8765`) — the queue with
  per-rule pass/fail, plus a **Validation rules** page carrying the draft rules, the image rulebook, the
  image scoring criteria, and the repurpose playbook (D-007). That page is the human-facing definition
  of "good", not a black-box score.
- **`python -m unittest discover pipeline\tests`** — the golden tests, rule by rule.

## 7. Working together afterwards

Short version: `main` is shared; every change is a short branch and a pull request; CI must be green;
`main` is protected. Machine-specific settings go in `config.local.json` (never committed), so a path
edit cannot create a conflict. Hooks are a local convenience, CI is the enforcement. The full rules,
including how a conflict is resolved, are in `COLLABORATION.md`.

## 8. The meeting agenda

`meeting_notes/AGENDA.md` is in git on purpose. The skill-training and workflow decisions are agreed
with MSME in conversation, and both of us need to append. **Append only** — add a row `AG-<n>`, never
renumber or delete another person's row; change the `status` instead. One file per meeting; the raw
recording never goes into git, the transcript does.

## 9. Security and client material

- The repository is private; the transcripts and the decision log are internal.
- `.env` never commits; `config.local.json` never commits; `Files_from_MSME/` and `corpus/` never commit.
- Do not forward client releases or meeting transcripts outside the two collaborating parties.
- Nothing in this project sends anything to MSME. Drafts and local pages only.

## 10. If something looks wrong

| symptom | first check |
|---|---|
| `python -m pipeline.run check` fails | `.env` has the key; `config.local.json` does not override the model to something invalid |
| preflight says "ambiguous" | one folder holds two release texts; split in your exporter |
| preflight says "no release text" | the extension/naming differs; set `intake.release_text_glob` or rename |
| an article is `HOLD` | the dashboard's red rules; `pipeline/GUIDE.md` §5 and §10 |
| the index does not list a validated article | run `python -m pipeline.run build` |
| a page renders without an image | the featured file is not on disk (`FEATURED_EXISTS`) |
| the build points at the wrong folder | `config.local.json`, not `config.json` |

