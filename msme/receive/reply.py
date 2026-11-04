# =============================================================================
# FILE HEADER
# file    : msme/receive/reply.py
# role    : Receive — rejection reply email
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : derive the rejection reasons from the checklist flags, write an AI (or template) message and send it
#           threaded into the original Gmail conversation.
# pages   : backs POST /api/reply (checklist page)
# calls   : config, creds, gmail; llm (lazy)
# called  : dashboard.api_reply; checklist.html
# amend   : REPLY_MODE=fixed_email now, sender later — never send when dry=1.
#           Test: POST /api/reply?...&dry=1 and read the preview
# =============================================================================
"""Rejection reply: when an article is NOT ready to filter, email the sender an
apology that explains why, what's missing, what to provide, and how to resend.

Why it's rejected is derived deterministically from the checklist row flags
(no extra lookup), then an AI (DeepSeek/Gemini via LLMClient) writes a warm,
clear, user-friendly message from those facts. The email is threaded into the
original conversation and sent FROM the connected Gmail account.

Recipient modes (config.REPLY_MODE):
  - "fixed_email" (now): send to config.REPLY_TO_EMAIL (a dev/test address)
  - "sender" (later):    send to the email's actual From address
"""

from msme import config
from msme.receive import gmail


# Deterministic reason map: checklist flag(s) -> (headline, what's missing, what to provide).
# Only the reasons that are actually false get included, so the message lists
# exactly what the sender needs to fix.
def build_reasons(row):
    """Return a list of reason dicts based on the row's flags.

    Each dict: {"reason": str, "missing": [..], "provide": [..]}

    Example:
        build_reasons({"hasArticle": "false", "hasPic": "false", ...})
        -> [{"reason": "No substantial press release article was found.",
             "missing": ["The actual press release text (at least a few sentences)."],
             "provide": ["The full release as text, or attach it as a PDF/DOCX."]}, ...]
    """
    reasons = []

    def _ok(v):
        return str(v).lower() in ("true", "1", "yes")

    has_article = _ok(row.get("hasArticle"))
    has_pic = _ok(row.get("hasPic"))
    has_logo = _ok(row.get("hasLogo"))
    has_logo_in = _ok(row.get("hasLogoInArticle"))
    has_img_in = _ok(row.get("hasImageInArticle"))
    subject_match = _ok(row.get("subjectMatch"))
    try:
        subject_score = int(row.get("subjectScore") or 0)
    except Exception:
        subject_score = 0

    needs_human_reason = row.get("_needs_human_reason") or ""
    if needs_human_reason:
        reasons.append({
            "reason": needs_human_reason,
            "missing": ["A press release we can actually read: an attachment, the text in the body, "
                        "or a Drive link with download enabled."],
            "provide": [
                "Enable download on the Google Drive file (Share → Viewer → allow download), or",
                "attach the PDF/DOCX directly (under 25 MB), or",
                "share it with our Google account so we can open it.",
            ],
        })

    if not has_article:
        reasons.append({
            "reason": "We could not find a substantial press release in the email.",
            "missing": ["The actual press release text (a few sentences or more, not just a pitch)."],
            "provide": [
                "Paste the full release in the email body, or",
                "attach it as a PDF/DOCX file.",
            ],
        })

    if not (has_pic or has_logo or has_logo_in or has_img_in):
        reasons.append({
            "reason": "No usable image or media was attached or linked.",
            "missing": ["At least one photo/image (preferably 1MB or larger), or a media-kit link."],
            "provide": [
                "Attach the images directly, or",
                "include a working Google Drive media-kit link.",
            ],
        })

    if not subject_match or subject_score <= 60:
        reasons.append({
            "reason": "The email subject did not clearly match the article's headline.",
            "missing": ["An email subject that matches the release title."],
            "provide": [
                "Use the release headline as the email subject when resending.",
            ],
        })

    if not reasons:
        reasons.append({
            "reason": "The submission is missing some required details for publication.",
            "missing": ["The required editorial details."],
            "provide": ["A complete press release with all the required elements."],
        })

    return reasons


