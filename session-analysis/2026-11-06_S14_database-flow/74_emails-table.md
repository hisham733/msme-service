# 74 — New `emails` table built and linked to the checklist

_2026-11-06 (S14) · code + docs · live container rebuilt._

## 1. What changed

| File | Change |
|---|---|
| `msme/db.py` | new `emails` table; `save_email`, `get_email`, `list_emails`; `list_checklist` now LEFT JOINs `emails`; index on `checklist.messageId` |
| `msme/receive/pipeline.py` | calls `db.save_email(model)` early in `_run_pipeline` when not dry-run |
| `tests/test_emails_table.py` (new, 4 tests) | round-trip, repeat keeps first `received_at`, missing id, checklist join |
| `docs/workflow/DATABASE-FLOW.md` | flow, table catalog, connections, §9 schema |
| `docs/workflow/database-schema.svg` / `.png` / `.dot` | graph regenerated with the `emails` node |

The table is exactly your list:

```sql
CREATE TABLE emails (
    message_id TEXT PRIMARY KEY,
    from_name TEXT, from_email TEXT,
    subject TEXT,
    received_at TEXT,
    links_json TEXT,
    attachment_count INTEGER DEFAULT 0
);
```

- `received_at` = **first time we saw the email** (UTC ISO); a re-run keeps the first value.
- `links_json` = `linksFound` as JSON.
- `attachment_count` = number of attachments.
- No body, no attachment bytes.

## 2. The link to the checklist

```sql
select c.id, c.subject, e.from_name, e.from_email, e.links_json, e.attachment_count
from checklist c
left join emails e on e.message_id = c.messageId;
```

`db.list_checklist()` already returns `emailFrom`, `emailFromName`, `emailLinks`,
`emailAttachments`, so the checklist/editor can show them without a second query.

## 3. Verification

| Check | Result |
|---|---|
| `compileall` | **OK** |
| Full suite | **195 tests, OK** (8 skipped) |
| Live container | rebuilt; `/health` **200** |
| `emails` table in the live DB | created, **7 columns** |
| Live rows | **0** (no new emails since the Gmail token expired) |
| `list_checklist` join | 241 rows; `emailFrom = None` for old rows, no crash |

✅ nothing to decide — the table and the link work.

## 4. One operational note

New emails will fill `emails` only when Gmail is receiving again. The token is still
`invalid_grant` (`T-028`), so intake is down; the table is ready for the next re-auth.

## 5. What I recommend next

**Carry on** (low effort): the **N-9** cost/credit note, then stop for the 11-Nov call.

| # | Item | State |
|---|---|---|
| 1 | `emails` table + checklist join | done |
| 2 | 195 tests + live container | verified |
| 3 | Docs + schema graph | updated |
| 4 | Gmail token (`T-028`) | **open — user action** |
| 5 | N-9 cost/credit | next |
