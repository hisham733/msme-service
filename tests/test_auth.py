# =============================================================================
# FILE HEADER
# file    : tests/test_auth.py
# role    : Tests — local login, roles, CSRF gate, audit and filter-config versions
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : prove scrypt roundtrip, 7-day sessions, the admin/editor matrix, 401/302/403
#           decisions, CSRF rejection, rate limit, last-admin protection and versioned
#           config saves/restores with sanitized audit rows. No network.
# pages   : n/a
# calls   : auth, db, config, dashboard, filter_service, settings_store
# called  : developer / CI (python3 -m unittest tests.test_auth -v)
# amend   : all state lives in a temporary SQLite file; filter paths are patched to temp.
# =============================================================================
"""Unit tests for T-047 (login, roles, audit, filter-config versions).

Run:
    python3 -m unittest tests.test_auth -v
"""
import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import HTTPException
from starlette.requests import Request

from msme import auth, config, db, settings_store
from msme.filtering import filter as filter_judge
from msme.filtering import filter_service
from msme.receive import dashboard


def _request(role="admin", user_id=1, username="admin", path="/api/test",
             method="POST", headers=None):
    scope = {
        "type": "http", "method": method, "path": path,
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
        "client": ("127.0.0.1", 0),
        "msme_user": {"id": user_id, "username": username, "role": role,
                      "csrf_token": "csrf-test", "must_change_password": 0},
    }
    return Request(scope)


class _Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = self.tmp.name
        self.patches = [
            patch.object(db.config, "SQLITE_PATH", os.path.join(root, "auth.sqlite3")),
            patch.object(settings_store, "SETTINGS_PATH", os.path.join(root, "settings.json")),
            patch.object(filter_judge, "SETTINGS_PATH", os.path.join(root, "filter_settings.json")),
            patch.object(filter_judge, "LAB_PATH", os.path.join(root, "jev-variants.json")),
            patch.object(config, "PASSWORD_MIN_LENGTH", 12),
            patch.object(config, "SESSION_DAYS", 7),
            patch.object(config, "COOKIE_SECURE", True),
            patch.object(config, "LOGIN_MAX_ATTEMPTS", 5),
            patch.object(config, "LOGIN_LOCK_MINUTES", 15),
        ]
        for p in self.patches:
            p.start()
        db.init_db()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def _admin(self, username="admin", password="correct-horse-battery"):
        uid = db.create_user(username, auth.hash_password(password), "admin")
        return uid, password


class PasswordTests(_Base):
    def test_roundtrip(self):
        h = auth.hash_password("a-long-password-123")
        self.assertTrue(h.startswith("scrypt$"))
        self.assertTrue(auth.verify_password("a-long-password-123", h))
        self.assertFalse(auth.verify_password("wrong", h))

    def test_malformed_hash_is_false(self):
        self.assertFalse(auth.verify_password("x", "nonsense"))
        self.assertFalse(auth.verify_password("x", "scrypt$bad"))

    def test_policy(self):
        self.assertIn("12", auth.validate_password("short"))
        self.assertEqual(auth.validate_password("twelve-chars!"), "")
        self.assertIn("characters", auth.validate_username("a"))

    def test_dummy_hash_is_a_real_hash(self):
        self.assertTrue(auth.dummy_hash().startswith("scrypt$"))
        self.assertFalse(auth.verify_password("guess", auth.dummy_hash()))


