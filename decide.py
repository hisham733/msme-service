# =============================================================================
# FILE HEADER
# file    : decide.py
# role    : Receive · AI step 1 — decide press source
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : pick the actual press-release attachment (English preferred) and flag images / media-kit link, from
#           attachment names and text only (never file contents).
# pages   : n/a
# calls   : llm.LLMClient, config, prompts/decide_prompt.txt
# called  : pipeline.py
# amend   : output keys are consumed by pipeline — keep them; wording belongs in prompts/, not here.
#           Test: run one email, inspect the decide stage in flow.html
# =============================================================================
"""Decide Press Source — AI step #1.

Given an email (subject, from, body, attachment names/types/sizes, links), the
model decides:
  1) WHICH attachment is the actual press-release article (English preferred)
  2) whether images are available (attachments or a media-kit link)
  3) whether there is a media-kit / Drive link to fetch

It only looks at NAMES and TEXT (never file contents) — the heavy extraction
happens later in `extract.py`.

Example output (parsed from the model's JSON):
    {
      "chosenAttachmentKey": "attachment_1",
      "chosenFileName": "EN_MRCA CELEBRATES 34 YEARS...docx",
      "chosenDocType": "docx",
      "isEnglish": true,
      "imagesAvailable": false,
      "imagesInAttachments": false,
      "imagesViaLink": false,
      "linkToFetch": "",
      "linkIsPressKit": false,
      "confidence": 0.88,
      "reason": "The single DOCX bearing the subject headline is the release..."
    }
"""
import config
from llm import LLMClient


def build_decision_input(model):
    """Build the plain-text block the AI decides from.

    Example of what it produces:
        SUBJECT: Fwd: [PRESS RELEASE] MRCA CELEBRATES 34 YEARS...
        FROM: Editor MSME <editor@malaysiasme.com.my>
        DATE: ...

        EMAIL BODY:
        <cleaned body — cover/disclaimer/forwarders removed>

        ATTACHMENTS (4):
          - EN_MRCA...docx [application/vnd...document] (12345 bytes)
          ...

        LINKS FOUND IN EMAIL:
        https://drive.google.com/drive/folders/...
    """
    subject = model.get("subject", "")
    from_ = model.get("from", "")
    date = model.get("date", "")
    # Use cleaned body for the AI (cover/disclaimer/forwarders removed)
    body = model.get("cleanBody", "") or model.get("bodyText", "")
    attachments = model.get("attachments", [])
    links = model.get("linksFound", [])

    att_lines = []
    for i, a in enumerate(attachments, 1):
        att_lines.append(
            f"  - {a['filename']} [{a['mimeType']}] "
            f"({a.get('size', 0)} bytes)"
        )
    link_lines = "\n".join(links) if links else "(no external links)"

    decision_input = (
        f"SUBJECT: {subject}\n"
        f"FROM: {from_}\n"
        f"DATE: {date}\n\n"
        f"EMAIL BODY:\n{body}\n\n"
        f"ATTACHMENTS ({len(attachments)}):\n"
        + ("\n".join(att_lines) if att_lines else "  (none)")
        + f"\n\nLINKS FOUND IN EMAIL:\n{link_lines}"
    )
    return decision_input


def decide(model, client=None, prompt_version=None):
    """Run the Decide Press Source AI call and return its JSON dict.

    Example:
        d = decide(model)
        d["chosenFileName"]  # -> "EN_MRCA...docx"
        d["linkToFetch"]     # -> "https://drive.google.com/drive/folders/..."
    """
    system = config.load_prompt("decide_prompt.txt", version=prompt_version)
    # Strip the n8n template tail ("EMAIL TO DECIDE: {{ $json.decisionInput }}")
    # since we pass the actual data in the user message.
    marker = "EMAIL TO DECIDE:"
    idx = system.find(marker)
    if idx != -1:
        system = system[:idx].rstrip()
    decision_input = build_decision_input(model)
    user = f"EMAIL TO DECIDE:\n{decision_input}"
    result = (client or LLMClient()).chat_json(system, user, max_tokens=4000)
    return result