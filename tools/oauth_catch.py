#!/usr/bin/env python3
"""Catch the Google OAuth redirect on :8080 and mint creds (runs in a container).

Prints the consent URL to stdout/logs, waits for GET /?code=..., exchanges it,
writes creds/{gmail,drive,sheets}.json, then exits.
"""
import http.server
import json
import os
import socketserver
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from msme import paths

CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
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
_code = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if "code" in q:
            _code["code"] = q["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>Authorised. You can close this tab.</h2>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(("error: " + q.get("error", ["no code"])[0]).encode())

    def log_message(self, *a):
        pass


def main():
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
    }
    url = AUTH_URL + "?" + urllib.parse.urlencode(params)
    print("CONSENT_URL=" + url, flush=True)

    port = int(urllib.parse.urlparse(REDIRECT).port or 8080)
    with socketserver.TCPServer(("0.0.0.0", port), Handler) as srv:
        srv.timeout = 600
        while "code" not in _code:
            srv.handle_request()

    data = urllib.parse.urlencode({
        "code": _code["code"],
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT,
        "grant_type": "authorization_code",
    }).encode()
    tok = json.loads(urllib.request.urlopen(urllib.request.Request(TOKEN_URL, data=data)).read())
    refresh = tok.get("refresh_token")
    if not refresh:
        print("ERROR: no refresh_token", flush=True)
        sys.exit(2)
    scope = tok.get("scope", "")
    paths.CREDS.mkdir(parents=True, exist_ok=True)
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
        with open(paths.CREDS / (name + ".json"), "w", encoding="utf-8") as f:
            json.dump(body, f, indent=2)
        print("WROTE creds/%s.json" % name, flush=True)
    print("OK", flush=True)


if __name__ == "__main__":
    main()
