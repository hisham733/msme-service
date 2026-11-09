# 15 — N-2 library update built + DeepSeek model fixed

_2026-11-07 (S15) · "go to N-2 now" · "decision C as written" · "full build" · "use deepseek-flash"._

## 1. N-2 library update (D44)

An email that only distributes a logo/building photo is now a **gallery update**, not "no article".

| Part | Where | What |
|---|---|---|
| Detector | `msme/receive/library_update.py` `classify` | after extract, before verify; hit needs body < 400 chars **and** ≥2 positive signals (phrase / image-only attachments / decide empty+images) **and** 0 negative ("for immediate release"/press release/…) |
| Store | `library_update.store_update` | `data/gallery/updates/<date>_<brand>/update.json` + `images/` + `originals/`; per-file sha1/bytes/width/height/kind |
| Promotion (decision C) | `gallery.promote_if_safe` | auto-active only when logo ≥200px/vector + confidence high + brand already active + readable/sized; else `pending` (`new-brand`/`not-a-logo`/`low-brand-confidence`/`unreadable`) |
| Pipeline | `pipeline.py` | `library_update` stage before gallery/verify; on hit skips verify/filter/archive/reply, returns `emailType=library_update` |
| Row | `db.py` | `emailType` column (outside the 14-col CSV contract) + save/select |
| UI | `editor_data.py`, `static/checklist.html`, `static/editor.html` | "Library update" badge instead of "no article" |
| CLI | `tools/gallery_admin.py` | `promote <id>` / `discard <id>` |
| Tests | `tests/test_library_update.py` | 11 tests (detector, promotion, store, corrupt index) · **271 pass** |

## 2. DeepSeek model fix

The re-run first failed with `'NoneType' object has no attribute 'choices'`. Diagnosed live against
`/models`: the account has **only `deepseek-flash` and `deepseek-v4-pro`** — `deepseek-v4-flash` does
not exist, and `deepseek-v4-pro` returns `None` on a plain call. `deepseek-flash` returns **HTTP 500
on `response_format={"type":"json_object"}`** but emits clean JSON in plain mode.

Fix: `msme/deepseek.py` no longer sends `response_format` (the prompts ask for JSON; `_parse_json` /
`_parse_json_hard` tolerate prose/fences). `docker-compose.yml` `DEEPSEEK_MODEL` and
`data/settings.json` `DEEPSEEK_MODEL` + `REPURPOSE_MODEL` all now = **`deepseek-flash`**.

## 3. Verification (measured)

| Check | Result |
|---|---|
| Full suite | **271 tests OK** (8 skipped) · `compileall` OK |
| Model | `chat_json` on `deepseek-flash` → `{'ok': True, 'word': 'hello'}` (was `{}`/500) |
| Live BPMB re-run (`1a0e70ae4af4d80b`) | `success`; checklist row 419 `emailType=library_update`, `hasArticle=false`, `readyToFilter=false`, **no reply** |
| Store | `data/gallery/updates/2026-11-07_bpmb/` — 6 files: **2 logos auto-promoted**, 4 building photos `pending (not-a-logo)` |
| Skip | `verify` and `filter` stages are `null` (not run) |

`index.json` after: BPMB has one `sender`-sourced **active** logo; the two older BPMB entries are
`superseded` (each new logo supersedes the previous — last logo wins).

## 4. Notes

- Two BPMB logos (EN "BPMB Group Logo" + BM "Logo Kumpulan BPMB") both auto-promoted; they share the
  AG-05 name, so the second overwrites the first and is the one active. Harmless (superseded entries
  are unused) — curate via `gallery_admin promote/discard` or `add` if a specific one is wanted.
- `deepseek-v4-pro` is currently unusable (returns `None`) — do not switch to it without re-testing.
- Code/decision changes are unstaged (profile denies `git commit`); `data/` is gitignored live data.

✅ nothing to decide — N-2 is built and live; the model is fixed to `deepseek-flash`.

## Recap

| # | Item | State |
|---|---|---|
| 1 | N-2 detector + store + promotion + UI + CLI | done |
| 2 | 11 new tests, 271 total | done |
| 3 | DeepSeek `response_format` removed (500 on flash) | done |
| 4 | Model standardised to `deepseek-flash` | done |
| 5 | Live BPMB re-run → `library_update`, 2 logos promoted | done |

## What I recommend next

Carry on in this session (low effort): point MSME at the live `/editor.html` "Library update" badge on
the BPMB row, and answer the three N-2 §10 questions at the 2026-11-11 call (replace-vs-keep,
auto-approve-vs-hold, how they identify these emails). N-3 (report link) is the next N-rule in T-049.
