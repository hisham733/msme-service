# =============================================================================
# FILE HEADER
# file    : msme/deepseek.py
# role    : Shared — DeepSeek client
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : Chat Completions with json_object + effort:low, the token-saving retry policy, and usage tallying.
# pages   : n/a
# calls   : openai client, config, creds, settings_store
# called  : llm.LLMClient
# amend   : retry rules (fail fast on 402/400, no blind retry on empty JSON) are a token guard; V4.1-Flash needs
#           effort:low. Test: python3 check_deepseek_key.py --model
# =============================================================================
"""Shared DeepSeek client (paid).

Supports Chat Completions with `response_format={"type": "json_object"}` and the
reasoning model via `extra_body={"effort": "low"}` (DeepSeek V4.1-Flash is a
reasoning model — without effort:low it often returns empty JSON).

Retry policy (token-saver):
  - Transport/rate/5xx errors  -> retry up to `retries` times.
  - HTTP 402 (no balance) / 400 (bad request) -> fail FAST, never retry.
  - HTTP 200 but empty/invalid JSON -> 1 hard re-parse, then ≤2 retries
    (reasoning models intermittently emit empty content), then give up.

Example:
    client = DeepSeekClient()           # uses settings DEEPSEEK_MODEL
    out = client.chat_json(sys, usr, max_tokens=4000)
    out["headline"]                     # parsed dict
"""
import json
import re

from openai import OpenAI

from msme import config, creds, settings_store

# Token tally accumulates across decide/extract/verify for ONE email.
_TOKEN_TALLY = {"prompt": 0, "completion": 0, "total": 0}

# Last DeepSeek error (surfaced to the pipeline so an API failure is never
# silently treated as "no article"). Shape: {"error", "status"}.
_LAST_ERROR = {"error": "", "status": None}


def last_error():
    """Return the last DeepSeek error seen, e.g. {'error': '...402...', 'status': 402}."""
    return dict(_LAST_ERROR)


def reset_token_tally():
    """Zero the tally at the start of each email."""
    _TOKEN_TALLY["prompt"] = 0
    _TOKEN_TALLY["completion"] = 0
    _TOKEN_TALLY["total"] = 0


def get_token_tally():
    """Return the DeepSeek-only token tally: {"prompt","completion","total"}."""
    return dict(_TOKEN_TALLY)


def _accum_usage(usage):
    """Add an OpenAI response.usage object into the tally."""
    p = getattr(usage, "prompt_tokens", 0) or 0
    c = getattr(usage, "completion_tokens", 0) or 0
    _TOKEN_TALLY["prompt"] += p
    _TOKEN_TALLY["completion"] += c
    _TOKEN_TALLY["total"] += (p + c)


class DeepSeekClient:
    """Minimal wrapper around the OpenAI SDK pointed at DeepSeek's base URL."""

    def __init__(self, model=None):
        self.client = OpenAI(api_key=creds.deepseek_api_key(), base_url=config.DEEPSEEK_BASE_URL)
        self.model = model or settings_store.get("DEEPSEEK_MODEL") or config.DEEPSEEK_MODEL
        self.last_usage = {}

    def chat_json(self, system, user, max_tokens=4000, temperature=0.2, retries=3):
        """Chat Completions with response_format json_object. Returns parsed dict.

        Retries ONLY on transport/rate/5xx/4xx-except-400 errors (a real failure).
        A 200 response with empty/invalid JSON is NOT blind-retried (that wastes
        tokens); we make one extra parse attempt then return what we have.

        Example:
            client.chat_json("Extract the release.", raw_text, max_tokens=12000)
            -> {"bodyText": "...", "hasLogoInArticle": False}
        """
        from openai import (
            APIConnectionError,
            APIError,
            APITimeoutError,
            RateLimitError,
        )
        last = {}
        for attempt in range(retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=max_tokens,
                    temperature=temperature,
                    extra_body={"effort": "low"},  # required for reasoning models
                )
            except (APIConnectionError, APITimeoutError, RateLimitError, APIError) as e:
                # Do NOT retry deterministic errors: 402 (balance), 400 (bad request).
                code = getattr(e, "status_code", None)
                _LAST_ERROR["error"] = f"{type(e).__name__}: {e}"
                _LAST_ERROR["status"] = code
                if code in (402, 400):
                    if code == 402:
                        print("[deepseek] FATAL: insufficient balance (402). Add credit then re-run.")
                    else:
                        print(f"[deepseek] bad request (400): {e}")
                    return {}
                print(f"[deepseek] error on attempt {attempt+1}: {type(e).__name__} {e}")
                if attempt + 1 < retries:
                    continue
                return last
            content = response.choices[0].message.content or ""
            # capture token usage
            try:
                _accum_usage(response.usage)
                self.last_usage = {
                    "prompt": getattr(response.usage, "prompt_tokens", 0) or 0,
                    "completion": getattr(response.usage, "completion_tokens", 0) or 0,
                    "total": (getattr(response.usage, "prompt_tokens", 0) or 0) + (getattr(response.usage, "completion_tokens", 0) or 0),
                }
            except Exception:
                self.last_usage = {}
            parsed = _parse_json(content)
            if parsed and any(parsed.values()):
                return parsed
            # Empty/invalid JSON on a 200: try aggressive re-parse, then up to 2
            # retries (reasoning models occasionally return empty), then stop.
            if attempt == 0:
                parsed = _parse_json_hard(content)
                if parsed and any(parsed.values()):
                    return parsed
            if attempt < 2:
                print(f"[deepseek] empty/invalid JSON on attempt {attempt+1}, retry {attempt+1}/2")
                continue
            print("[deepseek] empty/invalid JSON after retries, giving up")
            _LAST_ERROR["error"] = "model returned empty/invalid JSON"
            _LAST_ERROR["status"] = 200
            break
        return last

    def chat_plain(self, system, user, max_tokens=2000, temperature=0.2):
        """Non-JSON call returning the raw text response."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    def vision(self, image_b64, mime_type, question):
        """Vision via chat completions with an inline base64 image.

        Example:
            client.vision(img_b64, "image/png", "Does this show a logo?")
            -> "Yes, the company logo is visible in the header."
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_b64}"}},
                    ],
                }
            ],
            max_tokens=500,
        )
        return response.choices[0].message.content or ""


def _parse_json(text):
    """Normal JSON parse with ```fence tolerance + first-object fallback."""
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


def _parse_json_hard(text):
    """More aggressive JSON recovery: strip code fences, find first balanced {..},
    and try to repair trailing commas / single quotes.

    Handles the worst-case output of reasoning models like:
        '```json\\n{"headline": "X",}'   -> trailing comma repaired
    """
    if not text:
        return {}
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n?", "", t)
        t = re.sub(r"```$", "", t).strip()
    # locate the outermost balanced object
    start = t.find("{")
    end = t.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}
    candidate = t[start:end + 1]
    # repair trailing commas before } or ]
    candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
    try:
        return json.loads(candidate)
    except Exception:
        pass
    # try with single-quote repair
    try:
        import ast
        fixed = re.sub(r"'", '"', candidate)
        fixed = re.sub(r'"([^"]*)"\s*:\s*"([^"]*)"', r'"\1": "\2"', fixed)
        return ast.literal_eval(fixed)
    except Exception:
        return {}
