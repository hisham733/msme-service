# Production email switch — runbook

_For moving the service from the test mailbox to the production mailbox._
_Do not commit `creds/`, `.env`, or any token. Keep a backup before changing credentials._

Production mailbox: `____________________________`  
OAuth client project (must own the Pub/Sub topic): `sme-ai-510803`  
Webhook GCP project named in early notes: `msme-news-webhook`

> **Hard rule:** Gmail `users.watch` only accepts a topic in the **same project as the
> OAuth client** behind `creds/gmail.json`. Otherwise it returns
> `Invalid topicName does not match projects/<oauth-project>/topics/*`. The push
> subscription must live in that same project too. The current working topic is
> `projects/sme-ai-510803/topics/gmail-push`.

| Date | Old mailbox | New mailbox | Changed by | Watch expires |
|---|---|---|---|---|
|  |  |  |  |  |

## What stays the same

If the Google Cloud project and domain stay the same, these do **not** need rebuilding:

- OAuth client project `sme-ai-510803`
- Pub/Sub topic `projects/sme-ai-510803/topics/gmail-push`
- Push subscription `gmail-push-sub` (in `sme-ai-510803`)
- Endpoint `https://hook.empi.site/webhooks/gmail`
- OIDC service account `msme-webhook-push@sme-ai-510803.iam.gserviceaccount.com`
  (push subscription authentication in `sme-ai-510803`)
- Cloudflare Tunnel and `hook.empi.site`

If the new mailbox's OAuth client belongs to a **different** project, recreate the
topic and subscription in that project and update `GMAIL_PUBSUB_TOPIC`; the endpoint
and tunnel can stay.

Only the **Gmail account, its OAuth credentials, and the Gmail watch** change.

## 1. Prepare the production mailbox

- [ ] Confirm the production Gmail address.
- [ ] Sign in to that Gmail once and confirm it can receive mail.
- [ ] Confirm Gmail API access is allowed for that account.
- [ ] If the OAuth app is in **Testing**, add the production address as a **Test user**:
  Google Cloud → APIs & Services → OAuth consent screen → Test users.
- [ ] Better for production: publish the OAuth consent screen to **Production** so refresh tokens do not expire every 7 days.

## 2. Back up the current credentials

```bash
mkdir -p data/backups
cp -a creds data/backups/creds-$(date +%Y%m%d-%H%M%S)
cp data/settings.json data/backups/settings-$(date +%Y%m%d-%H%M%S).json
```

Never copy `creds/` into git.

## 3. Re-authorize the production Gmail account

Use the existing OAuth client ID/secret from the Google Cloud OAuth client.

```bash
export GOOGLE_CLIENT_ID='...'
export GOOGLE_CLIENT_SECRET='...'
export OAUTH_REDIRECT='http://127.0.0.1:8080/'

python3 reauth_google.py url
```

1. Open the printed URL.
2. Sign in as the **production Gmail account**.
3. Approve all requested scopes.
4. The browser will fail to load `127.0.0.1:8080`; that is normal.
5. Copy the full redirected URL.

Exchange the code:

```bash
python3 reauth_google.py exchange "http://127.0.0.1:8080/?code=...&scope=..."
```

This rewrites:

```text
creds/gmail.json
creds/drive.json
creds/sheets.json
```

## 4. Update settings

In **Config → Config Receive** (or `data/settings.json`):

- [ ] `GMAIL_QUERY` — keep:
  `in:inbox is:unread -category:promotions`
- [ ] Confirm the checklist Sheet ID / Drive folder if they changed for production.
- [ ] Reply settings in `docker-compose.yml` environment:
  - `REPLY_ENABLED=true`
  - `REPLY_MODE=fixed_email`
  - `REPLY_TO_EMAIL=fhwvdu@gmail.com`

Then rebuild/restart:

```bash
docker compose up -d --build
```

## 5. Verify the Gmail account

```bash
docker compose exec -T msme-service python3 - <<'PY'
import creds
p = creds.gmail().users().getProfile(userId="me").execute()
print(p["emailAddress"])
PY
```

It must print the **production** address, not the old one.

Check the queue:

```bash
curl -s 'http://localhost:8899/api/emails?force=1'
```

Only unread production mail should appear.

## 6. Reset the Gmail Push watch

> **From 2026-11-07 the Config page owns this:** `/config.html` → **Config Receive** has
> *Gmail push webhook* (Enable/Disable, watch expiry, polling warning) and *Google account —
> reconnect* (consent URL + paste the redirected URL). The manual command below remains the
> fallback (`D41`).

Do this **after** `/webhooks/gmail` is deployed. If the webhook is not live, skip this step.

```bash
docker compose exec -T msme-service python3 - <<'PY'
import creds
topic = "projects/sme-ai-510803/topics/gmail-push"
svc = creds.gmail()
r = svc.users().watch(userId="me", body={
    "topicName": topic,
    "labelIds": ["INBOX"],
}).execute()
print("historyId", r["historyId"])
print("expiration", r["expiration"])
PY
```

- [ ] Save `historyId` and `expiration` in the app watch state once the webhook code stores it.
- [ ] A watch expires in ~7 days; renew every 6 days.
- [ ] If the watch is not renewed, polling remains the fallback.

## 7. Test one email end to end

- [ ] Send one new email to the production Gmail.
- [ ] Wait for the webhook or click **Refresh** on the Checklist.
- [ ] Select and run the email.
- [ ] Confirm:
  - a new checklist row appears;
  - the article is archived under `all_emails/`;
  - the filter result is stored;
  - the Repurpose column reaches `Published Locally` when validated;
  - if the receive has an issue, a reply goes to `fhwvdu@gmail.com` with the reason and resend request.
- [ ] Send a second email to prove repeatability.

## 8. If the Google Cloud project or domain changes

Redo only the affected parts:

- New GCP project: it must be the **OAuth client's** project. Create `gmail-push` there, grant `gmail-api-push@system.gserviceaccount.com` Pub/Sub Publisher, create the OIDC service account, and create the push subscription in the same project.
- New webhook domain: update the subscription endpoint + audience, update the Cloudflare Tunnel public hostname, and update `WEBHOOK_AUDIENCE` / `WEBHOOK_SERVICE_ACCOUNT`.
- New Gmail mailbox: only sections 2–7 are needed.

## 9. Rollback

- Stop the Gmail watch if needed.
- Restore the backed-up `creds/` and `settings.json`.
- Restart the container.
- Re-authorize the old mailbox if necessary.
- Confirm `/api/emails?force=1` and `/api/health`.

## 10. After switching

- [ ] Rotate any tunnel token that was exposed in chat.
- [ ] Keep Cloudflare Access on the dashboard; bypass only `/webhooks/gmail`.
- [ ] Keep polling enabled as fallback.
- [ ] Check the fixed reply address is still `fhwvdu@gmail.com` until sender replies are approved.
