# =============================================================================
# FILE HEADER
# file    : msme/config.py
# role    : Shared configuration — env-overridable defaults
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : central constants: ports, paths, archive root, sheet id, models, Gmail query, API endpoints.
# pages   : n/a
# calls   : os only
# called  : almost every module; runtime-tweakables are overridden by settings_store
# amend   : add a constant + its env var + the docker-compose entry together; never put a secret literal here.
#           Test: python3 -c "import config; print(config.API_PORT)"
# =============================================================================
"""Central configuration for the MSME newsbot service.

Every value can be overridden by environment variables (used by the Docker
`-e` flags). The runtime-tweakable settings (provider, keys, sheet, gmail query,
auto-poll) live separately in `data/settings.json` via `settings_store`.

Example run:
    API_HOST=0.0.0.0 API_PORT=8898 DASH_PORT=8899 \
    LOCAL_ARCHIVE_DIR=/app/emails SETTINGS_PATH=data/settings.json \
    python run.py
"""
import os

from msme import paths

# --- Server ---
API_HOST = os.environ.get("API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("API_PORT", "8898"))
DASH_PORT = int(os.environ.get("DASH_PORT", "8899"))
FILTER_PORT = int(os.environ.get("FILTER_PORT", "8900"))
ENABLE_AUTO = os.environ.get("ENABLE_AUTO", "false").lower() == "true"
SCHEDULE_MINUTES = int(os.environ.get("SCHEDULE_MINUTES", "5"))

# --- DeepSeek ---
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-flash")

# --- Google ---
# Credential JSON files exported from n8n (see export_creds.py)
GMAIL_CRED = str(paths.resolve(os.environ.get("GMAIL_CRED"), paths.CREDS / "gmail.json"))
SHEETS_CRED = str(paths.resolve(os.environ.get("SHEETS_CRED"), paths.CREDS / "sheets.json"))
DRIVE_CRED = str(paths.resolve(os.environ.get("DRIVE_CRED"), paths.CREDS / "drive.json"))

# --- Google resources ---
CHECKLIST_SHEET_ID = os.environ.get("CHECKLIST_SHEET_ID", "1T_XURPN4uuC8d7YqWbRFS-0QHLXW7-Y1UQ82rJPrQCo")
CHECKLIST_TAB = os.environ.get("CHECKLIST_TAB", "Checklist")
ARCHIVE_PARENT_FOLDER = os.environ.get("ARCHIVE_PARENT_FOLDER", "1XbFjzVLOe8CVhd8YPRVKmKi2e2-JI2Lm")
GMAIL_QUERY = os.environ.get("GMAIL_QUERY", "in:inbox is:unread -category:promotions")
# Which Gmail web account the "Open email" link targets. "0" = the first signed-in
# account; set it to the connected mailbox address when several accounts are open.
GMAIL_WEB_USER = os.environ.get("GMAIL_WEB_USER", "0").strip() or "0"

# --- Storage ---
# SQLite now; MySQL schema prepared (docs/reference/future-mysql/schema_mysql.sql) for a later switch.
DB_ENGINE = os.environ.get("DB_ENGINE", "sqlite")
SQLITE_PATH = str(paths.resolve(os.environ.get("SQLITE_PATH"), paths.DATA / "msme.sqlite3"))
MYSQL_DSN = os.environ.get("MYSQL_DSN", "")

# --- Local archive (where articles + images are saved on the PC) ---
LOCAL_ARCHIVE_DIR = str(paths.resolve(os.environ.get("LOCAL_ARCHIVE_DIR"), paths.LEGACY_ARCHIVE))

# --- Filter report input ---
# The report manager reads the live receive archive, not the legacy test store.
# Override with REPORT_ARCHIVE_DIR (or FILTER_ARCHIVE_DIR for a single root).
REPORT_ARCHIVE_DIR = str(paths.resolve(os.environ.get("REPORT_ARCHIVE_DIR"), paths.ARCHIVE))

# --- Repurpose engine bridge (D35) ---
REPURPOSE_INBOX = str(paths.REPURPOSE_INBOX)
REPURPOSE_SITE = str(paths.REPURPOSE_SITE)
REPURPOSE_DASHBOARD = os.environ.get("REPURPOSE_DASHBOARD", "/repurpose-site/index.html")
# T-050/D40: run the vendored engine in a daemon thread in this process.
REPURPOSE_INPROCESS = os.environ.get("REPURPOSE_INPROCESS", "true").lower() == "true"
REPURPOSE_POLL_SECONDS = int(os.environ.get("REPURPOSE_POLL_SECONDS", "5"))
ENABLE_AUTO_REPURPOSE = os.environ.get("ENABLE_AUTO_REPURPOSE", "true").lower() == "true"
# Engine knobs editable on Config → Repurpose (read fresh per article).
REPURPOSE_MODEL = os.environ.get("REPURPOSE_MODEL", DEEPSEEK_MODEL)
REPURPOSE_TEMPERATURE = float(os.environ.get("REPURPOSE_TEMPERATURE", "0.2"))
REPURPOSE_RETRY_LIMIT = int(os.environ.get("REPURPOSE_RETRY_LIMIT", "2"))

# --- Google OAuth reconnect (Config page) ---
# Must match a redirect URI registered on the OAuth client in Google Cloud.
OAUTH_REDIRECT = os.environ.get("OAUTH_REDIRECT", "http://127.0.0.1:8080/")

# --- Image size threshold ---
# Images smaller than this (bytes) are considered social-media logos / email
# signatures, NOT real article photos, so they don't count toward hasPic /
# hasImageInArticle. Real press photos are usually MBs (1-10MB).
MIN_IMAGE_BYTES = int(os.environ.get("MIN_IMAGE_BYTES", str(1024 * 1024)))  # default 1 MB

# --- Box.com press-kit fetch (public shared links) ---
# The receive can pull media from a PUBLIC Box shared folder link (no login).
# Files larger than BOX_MAX_BYTES are skipped (e.g. print-res TIFFs); BOX_MAX_ITEMS
# bounds how many files we consider; BOX_TIMEOUT bounds each HTTP request.
BOX_MAX_BYTES = int(os.environ.get("BOX_MAX_BYTES", str(25 * 1024 * 1024)))  # 25 MB
BOX_MAX_ITEMS = int(os.environ.get("BOX_MAX_ITEMS", "40"))
BOX_TIMEOUT = int(os.environ.get("BOX_TIMEOUT", "40"))

# --- Google Drive FILE links (/file/d/<id>) ---
# The receive can fetch a single Drive FILE linked from the email body (not
# only a media-kit folder). Files larger than DRIVE_MAX_FILE_BYTES are refused
# rather than downloaded (memory safety), and the text sent to the extract AI
# is capped by EXTRACT_MAX_CHARS so a long PDF cannot overflow the prompt.
DRIVE_MAX_FILE_BYTES = int(os.environ.get("DRIVE_MAX_FILE_BYTES", str(60 * 1024 * 1024)))
EXTRACT_MAX_CHARS = int(os.environ.get("EXTRACT_MAX_CHARS", "120000"))

# --- Collect-then-select (D24) ---
# Every fetched source (attachments, Drive, OneDrive, Box, web) becomes an
# article candidate. The extract AI sees the top N, each capped to keep the
# prompt bounded, then chooses the real release.
COLLECT_CANDIDATE_MAX_CHARS = int(os.environ.get("COLLECT_CANDIDATE_MAX_CHARS", "30000"))
COLLECT_CANDIDATE_TOP_N = int(os.environ.get("COLLECT_CANDIDATE_TOP_N", "4"))
COLLECT_MAX_WEB_LINKS = int(os.environ.get("COLLECT_MAX_WEB_LINKS", "3"))

# --- Web fetching mode (D28) ---
# off   = no linked web pages/images (attachments/Drive/OneDrive/Box still work)
# known = only the configured known hosts/paths (no unknown-site probe)
# probe = generic content probe for any public article page (default)
WEB_FETCH_MODE = os.environ.get("WEB_FETCH_MODE", "probe").strip().lower()
WEB_KNOWN_SITES = os.environ.get(
    "WEB_KNOWN_SITES",
    "www.pitchmystory.com/newswire/,news.cision.com/r/,mynewsdesk.com",
)
WEB_PROBE_MAX_LINKS = int(os.environ.get("WEB_PROBE_MAX_LINKS", "2"))

# --- D25 document-processing limits ---
# A 38 MB / 906-page report must not block the single worker. Text is read only
# from the first pages and images are sampled, never exhausted.
MAX_DOC_IMAGES = int(os.environ.get("MAX_DOC_IMAGES", "10"))       # saved/classified
DOC_IMAGE_SCAN_MAX = int(os.environ.get("DOC_IMAGE_SCAN_MAX", "25"))  # examined to find 10
PDF_TEXT_MAX_PAGES = int(os.environ.get("PDF_TEXT_MAX_PAGES", "30"))
DOC_TEXT_MAX_CHARS = int(os.environ.get("DOC_TEXT_MAX_CHARS", "150000"))

# --- Images embedded in the HTML body (<img src="https://...">) ---
# Many senders inline press photos instead of attaching them. Web-sized photos
# are small (30-100 KB), so the 1 MB attachment rule does NOT apply here: a body
# image counts when its DIMENSIONS classify it as a photo (extract._kind_from_bytes).
BODY_IMAGE_MAX_BYTES = int(os.environ.get("BODY_IMAGE_MAX_BYTES", str(8 * 1024 * 1024)))
# D24: a file-size floor must never decide media by itself. Dimensions classify
# the image; this tiny floor only rejects empty/error responses (an 8.6 KB
# 250x87 logo is a valid logo, not "too small").
BODY_IMAGE_MIN_BYTES = int(os.environ.get("BODY_IMAGE_MIN_BYTES", "512"))
BODY_IMAGE_TIMEOUT = int(os.environ.get("BODY_IMAGE_TIMEOUT", "20"))
# A body logo smaller than this is an icon/signature, not a usable asset.
BODY_LOGO_MIN_DIM = int(os.environ.get("BODY_LOGO_MIN_DIM", "200"))

# --- N-1 local logo gallery (docs/new-rules/N-1-logo-gallery.md) ---
# A local, curated logo store used only when an article has no usable image.
GALLERY_ENABLED = os.environ.get("GALLERY_ENABLED", "true").lower() == "true"
GALLERY_DIR = os.environ.get("GALLERY_DIR", str(paths.GALLERY))
GALLERY_INDEX = os.environ.get("GALLERY_INDEX", str(paths.GALLERY / "index.json"))
GALLERY_MAX_FILE_BYTES = int(os.environ.get("GALLERY_MAX_FILE_BYTES", str(10 * 1024 * 1024)))
GALLERY_FUZZY_MIN = float(os.environ.get("GALLERY_FUZZY_MIN", "0.88"))
# Tier 5: the leading body window (headline + first paragraph) where an exact
# alias corroborates the 2x body repetition. Default 600 chars (N-1 §4.2/§6).
GALLERY_BODY_LEAD_CHARS = int(os.environ.get("GALLERY_BODY_LEAD_CHARS", "600"))
# PR agencies send on behalf of brands; their domains are never mapped in the index.
GALLERY_AGENCY_DOMAINS = tuple(
    d.strip().lower() for d in os.environ.get(
        "GALLERY_AGENCY_DOMAINS",
        "cision.com,mediaoutreach.com,vritimes.com",
    ).split(",") if d.strip()
)

# --- N-2 "library update" intake (docs/new-rules/N-2-library-update.md) ---
# An email that only distributes a logo/building photo is a gallery update, not
# a press release: store the assets, skip verify/filter/reply, never "no article".
GALLERY_UPDATES_DIR = os.environ.get("GALLERY_UPDATES_DIR", str(paths.GALLERY / "updates"))
LIBRARY_UPDATE_MIN_CHARS = int(os.environ.get("LIBRARY_UPDATE_MIN_CHARS", "400"))
LIBRARY_UPDATE_PHRASES = tuple(
    p.strip().lower() for p in os.environ.get(
        "LIBRARY_UPDATE_PHRASES",
        "new logo,updated logo,logo update,building photograph,building photo,facade,"
        "update our records,for your records,update our library",
    ).split(",") if p.strip()
)
LIBRARY_UPDATE_NEGATIVE = tuple(
    p.strip().lower() for p in os.environ.get(
        "LIBRARY_UPDATE_NEGATIVE",
        "for immediate release,press release,media release,siaran akhbar,byline,"
        "contributed article,op-ed,opinion piece",
    ).split(",") if p.strip()
)

# --- Direct asset links (e.g. a "Click to download" image/logo) ---
ASSET_LINK_MAX_BYTES = int(os.environ.get("ASSET_LINK_MAX_BYTES", str(15 * 1024 * 1024)))
ASSET_LINK_TIMEOUT = int(os.environ.get("ASSET_LINK_TIMEOUT", "25"))
ASSET_LINK_MAX_LINKS = int(os.environ.get("ASSET_LINK_MAX_LINKS", "2"))

# --- OneDrive public share links (1drv.ms / onedrive.live.com) ---
# A browser User-Agent + cookie jar gets a guest FedAuth cookie; listing/download
# then uses the v2.0 item API on onedrive.live.com.
ONEDRIVE_MAX_FILE_BYTES = int(os.environ.get("ONEDRIVE_MAX_FILE_BYTES", str(60 * 1024 * 1024)))
ONEDRIVE_MAX_ITEMS = int(os.environ.get("ONEDRIVE_MAX_ITEMS", "40"))
ONEDRIVE_MAX_IMAGES = int(os.environ.get("ONEDRIVE_MAX_IMAGES", "15"))
ONEDRIVE_TIMEOUT = int(os.environ.get("ONEDRIVE_TIMEOUT", "30"))

# --- Public web article/speech pages (linked in the email, no attachment) ---
WEB_FETCH_MAX_BYTES = int(os.environ.get("WEB_FETCH_MAX_BYTES", str(5 * 1024 * 1024)))
WEB_IMAGE_MAX_BYTES = int(os.environ.get("WEB_IMAGE_MAX_BYTES", str(8 * 1024 * 1024)))
WEB_MAX_IMAGES = int(os.environ.get("WEB_MAX_IMAGES", "10"))
WEB_FETCH_TIMEOUT = int(os.environ.get("WEB_FETCH_TIMEOUT", "20"))

# --- Prompts ---
PROMPT_DIR = str(paths.PROMPTS)
# Versioned prompt packs: empty = the base file, e.g. "v1" = <name>.v1.txt when present.
PROMPT_VERSION = os.environ.get("PROMPT_VERSION", "").strip()

# --- Rejection reply to sender ---
# When an article is NOT ready to filter, we email the sender an apology that
# explains why + what's missing + how to resend.
#   REPLY_TO_EMAIL : the recipient. In development this is a fixed test address;
#                    later flip REPLY_MODE to "sender" to use the email's real From.
#   REPLY_MODE     : "fixed_email" (now) | "sender" (later, uses original From)
#   REPLY_ENABLED  : master switch (off while testing, on for production)
REPLY_TO_EMAIL = os.environ.get("REPLY_TO_EMAIL", "fhwvdu@gmail.com")
REPLY_MODE = os.environ.get("REPLY_MODE", "fixed_email")
REPLY_ENABLED = os.environ.get("REPLY_ENABLED", "true").lower() == "true"

# --- Gmail Push webhook ---
ENABLE_WEBHOOK = os.environ.get("ENABLE_WEBHOOK", "false").lower() == "true"
GMAIL_PUBSUB_TOPIC = os.environ.get("GMAIL_PUBSUB_TOPIC", "").strip()
WEBHOOK_AUDIENCE = os.environ.get("WEBHOOK_AUDIENCE", "").strip()
WEBHOOK_SERVICE_ACCOUNT = os.environ.get("WEBHOOK_SERVICE_ACCOUNT", "").strip()

# --- Local login (T-047) ---
# Sessions live in SQLite; the cookie holds an opaque token. COOKIE_SECURE must be
# false only for direct http://localhost access (the tunnel is HTTPS).
SESSION_DAYS = int(os.environ.get("SESSION_DAYS", "7"))
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").lower() == "true"
LOGIN_MAX_ATTEMPTS = int(os.environ.get("LOGIN_MAX_ATTEMPTS", "5"))
LOGIN_LOCK_MINUTES = int(os.environ.get("LOGIN_LOCK_MINUTES", "15"))
PASSWORD_MIN_LENGTH = int(os.environ.get("PASSWORD_MIN_LENGTH", "12"))
# One-time bootstrap: used only while the users table is empty.
AUTH_BOOTSTRAP_USERNAME = os.environ.get("AUTH_BOOTSTRAP_USERNAME", "").strip()
AUTH_BOOTSTRAP_PASSWORD = os.environ.get("AUTH_BOOTSTRAP_PASSWORD", "")

# --- Jev / TypeSafe filter (Stage-1 editorial judge) ---
# Jev is TypeSafe's System One model: POST api.typesafe.ai/v1/systemone with
# typed questions (noul/score/choice) that return calibrated probabilities.
TYPESAFE_BASE_URL = os.environ.get("TYPESAFE_BASE_URL", "https://api.typesafe.ai")
TYPESAFE_API_KEY = os.environ.get("TYPESAFE_API_KEY", "")
JEV_MODEL = os.environ.get("JEV_MODEL", "jev-latest")

# Auto-run the Jev filter inside receive when readyToFilter=true.
ENABLE_AUTO_FILTER = os.environ.get("ENABLE_AUTO_FILTER", "true").lower() == "true"

# Decision thresholds (mirrors the old n8n Stage-1 filter):
#   any hard gate >= GATE_THRESHOLD  -> REJECT immediately
#   weighted%   >= ACCEPT_THRESHOLD  -> ACCEPT (only if no gate fired)
# GATE_THRESHOLD is 0.85 (not 0.7) because Jev flags genuine press releases at
# ~0.7-0.8 on "is_it_commercial_intent" (normal PR language) simply due to
# ordinary promotional wording; only genuine hard-sell should trip a gate.
GATE_THRESHOLD = float(os.environ.get("GATE_THRESHOLD", "0.85"))
ACCEPT_THRESHOLD = float(os.environ.get("ACCEPT_THRESHOLD", "60"))

# --- DeepSeek assist alongside Jev (patterns 1 + 2) ---
# DeepSeek preprocesses (clean/translate/extract) and gives a second opinion on
# ambiguous weak-gate / borderline-weighted cases. Jev stays the calibrated router.
#
# ENABLE_LLM_ASSIST=false == NO-LLM MODE:
#   - pattern 1 (preprocess) is skipped (raw article text is judged), and
#   - pattern 2 is replaced by a deterministic router (filter._route_ambiguity):
#     any ambiguous weak gate, or a borderline weighted score, goes to a human
#     (EDITOR REVIEW) instead of an LLM tie-break. No external model is called.
ENABLE_LLM_ASSIST = os.environ.get("ENABLE_LLM_ASSIST", "true").lower() == "true"
# Ambiguity bands that trigger the second opinion (also used by the no-LLM router):
LLM_GATE_BAND = (
    float(os.environ.get("LLM_GATE_LOW", "0.5")),
    float(os.environ.get("LLM_GATE_HIGH", "0.85")),
)
LLM_WEIGHTED_BAND = (
    int(os.environ.get("LLM_W_LOW", "45")),
    int(os.environ.get("LLM_W_HIGH", "65")),
)


def load_prompt(name: str, version: str = None) -> str:
    """Read a system prompt, preferring a versioned pack when one is requested.

    `version=None` uses config.PROMPT_VERSION (env PROMPT_VERSION). An empty
    version reads the base file; e.g. version="v1" reads
    `prompts/extract_prompt.v1.txt` and falls back to the base if missing.

    Example:
        system = config.load_prompt("decide_prompt.txt")          # base / env
        system = config.load_prompt("decide_prompt.txt", "v1")    # v1 pack
    """
    v = (PROMPT_VERSION if version is None else str(version or "")).strip()
    path = os.path.join(PROMPT_DIR, name)
    if v:
        stem, ext = os.path.splitext(name)
        candidate = os.path.join(PROMPT_DIR, f"{stem}.{v}{ext}")
        if os.path.exists(candidate):
            path = candidate
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