def _recipient(model):
    """Choose who receives the reply based on REPLY_MODE."""
    if config.REPLY_MODE == "sender":
        from_email = (model.get("fromEmail") or "").strip()
        if from_email:
            return from_email
        from_raw = (model.get("from") or "")
        # fallback: extract address from "Name <email>"
        import re
        m = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", from_raw)
        return m.group(0) if m else config.REPLY_TO_EMAIL
    return config.REPLY_TO_EMAIL


def _ai_message(row, reasons):
    """Ask the LLM to write a warm, clear, user-friendly rejection email."""
    from msme.llm import LLMClient

    bullets = "\n".join(
        f"- {r['reason']}\n  Missing: {'; '.join(r['missing'])}\n  Please provide: {'; '.join(r['provide'])}"
        for r in reasons
    )
    system = (
        "You write polite, warm, and very clear rejection emails for a business news"
        " website's editorial team. The sender is a PR person or company who submitted"
        " a press release. Be apologetic and encouraging — never cold or blaming. Give"
        " them exactly what they must fix to resend. Plain text only, no markdown symbols,"
        " no bullet asterisks. Keep it under ~160 words."
    )
    user = (
        "Write the email body ONLY (no subject, no greeting/sign-off placeholders beyond "
        "'Dear Sender,' and 'Best regards,'). The submission:\n"
        f"Subject: {row.get('subject', '')}\n"
        f"Reasons:\n{bullets}\n\n"
        "Return ONLY valid JSON, no prose: {\"message\": \"the email body text\"}"
    )
    result = LLMClient().chat_json(system, user, max_tokens=4000)
    return str(result.get("message") or result.get("body") or result.get("text") or "").strip()


def _template_message(row, reasons):
    """Fallback plain-text message if the AI call fails (still clear + friendly)."""
    lines = [
        "Dear Sender,",
        "",
        f'Thank you for your press release, "{row.get("subject", "")}".',
        "We're sorry, but it is not ready for publication yet because:",
        "",
    ]
    for r in reasons:
        lines.append(f"- {r['reason']}")
        lines.append(f"  Missing: {'; '.join(r['missing'])}")
        lines.append(f"  Please provide: {'; '.join(r['provide'])}")
        lines.append("")
    lines.append("Once you've updated it, please resend and we'll review it again.")
    lines.append("")
    lines.append("Best regards,")
    lines.append("Malaysia SME Editorial Team")
    return "\n".join(lines)


def build_email_body(row, reasons):
    """Produce the reply body — AI-friendly message, falling back to the template."""
    try:
        body = _ai_message(row, reasons)
        if body and len(body) > 40:
            return body
    except Exception as e:
        print(f"[reply] AI message failed, using template: {e}")
    return _template_message(row, reasons)


def send_reply_for_row(service, model, row, thread_id=None, msg_id=None, force=False):
    """Send the rejection reply for a not-ready row. Returns {"ok", "sent_to", "id"}.

    No-ops (and returns {"ok": False, "skipped": "disabled"}) unless:
      - config.REPLY_ENABLED is true, OR
      - force=True (manual button on the dashboard)
    """
    if not (config.REPLY_ENABLED or force):
        return {"ok": False, "skipped": "reply_disabled"}

    to = _recipient(model)
    reasons = build_reasons(row)
    subject = f"Re: {row.get('subject', '')[:120]}"
    body = build_email_body(row, reasons)

    sent_id = gmail.send_message(
        service, to, subject, body,
        thread_id=thread_id or model.get("threadId"),
        msg_id=msg_id or model.get("messageId"),
    )
    # record that we replied, so re-runs don't send again
    try:
        from msme import db
        db.mark_reply_sent(row.get("threadId") or model.get("threadId") or "", to, status="true")
    except Exception as e:
        print(f"[reply] mark_reply_sent failed: {e}")
    return {"ok": True, "sent_to": to, "id": sent_id, "reasons": [r["reason"] for r in reasons]}


def preview_reply(row, model=None):
    """Return the reply body WITHOUT sending (for the dashboard preview)."""
    reasons = build_reasons(row)
    return {
        "to": _recipient(model or {}),
        "subject": f"Re: {row.get('subject', '')[:120]}",
        "body": build_email_body(row, reasons),
        "reasons": reasons,
    }