class BootstrapTests(_Base):
    def test_env_bootstrap_once(self):
        with patch.object(config, "AUTH_BOOTSTRAP_USERNAME", "hisham"), \
                patch.object(config, "AUTH_BOOTSTRAP_PASSWORD", "a-very-long-password"):
            uid = auth.ensure_bootstrap_admin()
        self.assertIsNotNone(uid)
        self.assertEqual(db.count_users(), 1)
        self.assertEqual(db.get_user(uid)["role"], "admin")
        with patch.object(config, "AUTH_BOOTSTRAP_USERNAME", "other"), \
                patch.object(config, "AUTH_BOOTSTRAP_PASSWORD", "another-long-password"):
            self.assertIsNone(auth.ensure_bootstrap_admin())
        self.assertEqual(db.count_users(), 1)

    def test_short_bootstrap_password_refused(self):
        with patch.object(config, "AUTH_BOOTSTRAP_USERNAME", "hisham"), \
                patch.object(config, "AUTH_BOOTSTRAP_PASSWORD", "short"):
            self.assertIsNone(auth.ensure_bootstrap_admin())
        self.assertEqual(db.count_users(), 0)


class SessionTests(_Base):
    def test_session_roundtrip_and_expiry(self):
        uid, _ = self._admin()
        token, csrf = auth.create_session(uid)
        session = auth.load_session(token)
        self.assertEqual(session["id"], uid)
        self.assertEqual(session["username"], "admin")
        self.assertEqual(session["csrf_token"], csrf)
        self.assertIsNone(auth.load_session("not-a-token"))
        c = db._connect()
        c.execute("update sessions set expires_at=0")
        c.commit()
        c.close()
        self.assertIsNone(auth.load_session(token))

    def test_cookie_flags(self):
        c = auth.session_cookie("tok")
        self.assertIn("HttpOnly", c)
        self.assertIn("SameSite=Lax", c)
        self.assertIn("Max-Age=604800", c)
        self.assertIn("Secure", c)
        self.assertNotIn("HttpOnly", auth.csrf_cookie("tok"))

    def test_logout_deletes(self):
        uid, _ = self._admin()
        token, _ = auth.create_session(uid)
        db.delete_session(auth.token_hash(token))
        self.assertIsNone(auth.load_session(token))


class AccessTests(_Base):
    def test_public_paths(self):
        for path in ("/login", "/api/auth/login", "/api/health", "/webhooks/gmail", "/auth.js"):
            self.assertEqual(auth.evaluate(path, "GET", None), "public", path)

    def test_anonymous(self):
        self.assertEqual(auth.evaluate("/", "GET", None), "login")
        self.assertEqual(auth.evaluate("/api/run", "POST", None), "login")

    def test_editor_matrix(self):
        for path in ("/editor.html", "/filter-config.html", "/config.json",
                     "/api/editor/articles", "/config-versions", "/repurpose-site/a.png"):
            self.assertEqual(auth.evaluate(path, "GET", "editor"), "allow", path)
        self.assertEqual(auth.evaluate("/config.json", "PUT", "editor"), "allow")
        self.assertEqual(auth.evaluate("/api/auth/me", "GET", "editor"), "allow")
        for path in ("/", "/checklist.html", "/api/run", "/api/users",
                     "/config-versions/1/restore", "/api/audit", "/docs"):
            self.assertEqual(auth.evaluate(path, "POST" if path.endswith("restore") else "GET", "editor"),
                             "forbidden", path)

    def test_admin_matrix(self):
        for path in ("/", "/api/run", "/api/users", "/config-versions/1/restore", "/docs"):
            self.assertEqual(auth.evaluate(path, "POST" if path.endswith("restore") else "GET", "admin"),
                             "allow", path)

    def test_csrf_required(self):
        self.assertTrue(auth.csrf_required("/api/users", "POST"))
        self.assertFalse(auth.csrf_required("/webhooks/gmail", "POST"))
        self.assertFalse(auth.csrf_required("/api/auth/login", "POST"))
        self.assertFalse(auth.csrf_required("/config.json", "GET"))


