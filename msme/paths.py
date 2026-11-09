# =============================================================================
# FILE HEADER
# file    : msme/paths.py
# role    : Shared — filesystem paths resolved from the repository root
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : resolve every runtime directory once (static, docs, prompts, data, creds,
#           archives, repurpose) from the package location, not the current working
#           directory; each one is still overridable by its environment variable.
# pages   : n/a
# calls   : os, pathlib only (no config import — avoids a cycle)
# called  : config, settings_store, filter_log, filter, filter_service, dashboard,
#           main, llm, creds, repurpose_export, repurpose_worker, workflow_lab
# amend   : add a directory here and its env var, then consume paths.<NAME>; never
#           rebuild a path from __file__ in a feature module.
#           Test: python3 -c "from msme import paths; print(paths.ROOT, paths.DOCS)"
# =============================================================================
"""Central filesystem paths for the MSME service.

`ROOT` is the repository root (the parent of the `msme` package). Every directory
defaults to a child of `ROOT`, so the service behaves the same whether it is
started from the repo, from Docker (`/app`), or from another working directory.
An environment variable wins when set; a relative value is anchored at `ROOT`.
"""
import os
from pathlib import Path

ROOT = Path(os.environ.get("MSME_ROOT") or Path(__file__).resolve().parent.parent).resolve()


def _dir(env: str, default: str) -> Path:
    """Resolve a directory: env value if set, else ROOT/<default>; relative -> ROOT."""
    raw = os.environ.get(env)
    p = Path(raw) if raw else (ROOT / default)
    return p if p.is_absolute() else (ROOT / p)


def resolve(value, default) -> Path:
    """Absolute path for `value`, falling back to `default`; relative -> ROOT."""
    p = Path(value) if value else Path(default)
    return p if p.is_absolute() else (ROOT / p)


STATIC = _dir("STATIC_DIR", "static")
DOCS = _dir("DOCS_DIR", "docs")
PROMPTS = _dir("PROMPT_DIR", "prompts")
DATA = _dir("DATA_DIR", "data")
CREDS = _dir("CREDS_DIR", "creds")
ARCHIVE = _dir("ARCHIVE_DIR", "all_emails")
LEGACY_ARCHIVE = _dir("LEGACY_ARCHIVE_DIR", "emails")
REPURPOSE_INBOX = _dir("REPURPOSE_INBOX", "repurpose_inbox")
REPURPOSE_SITE = _dir("REPURPOSE_SITE", "repurpose_site")
GALLERY = _dir("GALLERY_DIR", "data/gallery")
