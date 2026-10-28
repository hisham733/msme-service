# =============================================================================
# FILE HEADER
# file    : verify.py
# role    : Receive · AI step 3 — checklist verdict
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : headline, subjectMatch/score, readyToFilter, logo/image verdicts; deterministic finalize after the AI.
# pages   : n/a
# calls   : llm.LLMClient, config, prompts/verify_prompt.txt
# called  : pipeline.py
# amend   : readyToFilter = hasArticle AND (hasPic OR hasLogo OR hasImageInArticle) AND subjectScore > 60 —
#           a checklist contract; change with checklist.py and the Sheet. Test: one full run
# =============================================================================
"""Checklist & Verify — AI step #3.

Given the extracted article + the email subject + logo/image flags, the model
decides the final verdict:
  - headline           : the real article title
  - subjectMatch/score : does the email subject match the headline (0-100)?
  - hasArticle / hasPic / hasLogo / hasLogoInArticle / hasImageInArticle
  - readyToFilter      : ready for the next stage (human/editor filter)
  - reason             : a one-line justification

This replaces the fragile regex/math checklist logic from the old n8n build.

Example output:
    {
      "headline": "Lion Parcel Officially Expands to Malaysia...",
      "subjectMatch": true, "subjectScore": 85,
      "hasArticle": true, "hasPic": true, "hasLogo": true,
      "hasLogoInArticle": true, "hasImageInArticle": true,
      "readyToFilter": true,
      "reason": "Subject matches the headline; full release with media present."
    }
"""
import config
from llm import LLMClient

# (Optional) strict JSON schema for the Responses API. Kept for reference;
# we currently use Chat Completions json_object via LLMClient.
VERIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
        "subjectMatch": {"type": "boolean"},
        "subjectScore": {"type": "integer"},
        "hasArticle": {"type": "boolean"},
        "hasPic": {"type": "boolean"},
        "hasLogo": {"type": "boolean"},
        "hasLogoInArticle": {"type": "boolean"},
        "hasImageInArticle": {"type": "boolean"},
        "readyToFilter": {"type": "boolean"},
        "reason": {"type": "string"},
    },
    "required": [
        "headline", "subjectMatch", "subjectScore", "hasArticle", "hasPic",
        "hasLogo", "hasLogoInArticle", "hasImageInArticle", "readyToFilter", "reason",
    ],
    "additionalProperties": False,
}


def build_verify_user(article, image_names, flags, evidence=""):
    """Build the user message for the Verify AI call.

    Token saver: the verifier only needs the title + a gist of the article,
    so we send the first ~1000 chars instead of the whole bodyText.

    `article`  : {subject, from, date, bodyText}
    `flags`    : {hasPic, docLogo, docPhoto, visionLogo, aiLogo, aiImage, hasLogoFile}
    """
    body = article.get('bodyText', '') or ''
    trimmed = body[:1000] + ('…' if len(body) > 1000 else '')
    return (
        f"- Subject: {article['subject']}\n"
        f"- From: {article['from']}\n"
        f"- Date: {article['date']}\n"
        f"- Article text (trimmed):\n{trimmed}\n"
        f"- Image names: {image_names}\n"
        f"- Flags: hasPic={flags['hasPic']}, hasLogo={flags.get('hasLogo')}, "
        f"docLogo={flags['docLogo']}, "
        f"docPhoto={flags['docPhoto']}, visionLogo={flags['visionLogo']}, "
        f"aiLogo={flags['aiLogo']}, aiImage={flags['aiImage']}, "
        f"hasLogoFile={flags['hasLogoFile']}\n"
        f"- Extraction evidence: {evidence}"
    )


def _truthy(v):
    return v in (True, "true", "True", 1, "1")


def _finalize(result, image_names, flags):
    """Deterministic consistency guard on the AI verdict.

    The text-only model is prone to hallucinating hasLogoInArticle /
    hasImageInArticle (e.g. claiming a logo inside an article that was never
    retrieved). A logo/photo can only be IN the article if an article actually
    exists AND there is real visual evidence. This keeps the checklist columns
    logically consistent regardless of what the model returns.
    """
    if not isinstance(result, dict):
        return result
    names = [str(n).lower() for n in (image_names or [])]
    has_article = _truthy(result.get("hasArticle"))

    logo_evidence = (
        _truthy(flags.get("docLogo"))
        or _truthy(flags.get("visionLogo"))
        or _truthy(flags.get("aiLogo"))
        or _truthy(flags.get("hasLogoFile"))
        or any("logo" in n for n in names)
    )
    image_evidence = (
        _truthy(flags.get("docPhoto"))
        or _truthy(flags.get("aiImage"))
        or any("logo" not in n for n in names)
    )

    if not (has_article and logo_evidence):
        result["hasLogoInArticle"] = False
    if not (has_article and image_evidence):
        result["hasImageInArticle"] = False

    # Deterministic readyToFilter (do NOT trust the model): an article is ready
    # when it has substance, a media asset (a photo file, a standalone logo file,
    # OR an image/logo inside the article), and a strong subject match.
    try:
        score = int(result.get("subjectScore", 0) or 0)
    except Exception:
        score = 0
    media = (
        _truthy(flags.get("hasPic"))
        or _truthy(flags.get("hasLogo"))
        or _truthy(flags.get("hasLogoFile"))
        or _truthy(result.get("hasImageInArticle"))
        or _truthy(result.get("hasLogoInArticle"))
    )
    result["readyToFilter"] = bool(has_article and media and score > 60)
    return result


def verify(article, image_names, flags, evidence="", client=None, prompt_version=None):
    """Run the Verify AI call and return the verdict dict.

    Example:
        v = verify(article, image_names, flags, evidence)
        v["hasArticle"]   # -> True
        v["subjectScore"] # -> 85
    """
    system = config.load_prompt("verify_prompt.txt", version=prompt_version)
    # Strip the n8n template tail ("INPUT: ... {{ $json }}") since we pass the
    # actual data in the user message.
    marker = "INPUT:"
    idx = system.find(marker)
    if idx != -1:
        system = system[:idx].rstrip()
    user = build_verify_user(article, image_names, flags, evidence)
    result = (client or LLMClient()).chat_json(system, user, max_tokens=4000)
    return _finalize(result, image_names, flags)