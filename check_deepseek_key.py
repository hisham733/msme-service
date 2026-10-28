"""Check a DeepSeek API key before using it.

Checks auth + balance against the official API (a single GET, no tokens spent).

Usage:
    python check_deepseek_key.py sk-xxxxxxxx          # check a key you paste
    python check_deepseek_key.py                      # check the configured key
    python check_deepseek_key.py --model              # also list models

Exit code: 0 = OK, 1 = auth/balance problem, 2 = no key given.
"""
import json
import os
import sys
import urllib.error
import urllib.request

BASE = "https://api.deepseek.com"


def _get(path, key):
    req = urllib.request.Request(f"{BASE}{path}", headers={"Authorization": f"Bearer {key}"})
    r = urllib.request.urlopen(req, timeout=25)
    return json.loads(r.read())


def check(key, show_models=False):
    print(f"key tail: {key[-4:]}  len={len(key)}  (real DeepSeek keys are 35 chars: sk- + 32)")
    # 1) auth + balance — the cleanest single check
    try:
        bal = _get("/user/balance", key)
        print("AUTH: OK")
        print("BALANCE:", json.dumps(bal))
        available = bal.get("is_available", bal.get("isAvailable"))
        if available is False:
            print("WARNING: balance is_available = false (no credit)")
    except urllib.error.HTTPError as e:
        body = e.read()[:300].decode("utf-8", "replace")
        print(f"AUTH: FAIL [HTTP {e.code}] {body}")
        if e.code == 401:
            print("  -> key is invalid (wrong/typo/revoked), or belongs to a DIFFERENT endpoint.")
        elif e.code == 402:
            print("  -> key is valid but the account has NO BALANCE.")
        return False
    except Exception as e:
        print(f"AUTH: ERROR {type(e).__name__}: {e}")
        return False
    if show_models:
        try:
            models = _get("/models", key)
            print("MODELS:", ", ".join(m.get("id", "?") for m in models.get("data", [])))
        except Exception as e:
            print("MODELS: error", e)
    return True


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--model"]
    if args:
        key = args[0]
    else:
        key = ""
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import creds
            key = creds.deepseek_api_key()
        except Exception:
            key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        print("No key given (pass one, or configure DEEPSEEK_API_KEY).")
        sys.exit(2)
    sys.exit(0 if check(key, show_models="--model" in sys.argv) else 1)
