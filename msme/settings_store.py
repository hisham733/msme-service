# =============================================================================
# FILE HEADER
# file    : msme/settings_store.py
# role    : Shared — persisted runtime settings
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : read/write data/settings.json (overrides config.py) and mask secrets before they reach a page.
# pages   : backs /api/config (receive) and /config.json (filter)
# calls   : config.py, json/os
# called  : creds, llm, deepseek, connection_test, main, dashboard, filter_service
# amend   : keep get_all(mask_secrets=True) masking; a new setting = key here + config default + page field.
#           Test: python3 -c "import settings_store; print(list(settings_store.get_all()))"
# =============================================================================
"""Persisted runtime settings.

Settings are stored in data/settings.json and override the config.py env defaults.

Format (data/settings.json):
    {
      "LLM_PROVIDER": "gemini",
      "DEEPSEEK_MODEL": "deepseek-flash",
      "DEEPSEEK_API_KEY": "sk-...",
      "GEMINI_API_KEY": "AIza...",
      "GEMINI_MODEL": "gemini-2.5-flash",
      "GMAIL_QUERY": "in:inbox is:unread -category:promotions",
      "CHECKLIST_SHEET_ID": "1T_XUR...",
      "CHECKLIST_TAB": "Checklist",
      "ARCHIVE_PARENT_FOLDER": "1XbFj...",
      "ENABLE_AUTO": false,
      "SCHEDULE_MINUTES": 5,
      "WEB_FETCH_MODE": "probe",
      "WEB_KNOWN_SITES": "www.pitchmystory.com/newswire/,news.cision.com/r/,mynewsdesk.com"
    }

`LLM_PROVIDER` is read fresh on every LLMClient() call → changing it in the
Config page switches the AI provider for the NEXT email immediately.

Example:
    settings_store.get("LLM_PROVIDER")            # -> "gemini"
    settings_store.get_all(mask_secrets=True)     # secrets masked with "********"
    settings_store.save({"ENABLE_AUTO": True})    # persist a change
"""
import json
import os

from msme import config, paths

SETTINGS_PATH = str(paths.resolve(os.environ.get("SETTINGS_PATH"), paths.DATA / "settings.json"))

# Editable settings: (key, default from config, is_secret?)
# Secrets are masked in the Config page and never written to logs.
FIELDS = [
    ("DEEPSEEK_API_KEY", "", True),
    ("DEEPSEEK_MODEL", config.DEEPSEEK_MODEL, False),
    ("LLM_PROVIDER", "deepseek", False),
    ("GEMINI_API_KEY", "", True),
    ("GEMINI_MODEL", "gemini-2.5-flash", False),
    ("GMAIL_QUERY", config.GMAIL_QUERY, False),
    ("GMAIL_WEB_USER", config.GMAIL_WEB_USER, False),
    ("CHECKLIST_SHEET_ID", config.CHECKLIST_SHEET_ID, False),
    ("CHECKLIST_TAB", config.CHECKLIST_TAB, False),
    ("ARCHIVE_PARENT_FOLDER", config.ARCHIVE_PARENT_FOLDER, False),
    ("ENABLE_AUTO", config.ENABLE_AUTO, False),
    ("SCHEDULE_MINUTES", config.SCHEDULE_MINUTES, False),
    ("ENABLE_LLM_ASSIST", config.ENABLE_LLM_ASSIST, False),
    ("ACCEPT_THRESHOLD", config.ACCEPT_THRESHOLD, False),
    ("ENABLE_AUTO_REPURPOSE", config.ENABLE_AUTO_REPURPOSE, False),
    ("ENABLE_AUTO_FILTER", config.ENABLE_AUTO_FILTER, False),
    ("WEB_FETCH_MODE", config.WEB_FETCH_MODE, False),
    ("WEB_KNOWN_SITES", config.WEB_KNOWN_SITES, False),
    # Gmail Push webhook (runtime toggle; the watch is created/stopped by the app).
    ("ENABLE_WEBHOOK", config.ENABLE_WEBHOOK, False),
    ("GMAIL_PUBSUB_TOPIC", config.GMAIL_PUBSUB_TOPIC, False),
    # Repurpose engine knobs (read fresh per article).
    ("REPURPOSE_MODEL", config.REPURPOSE_MODEL, False),
    ("REPURPOSE_TEMPERATURE", config.REPURPOSE_TEMPERATURE, False),
    ("REPURPOSE_RETRY_LIMIT", config.REPURPOSE_RETRY_LIMIT, False),
    ("REPURPOSE_POLL_SECONDS", config.REPURPOSE_POLL_SECONDS, False),
    # Cost rates (USD). 0 = not priced; the UI flags it instead of showing a confident $0.
    ("COST_DEEPSEEK_PER_M", 0.65, False),
    ("COST_JEV_INPUT_PER_M", 0.042, False),
    ("COST_GEMINI_PER_M", 0.65, False),
    ("COST_BUDGET_USD", 0.0, False),
]


def _ensure_dir():
    d = os.path.dirname(SETTINGS_PATH)
    if d:
        os.makedirs(d, exist_ok=True)


def load():
    """Read the settings file into a dict ({} if missing/corrupt)."""
    _ensure_dir()
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def get(key):
    """Return one setting: saved value first, else the config default, else None."""
    s = load()
    if key in s:
        return s[key]
    for k, default, _ in FIELDS:
        if k == key:
            return default
    return None


def get_all(mask_secrets=True):
    """Return all settings as a dict; secret values become '********' by default.

    Example:
        get_all()  # -> {"DEEPSEEK_API_KEY": "********", "LLM_PROVIDER": "gemini", ...}
    """
    out = {}
    for key, default, secret in FIELDS:
        val = get(key)
        if secret and mask_secrets and val:
            val = "********"
        out[key] = val
    return out


def save(patch):
    """Merge `patch` into settings.json (only known FIELDS are persisted).

    Example:
        settings_store.save({"LLM_PROVIDER": "gemini", "GEMINI_MODEL": "gemini-2.5-flash"})
    """
    s = load()
    for key in patch:
        if any(k == key for k, _, _ in FIELDS):
            s[key] = patch[key]
    _ensure_dir()
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2)
    return s
