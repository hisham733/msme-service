# =============================================================================
# FILE HEADER
# file    : filter.py
# role    : Filter · Jev judge core
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : ask Jev one battery (3 hard gates + 11 weighted scores) in one request, then route in code to
#           ACCEPT / REJECT / EDITOR REVIEW; apply Lab + Config overrides; optional DeepSeek assist.
# pages   : backs every judgement on :8900 (filter, lab, testfilter, report)
# calls   : config, Jev API, docs/jev-variants.json, data/filter_settings.json; prefilter/filter_llm (lazy)
# called  : filter_service.py; test_jev_weakness.py (via HTTP)
# amend   : GATES / SCORES / EXTRA are the battery; wording precedence is Lab > Config > built-in — don't reorder;
#           the SCORES comment says 96 but the weights sum to 100 — both intentional, do NOT reconcile
#           (decisions/D5); live truth is GET /filters.json. Test: GET /filters.json
# =============================================================================
"""Jev filter: the Stage-1 editorial judge using TypeSafe's System One model.

Given an extracted article (subject/from/date/bodyText), we ask Jev one question
battery in a SINGLE HTTP request:
  - 6 HARD GATES (noul): any near-1 probability -> REJECT (or EDITOR REVIEW for the review gates)
  - 8 SCORED CRITERIA (noul, phrased NEGATIVELY): the "no" side (1 - noul) is the
    good score; weighted -> weighted%. High NO% displayed = ready to accept.

The decision (ACCEPT/REJECT) is made in CODE from the returned probabilities,
mirroring the old n8n Stage-1 filter exactly (gates >= 0.85, weighted >= 60%).

Example:
    verdict = filter.judge({
        "subject": "Fwd: [PRESS RELEASE] ...",
        "from": "Editor MSME <editor@malaysiasme.com.my>",
        "date": "Wed, 30 Sep 2026",
        "bodyText": "KUALA LUMPUR, 29 Sep 2026 - ...",
    })
    verdict["outcome"]   # -> "ACCEPT" | "REJECT"
    verdict["weighted"]  # -> 78
"""
import hashlib
import json
import os
import time
import urllib.error
import urllib.request

import config
import settings_store


# Human-readable, grammatical names shown in the UI (keys stay stable).
GATE_LABELS = {
    "royal_respect": "Royal institution respect",
    "religious_respect": "Religion respect",
    "racial_respect": "Racial / ethnic respect",
}

# The 3 hard gates all auto-REJECT when they fire.
GATE_OUTCOMES = {
    "royal_respect": "REJECT",
    "religious_respect": "REJECT",
    "racial_respect": "REJECT",
}

# --- 3 hard gates (POSITIVE: high YES = good; a gate REJECTS when the good is ABSENT) ---
GATES = {
    'royal_respect': {
        "type": "noul",
        "instructions": "Is the article free of any disparagement of, disrespect toward, or challenge to the legitimacy or authority of Malaysia's royal institution (the Yang di-Pertuan Agong, the Sultans, or the monarchy)?",
        "criteria": {
            "true": 'Shows respect for the royal institution, praises or reports royal news neutrally, and does not attack or question the monarchy.',
            "false": 'Disparages, mocks, insults, or challenges the monarchy — e.g. argues royal powers are illegitimate, excessive or should be curtailed; questions a Ruler\'s legitimacy, authority, or right to rule; or centres on a demand/attempt to remove, depose, or rival a Ruler. Answer NO for such content even when it is a news report or opinion piece.',
        },
    },
    'religious_respect': {
        "type": "noul",
        "instructions": 'Is the article free of disparagement of, disrespect toward, or mockery of any religion, religious practice, or religious group?',
        "criteria": {
            "true": 'Respects all religions, or reports religious news neutrally without belittling, insulting or mocking any faith.',
            "false": 'Disparages, insults, mocks, or defiles any religion, religious site, or religious community — including when the article\'s subject is mocking/insulting a religion or desecrating a place of worship. Answer NO for such content even when it is a news report.',
        },
    },
    'racial_respect': {
        "type": "noul",
        "instructions": 'Is the article free of racial or ethnic disparagement, discrimination, or incitement?',
        "criteria": {
            "true": 'Promotes racial/ethnic harmony and equal respect, or reports race-related news neutrally without endorsing division.',
            "false": 'Disparages or discriminates against a race or ethnicity; questions the loyalty, belonging or rights of any community by race; or stirs racial tension — including when the article centres on such remarks or rhetoric. Answer NO for such content even when it is a news report or opinion piece.',
        },
    },
}

