# Production email switch — runbook created

**Session:** 2026-10-27 · S06 · reply 13

## File

`docs/PRODUCTION-EMAIL-SETUP.md`

## Covers

- What stays the same when the GCP project/domain do not change.
- Backing up `creds/` and `settings.json`.
- Re-authorizing the production Gmail account with `reauth_google.py`.
- Updating `GMAIL_QUERY`, Sheet/Drive IDs and reply environment.
- Verifying the connected Gmail account.
- Resetting the Gmail Push watch **after** the webhook is deployed.
- End-to-end test, new-project/new-domain differences, and rollback.
- A change-record table for the old/new mailbox, operator and watch expiry.

Indexed in `docs/INDEX.md` and `README.md`.

✅ nothing to decide