class GateTests(_Base):
    def _run(self, gate, path, method="GET", cookie="", csrf=""):
        sent, called = [], []
        headers = []
        if cookie:
            headers.append((b"cookie", f"msme_session={cookie}".encode()))
        if csrf:
            headers.append((b"x-csrf-token", csrf.encode()))
        scope = {"type": "http", "path": path, "method": method,
                 "headers": headers, "client": ("127.0.0.1", 0)}

        async def receive():
            return {"type": "http.request", "body": b""}

        async def send(msg):
            sent.append(msg)

        async def inner(scope, receive, send):
            called.append(scope)

        asyncio.run(auth.AuthGate(inner)(scope, receive, send))
        status = next((m["status"] for m in sent if m["type"] == "http.response.start"), None)
        return status, sent, called

    def test_anonymous_page_redirects_and_api_401(self):
        gate = auth.AuthGate(None)
        status, sent, called = self._run(gate, "/")
        self.assertEqual(status, 302)
        self.assertFalse(called)
        status, _, called = self._run(gate, "/api/run", "POST")
        self.assertEqual(status, 401)

    def test_admin_passes_and_scope_has_user(self):
        uid, _ = self._admin()
        token, csrf = auth.create_session(uid)
        status, _, called = self._run(auth.AuthGate(None), "/api/run", "POST",
                                      cookie=token, csrf=csrf)
        self.assertIsNone(status)
        self.assertTrue(called)
        self.assertEqual(called[0]["msme_user"]["role"], "admin")

    def test_editor_forbidden(self):
        uid = db.create_user("ed", auth.hash_password("a-very-long-password"), "editor")
        token, _ = auth.create_session(uid)
        status, _, called = self._run(auth.AuthGate(None), "/api/run", "POST", cookie=token)
        self.assertEqual(status, 403)
        self.assertFalse(called)

    def test_csrf_blocks_and_allows(self):
        uid, _ = self._admin()
        token, csrf = auth.create_session(uid)
        status, _, called = self._run(auth.AuthGate(None), "/api/users", "POST", cookie=token)
        self.assertEqual(status, 403)
        status, _, called = self._run(auth.AuthGate(None), "/api/users", "POST",
                                      cookie=token, csrf=csrf)
        self.assertIsNone(status)
        self.assertTrue(called)

    def test_webhook_stays_public(self):
        status, _, called = self._run(auth.AuthGate(None), "/webhooks/gmail", "POST")
        self.assertIsNone(status)
        self.assertTrue(called)

    def test_must_change_password_redirects(self):
        uid, _ = self._admin()
        db.update_user(uid, must_change_password=1)
        token, _ = auth.create_session(uid)
        status, sent, called = self._run(auth.AuthGate(None), "/", cookie=token)
        self.assertEqual(status, 302)
        self.assertFalse(called)
        status, _, called = self._run(auth.AuthGate(None), "/api/auth/me", cookie=token)
        self.assertIsNone(status)
        self.assertTrue(called)
        # The forced-change page still needs /auth.js (CSRF helper) and /api/health.
        for path in ("/account.html", "/auth.js", "/api/health"):
            status, _, called = self._run(auth.AuthGate(None), path, cookie=token)
            self.assertIsNone(status, path)
            self.assertTrue(called, path)


