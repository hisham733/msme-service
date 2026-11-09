# Handover — what goes in git, what goes on the USB

_Measured 2026-11-03. The repo push is ~10 MB; the live archive is 2.7 GB and never goes in git._

## 1. Push (git) — everything except the ignored folders

| Group | What |
|---|---|
| Code | `msme/`, `run.py`, `tests/`, `tools/`, `static/`, `prompts/` |
| Config / tooling | `pyproject.toml`, `Makefile`, `.github/`, `Dockerfile`, `docker-compose.yml`, `requirements.txt`, `.env.example`, `.gitignore` |
| Docs | `docs/` (workflow, filter, meetings, operations, receive, reference + the code-read files), `decisions/`, `todo/`, `INDEX.md` |
| Project files | `README.md`, `NOW.md`, `AGENTS.md`, `opencode.json`, `.claude/` |
| Replies | `session-analysis/` |

**~10 MB total.** Biggest files: `docs/reference/` client docs (2.9 MB), filter experiment JSONs (~2 MB).

**Not in git (ignored):** `creds/`, `data/`, `emails/`, `all_emails/`, `repurpose_inbox/`, `repurpose_site/`, `delet/`, `.env`, `docs/report-runs.jsonl`, `Ainews.mp4`, `15578431.gif`, `usage_data_*`.

## 2. USB (manual) — sizes measured today

| Item | Size | Give it? | Why |
|---|---:|---|---|
| `all_emails/` | **2.7 GB** | **Yes** (or a 3–5 folder subset) | the live article archive; the report/editor links point into it |
| `data/` | **5.2 MB** | **Yes, sanitised** | `msme.sqlite3` (241 checklist rows, 24 filter results), `settings.json`, `filter_settings.json` |
| `creds/` (4 live files) | **~2.5 KB** | **Yes** | `gmail.json`, `drive.json`, `sheets.json`, `deepseek.json` — shared project Gmail |
| `emails/` | 694 MB | Optional | legacy archive / old test pages; the live report does not read it |
| `repurpose_inbox/` | 182 MB | Optional | only if he continues mid-stream; it can be rebuilt from ACCEPT rows |
| `repurpose_site/` | 35 MB | Optional | build output; the engine can rebuild it |
| `delet/` | 878 MB | **No** | old/duplicate material, manual-review only |
| `Ainews.mp4` · `15578431.gif` · `usage_data_*` | ~10 MB | **No** | demo/junk, not project data |

### Minimum USB that still works

1. `data/msme.sqlite3` + `data/settings.json` + `data/filter_settings.json` (sanitised).
2. `creds/{gmail,drive,sheets,deepseek}.json` (or send via password manager).
3. 3–5 folders from `all_emails/` for sample articles (or the full 2.7 GB for the full report).
4. `.env` values — **password manager, not USB** (`TYPESAFE_API_KEY`, `DEEPSEEK_API_KEY`,
   bootstrap user/password).
5. Repurpose: nothing extra — the engine ships in the image (`D40`); `/repurpose.html` shows the queue.

## 3. Never hand over

- `.env` (live keys).
- The **6 archived client secrets** in `creds/`: `ai_sme.json`, `ai_sme_last.json`, `last.json`,
  `mse_ai_app.json`, `client_secret_new.json`, `client_secret_2_*.json` — rotate or keep local (`D3`).
- The Cloudflare tunnel token (`T-046`).
- `delet/` and the demo media.

## 4. Sanitise the data snapshot before copying

```bash
mkdir -p /media/usb/msme-handover/data
cp data/settings.json data/filter_settings.json /media/usb/msme-handover/data/
sqlite3 data/msme.sqlite3 ".backup '/media/usb/msme-handover/data/msme.sqlite3'"
sqlite3 /media/usb/msme-handover/data/msme.sqlite3 \
  "DELETE FROM sessions; DELETE FROM login_attempts; DELETE FROM audit_log;"
# blank the keys in the copied settings.json (keep the rest)
python3 - <<'PY'
import json
p='/media/usb/msme-handover/data/settings.json'
d=json.load(open(p))
for k in ('DEEPSEEK_API_KEY','GEMINI_API_KEY'):
    if k in d: d[k]=''
json.dump(d, open(p,'w'), indent=2)
PY
```

Keep in the snapshot: `users` (admin/MG123/user1), `checklist` (241), `filter_results` (24),
`pipeline_results`. The `sessions`/`login_attempts`/`audit_log` rows are removed (live sessions and
your IPs).

## 5. Copy the archive

```bash
# full archive
rsync -a --info=progress2 all_emails/ /media/usb/msme-handover/all_emails/
# or a small sample (3 folders)
mkdir -p /media/usb/msme-handover/all_emails
rsync -a all_emails/<folder-1> all_emails/<folder-2> all_emails/<folder-3> /media/usb/msme-handover/all_emails/
```

`all_emails/` is client material: use an encrypted USB or an encrypted archive.

## 6. Push commands (you run them)

```bash
git fetch origin
git status                       # no creds/ data/ .env/ all_emails/ staged
git add -A
git commit -m "handover: msme/ package reorg, auth, docs grouping, meeting brief"
git tag handover-20261103
git push origin main --tags
```

Then GitHub → Settings → Collaborators → add the partner with **Write**.

## 7. Partner setup after the pull

```bash
git clone https://github.com/hisham733/msme-service.git
cd msme-service
mkdir -p creds data emails all_emails repurpose_inbox repurpose_site
cp .env.example .env             # fill keys; COOKIE_SECURE=false; ENABLE_AUTO=false;
                                 # REPURPOSE_INPROCESS=false; REPLY_ENABLED=false
# copy the USB data/ + creds/ + (optional) all_emails/ into place
docker compose up -d --build
curl -s localhost:8899/health
python3 -m unittest discover -s tests -p 'test_*.py'   # 191 pass
```

Keep `ENABLE_AUTO=false` while your instance polls the same mailbox — the first poller consumes the
UNREAD label (`msme/receive/gmail.py`).
