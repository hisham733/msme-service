# =============================================================================
# FILE HEADER
# file    : msme/filtering/filter_llm.py
# role    : Filter — DeepSeek assist for Jev
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : pattern 1 preprocess (clean/translate/extract) before judging; pattern 2 second opinion on ONE weak
#           question. Every path falls back to the raw input on error.
# pages   : n/a
# calls   : llm.LLMClient, config, settings_store, prompts/filter_preprocess.txt, filter_second_opinion.txt
# called  : filter.py (lazy)
# amend   : assist must never block a verdict and never retry a paid call blindly.
#           Test: set ENABLE_LLM_ASSIST=false, judge one article, then true
# =============================================================================
"""DeepSeek assist for the Jev filter (patterns 1 + 2).

Jev is the calibrated router. DeepSeek handles what Jev is weak at:
  1. preprocess()      — clean/translate/extract before Jev judges  (pattern 1)
  2. second_opinion()  — re-judge ONE ambiguous/weak question        (pattern 2)

All calls are JSON, via llm.LLMClient (provider=deepseek, model deepseek-flash
by default), parsed with the shared tolerant JSON extractor. Everything is
fail-safe: on any error/disable, callers fall back to the raw input.

Example:
    prep = filter_llm.preprocess(article)          # {} on failure
    op   = filter_llm.second_opinion(article, ...)  # {} on failure
"""
import json

from msme import config, settings_store
from msme.llm import LLMClient  # shared provider switch + JSON parser


def enabled():
    """Whether DeepSeek assist is on (live-toggleable via settings)."""
    val = settings_store.get("ENABLE_LLM_ASSIST")
    if val is None:
        return bool(config.ENABLE_LLM_ASSIST)
    return bool(val)


def _usage_of(client):
    """Best-effort token usage for the call just made (DeepSeek or Gemini)."""
    ds = getattr(client, "_ds", None)
    if ds is not None and getattr(ds, "last_usage", None):
        return ds.last_usage
    return getattr(client, "last_usage", {}) or {}


def preprocess(article):
    """Clean + translate + extract metadata via DeepSeek.

    Returns a dict (possibly {}), always with keys when successful:
      is_english, language, headline, bodyText, orgs, speakers, contacts,
      dates, links, claims, notes  (+ _usage)
    """
    if not enabled():
        return {}
    try:
        system = config.load_prompt("filter_preprocess.txt")
    except Exception as e:
        print(f"[filter_llm] preprocess prompt missing: {e}")
        return {}
    user = (
        f"SUBJECT: {article.get('subject','')}\n"
        f"FROM: {article.get('from','')}\n"
        f"DATE: {article.get('date','')}\n\n"
        f"ARTICLE:\n{(article.get('bodyText') or '')[:14000]}"
    )
    try:
        client = LLMClient()
        out = client.chat_json(system, user, max_tokens=6000) or {}
        out["_usage"] = _usage_of(client)
        return out
    except Exception as e:
        print(f"[filter_llm] preprocess failed: {e}")
        return {}


def second_opinion(article, key, instructions, criteria, jvalue):
    """Re-judge ONE question via DeepSeek and explain. Returns {} on failure.

    `jvalue` is Jev's noul probability (0-1) for the same question.
    Returns: {"judgment","agree_with_primary","reason","confidence","_usage"}
    """
    if not enabled():
        return {}
    try:
        system = config.load_prompt("filter_second_opinion.txt")
    except Exception as e:
        print(f"[filter_llm] second-opinion prompt missing: {e}")
        return {}
    user = json.dumps({
        "article": {
            "subject": article.get("subject", ""),
            "from": article.get("from", ""),
            "date": article.get("date", ""),
            "bodyText": (article.get("bodyText") or "")[:10000],
        },
        "criterion": key,
        "question": instructions,
        "criteria": criteria,
        "primary_probability_yes": jvalue,
    }, ensure_ascii=False)
    try:
        client = LLMClient()
        out = client.chat_json(system, user, max_tokens=1200) or {}
        out["_usage"] = _usage_of(client)
        return out
    except Exception as e:
        print(f"[filter_llm] second_opinion failed: {e}")
        return {}
