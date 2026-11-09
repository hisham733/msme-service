# 41 — N-6 built: Open email + Find in Gmail

_2026-11-05 (S13) · code + docs · live container rebuilt._

## 1. What changed

| File | Change |
|---|---|
| `docs/new-rules/N-6-email-link.md` (new) | the N-6 spec: two links, the two stored ids, backfill, tests, no MSME question |
| `msme/receive/email_link.py` (new) | builds `#all/<id>` and `#search/rfc822msgid:<id>`, validates and encodes |
| `msme/config.py` · `msme/settings_store.py` | `GMAIL_WEB_USER` (default `0`; can be the connected mailbox) |
| `msme/receive/normalize.py` | stores the RFC822 `Message-ID` header |
| `msme/receive/pipeline.py` | row now carries `messageId` + `rfc822MessageId` |
| `msme/db.py` | two extra columns (migration), saved and selected |
| `msme/receive/dashboard.py` · `editor_data.py` | `/checklist.json` and editor items include `emailUrl` + `emailSearchUrl` |
| `static/checklist.html` · `static/editor.html` | **Open email ↗** + **Find in Gmail** in both detail panels |
| `tools/backfill_message_ids.py` (new) | fills `messageId` on old rows from `pipeline_results` |
| `tests/test_email_link.py` (new, 8 tests) | URL builder, encoding, invalid/missing ids, DB round-trip |
| `docs/INDEX.md` · `NEXT_MEETING.md` §8 · `todo/🟢 T-049.md` | N-6 documented; T-049 N-6 ticked |

The backfill was applied: **241 of 241** old rows now have their Gmail id.

✅ nothing to decide — N-6 is built as agreed.

## 2. Verification

| Check | Result |
|---|---|
| `python3 -m compileall -q msme run.py tools tests` | **OK** |
| Full suite | **157 tests, OK** (149 + 8 new) |
| Live container | rebuilt and restarted; `/health` **200** |
| Link builder in the container | `#all/1a162cc0b30af0e7` + `#search/rfc822msgid:CAM1%40mail.gmail.com` |
| Live DB | **241 rows**; first row has `messageId` and `emailUrl` |
| Static pages in the image | `Open email` present in both `checklist.html` and `editor.html` |
| Old-row search link | empty (no RFC822 header saved before N-6); new rows get both links |

✅ nothing to decide — measured, not assumed.

## 3. Live finding — Gmail intake is not renewing (not caused by N-6)

The container log on restart shows:

> `[webhook] watch renewal failed: invalid_grant: Token has been expired or revoked.`

The saved watch has **no expiration** and was last updated **2026-10-29**; runtime settings have
`ENABLE_AUTO=false`, so polling is off. The Gmail token is expired/revoked, which is `T-028` (re-auth
every 7 days; last re-auth 2026-10-22).

**What it means:** new emails may not arrive — push cannot renew and polling is disabled.
**Options:**
- **A (recommended)** — re-authenticate Gmail now (`T-028`), then the watch renews on restart.
- **B** — enable polling (`ENABLE_AUTO=true`) as a stopgap; it still needs a valid token.
- **C** — leave it; intake stays down.

**Effect of not deciding:** the live receive stops; the N-6 link has no new rows to show.
**Blocks:** live receive, not the N-6 build.

⭐ Decision — §3: **A / B / C** for the Gmail token.

## 4. What I recommend next

**Carry on in this session** (low effort): re-auth Gmail (A), then write the N-7/N-8/N-9 notes.
Reason: the demo on 11 Nov needs live rows with the new links.

| # | Item | State |
|---|---|---|
| 1 | N-6 spec + code + UI | done |
| 2 | 157 tests + live container | verified |
| 3 | 241 old rows backfilled | done |
| 4 | Gmail token expired/revoked | **open — §3** |
| 5 | N-7/N-8/N-9 | next |