# --- 11 scored criteria (POSITIVE: high YES = good; weights sum to 96) ------
SCORES = {
    'sme_relevance': {
        "weight": 26,
        "type": "noul",
        "instructions": 'Is this relevant to SMEs or the wider business ecosystem — an SME, policy, financing, trade, technology, workforce or market-access angle?',
        "criteria": {"true": 'Relevant: affects how SMEs operate/earn/compete/comply (financing, policy, tax, trade, market access, technology, talent, supply chain); industry/sector development.', "false": "Off-topic: consumer/lifestyle; one company's own news; education/edtech; event previews; foreign delegation PR; consumer money-advice; overseas op-ed."},
    },
    'sme_voice_business_updates': {
        "weight": 7,
        "type": "noul",
        "instructions": 'Does the submission contribute knowledge, experience or perspective for the wider SME community (updates, insights or opinion)?',
        "criteria": {"true": '', "false": ''},
    },
    'commercial_intent': {
        "weight": 10,
        "type": "noul",
        "instructions": "Is this a genuine development rather than a hard sell of the sender's product or service (discounts, sales offers, direct customer acquisition)?",
        "criteria": {"true": 'A genuine development (a product may be mentioned within a wider development).', "false": "A hard sell of the sender's product/service (discounts, sales offers, direct customer acquisition)."},
    },
    'substance': {
        "weight": 6,
        "type": "noul",
        "instructions": 'Is there sufficient factual material here to construct a meaningful article without adding external information?',
        "criteria": {"true": '', "false": ''},
    },
    'source_attribution': {
        "weight": 6,
        "type": "noul",
        "instructions": 'Is the issuing organisation (and any speakers) identifiable?',
        "criteria": {"true": '', "false": ''},
    },
    'claims_statistics': {
        "weight": 6,
        "type": "noul",
        "instructions": "Are the article's claims and figures attributed to a source?",
        "criteria": {"true": '', "false": ''},
    },
    'timeliness': {
        "weight": 4,
        "type": "noul",
        "instructions": 'Is this a current development (recent or upcoming) or still-useful insight?',
        "criteria": {"true": '', "false": ''},
    },
    'geographic_relevance': {
        "weight": 7,
        "type": "noul",
        "instructions": 'Does this concern Malaysia, ASEAN or markets that Malaysian SMEs can access?',
        "criteria": {"true": '', "false": ''},
    },
    'safety_reputation': {
        "weight": 10,
        "type": "noul",
        "instructions": 'Is the article free of reputational/legal risk (no defamatory, discriminatory or unsubstantiated claims about a person or company)?',
        "criteria": {"true": 'No defamatory, discriminatory or unsubstantiated claims.', "false": 'Contains defamatory/discriminatory/unsubstantiated claims.'},
    },
    'political_advocacy': {
        "weight": 6,
        "type": "noul",
        "instructions": 'Is this free of political/advocacy content (campaigning, endorsements, partisan messaging) and of bylined opinion pieces that need editor review?',
        "criteria": {"true": '', "false": ''},
    },
    'overall_editorial_test': {
        "weight": 12,
        "type": "noul",
        "instructions": 'Does an SME reader learn something from this submission — does it inform, add a useful SME perspective, or share a meaningful business update rather than mainly promote the sender?',
        "criteria": {"true": 'Informs the reader / contributes a useful SME perspective or a meaningful business update.', "false": "The only meaningful takeaway is a sales message about the sender's product or service."},
    },
}

