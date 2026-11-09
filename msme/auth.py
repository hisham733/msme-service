# =============================================================================
# FILE HEADER
# file    : msme/auth.py
# role    : Security — local login, roles, CSRF and the single request gate
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : scrypt passwords, SQLite sessions, a 7-day HttpOnly cookie, CSRF tokens,
#           the admin/editor access matrix, one-time bootstrap and audit helpers.
# pages   : backs /login, /account.html, /users.html and every protected route
# calls   : config, db; stdlib only (no FastAPI in the gate)
# called  : combined.py (AuthGate + bootstrap), dashboard.py, filter_service.py
# amend   : the public allowlist is a security boundary — add a path only with a reason.
#           The webhook stays public (Pub/Sub OIDC is its auth). Test: python3 -m unittest tests.test_auth -v
# =============================================================================
"""Local login, roles, CSRF and the ASGI gate for the combined app.

Example:
    login  -> cookie `msme_session` (HttpOnly) + `msme_csrf` (readable by auth.js)
    gate   -> anonymous page = 302 /login, anonymous API = 401, wrong role = 403
"""
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from http.cookies import SimpleCookie
from urllib.parse import quote

from msme import config, db

SESSION_COOKIE = "msme_session"
CSRF_COOKIE = "msme_csrf"
USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]{3,32}$")

# Paths that never need a session. `/webhooks/gmail` is guarded by Pub/Sub OIDC.
PUBLIC = {
    "/health", "/api/health", "/login", "/login.html",
    "/api/auth/login", "/webhooks/gmail", "/auth.js", "/favicon.ico",
}
# Self-service routes available to any signed-in role.
SELF = {"/api/auth/me", "/api/auth/logout", "/api/auth/password", "/account.html"}
EDITOR_GET = {
    "/editor.html", "/filter-config.html", "/filters.json",
    "/config.json", "/config-versions",
    "/api/senders.json", "/api/sender.json",
    # The AI Model page is now the Cost page: admin-only (with /api/costs.json,
    # /api/models.json, the webhook toggle and Google reconnect).
}
EDITOR_GET_PREFIXES = ("/api/editor/", "/repurpose-site/", "/config-versions/")

_SCRYPT_N = 2 ** 14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_LEN = 64
_SCRYPT_MAXMEM = 64 * 1024 * 1024
_DUMMY = [""]


# --- Passwords ---------------------------------------------------------------

def _b64(raw):
    return base64.b64encode(raw).decode("ascii")


def hash_password(password):
    """Return a salted scrypt string: scrypt$N$r$p$salt$hash."""
    salt = os.urandom(16)
    dk = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R,
        p=_SCRYPT_P, dklen=_SCRYPT_LEN, maxmem=_SCRYPT_MAXMEM,
    )
    return f"scrypt${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${_b64(salt)}${_b64(dk)}"


def verify_password(password, stored):
    """Constant-time check against a stored scrypt string (False on any error)."""
    if not password or len(password) > 1024:
        return False
    try:
        algo, n, r, p, salt_b64, hash_b64 = (stored or "").split("$")
        if algo != "scrypt":
            return False
        n, r, p = int(n), int(r), int(p)
        if n > 2 ** 16 or r > 16 or p > 4:
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        dk = hashlib.scrypt(
            password.encode("utf-8"), salt=salt, n=n, r=r, p=p,
            dklen=len(expected), maxmem=_SCRYPT_MAXMEM,
        )
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


def dummy_hash():
    """A real hash used for unknown usernames so timing does not reveal them."""
    if not _DUMMY[0]:
        _DUMMY[0] = hash_password(secrets.token_urlsafe(24))
    return _DUMMY[0]


def validate_password(password):
    """Return an error message, or "" when the password is acceptable."""
    if not password:
        return "Password is required."
    if len(password) < config.PASSWORD_MIN_LENGTH:
        return f"Password must be at least {config.PASSWORD_MIN_LENGTH} characters."
    if len(password) > 256:
        return "Password is too long (max 256)."
    return ""


