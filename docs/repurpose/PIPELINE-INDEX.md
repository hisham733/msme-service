# pipeline — INDEX

> **Vendored here (`D40` / `T-050`, 2026-11-06).** This is the upstream engine document.
> In this repository the engine lives in `msme/repurpose/engine/` and runs in-process on :8899;
> `config.local.json`, the `:8765` dashboard and `python -m pipeline.*` commands no longer apply.
> Use `python -m msme.repurpose.engine.<module>` and `/repurpose.html`; paths come from
> `msme/paths.py`.

_Hand-maintained (2026-10-22, updated 2026-10-26). The repurpose→upload engine (T-011) + the DLW builder
(T-010) + the operator dashboard (T-014). Stdlib-only Python; runs from the project root; exports as a
built handoff (D-017: `python tools\build_export.py`). Spec + decisions: `session_analysis\2026-10-22_S06_image-skill-questions\2_dlw_engine_plan.md` · `3_dlw_engine_answers.md`._

| file | what it does | proves / proves-by |
|---|---|---|
| `config.py` | loads `config.json` (shared, committed) over `config.local.json` (this machine, gitignored) + `.env`; fills the intake defaults | handoff tests (config layer) |
| `scan.py` | work queue over `Email_Articles\` (one folder at a time / selected set / all); status per folder; reports `n_release_texts` / `ambiguous`; shapes come from `intake` | `python -m pipeline.run scan` · preflight |
| `preflight.py` | **read-only intake check** — per folder: release text, ambiguity, link, images, already-processed; exit 1 on FAIL; writes nothing unless `--report` | `python -m pipeline.preflight --root partner_handoff\demo_releases --strict` |
| `parser.py` | parses a skill draft (cold-run format contract) → Draft dict | golden tests on N-01/N-02 |
| `llm_step.py` | DeepSeek direct API; the two `SKILL.md` files are the system prompt; writes `draft.md` | `python -m pipeline.run check` |
| `vision.py` | **the eyes** — reads every supplied image with DeepSeek image parts (kind · people · text · subject); cached by file sha | used by imgselect; cache is audit evidence |
| `harvest.py` | **mines the attachment** — pulls pictures out of the supplied `.pdf`/`.docx` | `Files_from_MSME\_harvest\<slug>\` (D-009) |
| `imgselect.py` | **the image decision as code** — gather → clean → read → story-gate → name → caption; emits the `## Images` block (D-010). Turn rules 2026-10-25 | TARGET match **84.4 %** calibration · **70.0 %** fresh (81.8 % where the asset was delivered) — `tools\imgeval.py` |
| `IMAGE_GUIDE.md` | **the image rulebook** — criteria, thresholds, both score sets, turn ledger, residual triage, tuning law | — |
| `validate.py` | mechanical acceptance: D-007 checks + numbers-trace (D-002) + **D-008 graph-never-featured** | 10 rule tests incl. graph-fail |
| `build_site.py` | renders `DLW\articles\<slug>.html`; regenerates `DLW\index.html` + `data\articles.js`; `DlwWriter` / `WordPressUploader` interface | renderer + build tests |
| `run.py` | one CLI entry chaining the stages; bounded re-prompt loop (max 2, carrying the failure list) → HOLD; `check` proves key + model | `python -m pipeline.run check` |
| `manifest.py` | per-article `run.json` (status · skill hash · model · validator results) | used by scan/build/dashboard |
| `dashboard.py` | operator surface: queue · Run/Validate · Settings (writes `config.local.json`; key → `.env`) · **`/rules` = draft rules + image rulebook + image criteria + the D-007 repurpose playbook** | `python -m pipeline.devtests` (dash) |
| `GUIDE.md` | **the human run guide** — setup, dashboard, CLI, HOLD loop, fine-tuning, export, troubleshooting | — |
| `tests\` | **38 unittest goldens** — parse/validate/render/build/archive + the handoff contract. 8 need client release text/images, so they skip in the export/CI and run on MG's laptop | `python -m unittest discover pipeline\tests` |
| `devtests\` | **development-only** harness (never imported, never exported): links · drafts · skills · dashboard · config · paths · intake · handoff · snapshots | `python -m pipeline.devtests` |
