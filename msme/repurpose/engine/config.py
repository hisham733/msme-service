"""Config for the in-process repurpose engine.

Paths come from `msme.paths` (one process, one repo), the DeepSeek key from `creds`, and the
model from `msme.config`. The engine's own `config.json` / `config.local.json` are no longer
read; the vendored defaults below are the engine's intake contract.
"""
import os
from pathlib import Path

from msme import config as app_config
from msme import creds, paths, settings_store

# The engine package root: skills/ and dlw_shell/ live beside this file.
ROOT = Path(__file__).resolve().parent

# The folder shape the repurpose stage consumes (one folder = one article).
DEFAULT_INTAKE = {
    "layout": "folder_per_release",
    "release_text_glob": "*.md",
    "release_text_exclude": ["link.md", "draft.md", "draft.prev.md", "index.md", "run.md",
                             "summary.md", "notes.md", "readme.md", "_links.md"],
    "link_names": ["Link.md", "link.md", "LINK.md"],
    "image_dirs": ["images", "originals"],
    "extra_image_dirs": [],
    "require_link": False,
}


def deep_merge(base, over):
    """Recursive dict merge; `over` wins. Lists and scalars are replaced, never concatenated."""
    out = dict(base)
    for key, value in (over or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def _chat_url() -> str:
    base = (app_config.DEEPSEEK_BASE_URL or "https://api.deepseek.com").rstrip("/")
    return base if base.endswith("/chat/completions") else base + "/chat/completions"


def _setting(key, default):
    """Runtime setting first, then the config/env default."""
    try:
        value = settings_store.get(key)
    except Exception:
        value = None
    return default if value in (None, "") else value


def load_config():
    """The engine config built from the app — no config files, no machine-local paths."""
    return {
        "email_articles_root": str(paths.REPURPOSE_INBOX),
        "dlw_root": str(paths.REPURPOSE_SITE),
        "queue_mode": "one",
        "skills": {
            "repurpose": "skills/msme-repurpose/SKILL.md",
            "image_select": "skills/msme-image-select/SKILL.md",
        },
        "llm": {
            "provider": "deepseek",
            "model": str(_setting("REPURPOSE_MODEL", app_config.REPURPOSE_MODEL)),
            "base_url": _chat_url(),
            "api_key_env": "DEEPSEEK_API_KEY",
            "temperature": float(_setting("REPURPOSE_TEMPERATURE", app_config.REPURPOSE_TEMPERATURE)),
            "retry_limit": int(_setting("REPURPOSE_RETRY_LIMIT", app_config.REPURPOSE_RETRY_LIMIT)),
        },
    }


def intake_cfg(cfg=None):
    """The intake rules with defaults applied (never mutates `cfg`)."""
    cfg = cfg if cfg is not None else load_config()
    return deep_merge(DEFAULT_INTAKE, cfg.get("intake") or {})


def api_key(cfg):
    """DeepSeek key: the app's runtime setting / creds file, then the environment."""
    return creds.deepseek_api_key() or os.environ.get("DEEPSEEK_API_KEY", "")
