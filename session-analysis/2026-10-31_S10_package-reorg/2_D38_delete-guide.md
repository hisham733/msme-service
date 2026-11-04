# 2 — D38 · delete guide (`INDEX.md`)

**Deliverable:** root `INDEX.md` — all **69** `.py` files, each with purpose, why it is needed, one
real example, and what breaks if deleted. Generated from the headers + the real import graph, then
checked against the code (34 files are FATAL, 5 package markers, 2 repurpose, 1 legacy, 14 tests,
10 tools).

## 1. What the file contains

| Section | Content |
|---|---|
| How to read | FATAL / BREAKS A FEATURE / OPERATOR ONLY / TEST ONLY / SAFE |
| 1. Entry + shared | `run.py`, `__main__`, `combined`, `config`, `paths`, `db`, `creds`, `settings_store`, `auth`, `connection_test`, `llm`, `deepseek` |
| 2. Receive | the 20 modules, each with a real call and the exact breakage |
| 3. Filtering | the 5 Jev modules |
| 4. Repurpose | export + worker |
| 5. Legacy | `main.py` |
| 6. Tests | 14 modules and what each one proves |
| 7. Tools | 10 scripts, their command and what you lose |
| 8. Delete guide | my tier assessment |

⭐ **Decision — §1:** ✅ nothing to decide; the file is ready to read.

## 2. The deletion tiers (short version)

- **Never (34 + 5 `__init__`):** the app stops starting. Includes `run.py`, `combined.py`, `config`,
  `paths`, `db`, `creds`, `settings_store`, `auth`, `llm`, `dashboard`, `pipeline`, all receive
  modules, `filter`, `filter_service`, `filter_log`.
- **Feature-level:** `deepseek` (DeepSeek provider), `filter_llm` (Jev assist), `prefilter`
  (deterministic pre-checks), `repurpose_export` (accepted articles stop reaching the engine),
  `repurpose_worker` (host worker only), `legacy/main` (tests + reference only).
- **Keep for the partner:** `tests/` (14), `reauth_google`, `oauth_catch`, `build_register_indexes`,
  `prompt_eval` (a test imports it).
- **Likely one-off, safe to retire:** `export_creds` (also carries the n8n key literal — rotate),
  `check_deepseek_key`, `drive_folder4`, `learn_jev_way`, `reorganize_archive`, `run_all_emails`,
  `tests/test_jev_weakness.py` (manual runner, not part of the 149).

⭐ **Decision — §2:** tell me which files you still need; I confirm the exact consequence and remove
only what you name. Nothing has been deleted.

## 3. Note

`INDEX.md` was added to the README map. No code changed this turn; the reorg from the previous turn
is unchanged (149 tests, ruff clean).

## 4. What I recommend next

Read `INDEX.md` §8 and reply with the files you still need. I will then delete the rest one by one,
name what stops working, and re-run the 149 tests + compile + ruff. Thinking effort: **low**.
