#!/usr/bin/env python3
"""One-time export of n8n OAuth credentials into creds/*.json for the Python service.

Reads the n8n database (mounted at /data) with the known encryption key and writes
creds/{gmail,sheets,drive,deepseek}.json in a format the service understands.

Usage:
    docker run --rm -v n8n_n8n_data:/data -v "$PWD":/wf \
        -w /wf python:3.12-alpine sh -c "pip install cryptography -q && python3 export_creds.py"

Output example (creds/gmail.json):
    {
      "clientId": "...", "clientSecret": "...",
      "oauthTokenData": {"access_token": "...", "refresh_token": "...", ...}
    }
"""
import base64
import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from msme import paths

# n8n's default encryption key (from its .env / docker-compose).
KEY = b"Ny1AASN78DLeRqTpF8aPuR3+M6eepYRm"
DB = os.environ.get("N8N_DB", "/data/database.sqlite")
OUT = os.environ.get("CRED_OUT") or str(paths.CREDS)

# n8n credential ids we use
CREDS = {
    "gmail": "RHqkBArAKb3yUzF9",      # Gmail account 6 (working)
    "sheets": "NNUUQaV0XfQLKWxe",     # Google Sheets account 2 (working)
    "drive": "bxqmIs8njqBr2Eyg",      # Google Drive account 5 (working)
    "deepseek": "tY7AnRzWG343mb5k",   # DeepSeek account
}


def decrypt(c):
    """Decrypt an n8n credential blob (OpenSSL-style AES-256-CBC + EVP_BytesToKey)."""
    raw = base64.b64decode(c)
    salt, ct = raw[8:16], raw[16:]
    d = b""
    prev = b""
    while len(d) < 48:
        prev = hashlib.md5(prev + KEY + salt).digest()
        d += prev
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    dec = Cipher(algorithms.AES(d[:32]), modes.CBC(d[32:48])).decryptor()
    pt = dec.update(ct) + dec.finalize()
    return pt[:-pt[-1]]


def main():
    """Read each credential row from n8n's sqlite DB and write creds/<name>.json."""
    c = sqlite3.connect(DB)
    os.makedirs(OUT, exist_ok=True)
    for name, cid in CREDS.items():
        row = c.execute("select data from credentials_entity where id=?", (cid,)).fetchone()
        if not row:
            print(f"[skip] {name}: credential {cid} not found")
            continue
        body = json.loads(decrypt(row[0]).decode())
        out_path = os.path.join(OUT, f"{name}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(body, f, indent=2)
        print(f"[ok] {name} -> {out_path}")
    print("done.")


if __name__ == "__main__":
    main()