def validate_username(username):
    return "" if USERNAME_RE.fullmatch((username or "").strip()) else (
        "Username must be 3-32 characters: letters, digits, dot, dash or underscore."
    )


# --- Sessions / CSRF ---------------------------------------------------------

def new_token():
    return secrets.token_urlsafe(32)


def token_hash(token):
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def create_session(user_id, ip="", user_agent=""):
    """Create a session row; return (raw token, csrf token)."""
    token = new_token()
    csrf = secrets.token_urlsafe(24)
    expires = int(time.time()) + config.SESSION_DAYS * 86400
    db.create_session(token_hash(token), user_id, csrf, expires, ip, user_agent)
    return token, csrf


def load_session(token):
    return db.get_session(token_hash(token)) if token else None


def _cookie(name, value, max_age, httponly):
    parts = [f"{name}={value}", "Path=/", f"Max-Age={int(max_age)}", "SameSite=Lax"]
    if httponly:
        parts.append("HttpOnly")
    if config.COOKIE_SECURE:
        parts.append("Secure")
    return "; ".join(parts)


def session_cookie(token):
    return _cookie(SESSION_COOKIE, token, config.SESSION_DAYS * 86400, True)


def csrf_cookie(token):
    return _cookie(CSRF_COOKIE, token, config.SESSION_DAYS * 86400, False)


def clear_session_cookie():
    return _cookie(SESSION_COOKIE, "", 0, True)


def clear_csrf_cookie():
    return _cookie(CSRF_COOKIE, "", 0, False)


def parse_cookies(header):
    out = {}
    if not header:
        return out
    try:
        jar = SimpleCookie()
        jar.load(header)
        out = {k: v.value for k, v in jar.items()}
    except Exception:
        pass
    return out


def csrf_required(path, method):
    return method in ("POST", "PUT", "PATCH", "DELETE") and path not in (
        "/api/auth/login", "/webhooks/gmail",
    )


# --- Request helpers ---------------------------------------------------------

def headers_dict(scope):
    out = {}
    for k, v in scope.get("headers") or []:
        try:
            out[k.decode("latin-1").lower()] = v.decode("latin-1")
        except Exception:
            continue
    return out


def client_ip(scope):
    h = headers_dict(scope)
    ip = (h.get("cf-connecting-ip") or "").strip()
    if not ip:
        ip = (h.get("x-forwarded-for") or "").split(",")[0].strip()
    if not ip:
        ip = (scope.get("client") or ("", 0))[0]
    return ip[:64]


def user_agent(scope):
    return (headers_dict(scope).get("user-agent") or "")[:300]


def actor_from_scope(scope):
    return (scope or {}).get("msme_user") or None


def session_token_from_scope(scope):
    return parse_cookies(headers_dict(scope).get("cookie", "")).get(SESSION_COOKIE, "")


# --- Access matrix -----------------------------------------------------------

def _is_editor_allowed(path, method):
    if method != "GET":
        return path == "/config.json" and method == "PUT"
    if path in EDITOR_GET:
        return True
    return any(path.startswith(p) for p in EDITOR_GET_PREFIXES)


def evaluate(path, method, role):
    """Return 'public' | 'login' | 'allow' | 'forbidden'."""
    method = (method or "GET").upper()
    if path in PUBLIC:
        return "public"
    if not role:
        return "login"
    if path in SELF:
        return "allow"
    if role == "admin":
        return "allow"
    if _is_editor_allowed(path, method):
        return "allow"
    return "forbidden"


def is_html(path):
    return path == "/" or path.endswith(".html")


# --- Audit -------------------------------------------------------------------

_SECRET_HINTS = ("KEY", "SECRET", "PASSWORD", "TOKEN")


def sanitize(value):
    """Deep-copy a dict/list with secret-looking values masked (never log a key)."""
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if v and any(h in str(k).upper() for h in _SECRET_HINTS):
                out[k] = "********"
            else:
                out[k] = sanitize(v)
        return out
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    return value