class LoginTests(_Base):
    def test_login_sets_cookies(self):
        uid, password = self._admin("hisham", "my-long-password-1")
        response = dashboard.api_auth_login(dashboard.LoginIn(username="hisham", password=password),
                                            _request(role=None, path="/api/auth/login"))
        self.assertEqual(response.status_code, 200)
        cookies = b" ".join(v for k, v in response.raw_headers if k.lower() == b"set-cookie")
        self.assertIn(b"msme_session=", cookies)
        self.assertIn(b"msme_csrf=", cookies)
        self.assertIn(b"HttpOnly", cookies)

    def test_login_wrong_password(self):
        self._admin("hisham", "my-long-password-1")
        response = dashboard.api_auth_login(dashboard.LoginIn(username="hisham", password="wrong"),
                                            _request(role=None, path="/api/auth/login"))
        self.assertEqual(response.status_code, 401)

    def test_login_rate_limit(self):
        self._admin("hisham", "my-long-password-1")
        for _ in range(5):
            dashboard.api_auth_login(dashboard.LoginIn(username="hisham", password="wrong"),
                                     _request(role=None, path="/api/auth/login"))
        response = dashboard.api_auth_login(dashboard.LoginIn(username="hisham", password="wrong"),
                                            _request(role=None, path="/api/auth/login"))
        self.assertEqual(response.status_code, 429)

    def test_login_rejects_cross_origin(self):
        self._admin("hisham", "my-long-password-1")
        response = dashboard.api_auth_login(
            dashboard.LoginIn(username="hisham", password="my-long-password-1"),
            _request(role=None, path="/api/auth/login", headers={"origin": "https://evil.example"}))
        self.assertEqual(response.status_code, 403)

    def test_login_page_sends_both_roles_to_editor(self):
        for role in ("admin", "editor"):
            response = dashboard.login_page(_request(role=role, path="/login", method="GET"))
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.headers.get("location"), "/editor.html")

    def test_change_password_with_real_session(self):
        uid, password = self._admin("hisham", "my-long-password-1")
        token, _ = auth.create_session(uid)
        session = auth.load_session(token)
        req = _request(path="/api/auth/password", method="POST")
        req.scope["msme_user"] = session
        req.scope["msme_token_hash"] = auth.token_hash(token)
        response = dashboard.api_auth_password(
            dashboard.PasswordChangeIn(current=password, new="my-new-password-2"), req)
        self.assertEqual(response.get("ok"), True)
        row = db.get_user(uid)
        self.assertTrue(auth.verify_password("my-new-password-2", row["password_hash"]))
        self.assertFalse(auth.verify_password(password, row["password_hash"]))
        # The current session survives; other sessions are revoked by the endpoint.
        self.assertIsNotNone(auth.load_session(token))
        change = [a for a in db.list_audit(10) if a["action"] == "password.change"][0]
        self.assertEqual(change["actor_id"], uid)

    def test_change_password_rejects_wrong_current(self):
        uid, password = self._admin("hisham", "my-long-password-1")
        token, _ = auth.create_session(uid)
        session = auth.load_session(token)
        req = _request(path="/api/auth/password", method="POST")
        req.scope["msme_user"] = session
        response = dashboard.api_auth_password(
            dashboard.PasswordChangeIn(current="wrong-password", new="my-new-password-2"), req)
        self.assertEqual(response.status_code, 400)
        self.assertTrue(auth.verify_password(password, db.get_user(uid)["password_hash"]))

    def test_me_and_logout(self):
        uid, _ = self._admin()
        token, csrf = auth.create_session(uid)
        req = _request(path="/api/auth/me", method="GET")
        req.scope["msme_user"] = auth.load_session(token)
        me = dashboard.api_auth_me(req)
        self.assertEqual(me["username"], "admin")
        self.assertEqual(me["csrf"], csrf)
        db.delete_session(auth.token_hash(token))
        self.assertIsNone(auth.load_session(token))


