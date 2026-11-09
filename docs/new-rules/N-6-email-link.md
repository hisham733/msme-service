# N-6 — Open the original email from the prototype

_Status: built 2026-11-05 · no MSME question (internal UI change)._
_Source: 30-Oct 2026 MSME call `[14:33–15:01]`, `[39:49]`; `docs/meetings/2026-11-09/MEETING-BRIEF-2026-11.md:116`._

## 1. The rule

Every checklist/editor row links to the **original Gmail message**, so MSME can read the exact email
behind a flagged row without searching Gmail.

Wayne's words: “the email is not here… if you want to see the exact email, we can make a link so when
you click it will open” (`[15:01]`); “I think the first thing we need to do is add the link to the email”
(`[39:49]`).

## 2. What the user sees

In the row's **detail panel**:

- **Open email ↗** — opens the Gmail message.
- **Find in Gmail** — a backup that searches Gmail by the email's own `Message-ID`; it still works when
  the direct link does not.

If an old row has no ID, both links are hidden. Nothing changes in the main table.

## 3. Why two links

Gmail's direct link (`#all/<id>`) can fail when Gmail is not already open. The search link
(`#search/rfc822msgid:<Message-ID>`) is reliable but needs the email's `Message-ID` header. We store
both and show both.

| Link | Format | Needs |
|---|---|---|
| Open email | `https://mail.google.com/mail/u/<account>/#all/<gmail-id>` | Gmail message id |
| Find in Gmail | `https://mail.google.com/mail/u/<account>/#search/rfc822msgid:<encoded Message-ID>` | RFC822 `Message-ID` header |

`<account>` is `config.GMAIL_WEB_USER` (default `"0"`; can be the connected mailbox address so multiple
Google accounts resolve correctly).

## 4. What is stored

Two extra checklist columns (not part of the 14-column CSV contract):

| Column | Source | Backfill |
|---|---|---|
| `messageId` | Gmail API `message["id"]` (already in the model) | yes, from `pipeline_results.email_id` |
| `rfc822MessageId` | `payload.headers["message-id"]` via `gmail.parse_message` | no — needs a Gmail re-fetch; old rows use Open email only |

## 5. Code touchpoints

| File | Change |
|---|---|
| `msme/receive/email_link.py` (new) | `gmail_urls(message_id, rfc822_message_id)` builder; validates and encodes |
| `msme/config.py` | `GMAIL_WEB_USER` (default `"0"`) |
| `msme/receive/normalize.py` | add `rfc822MessageId` from the parsed headers |
| `msme/receive/pipeline.py` | put `messageId` + `rfc822MessageId` in the checklist row |
| `msme/db.py` | migration for the two columns; write in `save_checklist`; select in `list_checklist` |
| `msme/receive/dashboard.py` | `/checklist.json` adds `emailUrl` + `emailSearchUrl` to each row |
| `msme/receive/editor_data.py` | same two fields in each editor item |
| `static/checklist.html` | **Open email** / **Find in Gmail** in the detail panel |
| `static/editor.html` | same in the editor detail panel |
| `tools/backfill_message_ids.py` (new) | fill `messageId` on old rows from `pipeline_results` |
| `tests/test_email_link.py` (new) | URL builder + DB round-trip + missing/invalid ids |

## 6. Safety

- The Gmail id must match `^[A-Za-z0-9_-]+$`; otherwise no link.
- The RFC822 id is URL-encoded; angle brackets are stripped.
- No secret is stored; the link opens the user's own Gmail session.

## 7. Tests

| Case | Assertion |
|---|---|
| valid message id | `#all/<id>` built |
| RFC822 id | `#search/rfc822msgid:` value encoded, angle brackets stripped |
| invalid id (`abc/def`) | no link |
| missing ids | no link, no error |
| account config | `u/<account>` used |
| DB round-trip | `messageId` / `rfc822MessageId` saved and returned |

Proving run: `python3 -m compileall -q msme run.py tools tests` +
`python3 -m unittest discover -s tests -p 'test_*.py'`.

## 8. No MSME question

This is an internal UI change; the link opens the connected mailbox. If MSME uses a different Google
account without access, the link will not open the message — that is a permissions issue, not a missing
feature.
