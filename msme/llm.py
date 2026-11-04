# =============================================================================
# FILE HEADER
# file    : msme/llm.py
# role    : Shared — provider-switchable LLM client
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : chat_json(system, user, max_tokens) over DeepSeek or Gemini, with tolerant JSON extraction and a
#           per-process token tally.
# pages   : n/a
# calls   : config, settings_store, deepseek, Gemini REST
# called  : decide, extract, verify, filter_llm, reply
# amend   : the provider switch must take effect on the next call (fresh client); keep the chat_json signature.
#           Test: python3 -c "from llm import LLMClient; print(LLMClient().provider)"
# =============================================================================
"""Unified LLM client: DeepSeek (paid) or Google Gemini (free tier).

Exposes the same `chat_json(system, user, max_tokens)` interface used by
decide/extract/verify. Provider is chosen from settings:
    LLM_PROVIDER = deepseek | gemini
DeepSeek keys in creds/deepseek.json or settings.DEEPSEEK_API_KEY.
Gemini keys in settings.GEMINI_API_KEY (or creds/gemini.json).

Every call builds a FRESH client, so switching LLM_PROVIDER in the Config page
takes effect on the very next email — no restart needed.

Example:
    client = LLMClient()
    client.provider          # "gemini"
    client.model             # "gemini-2.5-flash"
    result = client.chat_json("You are an editor.", "Classify this: ...", max_tokens=1000)
    result["headline"]       # parsed JSON dict
"""
import json
import re

from msme import paths, settings_store


def _json_extract(text):
    """Parse JSON out of a model response, tolerating ``` fences or prose.

    Example:
        _json_extract('```json\\n{"headline": "X"}\\n```')  # -> {"headline": "X"}
        _json_extract('Sure! {"headline": "X"} done.')      # -> {"headline": "X"}
    """
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
    return {}


class LLMClient:
    """Thin wrapper that picks DeepSeek or Gemini based on settings.

    Usage:
        client = LLMClient()
        json_result = client.chat_json(system_prompt, user_text, max_tokens=4000)
    """

    def __init__(self, model=None):
        # Read provider fresh every time -> live provider switching.
        provider = (settings_store.get("LLM_PROVIDER") or "deepseek").lower()
        self.provider = provider
        self.last_usage = {}
        if provider == "gemini":
            self.model = model or settings_store.get("GEMINI_MODEL") or "gemini-2.5-flash"
            self._api_key = settings_store.get("GEMINI_API_KEY") or ""
            if not self._api_key:
                gemini_cred = paths.CREDS / "gemini.json"
                if gemini_cred.exists():
                    with open(gemini_cred, "r", encoding="utf-8") as f:
                        self._api_key = json.load(f).get("apiKey", "")
        else:
            from msme.deepseek import DeepSeekClient
            self._ds = DeepSeekClient(model=model)
            self.model = self._ds.model

    def chat_json(self, system, user, max_tokens=4000, temperature=0.2):
        """Call the active provider and return a parsed JSON dict.

        Example:
            client.chat_json("You extract press releases.",
                             "Extract: {email}",
                             max_tokens=12000)
            -> {"bodyText": "...", "articleSource": "attachment_pdf"}
        """
        if self.provider == "gemini":
            return self._gemini_json(system, user, max_tokens)
        return self._ds.chat_json(system, user, max_tokens=max_tokens, temperature=temperature)

    def _gemini_json(self, system, user, max_tokens):
        """Call Gemini's generateContent REST API with response_mime_type=json."""
        import urllib.request
        body = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.2,
                "maxOutputTokens": max_tokens,
            },
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self._api_key}"
        req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                     headers={"Content-Type": "application/json"})
        for attempt in range(3):
            try:
                r = urllib.request.urlopen(req, timeout=90)
                d = json.loads(r.read())
                text = d["candidates"][0]["content"]["parts"][0]["text"]
                um = d.get("usageMetadata", {})
                pt = um.get("promptTokenCount", 0) or 0
                ct = um.get("candidatesTokenCount", 0) or 0
                _TOKEN_TALLY["prompt"] += pt
                _TOKEN_TALLY["completion"] += ct
                _TOKEN_TALLY["total"] += (pt + ct)
                self.last_usage = {"prompt": pt, "completion": ct, "total": pt + ct}
                parsed = _json_extract(text)
                if parsed and any(parsed.values()):
                    return parsed
                # retry once on empty/invalid JSON
                print(f"[gemini] empty/invalid JSON attempt {attempt+1}")
            except Exception as e:
                code = getattr(e, "code", None)
                _GEMINI_ERROR["error"] = f"{type(e).__name__}: {e}"
                _GEMINI_ERROR["status"] = code
                if code == 403:
                    print(f"[gemini] key invalid/expired: {e}")
                    return {}
                print(f"[gemini] error attempt {attempt+1}: {e}")
                if attempt < 2:
                    continue
                return {}
        _GEMINI_ERROR["error"] = "model returned empty/invalid JSON"
        _GEMINI_ERROR["status"] = 200
        return {}


# Token tally accumulates across the decide/extract/verify calls for ONE email.
_TOKEN_TALLY = {"prompt": 0, "completion": 0, "total": 0}

# Last Gemini error (DeepSeek tracks its own) — surfaced so a provider failure
# is never silently mistaken for "no article".
_GEMINI_ERROR = {"error": "", "status": None}


def last_error():
    """Return the last LLM provider error (DeepSeek or Gemini), else {'error':''}."""
    try:
        from msme.deepseek import last_error as _ds_err
        d = _ds_err()
        if d.get("error"):
            return d
    except Exception:
        pass
    return dict(_GEMINI_ERROR)


def reset_token_tally():
    """Zero the tally at the start of each email."""
    _TOKEN_TALLY["prompt"] = 0
    _TOKEN_TALLY["completion"] = 0
    _TOKEN_TALLY["total"] = 0
    try:
        from msme.deepseek import reset_token_tally as _r
        _r()
    except Exception:
        pass


def get_token_tally():
    """Return combined token usage (Gemini tally + DeepSeek tally).

    Example return:
        {"prompt": 2718, "completion": 459, "total": 3177}
    """
    try:
        from msme.deepseek import get_token_tally as _t
        d = _t()
    except Exception:
        d = {"prompt": 0, "completion": 0, "total": 0}
    d["prompt"] += _TOKEN_TALLY["prompt"]
    d["completion"] += _TOKEN_TALLY["completion"]
    d["total"] += _TOKEN_TALLY["total"]
    return d
