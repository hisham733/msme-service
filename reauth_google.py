#!/usr/bin/env python3
"""One-off Google OAuth re-auth for the MSME service (Gmail + Drive).

Two-step (no background server needed):

  1)  print the consent URL:
        GOOGLE_CLIENT_ID=... GOOGLE_CLIENT_SECRET=... OAUTH_REDIRECT=http://127.0.0.1:8080/ \
        python3 reauth_google.py url

      Open it, sign in as the target account, consent. The browser will try to
      redirect to http://127.0.0.1:8080/?code=... (it will fail to load — that's
      fine). COPY the full address from the browser bar.

  2)  exchange the code for tokens and write creds/gmail.json + creds/drive.json:
        python3 reauth_google.py exchange "http://127.0.0.1:8080/?code=...&scope=..."

      (You may pass just the `code` value instead of the whole URL.)

Output files use the same shape the service reads: {clientId, clientSecret, oauthTokenData:{...}}.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

CLIENT_ID = (os.environ.get("GOOGLE_CLIENT_ID") or "").strip()
CLIENT_SECRET = (os.environ.get("GOOGLE_CLIENT_SECRET") or "").strip()
REDIRECT = os.environ.get("OAUTH_REDIRECT", "http://127.0.0.1:8080/")
SCOPES = os.environ.get(
    "OAUTH_SCOPES",
    "openid email "
    "https://www.googleapis.com/auth/gmail.modify "
    "https://www.googleapis.com/auth/drive "
    "https://www.googleapis.com/auth/spreadsheets",
).split()

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"


def print_url():
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
    }
    print(AUTH_URL + "?" + urllib.parse.urlencode(params))


def _extract_code(arg):
    if "code=" in arg:
        return urllib.parse.parse_qs(urllib.parse.urlparse(arg).query)["code"][0]
    return arg.strip()


def exchange(arg):
    code = _extract_code(arg)
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT,
        "grant_type": "authorization_code",
    }).encode()
    tok = json.loads(urllib.request.urlopen(urllib.request.Request(TOKEN_URL, data=data)).read())
    refresh = tok.get("refresh_token")
    if not refresh:
        print("ERROR: no refresh_token returned. Re-run step 1 (prompt=consent is set).")
        sys.exit(2)
    scope = tok.get("scope", "")
    os.makedirs("creds", exist_ok=True)
    for name in ("gmail", "drive", "sheets"):
        body = {
            "clientId": CLIENT_ID,
            "clientSecret": CLIENT_SECRET,
            "oauthTokenData": {
                "access_token": tok.get("access_token"),
                "refresh_token": refresh,
                "scope": scope,
                "token_type": tok.get("token_type", "Bearer"),
                "expires_in": tok.get("expires_in"),
            },
        }
        with open(os.path.join("creds", name + ".json"), "w", encoding="utf-8") as f:
            json.dump(body, f, indent=2)
        print("wrote creds/%s.json" % name)
    print("OK")


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("ERROR: set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET")
        sys.exit(1)
    if len(sys.argv) < 2 or sys.argv[1] not in ("url", "exchange"):
        print(__doc__)
        sys.exit(1)
    if sys.argv[1] == "url":
        print_url()
    else:
        if len(sys.argv) < 3:
            print("usage: reauth_google.py exchange \"<redirect_url_or_code>\"")
            sys.exit(1)
        exchange(sys.argv[2])


if __name__ == "__main__":
    main()