# Informational questions sent to Jev for context (NOT gates, NOT weighted).
EXTRA = {}


def accept_threshold():
    """Live ACCEPT cut-off (0-100), saved on the Config page; env is the fallback."""
    try:
        val = float(settings_store.get("ACCEPT_THRESHOLD"))
    except Exception:
        val = float(config.ACCEPT_THRESHOLD)
    return max(0.0, min(100.0, val))


def build_state(article):
    """Build the `state` Jev evaluates: the article with its metadata on top."""
    return {
        "subject": article.get("subject", ""),
        "from": article.get("from", ""),
        "date": article.get("date", ""),
        "bodyText": (article.get("bodyText") or "")[:12000],
    }


# --- Editable overrides ------------------------------------------------------
# Live edits from the Config page (gate wording, criteria levels, weights) are
# persisted to data/filter_settings.json and merged over the defaults here, so
# you can tune the rubric WITHOUT redeploying.
SETTINGS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "filter_settings.json"
)


def _load_overrides():
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_overrides(overrides):
    try:
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(overrides, f, indent=2)
    except Exception as e:
        raise RuntimeError(f"could not save settings: {e}")


# --- Jev Lab source ----------------------------------------------------------
# The Jev Lab file (docs/jev-variants.json) is the SOURCE OF TRUTH for each
# question's instruction + criteria. Its base entries (ids == the question name)
# are read here; variants (_1.._4, _jev_best_qu) are for Lab testing only.
# Precedence: Lab file  >  data/filter_settings.json  >  built-in defaults.
LAB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "docs", "jev-variants.json"
)


