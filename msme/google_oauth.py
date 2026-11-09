# =============================================================================
# FILE HEADER
# file    : msme/google_oauth.py
# role    : Shared — Google OAuth consent URL + code exchange for the Config page
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : let an admin reconnect Gmail/Drive/Sheets from /config.html without a terminal:
#           build the consent URL from creds/gmail.json and exchange the pasted redirect URL.
# pages   : backs /api/google/reauth (dashboard.py); tools/reauth_google.py reuses it
# calls   : config, paths
# called  : dashboard.py, tools/reauth_google.py
# amend   : never return, print or log a token or the client secret; write creds atomically.
#           Test: python3 -m unittest tests.test_google_oauth -v
# =============================================================================
"""Google OAuth for the in-app reconnect flow.

Two steps (the browser cannot reach a port inside the container):

1. `consent_url()` prints the Google consent URL (client id only, never the secret).
2. The browser redirects to `OAUTH_REDIRECT` (normally http://127.0.0.1:8080/) which
   fails to load; the admin copies the whole address and posts it back. `exchange()`
   turns the `code` into tokens and rewrites creds/{gmail,drive,sheets}.json.
"""
import json
import os
import urllib.parse
import urllib.request

from msme import config, paths

SCOPES = (
    "openid email "
    "https://www.googleapis.com/auth/gmail.modify "
    "https://www.googleapis.com/auth/drive "
    "https://www.googleapis.com/auth/spreadsheets"
).split()

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"


def redirect_uri():
    return (os.environ.get("OAUTH_REDIRECT") or config.OAUTH_REDIRECT
            or "http://127.0.0.1:8080/")


def _client():
    """Read clientId/clientSecret from creds/gmail.json (never expose the secret)."""
    path = paths.CREDS / "gmail.json"
    if not path.exists():
        raise FileNotFoundError("creds/gmail.json is missing")
    body = json.loads(path.read_text(encoding="utf-8"))
    client_id = str(body.get("clientId") or "").strip()
    client_secret = str(body.get("clientSecret") or "").strip()
    if not client_id or not client_secret:
        raise ValueError("creds/gmail.json has no clientId/clientSecret")
    return client_id, client_secret


def consent_url():
    """Build the Google consent URL (offline access, forced consent for a refresh token)."""
    client_id, _ = _client()
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri(),
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
    }
    return AUTH_URL + "?" + urllib.parse.urlencode(params)


def _extract_code(arg):
    arg = str(arg or "").strip()
    if not arg:
        raise ValueError("paste the redirected URL (it contains ?code=...)")
    if "code=" in arg:
        values = urllib.parse.parse_qs(urllib.parse.urlparse(arg).query).get("code")
        if not values:
            raise ValueError("the pasted URL has no code parameter")
        return values[0]
    return arg


def _write_creds(client_id, client_secret, token):
    """Write the same shape every loader expects, atomically (no half-written cred)."""
    refresh = token.get("refresh_token")
    if not refresh:
        raise ValueError("Google returned no refresh_token — run the consent step again")
    scope = token.get("scope", "")
    body = {
        "clientId": client_id,
        "clientSecret": client_secret,
        "oauthTokenData": {
            "access_token": token.get("access_token"),
            "refresh_token": refresh,
            "scope": scope,
            "token_type": token.get("token_type", "Bearer"),
            "expires_in": token.get("expires_in"),
        },
    }
    paths.CREDS.mkdir(parents=True, exist_ok=True)
    wrote = []
    for name in ("gmail", "drive", "sheets"):
        target = paths.CREDS / (name + ".json")
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(body, indent=2), encoding="utf-8")
        os.replace(tmp, target)
        wrote.append(name + ".json")
    return scope, wrote


def exchange(redirect_url_or_code):
    """Exchange the pasted redirect URL (or a bare code) for tokens; rewrite creds.

    Returns {"ok": True, "scope": ..., "wrote": [...]} — never the tokens.
    """
    client_id, client_secret = _client()
    code = _extract_code(redirect_url_or_code)
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri(),
        "grant_type": "authorization_code",
    }).encode()
    with urllib.request.urlopen(urllib.request.Request(TOKEN_URL, data=data), timeout=30) as resp:
        token = json.loads(resp.read().decode("utf-8"))
    scope, wrote = _write_creds(client_id, client_secret, token)
    return {"ok": True, "scope": scope, "wrote": wrote}
