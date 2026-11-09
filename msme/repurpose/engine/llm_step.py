"""llm_step.py — the LLM stage: DeepSeek direct API, the two SKILL.md files as the system prompt.

The API key comes from .env (never code, never logs). The exact model id is a config.json value
(MG supplies it with the key — 'Deepseek Flash 4.1 direct api from DS provider'). For tests, the
caller can inject a fake call_llm.
"""
import urllib.request
import json as jsonlib
import shutil
from pathlib import Path

from . import usage
from .config import ROOT, api_key
from .scan import find_images, find_release_text

DRAFT_CONTRACT = """Write the draft as plain markdown with EXACTLY these section headings, in this order.
NEWS articles also require 3-8 H2 subheaders INSIDE the body: each subheader is its OWN "## "
heading placed between "## Body" and "## Categories" (the body is the text before the first such
subheader). Structure:

## Branch
<classification + why>
## Title
<one line>
## Excerpt
<one sentence; news: 25-42 words with the dateline prefix>
## Body
<3-4 opening paragraphs>
## <First H2 subheader>
<2-3 paragraphs>
## <Second H2 subheader>
<2-3 paragraphs>
... (3-8 subheaders total for news; commentary: no subheaders)
## Categories
<1-4 bullets>
## Images
**featured**
- file: `ORIGINAL_FILENAME.ext`
- renamed: `Subject_MONTH_YYYY_MALAYSIA-SME.ext`
- rung: people
- caption: "one factual sentence, supplied facts only"
- why: <one line: which rung and why>

**in_body[]**
1. file: `X.jpg` · renamed: `<...>_MALAYSIA-SME.ext` · position: after "<subheader>" · caption: "..."

**captions**
- `renamed.ext`: "one factual sentence"
## Flags
<context opportunities + [FLAG] items>
## Final check
<the skill's checklist with pass/fix/flag>

Follow the two skill files for every rule. Never guess an image's people/identity from a bare
filename — if it cannot be verified from supplied material, do not claim the people rung. Never
repeat a paragraph or a section heading; every section must add new information. Reuse the site's
existing category vocabulary instead of inventing phrases."""


def replace_images_section(text: str, block: str) -> str:
    """Swap the draft's `## Images` section for the code's decision; keep everything else."""
    import re as _re
    m = _re.search(r"^##\s*Images\s*$", text, _re.M)
    if not m:
        return text.rstrip() + "\n\n" + block + "\n"
    nxt = _re.search(r"^##\s+\S", text[m.end():], _re.M)
    end = m.end() + nxt.start() if nxt else len(text)
    return text[:m.start()] + block + "\n\n" + text[end:]


def call_llm(messages, cfg) -> str:
    key = api_key(cfg)
    if not key:
        raise RuntimeError(f"no API key in .env ({cfg['llm']['api_key_env']=}) — the dashboard "
                           "Settings tab or a manual .env edit sets it")
    body = jsonlib.dumps({
        "model": cfg["llm"]["model"],
        "messages": messages,
        "temperature": cfg["llm"].get("temperature", 0.2),
    }).encode("utf-8")
    req = urllib.request.Request(
        cfg["llm"]["base_url"], data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = jsonlib.loads(resp.read().decode("utf-8"))
    usage.add(data.get("usage") or {}, data.get("model") or cfg["llm"]["model"])
    return data["choices"][0]["message"]["content"]


def draft_release(cfg, folder: Path, call=None, feedback=None) -> Path:
    """One LLM draft attempt for one release folder; returns the draft.md path.

    feedback = the failing checks from the previous attempt (bounded re-prompt loop, run.py).
    """
    from . import manifest
    folder = Path(folder)
    release = find_release_text(folder)
    if not release:
        raise FileNotFoundError(f"no release text .md in {folder}")
    images = "\n".join(f"- {p.name}" for p in find_images(folder))
    skill_paths = {k: str((ROOT / v)) for k, v in cfg["skills"].items()}
    system = "\n\n".join(Path(p).read_text(encoding="utf-8") for p in skill_paths.values())
    user = (f"Release file: {release.name}\n\n"
            f"{release.read_text(encoding='utf-8', errors='replace')}\n\n"
            f"Image files supplied (in images/ and originals/):\n{images or '(none)'}\n\n"
            f"{DRAFT_CONTRACT}")
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    if feedback:
        messages.append({"role": "user", "content":
                         "A previous attempt failed these acceptance checks:\n"
                         + "\n".join(f"- {f}" for f in feedback)
                         + "\nRewrite the COMPLETE draft fixing exactly these failures; keep "
                           "everything that already passed unchanged."})
    call = call or call_llm
    text = call(messages, cfg)
    # the IMAGE decision is NOT the model's: pipeline/imgselect.py chooses it from the pixels and the
    # story, so the prose model cannot invent a file name or guess who is in a photograph. Its
    # "## Images" section is replaced by the code's decision (measured 80% TARGET-match, v4).
    try:
        from . import imgselect
        sel = imgselect.select(folder, cfg=cfg, captions=True, use_llm=True)
        text = replace_images_section(text, imgselect.to_draft_block(sel))
        declared = sel.get("asset") or {}
        manifest.write(folder, image_rung=sel["rung"],
                       image_file=(sel["featured"] or {}).get("file", ""),
                       image_declared=declared.get("subject", ""))
        if declared:
            # D-012: the receive stage guarantees a usable picture (it emails the sender when one is
            # missing), so a picture the skill cannot find is a RECEIVE-STAGE ERROR surfaced here —
            # not an editorial HOLD a human has to re-diagnose.
            manifest.write(folder, status="image-error", error_stage="image",
                           error_detail=f"no usable picture in the folder — declared "
                                        f"{declared.get('kind')} '{declared.get('subject')}'")
    except Exception as e:  # noqa: BLE001 — an image failure must not lose the prose draft
        manifest.write(folder, image_error=f"{type(e).__name__}: {e}")
    draft_path = folder / "draft.md"
    if draft_path.exists():
        shutil.copy2(draft_path, folder / "draft.prev.md")
    draft_path.write_text(text, encoding="utf-8")
    manifest.write(folder, status="drafted", model=cfg["llm"]["model"])
    manifest.stamp_skills(folder, skill_paths)
    return draft_path
