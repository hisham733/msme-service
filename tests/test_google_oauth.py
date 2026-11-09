"""Tests for the Config-page Google reconnect flow (no network).

Run: python3 -m unittest tests.test_google_oauth -v
"""
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from msme import google_oauth


class _FakeResponse:
    def __init__(self, body):
        self._body = body

    def __enter__(self):
        return io.BytesIO(self._body)

    def __exit__(self, *exc):
        return False


class GoogleOAuthTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.creds = Path(self.tmp.name) / "creds"
        self.creds.mkdir()
        (self.creds / "gmail.json").write_text(json.dumps({
            "clientId": "client-123.apps.googleusercontent.com",
            "clientSecret": "super-secret",
            "oauthTokenData": {"refresh_token": "old"},
        }), encoding="utf-8")
        self.patches = [
            patch.object(google_oauth.paths, "CREDS", self.creds),
            patch.object(google_oauth.config, "OAUTH_REDIRECT", "http://127.0.0.1:8080/"),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def test_consent_url_has_client_but_not_secret(self):
        url = google_oauth.consent_url()
        self.assertIn("client-123", url)
        self.assertIn("redirect_uri=http%3A%2F%2F127.0.0.1%3A8080%2F", url)
        self.assertIn("gmail.modify", url)
        self.assertNotIn("super-secret", url)

    def test_exchange_writes_all_three_creds(self):
        token = json.dumps({
            "access_token": "new-access", "refresh_token": "new-refresh",
            "scope": "gmail drive sheets", "token_type": "Bearer", "expires_in": 3600,
        }).encode()
        with patch.object(google_oauth.urllib.request, "urlopen",
                          return_value=_FakeResponse(token)):
            result = google_oauth.exchange("http://127.0.0.1:8080/?code=abc123&scope=x")
        self.assertTrue(result["ok"])
        self.assertEqual(sorted(result["wrote"]), ["drive.json", "gmail.json", "sheets.json"])
        for name in ("gmail", "drive", "sheets"):
            body = json.loads((self.creds / (name + ".json")).read_text(encoding="utf-8"))
            self.assertEqual(body["oauthTokenData"]["refresh_token"], "new-refresh")
            self.assertEqual(body["clientId"], "client-123.apps.googleusercontent.com")

    def test_bare_code_is_accepted(self):
        token = json.dumps({"refresh_token": "r", "scope": "s"}).encode()
        with patch.object(google_oauth.urllib.request, "urlopen",
                          return_value=_FakeResponse(token)):
            result = google_oauth.exchange("abc123")
        self.assertTrue(result["ok"])

    def test_missing_code_raises(self):
        with self.assertRaises(ValueError):
            google_oauth.exchange("")

    def test_missing_refresh_token_raises(self):
        token = json.dumps({"access_token": "a", "scope": "s"}).encode()
        with patch.object(google_oauth.urllib.request, "urlopen",
                          return_value=_FakeResponse(token)):
            with self.assertRaises(ValueError):
                google_oauth.exchange("abc")

    def test_api_returns_the_url(self):
        from msme.receive import dashboard
        with patch.object(dashboard.google_oauth, "consent_url", return_value="https://consent"):
            body = dashboard.api_google_reauth_url()
        self.assertEqual(body["url"], "https://consent")
        self.assertEqual(body["redirect_uri"], "http://127.0.0.1:8080/")


if __name__ == "__main__":
    unittest.main()
