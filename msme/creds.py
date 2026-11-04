# =============================================================================
# FILE HEADER
# file    : msme/creds.py
# role    : Shared — OAuth/key loading
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : load creds/*.json, refresh Google tokens and build gmail/sheets/drive services; expose the LLM API key
#           (settings first, file second).
# pages   : n/a
# calls   : google-auth, googleapiclient, config, settings_store
# called  : gmail callers, checklist, drive_fetch, reply, main, dashboard, connection_test
# amend   : never log token contents; a new service = new loader + creds/<service>.json.
#           Test: python3 -c "import creds; print(bool(creds.deepseek_api_key()))"
# =============================================================================
"""Load Google OAuth credentials and the DeepSeek key.

Credentials are exported from the n8n database by export_creds.py into
creds/*.json. Each file is the n8n credential body::
    { "clientId": ..., "clientSecret": ..., "oauthTokenData": { "access_token",
      "refresh_token", "expires_in", "scope", "token_type", "n8n_expires_at", ... } }

Example usage:
    gmail_svc  = creds.gmail()    # Google API service (messages.list, etc.)
    sheets_svc = creds.sheets()   # spreadsheet values().append(...)
    drive_svc  = creds.drive()    # files().list(...), files().get_media(...)
    key        = creds.deepseek_api_key()   # DeepSeek API key (settings first)
"""
import json

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from msme import config, paths, settings_store

_SCOPES = {
    "gmail": "https://www.googleapis.com/auth/gmail.modify",
    "sheets": "https://www.googleapis.com/auth/spreadsheets",
    "drive": "https://www.googleapis.com/auth/drive",
}


def load_oauth_credentials(cred_path: str, scope: str) -> Credentials:
    """Build a google.oauth2 Credentials object from an n8n-exported cred file.

    n8n stores client id/secret at the top level and the tokens under
    `oauthTokenData`. The refresh_token lets googleapiclient auto-refresh.
    """
    with open(cred_path, "r", encoding="utf-8") as f:
        body = json.load(f)
    token_data = body["oauthTokenData"]
    creds = Credentials(
        token=token_data.get("access_token", ""),
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=body.get("clientId", ""),
        client_secret=body.get("clientSecret", ""),
        scopes=[scope],
    )
    return creds


def _service(api_name, version, cred_path, scope):
    """Build an authenticated Google API client for one API."""
    creds = load_oauth_credentials(cred_path, scope)
    return build(api_name, version, credentials=creds)


def gmail():
    """Authenticated Gmail API v1 service (read/modify)."""
    return _service("gmail", "v1", config.GMAIL_CRED, _SCOPES["gmail"])


def sheets():
    """Authenticated Google Sheets API v4 service (append checklist rows)."""
    return _service("sheets", "v4", config.SHEETS_CRED, _SCOPES["sheets"])


def drive():
    """Authenticated Google Drive API v3 service (media-kit walk + downloads)."""
    return _service("drive", "v3", config.DRIVE_CRED, _SCOPES["drive"])


def deepseek_api_key() -> str:
    """DeepSeek API key: runtime setting first, else creds/deepseek.json.

    Priority: settings.DEEPSEEK_API_KEY > creds/deepseek.json > "".
    """
    key = settings_store.get("DEEPSEEK_API_KEY") or ""
    if key:
        return key
    deepseek_cred = paths.CREDS / "deepseek.json"
    if deepseek_cred.exists():
        with open(deepseek_cred, "r", encoding="utf-8") as f:
            body = json.load(f)
        return body.get("apiKey", body.get("api_key", ""))
    return ""
