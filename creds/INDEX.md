# creds/ — INDEX

**Secrets. Git-ignored (`creds/*.json`). Never print, copy into a reply, or commit.**

| File | Used by | What it is |
|---|---|---|
| `gmail.json` · `drive.json` · `sheets.json` | `creds.py` | exported n8n OAuth tokens (auto-refresh) |
| `deepseek.json` | `creds.deepseek_api_key()` | DeepSeek API key |
| `ai_sme.json` · `ai_sme_last.json` · `last.json` · `mse_ai_app.json` · `client_secret_new.json` · `client_secret_2_*.json` | **nothing (archive)** | Google OAuth client-secret files moved here from the project root on 2026-10-21 — rotate or confirm test-only (`decisions/D3.md`) |

Adding a credential: name it `<service>.json`, load it through `creds.py`, and keep it out of logs.
