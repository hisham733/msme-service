# T-046 — pull vs push: your subscription must be Push

**Session:** 2026-10-28 · S07 · reply 4
**Register:** `todo/✅ T-046.md` · **Previous:** `3_T-046_push-test.md`

## 1. Short answer

**Yes — a pull subscription will never call the webhook.** Pull means Pub/Sub keeps the
messages until a client asks for them. Nothing is POSTed to `hook.empi.site`, which is exactly
what the last test showed: the topic received Gmail's notification, but the endpoint got zero
requests. The app never pulls from the subscription, so a pull subscription is invisible to it.

Push is the delivery mode that makes the HTTP POST. It is not a different topic — same topic,
different subscription delivery type.

✅ nothing to decide — this is the explanation of the measurement.

## 2. Do you need a new subscription? Only if it is in the wrong project

Check **which project** the pull subscription you shared lives in:

- **If it is in `sme-ai-510803` on topic `gmail-push`** → **no new subscription needed.**
  Edit that subscription and change **Delivery type: Pull → Push**:
  - endpoint `https://hook.empi.site/webhooks/gmail`
  - enable authentication; audience `https://hook.empi.site/webhooks/gmail`
  - service account: the same one the pull subscription already uses, or per option A/B in
    reply 2.
  Google Cloud allows changing the push configuration of an existing subscription; the topic
  cannot be changed, but this one is already on the right topic.
- **If it is in `msme-news-webhook`** → **create a new one** in `sme-ai-510803` on topic
  `gmail-push` (delivery Push, same three settings). A subscription's topic is fixed at
  creation, and that project's topic is the one Gmail rejects anyway. The old pull
  subscription can stay or be deleted; it will receive nothing useful.

Not sure which project? The subscription page header shows `sme-ai-510803` or
`msme-news-webhook`; that word decides between the two paths.

✅ nothing to decide — one conditional action, no choice to make.

## 3. What happens to the messages already sitting in the pull subscription

Nothing important. Gmail's Pub/Sub payload is only `{emailAddress, historyId}` — a "check the
mailbox" ping, not the email. The app replays Gmail history from its own cursor (`63372` after
the cleanup in reply 3), so old pings are not needed and no mail is lost when you switch.
The first real push after the switch replays everything that arrived after `63372`.

✅ nothing to decide.

## 4. What I will do once it is Push

Reply "subscription is push" (or "created"), and I will insert one inbound test message and
expect, within seconds:

- `[webhook] ... history: 1 id(s), 1 queued` in `docker logs msme-service`;
- one row in `webhook_events` (`done`);
- one row in `webhook_messages` (`done`);
- the endpoint log line `POST /webhooks/gmail 200`.

Then I trash the test message and close T-046's live proof. Stay in this session; **low
thinking effort**.

## Recap

| Question | Answer |
|---|---|
| Does pull work for a webhook? | No — it never POSTs |
| Same topic or new topic? | Same topic; only the subscription delivery type changes |
| New subscription? | Only if the pull one is in `msme-news-webhook` |
| Messages lost while switching? | No — Gmail pings carry no email; history replays them |
| Fallback meanwhile | 5-minute polling |
