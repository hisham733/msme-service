"""Read run.json manifests — the joiner between engine stages (reply 3 §3.6)."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def skill_hash(path) -> str:
    """Content hash of a skill file, line-ending insensitive.

    A skill's identity is its text, not its checkout. `.gitattributes` (`* text=auto`) normalises a
    Windows CRLF checkout to LF in the index, so a raw-byte hash changes when nothing was edited — that
    is what turned three drafts "stale" on 2026-10-26. Normalising CRLF/CR to LF makes the stamp mean
    "these words", which is what the staleness audit is for.
    """
    data = Path(path).read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()[:12]


def path_for(folder: Path) -> Path:
    return Path(folder) / "run.json"


def read(folder: Path):
    p = path_for(folder)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return None


def write(folder: Path, **fields):
    p = path_for(folder)
    data = read(folder) or {}
    data.update(fields)
    data["updated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return data


def stamp_skills(folder: Path, files: dict):
    """Record the hash of every skill file used by a run (fine-tune provenance) — and persist it."""
    hashes = {name: skill_hash(p) for name, p in files.items() if Path(p).exists()}
    return write(folder, skills=hashes)