def _load_lab():
    try:
        with open(LAB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _lab_wording(name):
    """Return {instructions, criteria} for a base question from the Jev Lab file."""
    q = (_load_lab().get("questions") or {}).get(name)
    if isinstance(q, dict):
        return {"instructions": q.get("instructions"), "criteria": q.get("criteria")}
    return {}


def _save_lab_wording(name, instructions=None, criteria=None):
    """Write a base question's instruction/criteria back into the Jev Lab file."""
    doc = _load_lab()
    if not isinstance(doc, dict) or not doc:
        return
    q = doc.setdefault("questions", {}).setdefault(name, {"type": "noul"})
    if instructions:
        q["instructions"] = instructions
    if criteria is not None:
        q["criteria"] = criteria
    _write_lab(doc)


def _write_lab(doc):
    try:
        with open(LAB_PATH, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def builtin_wording(name):
    """The built-in (code) instruction + criteria for a question name."""
    for src in (GATES, SCORES, EXTRA):
        q = src.get(name)
        if q:
            return {"instructions": q.get("instructions", ""), "criteria": q.get("criteria", {"true": "", "false": ""})}
    return {}


def build_questions_builtin():
    """All base questions using BUILT-IN wording (ignores Lab + overrides)."""
    out = {}
    for name in list(GATES) + list(SCORES) + list(EXTRA):
        w = builtin_wording(name)
        if w:
            out[name] = {"type": "noul", "instructions": w["instructions"], "criteria": w["criteria"]}
    return out


def reset_lab_base():
    """Restore every Lab base entry to the built-in wording (rollback)."""
    doc = _load_lab()
    if not isinstance(doc, dict) or not doc:
        return False
    qs = doc.setdefault("questions", {})
    for name in list(GATES) + list(SCORES) + list(EXTRA):
        w = builtin_wording(name)
        if not w:
            continue
        qs.setdefault(name, {"type": "noul"})
        qs[name]["instructions"] = w["instructions"]
        qs[name]["criteria"] = w["criteria"]
    return _write_lab(doc)


def reset_overrides():
    """Clear data/filter_settings.json (remove all Config-page overrides)."""
    _save_overrides({})
    return True


def gates():
    """Gates with any Config-page overrides applied (instructions/criteria/threshold).

    Custom gates added from the Config page live in the overrides file and are
    merged in alongside the built-in ones. `deleted: true` hides a gate.
    """
    ov = _load_overrides().get("gates", {})
    names = list(GATES.keys()) + [n for n in ov if n not in GATES]
    merged = {}
    for name in names:
        base = GATES.get(name, {})
        o = ov.get(name, {})
        if o.get("deleted"):
            continue
        lab = _lab_wording(name)
        merged[name] = {
            "type": "noul",
            "label": o.get("label", base.get("label", GATE_LABELS.get(name, name.replace("_", " ")))),
            "threshold": float(o.get("threshold", base.get("threshold", config.GATE_THRESHOLD))),
            "instructions": lab.get("instructions") or o.get("instructions") or base.get("instructions", ""),
            "criteria": (lab.get("criteria") if lab.get("criteria") is not None
                         else o.get("criteria", base.get("criteria", {"true": "", "false": ""}))),
        }
    return merged


def scores():
    """Scores with any Config-page overrides applied (instructions/criteria/weight).

    Custom criteria added from the Config page are merged in alongside the
    built-in ones. `deleted: true` hides a criterion.
    """
    ov = _load_overrides().get("scores", {})
    names = list(SCORES.keys()) + [n for n in ov if n not in SCORES]
    merged = {}
    for name in names:
        base = SCORES.get(name, {})
        o = ov.get(name, {})
        if o.get("deleted"):
            continue
        lab = _lab_wording(name)
        merged[name] = {
            "type": "noul",
            "weight": o.get("weight", base.get("weight", 0)),
            "instructions": lab.get("instructions") or o.get("instructions") or base.get("instructions", ""),
            "criteria": (lab.get("criteria") if lab.get("criteria") is not None
                         else o.get("criteria", base.get("criteria", {"true": "", "false": ""}))),
        }
    return merged


def update_settings(patch):
    """Merge a Config-page patch into the overrides file.

    patch shape: {"gates": {"advertorial": {"instructions": "..."}},
                  "scores": {"no_substance": {"weight": 3}}}
    """
    ov = _load_overrides()
    for section in ("gates", "scores"):
        if section in patch and isinstance(patch[section], dict):
            sec = ov.setdefault(section, {})
            for name, changes in patch[section].items():
                if not isinstance(changes, dict):
                    continue
                entry = sec.setdefault(name, {})
                for k, v in changes.items():
                    if v is not None and v != "":
                        entry[k] = v
                # Mirror wording into the Jev Lab file (the source of truth).
                if "instructions" in changes or "criteria" in changes:
                    _save_lab_wording(name, changes.get("instructions"), changes.get("criteria"))
    _save_overrides(ov)
    return ov


def build_questions():
    """Combine the hard gates + scored criteria into one questions map.

    Both gates and scores are `noul` questions now. Scores are phrased as the
    defect ("Is this NOT ...?"); their "no" side is the good score.
    """
    questions = {}
    for name, q in gates().items():
        questions[name] = {"type": "noul", "instructions": q["instructions"], "criteria": q["criteria"]}
    for name, q in scores().items():
        questions[name] = {"type": "noul", "instructions": q["instructions"], "criteria": q["criteria"]}
    for name, q in EXTRA.items():
        lab = _lab_wording(name)
        questions[name] = {
            "type": "noul",
            "instructions": lab.get("instructions") or q["instructions"],
            "criteria": lab.get("criteria") or q["criteria"],
        }
    return questions


def _post(body, retries=4):
    """POST to the Jev endpoint with retry+backoff on 429/529."""
    url = f"{config.TYPESAFE_BASE_URL}/v1/systemone"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {config.TYPESAFE_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 529):
                wait = 1.5 ** (attempt + 1)
                print(f"[filter] Jev {e.code} (rate/overload), retry in {wait:.1f}s")
                time.sleep(wait)
                continue
            if e.code in (401,):
                raise RuntimeError("Jev API key invalid (401)")
            raise RuntimeError(f"Jev HTTP {e.code}: {e.read()[:300].decode('utf-8', 'replace')}")
        except Exception as e:
            raise RuntimeError(f"Jev request failed: {e}")
    raise RuntimeError("Jev rate-limit retries exhausted")


def decide(answers):
    """Turn Jev answers into an outcome using code thresholds.

    Returns (outcome, reason, reasons) where outcome is one of
    ACCEPT / REJECT / EDITOR REVIEW. The 3 sensitivity gates (`royal_respect`,
    `religious_respect`, `racial_respect`) auto-REJECT; everything else is a weighted score
    (a borderline weighted score still routes to EDITOR REVIEW).

    Example:
        decide(answers)  # -> ("REJECT", "RELIGION", [...])
    """
    fired_reject, fired_review = [], []
    for name, q in gates().items():
        a = answers.get(name) or {}
        good = float(a.get("noul", 0) or 0)   # POSITIVE question: high = good
        thr = float(q.get("threshold", config.GATE_THRESHOLD))
        if (1.0 - good) >= thr:               # the good is absent -> defect present
            code = name.upper()
            if GATE_OUTCOMES.get(name) == "EDITOR REVIEW":
                fired_review.append(code)
            else:
                fired_reject.append(code)
    if fired_reject:
        return "REJECT", fired_reject[0], fired_reject
    if fired_review:
        return "EDITOR REVIEW", fired_review[0], fired_review
    # weighted score: questions are POSITIVE, so good = noul (yes)
    total = 0.0
    denom = 0.0
    for name, q in scores().items():
        a = answers.get(name) or {}
        good = float(a.get("noul", 0) or 0)   # high = good
        total += good * q["weight"]
        denom += q["weight"]
    weighted = round((total / denom) * 100) if denom else 0
    if weighted >= accept_threshold():
        return "ACCEPT", None, []
    return "REJECT", "LOW_WEIGHTED_SCORE", ["LOW_WEIGHTED_SCORE"]


_WEAK_GATES = ("royal_respect", "religious_respect", "racial_respect")


def _route_ambiguity(answers, outcome, reason, reasons, weighted):
    """Deterministic ambiguity router used when the LLM assist is OFF.

    Replaces the DeepSeek second opinion: any uncertain weak gate, or a
    borderline weighted score, is routed to a human (EDITOR REVIEW) instead of
    being tie-broken by a model. Never downgrades an existing REJECT or
    EDITOR REVIEW. Returns (outcome, reason, reasons, notes).
    """
    notes = {}
    lo, _ = config.LLM_GATE_BAND
    _gates = gates()
    for name in _WEAK_GATES:
        q = _gates.get(name)
        if not q:
            continue
        prob = float((answers.get(name) or {}).get("noul", 0) or 0)
        thr = float(q.get("threshold", config.GATE_THRESHOLD))
        defect = 1.0 - prob
        if lo <= defect < thr:
            notes[name] = {"rule": "ambiguous_gate", "defect": round(defect, 3), "threshold": thr}
            if outcome == "ACCEPT":
                code = "AMBIGUOUS_" + name.upper()
                outcome, reason, reasons = "EDITOR REVIEW", code, [code]
    wlo, whi = config.LLM_WEIGHTED_BAND
    if reason in (None, "LOW_WEIGHTED_SCORE") and wlo <= weighted <= whi:
        notes["weighted"] = {"rule": "borderline", "weighted": weighted, "band": [wlo, whi]}
        if outcome in ("ACCEPT", "REJECT"):
            outcome, reason, reasons = "EDITOR REVIEW", "BORDERLINE", ["BORDERLINE"]
    return outcome, reason, reasons, notes


def assist(article, answers, outcome, reason, reasons, weighted):
    """Second opinion for weak-gate ambiguity and borderline weighted.

    LLM assist ON  -> DeepSeek re-judges the ambiguous question (pattern 2).
    LLM assist OFF -> deterministic fallback (`_route_ambiguity`): uncertainty
    goes to a human. Never raises; on any failure returns the inputs unchanged.
    Returns (outcome, reason, reasons, notes).
    """
    notes = {}
    try:
        import filter_llm
    except Exception:
        filter_llm = None
    if not (filter_llm and filter_llm.enabled()):
        return _route_ambiguity(answers, outcome, reason, reasons, weighted)

    _gates = gates()
    lo, hi = config.LLM_GATE_BAND
    review_names = {n for n, o in GATE_OUTCOMES.items() if o == "EDITOR REVIEW"}

    for name in _WEAK_GATES:
        q = _gates.get(name)
        if not q:
            continue
        prob = float((answers.get(name) or {}).get("noul", 0) or 0)
        thr = float(q.get("threshold", config.GATE_THRESHOLD))
        defect = 1.0 - prob
        fired = defect >= thr
        ambiguous = lo <= defect < thr
        if not (fired or ambiguous):
            continue
        op = filter_llm.second_opinion(article, name, q["instructions"], q["criteria"], defect)
        if not op:
            continue
        says_defect = str(op.get("judgment", "")).lower() == "true"
        notes[name] = {"judgment": op.get("judgment"), "agree": op.get("agree_with_primary"),
                       "reason": op.get("reason"), "confidence": op.get("confidence")}
        if ambiguous and says_defect:
            if name in review_names:
                if outcome == "ACCEPT":
                    outcome, reason, reasons = "EDITOR REVIEW", name.upper(), [name.upper()]
            else:
                if outcome in ("ACCEPT", "EDITOR REVIEW"):
                    outcome, reason, reasons = "REJECT", name.upper(), [name.upper()]

    # borderline weighted -> second opinion on the overall editorial test
    wlo, whi = config.LLM_WEIGHTED_BAND
    if reason in (None, "LOW_WEIGHTED_SCORE") and wlo <= weighted <= whi:
        q = scores().get("no_editorial_value")
        if q:
            jval = float((answers.get("no_editorial_value") or {}).get("noul", 0) or 0)
            op = filter_llm.second_opinion(article, "no_editorial_value", q["instructions"], q["criteria"], jval)
            if op:
                notes["weighted"] = {"judgment": op.get("judgment"), "reason": op.get("reason")}
                says_no_value = str(op.get("judgment", "")).lower() == "true"
                if (outcome == "ACCEPT" and says_no_value) or (outcome == "REJECT" and not says_no_value):
                    outcome, reason, reasons = "EDITOR REVIEW", "BORDERLINE", ["BORDERLINE"]
    return outcome, reason, reasons, notes


def _config_hash(snapshot):
    raw = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]


def battery_snapshot():
    """The effective rubric used for a judgement (Lab + Config + defaults)."""
    b = battery()
    try:
        assist = settings_store.get("ENABLE_LLM_ASSIST")
    except Exception:
        assist = None
    if assist is None:
        assist = config.ENABLE_LLM_ASSIST
    snap = {
        "gates": b.get("gates", {}),
        "scores": b.get("scores", {}),
        "accept_threshold": accept_threshold(),
        "llm_assist": bool(assist),
        "jev_model": config.JEV_MODEL,
    }
    return snap, _config_hash(snap)


def judge(article):
    """Judge one article with Jev (+ DeepSeek assist) and return the verdict dict.

    Pipeline: DeepSeek preprocess (clean/translate/extract) -> Jev battery ->
    deterministic checks. Falls back to the raw article if DeepSeek is off/errors.

    Example:
        v = filter.judge({"subject": "...", "from": "...", "date": "...", "bodyText": "..."})
        v["outcome"]    # "ACCEPT" | "REJECT"
        v["weighted"]   # 0-100
    """
    # --- P1: DeepSeek preprocess (pattern 1) — fail-safe to raw text ---
    try:
        import filter_llm
        import prefilter
    except Exception:
        filter_llm = prefilter = None

    prep = filter_llm.preprocess(article) if filter_llm else {}
    clean = dict(article)
    if prep.get("bodyText"):
        clean["bodyText"] = prep["bodyText"]

    body = {
        "state": build_state(clean),
        "model": config.JEV_MODEL,
        "questions": build_questions(),
    }
    resp = _post(body)

    answers = resp.get("answers", {})
    outcome, gate, reasons = decide(answers)

    # collect the per-question values for the caller
    scores_out = {}
    gates_out = {}
    _scores = scores()
    _gates = gates()
    for name, q in _gates.items():
        a = answers.get(name) or {}
        gates_out[name] = round(1.0 - float(a.get("noul", 0) or 0), 3)   # defect prob (fires >= thr)
    # questions are POSITIVE: the good value = the "yes" side = noul
    for name, q in _scores.items():
        a = answers.get(name) or {}
        noul = float(a.get("noul", 0) or 0)
        norm = round(noul, 3)
        scores_out[name] = {"raw": a.get("noul"), "norm": norm, "confidence": a.get("confidence")}

    # weighted%
    total = sum((scores_out[n]["norm"] or 0) * q["weight"] for n, q in _scores.items())
    denom = sum(q["weight"] for q in _scores.values())
    weighted = round((total / denom) * 100) if denom else 0

    # --- P1: deterministic checks (date / contacts / sponsored strings) ---
    deterministic = prefilter.run(clean, prep) if prefilter else {}
    preprocess_summary = {}
    if prep:
        preprocess_summary = {
            "is_english": prep.get("is_english"),
            "language": prep.get("language"),
            "headline": prep.get("headline"),
            "orgs": prep.get("orgs"),
            "speakers": prep.get("speakers"),
            "claims_count": len(prep.get("claims") or []),
            "notes": prep.get("notes"),
            "usage": prep.get("_usage", {}),
        }

    # --- P2: DeepSeek second opinion (weak gates + borderline weighted) ---
    outcome, gate, reasons, assist_notes = assist(clean, answers, outcome, gate, reasons, weighted)
    extra_out = {name: round(float((answers.get(name) or {}).get("noul", 0) or 0), 3) for name in EXTRA}

    usage = resp.get("usage", {})
    _snapshot, _chash = battery_snapshot()
    return {
        "outcome": outcome,
        "gate": gate,
        "reasons": reasons,
        "weighted": weighted,
        "threshold": accept_threshold(),
        "gates": gates_out,
        "gate_thresholds": {name: q["threshold"] for name, q in _gates.items()},
        "gate_labels": {name: q.get("label", name) for name, q in _gates.items()},
        "scores": scores_out,
        "confidence": round(sum((a.get("confidence") or 0) for a in answers.values()) / max(1, len(answers)), 3),
        "usage": usage,
        "model": resp.get("model"),
        "preprocess": preprocess_summary,
        "deterministic": deterministic,
        "assist": assist_notes,
        "extra": extra_out,
        "battery": _snapshot,
        "config_hash": _chash,
    }


def battery():
    """Return the live battery (6 gates + 8 scores + 1 context) for the dashboard.

    Each gate carries its `outcome` (REJECT or EDITOR REVIEW) so consumers (UI,
    printable rule sheet) show what the gate does without duplicating the rule.
    """
    gates_out = {}
    for name, q in gates().items():
        item = dict(q)
        item["outcome"] = GATE_OUTCOMES.get(name, "REJECT")
        gates_out[name] = item
    return {"gates": gates_out, "scores": scores(), "context": EXTRA}
