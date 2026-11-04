# =============================================================================
# FILE HEADER
# file    : msme/connection_test.py
# role    : Shared — connectivity checks for the Config page
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : test Gmail, Sheets, Drive and the active LLM provider; return {ok, detail} per service.
# pages   : backs /api/test-connection on receive-config.html
# calls   : creds, re
# called  : main.py, dashboard.py
# amend   : add a service = new test_* plus a line in test_all(); never echo a key or token in detail.
#           Test: POST /api/test-connection
# =============================================================================
"""Test connectivity for each external service (Config page → Test connection).

Each `test_*` returns {"ok": bool, "detail": str} so the page can show a green
check or the error message.

Example result dict:
    {
      "gmail":   {"ok": true,  "detail": "ainews.msme@gmail.com"},
      "sheets":  {"ok": true,  "detail": "sheet ok, 14 columns"},
      "drive":   {"ok": true,  "detail": "drive ok, sample 3 files"},
      "deepseek":{"ok": true,  "detail": "gemini ok, model=gemini-2.5-flash"},
    }
"""
import re

from msme import creds


def _rate_limit_detail(e):
    """Human-readable message for a Gmail API 429 rate-limit error.

    Extracts the 'Retry after <time>' from the HttpError so the dashboard can
    tell the user WHEN they can try again, instead of showing raw JSON.
    """
    m = re.search(r"Retry after ([0-9T:.Z+\-]+)", str(e))
    retry = m.group(1) if m else "later"
    return f"Gmail rate limit reached — try again after {retry}"


def test_gmail():
    """Verify the Gmail credential by reading the account profile."""
    try:
        s = creds.gmail()
        p = s.users().getProfile(userId="me").execute()
        return {"ok": True, "detail": p.get("emailAddress", "gmail ok")}
    except Exception as e:
        if "429" in str(e) or "rateLimitExceeded" in str(e) or "User-rate limit exceeded" in str(e):
            return {"ok": False, "detail": _rate_limit_detail(e)}
        return {"ok": False, "detail": str(e)[:200]}


def test_sheets():
    """Verify the Sheets credential + read the checklist header row (14 cols)."""
    try:
        s = creds.sheets()
        r = (
            s.spreadsheets()
            .values()
            .get(spreadsheetId=settings_sheet_id(), range=f"{settings_tab()}!A1:N1")
            .execute()
        )
        vals = r.get("values", [[]])
        n = len(vals[0]) if vals else 0
        return {"ok": True, "detail": f"sheet ok, {n} columns"}
    except Exception as e:
        return {"ok": False, "detail": str(e)[:200]}


def test_drive():
    """Verify the Drive credential by listing a few files."""
    try:
        d = creds.drive()
        r = d.files().list(q="trashed=false", pageSize=3, fields="files(id,name)").execute()
        return {"ok": True, "detail": f"drive ok, sample {len(r.get('files', []))} files"}
    except Exception as e:
        return {"ok": False, "detail": str(e)[:200]}


def test_deepseek():
    """Verify the ACTIVE AI provider (deepseek OR gemini) with a tiny call."""
    try:
        from msme.llm import LLMClient
        client = LLMClient()
        if client.provider == "gemini":
            r = client.chat_json("reply ok", "say OK", max_tokens=10)
            return {"ok": True, "detail": f"gemini ok, model={client.model}"}
        from msme.deepseek import DeepSeekClient
        c = DeepSeekClient()
        r = c.client.chat.completions.create(
            model=c.model,
            messages=[{"role": "user", "content": "reply ok"}],
            max_tokens=5,
        )
        return {"ok": True, "detail": f"deepseek ok, model={c.model}"}
    except Exception as e:
        return {"ok": False, "detail": str(e)[:200]}


def settings_sheet_id():
    """Checklist sheet id: runtime setting first, else config default."""
    from msme import config, settings_store
    return settings_store.get("CHECKLIST_SHEET_ID") or config.CHECKLIST_SHEET_ID


def settings_tab():
    """Checklist tab name: runtime setting first, else config default."""
    from msme import config, settings_store
    return settings_store.get("CHECKLIST_TAB") or config.CHECKLIST_TAB


def test_all():
    """Run every connectivity check and return them keyed by service name."""
    return {
        "gmail": test_gmail(),
        "sheets": test_sheets(),
        "drive": test_drive(),
        "deepseek": test_deepseek(),
    }
