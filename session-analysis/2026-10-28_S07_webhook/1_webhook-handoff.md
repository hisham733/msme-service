# Email webhook — handoff to a new session

**Session:** 2026-10-28 · S07 · reply 1
**State:** in progress; continue from `todo/T-046.md`.

## Done

- Cloudflare Tunnel route `hook.empi.site` → `http://172.17.0.1:8899`; `/api/health` = 200.
- GCP topic/subscription/OIDC/audience validated by the user.
- `config.py`: webhook env keys.
- `db.py`: `gmail_watch`, `webhook_events`, `webhook_messages` + queue primitives.
- `gmail.py`: `profile`, `watch`, `stop_watch`, `history_list`.
- `receive_queue.py`: DB-backed one-at-a-time worker + watch renewal.
- Compile/tests: **81 pass**.

## Not done

1. `webhook_gmail.py` OIDC verification + history decoding + enqueue.
2. `POST /webhooks/gmail` route.
3. `receive_queue.start()` in `combined.py`.
4. Scheduler enqueue switch.
5. Docker env values for webhook + fixed replies.
6. `tools/test_webhook.py`.
7. Rebuild, `users.watch`, real Gmail test.

## Continue in a new session

Open the same folder:

`/home/hisham/Desktop/new_div/msme-service`

Then read `AGENTS.md` → `README.md` → `NOW.md` → `todo/T-046.md` → this reply. Start with `webhook_gmail.py`.

Do not repeat the Cloudflare/GCP setup. The endpoint is still **404** until step 1–2 are deployed.

✅ nothing to decide
