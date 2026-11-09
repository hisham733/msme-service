"""vision.py — read pictures, not filenames.

The image skill's founding failure was claiming a "people" rung for `1.jpg` because nothing in the
run could see the file. DeepSeek's `deepseek-flash` accepts image parts (`image_url` with a base64
data URI), so the pipeline can look at every supplied image and record what is actually in it.

Design notes
------------
* One API call per folder: every image is sent as its own labelled image part, and the model answers
  with a JSON array in the same order. Cheap, and it lets the model compare candidates inside a folder.
* Every answer is cached by (model, prompt version, file sha256) in ``analysis/imageeval/vision_cache
  .json`` — a re-run costs nothing and the cache doubles as audit evidence.
* Any image the model has not seen yet is tagged on the next call; a folder with no new files costs 0.
* Failure is soft: an untagged image is reported as ``unknown`` and the caller drops a rung rather
  than guessing. Nothing here writes into a release folder.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from msme import paths
from . import usage
from .config import api_key

CACHE = paths.DATA / "repurpose" / "vision_cache.json"
PROMPT_VERSION = "v1"
MAX_SIDE = 768
KINDS = ("people", "logo", "graph", "event-visual", "product", "junk", "unknown")

SYSTEM = """You are an image librarian for business news publishing. For each image you are shown you
answer with strict JSON and nothing else. Judge only what is visible in the pixels."""

INSTRUCTIONS = """Classify each image. Return a JSON object:
{"images":[{"id":"<the id label given>","kind":"people|logo|graph|event-visual|product|junk|unknown",
"people":<integer, number of clearly visible people, 0 if none>,
"capture":"photo|crop-art|screenshot|render|scanned",
"text_in_image":"none|some|heavy",
"subject":"<short: the brand, person or object shown, e.g. 'AFFIN BANK logo', 'three executives holding
 a drink', 'bar chart of sales', 'white Mercedes coupe'>",
"caption_facts":"<comma-separated only what is VISIBLE and nameable: e.g. 'three people, orange cups,
 backdrop with Tealive logo'. Never guess a person's name>"}]}

Definitions:
people        a photograph whose subject is one or more human beings
logo          a brand or organisation mark on a plain/flat background (no scene)
graph         a chart, plot, table, diagram or infographic — data, not a photograph
event-visual  a banner, poster, key art, stage backdrop or card with heavy text and no real scene
product       an object is the subject (vehicle, device, food, drink) and no person is the subject
junk          email signature, social icon, tracking pixel, near-blank strip, screenshot of a UI
Report every person you can see. Do not infer names, roles or brands that are not legible."""


def _cfg_load():
    from .config import load_config
    return load_config()


def prep(path: Path, max_side: int = MAX_SIDE) -> tuple[str, str]:
    """Downscale one image to a base64 JPEG data URI + the sha256 of the ORIGINAL bytes."""
    from PIL import Image
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except Exception:  # noqa: BLE001
        pass
    raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    Image.MAX_IMAGE_PIXELS = None
    with Image.open(io.BytesIO(raw)) as im:
        if hasattr(im, "draft"):
            im.draft("RGB", (max_side, max_side))
        im = im.convert("RGB")
        im.thumbnail((max_side, max_side))
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=82, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode(), sha


def _post(cfg, messages, model=None, timeout=300) -> str:
    import urllib.request
    key = api_key(cfg)
    if not key:
        raise RuntimeError("no API key in .env — vision tagging needs it")
    body = json.dumps({"model": model or cfg["llm"]["model"], "messages": messages,
                       "temperature": 0}).encode("utf-8")
    req = urllib.request.Request(cfg["llm"]["base_url"], data=body,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    usage.add(data.get("usage") or {}, data.get("model") or model or cfg["llm"]["model"])
    return data["choices"][0]["message"].get("content") or ""


def _parse_json_array(text: str) -> list:
    """Tolerate fences/prose around the JSON object."""
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < 0:
        return []
    try:
        obj = json.loads(text[start:end + 1])
    except Exception:  # noqa: BLE001
        return []
    rows = obj.get("images") if isinstance(obj, dict) else None
    return rows if isinstance(rows, list) else []


def _load_cache() -> dict:
    if CACHE.exists():
        try:
            return json.loads(CACHE.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=1, ensure_ascii=False), encoding="utf-8")


def tag_folder(paths: list[Path], cfg=None, model=None, force=False, verbose=False) -> dict:
    """Tag every image in one folder. Returns {filename: tag-dict}. Cached; only unseen files cost."""
    cfg = cfg or _cfg_load()
    model = model or cfg["llm"]["model"]
    cache = _load_cache()
    out, need = {}, []
    for p in paths:
        try:
            _uri, sha = prep(p)
        except Exception as e:  # noqa: BLE001
            out[p.name] = {"kind": "unknown", "error": f"{type(e).__name__}: {e}", "people": 0}
            continue
        key = f"{model}|{PROMPT_VERSION}|{sha}"
        hit = cache.get(key)
        if hit and not force:
            out[p.name] = {**hit, "sha": sha}
        else:
            need.append((p, sha, key))
    if need:
        parts = [{"type": "text", "text": INSTRUCTIONS + "\n\nImages in order:\n"
                  + "\n".join(f"- id: {p.name}" for p, _s, _k in need)}]
        for p, _sha, _key in need:
            parts.append({"type": "text", "text": f"IMAGE id={p.name}"})
            parts.append({"type": "image_url", "image_url": {"url": prep(p)[0]}})
        text = _post(cfg, [{"role": "system", "content": SYSTEM},
                           {"role": "user", "content": parts}], model=model)
        rows = _parse_json_array(text)
        by_id = {str(r.get("id", "")).strip(): r for r in rows if isinstance(r, dict)}
        for p, sha, key in need:
            r = by_id.get(p.name)
            if not r:                                  # model skipped it -> retry once, alone
                try:
                    solo = _post(cfg, [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": [
                            {"type": "text", "text": INSTRUCTIONS + f"\n\nOne image, id: {p.name}"},
                            {"type": "image_url", "image_url": {"url": prep(p)[0]}}]}], model=model)
                    got = _parse_json_array(solo)
                    r = got[0] if got else None
                except Exception:  # noqa: BLE001
                    r = None
            if r is None:
                out[p.name] = {"kind": "unknown", "people": 0, "sha": sha,
                               "error": "model returned no row"}
                continue
            r = {k: r.get(k) for k in ("kind", "people", "capture", "text_in_image", "subject",
                                       "caption_facts")}
            r["kind"] = r["kind"] if r["kind"] in KINDS else "unknown"
            try:
                r["people"] = int(r.get("people") or 0)
            except Exception:  # noqa: BLE001
                r["people"] = 0
            r["sha"] = sha
            cache[key] = {k: v for k, v in r.items() if k != "sha"}
            out[p.name] = r
        _save_cache(cache)
    if verbose:
        for name, t in out.items():
            print(f"    {name[:52]:54} {t.get('kind','?'):12} people={t.get('people',0)} "
                  f"{(t.get('subject') or '')[:44]}")
    return out


def tag_folders(pairs: list[tuple[str, list[Path]]], cfg=None, model=None, workers=3,
                force=False) -> dict:
    """Tag several folders in parallel (one API call each)."""
    cfg = cfg or _cfg_load()
    results = {}

    def work(pair):
        name, paths = pair
        if not paths:
            return name, {}
        if not paths:
            return name, {}
        try:
            return name, tag_folder(paths, cfg=cfg, model=model, force=force)
        except Exception as e:  # noqa: BLE001
            return name, {"__error__": {"kind": "unknown", "error": f"{type(e).__name__}: {e}"}}

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for name, tags in ex.map(work, pairs):
            results[name] = tags
    return results


if __name__ == "__main__":
    import sys
    t0 = time.time()
    paths = [Path(a) for a in sys.argv[1:]]
    tags = tag_folder(paths, verbose=True)
    print(f"{len(tags)} images in {time.time() - t0:.1f}s")
