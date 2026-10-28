# prompts/ — INDEX

_DeepSeek/Gemini system prompts, loaded by name via `config.load_prompt()` (read-only in Docker)._

## Base prompts (v0)

| File | Loaded by | Step |
|---|---|---|
| `decide_prompt.txt` | `decide.py` | AI step 1 — which attachment is the press release, image/media-kit detection |
| `extract_prompt.txt` | `extract.py` | AI step 2 — verbatim article + metadata |
| `verify_prompt.txt` | `verify.py` | AI step 3 — headline, subject match, ready-to-filter |
| `filter_preprocess.txt` | `filter_llm.py` | Jev assist pattern 1 — clean/translate/extract |
| `filter_second_opinion.txt` | `filter_llm.py` | Jev assist pattern 2 — re-judge one weak question |

## Versioned packs (v1)

| File | Loaded when | What changed |
|---|---|---|
| `decide_prompt.v1.txt` | `PROMPT_VERSION=v1` | English-first, release-vs-report names, link guard, examples |
| `extract_prompt.v1.txt` | `PROMPT_VERSION=v1` | slim 7-key schema, candidate rule, no-article path, examples |
| `verify_prompt.v1.txt` | `PROMPT_VERSION=v1` | exact headline/label-subject rules, media-flag guard, examples |

`config.load_prompt("extract_prompt.txt", version="v1")` reads `extract_prompt.v1.txt`
and falls back to the base when the versioned file is missing. **v1 is live since 2026-10-24**
(`PROMPT_VERSION=v1`); the base is the rollback (`PROMPT_VERSION=v0`).

## How to evaluate / switch

```bash
# dry-run A/B on archived emails (no writes); report in docs/
python3 tools/prompt_eval.py --limit 6 --versions v0,v1 --yes

# make v1 live
#   add PROMPT_VERSION=v1 to docker-compose.yml, then:
docker compose up -d --build

# rollback: remove PROMPT_VERSION (or set it to v0)
```

Change a prompt → re-run one email and record the verdict/checklist row that proves the effect.