def audit(action, actor=None, target_type="", target_id="", before=None, after=None, scope=None):
    actor = actor or {}
    try:
        db.add_audit(
            actor_id=actor.get("id"), actor_username=actor.get("username", ""),
            action=action, target_type=target_type, target_id=target_id,
            before_json=json.dumps(sanitize(before), ensure_ascii=False) if before is not None else "",
            after_json=json.dumps(sanitize(after), ensure_ascii=False) if after is not None else "",
            ip=client_ip(scope) if scope else "",
            user_agent=user_agent(scope) if scope else "",
        )
    except Exception as e:
        print(f"[auth] audit failed ({action}): {e}")


# --- Bootstrap / rate limit --------------------------------------------------

def ensure_bootstrap_admin():
    """Create the first admin from env only while the users table is empty."""
    if db.count_users() > 0:
        return None
    username = config.AUTH_BOOTSTRAP_USERNAME
    password = config.AUTH_BOOTSTRAP_PASSWORD
    if not username or not password:
        print("[auth] no users yet; set AUTH_BOOTSTRAP_USERNAME/PASSWORD once")
        return None
    err = validate_username(username) or validate_password(password)
    if err:
        print(f"[auth] bootstrap refused: {err}")
        return None
    uid = db.create_user(username, hash_password(password), "admin", must_change_password=0)
    audit("user.bootstrap", after={"username": username, "role": "admin"})
    print(f"[auth] bootstrap admin created: {username}")
    return uid


def startup_cleanup():
    try:
        db.cleanup_sessions()
        db.cleanup_login_attempts(int(time.time()) - 7 * 86400)
    except Exception as e:
        print(f"[auth] cleanup failed: {e}")


def login_locked(username, ip):
    since = int(time.time()) - config.LOGIN_LOCK_MINUTES * 60
    return db.count_login_failures(username, ip, since) >= config.LOGIN_MAX_ATTEMPTS


# --- ASGI responses ----------------------------------------------------------

async def _send(send, status, body, headers):
    headers = [(b"cache-control", b"no-store")] + headers
    headers.append((b"content-length", str(len(body)).encode()))
    await send({"type": "http.response.start", "status": status, "headers": headers})
    await send({"type": "http.response.body", "body": body})


async def json_response(send, status, payload, extra_headers=None):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = [(b"content-type", b"application/json; charset=utf-8")]
    headers += extra_headers or []
    await _send(send, status, body, headers)


async def text_response(send, status, text):
    await _send(send, status, text.encode("utf-8"), [(b"content-type", b"text/plain; charset=utf-8")])


async def redirect(send, location):
    await _send(send, 302, b"", [(b"location", location.encode("latin-1"))])


class AuthGate:
    """ASGI wrapper: session lookup, role matrix, CSRF and user injection."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path") or "/"
        method = (scope.get("method") or "GET").upper()
        csrf_header = headers_dict(scope).get("x-csrf-token", "")
        token = session_token_from_scope(scope)
        session = load_session(token) if token else None
        role = session.get("role") if session else None
        decision = evaluate(path, method, role)

        if decision == "login":
            if is_html(path):
                next_path = quote(path, safe="/?=&")
                await redirect(send, f"/login?next={next_path}")
            else:
                await json_response(send, 401, {"error": "unauthorized"})
            return
        if decision == "forbidden":
            if is_html(path):
                await text_response(send, 403, "Forbidden. Ask an administrator for access.")
            else:
                await json_response(send, 403, {"error": "forbidden"})
            return

        if decision != "public" and csrf_required(path, method):
            if not session or not csrf_header or not hmac.compare_digest(
                    csrf_header, session.get("csrf_token", "")):
                await json_response(send, 403, {"error": "csrf"})
                return

        if session and session.get("must_change_password") and decision != "public":
            allowed = path in SELF or path.startswith("/api/auth/")
            if not allowed:
                if is_html(path):
                    await redirect(send, "/account.html")
                else:
                    await json_response(send, 403, {"error": "password change required"})
                return

        scope = dict(scope)
        scope["msme_user"] = session
        scope["msme_token_hash"] = token_hash(token) if token else ""
        scope["msme_ip"] = client_ip(scope)
        await self.app(scope, receive, send)