class UserAdminTests(_Base):
    def test_last_admin_cannot_be_disabled_or_demoted(self):
        uid, _ = self._admin()
        req = _request(role="admin", user_id=uid, username="admin")
        self_deactivate = dashboard.api_users_patch(uid, dashboard.UserPatchIn(active=False), req)
        self.assertEqual(self_deactivate.status_code, 400)
        response = dashboard.api_users_patch(uid, dashboard.UserPatchIn(role="editor"), req)
        self.assertEqual(response.status_code, 400)

    def test_second_admin_allows_demotion(self):
        uid, _ = self._admin("admin1")
        uid2 = db.create_user("admin2", auth.hash_password("another-long-pass"), "admin")
        req = _request(role="admin", user_id=uid2, username="admin2")
        response = dashboard.api_users_patch(uid, dashboard.UserPatchIn(role="editor"), req)
        self.assertEqual(response.get("ok"), True)
        self.assertEqual(db.get_user(uid)["role"], "editor")

    def test_self_deactivation_blocked_with_real_session(self):
        uid1, _ = self._admin("admin1")
        uid2 = db.create_user("admin2", auth.hash_password("another-long-pass"), "admin")
        token, _ = auth.create_session(uid2)
        req = _request(path="/api/users/2", method="PATCH")
        req.scope["msme_user"] = auth.load_session(token)
        response = dashboard.api_users_patch(
            uid2, dashboard.UserPatchIn(active=False), req)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(db.get_user(uid2)["active"], 1)

    def test_create_duplicate_user(self):
        admin_uid, _ = self._admin()
        req = _request(role="admin", user_id=admin_uid)
        body = dashboard.NewUserIn(username="editor1", password="a-very-long-password", role="editor")
        first = dashboard.api_users_create(body, req)
        self.assertEqual(first["ok"], True)
        second = dashboard.api_users_create(body, req)
        self.assertEqual(second.status_code, 409)

    def test_audit_sanitizes_secrets(self):
        clean = auth.sanitize({"DEEPSEEK_API_KEY": "sk-secret", "GEMINI_API_KEY": "AIza",
                               "name": "keep", "nested": {"PASSWORD": "x"}})
        self.assertEqual(clean["DEEPSEEK_API_KEY"], "********")
        self.assertEqual(clean["GEMINI_API_KEY"], "********")
        self.assertEqual(clean["name"], "keep")
        self.assertEqual(clean["nested"]["PASSWORD"], "********")


class FilterVersionTests(_Base):
    def setUp(self):
        super().setUp()
        self.uid, _ = self._admin()
        self.req = _request(role="admin", user_id=self.uid, username="admin")

    def test_save_creates_version_and_audit(self):
        result = filter_service.update_config_json(
            {"settings": {"ACCEPT_THRESHOLD": 77}}, self.req)
        self.assertTrue(result["ok"], result)
        versions = db.list_filter_versions()
        self.assertEqual(len(versions), 1)
        self.assertEqual(versions[0]["action"], "save")
        self.assertTrue(versions[0]["actor_username"] == "admin")
        audit = db.list_audit(10)
        self.assertTrue(any(a["action"] == "filter_config.save" for a in audit))

    def test_restore_creates_new_version(self):
        first = filter_service.update_config_json({"settings": {"ACCEPT_THRESHOLD": 77}}, self.req)
        second = filter_service.update_config_json(
            {"scores": {"sme_relevance": {"weight": 5}}}, self.req)
        self.assertNotEqual(first["config_hash"], second["config_hash"])
        restored = filter_service.config_version_restore(first["version"], self.req)
        self.assertTrue(restored["ok"])
        self.assertEqual(restored["restored_from"], first["version"])
        self.assertEqual(restored["config_hash"], first["config_hash"])
        versions = db.list_filter_versions()
        self.assertEqual(versions[0]["action"], "restore")
        self.assertTrue(any(a["action"] == "filter_config.restore" for a in db.list_audit(20)))

    def test_config_endpoint_ignores_receive_settings(self):
        result = filter_service.update_config_json(
            {"settings": {"ACCEPT_THRESHOLD": 70, "ENABLE_AUTO": True,
                          "GMAIL_QUERY": "in:anywhere"}}, self.req)
        self.assertTrue(result["ok"], result)
        self.assertNotIn("ENABLE_AUTO", settings_store.load())
        self.assertNotIn("GMAIL_QUERY", settings_store.load())
        self.assertEqual(settings_store.get("ACCEPT_THRESHOLD"), 70)

    def test_editor_cannot_restore(self):
        first = filter_service.update_config_json({"settings": {"ACCEPT_THRESHOLD": 77}}, self.req)
        editor = _request(role="editor", user_id=2, username="ed")
        with self.assertRaises(HTTPException) as ctx:
            filter_service.config_version_restore(first["version"], editor)
        self.assertEqual(ctx.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
