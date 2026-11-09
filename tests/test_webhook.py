# =============================================================================
# FILE HEADER
# file    : tests/test_webhook.py
# role    : Tests — Gmail Push webhook + shared receive queue
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : prove OIDC rejection (empty/invalid/wrong audience/wrong service account), payload
#           rejection, event dedupe, history → queue, retryable history errors, and queue
#           claim/finish/error/recovery with no network and a temporary SQLite file.
# pages   : n/a
# calls   : webhook_gmail, receive_queue, db, dashboard
# called  : developer / CI (python3 -m unittest tests.test_webhook -v)
# amend   : no live Gmail, no live DB; the OIDC verifier and Gmail service are patched.
# =============================================================================
"""Unit tests for T-046 (Gmail Push webhook).

Run:
    python3 -m unittest tests.test_webhook -v
"""
import base64
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from msme import db
from msme.receive import dashboard, receive_queue, webhook_gmail

AUDIENCE = "https://hook.empi.site/webhooks/gmail"
SERVICE_ACCOUNT = "msme-webhook-push@sme-ai-510803.iam.gserviceaccount.com"
AUTH = "Bearer fake-token"


def _b64(obj):
    raw = obj if isinstance(obj, bytes) else json.dumps(obj).encode()
    return base64.b64encode(raw).decode()


def _push(history_id="250", email="msme@example.com", message_id="msg-1", data=None):
    if data is None:
        data = _b64({"emailAddress": email, "historyId": str(history_id)})
    return json.dumps({"message": {"data": data, "messageId": message_id},
                       "subscription": "projects/p/subscriptions/gmail-push-sub"}).encode()


class _Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patch_db = patch.object(db.config, "SQLITE_PATH",
                                     os.path.join(self.tmp.name, "webhook.sqlite3"))
        self.patch_db.start()
        db.init_db()
        self.cfg = [
            patch.object(webhook_gmail.config, "WEBHOOK_AUDIENCE", AUDIENCE),
            patch.object(webhook_gmail.config, "WEBHOOK_SERVICE_ACCOUNT", SERVICE_ACCOUNT),
            patch.object(webhook_gmail.config, "GMAIL_PUBSUB_TOPIC",
                         "projects/msme-news-webhook/topics/gmail-push"),
            patch.object(webhook_gmail.config, "GMAIL_QUERY", "in:inbox is:unread"),
        ]
        for p in self.cfg:
            p.start()
        # The webhook is ON by default in these tests (the toggle has its own class below).
        self.patch_enabled = patch.object(
            webhook_gmail.receive_queue, "webhook_enabled", return_value=True)
        self.patch_enabled.start()

    def tearDown(self):
        self.patch_enabled.stop()
        for p in reversed(self.cfg):
            p.stop()
        self.patch_db.stop()
        self.tmp.cleanup()

    def _valid_token(self):
        return patch.object(
            webhook_gmail.id_token, "verify_oauth2_token",
            return_value={"email": SERVICE_ACCOUNT, "email_verified": True, "aud": AUDIENCE},
        )

    def _count(self, sql, args=()):
        c = db._connect()
        try:
            return c.execute(sql, args).fetchone()[0]
        finally:
            c.close()

    def _status(self, message_id):
        c = db._connect()
        try:
            r = c.execute("select status, error from webhook_messages where message_id=?",
                          (message_id,)).fetchone()
            return r["status"] if r else None
        finally:
            c.close()


class AuthTests(_Base):
    def test_missing_token_rejected(self):
        status, body = webhook_gmail.handle_push_request("", _push())
        self.assertEqual(status, 401)
        self.assertEqual(self._count("select count(*) from webhook_events"), 0)

    def test_non_bearer_header_rejected(self):
        status, _ = webhook_gmail.handle_push_request("Basic abc", _push())
        self.assertEqual(status, 401)

    def test_invalid_token_rejected(self):
        with patch.object(webhook_gmail.id_token, "verify_oauth2_token",
                          side_effect=ValueError("bad signature")):
            status, _ = webhook_gmail.handle_push_request(AUTH, _push())
        self.assertEqual(status, 401)

    def test_audience_is_enforced(self):
        captured = {}

        def fake(token, request, audience=None, **kwargs):
            captured["audience"] = audience
            return {"email": SERVICE_ACCOUNT, "email_verified": True}

        with patch.object(webhook_gmail.id_token, "verify_oauth2_token", side_effect=fake), \
                patch.object(webhook_gmail.gmail, "list_unread", return_value=[]):
            status, _ = webhook_gmail.handle_push_request(AUTH, _push(), service=object())
        self.assertEqual(status, 200)
        self.assertEqual(captured["audience"], AUDIENCE)

    def test_wrong_audience_rejected(self):
        def fake(token, request, audience=None, **kwargs):
            raise ValueError("Token audience doesn't match")

        with patch.object(webhook_gmail.config, "WEBHOOK_AUDIENCE", "https://wrong.example/hook"), \
                patch.object(webhook_gmail.id_token, "verify_oauth2_token", side_effect=fake):
            status, _ = webhook_gmail.handle_push_request(AUTH, _push())
        self.assertEqual(status, 401)

    def test_wrong_service_account_rejected(self):
        with patch.object(webhook_gmail.id_token, "verify_oauth2_token",
                          return_value={"email": "attacker@example.com", "email_verified": True}):
            status, _ = webhook_gmail.handle_push_request(AUTH, _push())
        self.assertEqual(status, 401)

    def test_missing_service_account_config_fails_closed(self):
        with patch.object(webhook_gmail.config, "WEBHOOK_SERVICE_ACCOUNT", ""), \
                self._valid_token():
            status, _ = webhook_gmail.handle_push_request(AUTH, _push())
        self.assertEqual(status, 401)

    def test_unverified_email_rejected(self):
        with patch.object(webhook_gmail.id_token, "verify_oauth2_token",
                          return_value={"email": SERVICE_ACCOUNT, "email_verified": False}):
            status, _ = webhook_gmail.handle_push_request(AUTH, _push())
        self.assertEqual(status, 401)

    def test_route_is_registered(self):
        routes = [r for r in dashboard.app.routes if getattr(r, "path", "") == "/webhooks/gmail"]
        self.assertTrue(routes)
        self.assertIn("POST", routes[0].methods)


class PayloadTests(_Base):
    def test_invalid_json_is_400(self):
        with self._valid_token():
            status, _ = webhook_gmail.handle_push_request(AUTH, b"not json")
        self.assertEqual(status, 400)

    def test_missing_message_is_400(self):
        with self._valid_token():
            status, _ = webhook_gmail.handle_push_request(AUTH, b"{}")
        self.assertEqual(status, 400)

    def test_missing_data_is_400(self):
        body = json.dumps({"message": {"messageId": "m"}}).encode()
        with self._valid_token():
            status, _ = webhook_gmail.handle_push_request(AUTH, body)
        self.assertEqual(status, 400)

    def test_bad_base64_is_400(self):
        with self._valid_token():
            status, _ = webhook_gmail.handle_push_request(AUTH, _push(data="!!!not-base64!!!"))
        self.assertEqual(status, 400)

    def test_missing_history_id_is_400(self):
        data = _b64({"emailAddress": "a@b.com"})
        with self._valid_token():
            status, _ = webhook_gmail.handle_push_request(AUTH, _push(data=data))
        self.assertEqual(status, 400)

    def test_auth_runs_before_payload_parsing(self):
        status, _ = webhook_gmail.handle_push_request("", b"not json")
        self.assertEqual(status, 401)


class HistoryTests(_Base):
    def test_history_enqueues_and_advances_cursor(self):
        db.save_gmail_watch("100", 999, "projects/msme-news-webhook/topics/gmail-push")
        with self._valid_token(), \
                patch.object(webhook_gmail.gmail, "history_list",
                             return_value=(["m1", "m2"], "250")):
            status, body = webhook_gmail.handle_push_request(AUTH, _push(), service=object())
        self.assertEqual(status, 200)
        self.assertEqual(body["mode"], "history")
        self.assertEqual(body["queued"], 2)
        self.assertEqual(self._count("select count(*) from webhook_messages where status='queued'"), 2)
        self.assertEqual(db.get_gmail_watch()["history_id"], "250")
        self.assertEqual(self._count("select count(*) from webhook_events where status='done'"), 1)

    def test_duplicate_event_is_not_reprocessed(self):
        db.save_gmail_watch("100", 999, "projects/msme-news-webhook/topics/gmail-push")
        calls = []

        def fake_history(service, start, **kwargs):
            calls.append(start)
            return ["m1"], "250"

        with self._valid_token(), \
                patch.object(webhook_gmail.gmail, "history_list", side_effect=fake_history):
            first = webhook_gmail.handle_push_request(AUTH, _push(), service=object())
            second = webhook_gmail.handle_push_request(AUTH, _push(), service=object())
        self.assertEqual(first[0], 200)
        self.assertEqual(second[0], 200)
        self.assertEqual(second[1]["status"], "duplicate")
        self.assertEqual(len(calls), 1)
        self.assertEqual(self._count("select count(*) from webhook_messages"), 1)

    def test_missing_watch_bootstraps_from_unread(self):
        with self._valid_token(), \
                patch.object(webhook_gmail.gmail, "list_unread",
                             return_value=[{"id": "u1"}, {"id": "u2"}]):
            status, body = webhook_gmail.handle_push_request(AUTH, _push("300"), service=object())
        self.assertEqual(status, 200)
        self.assertEqual(body["mode"], "bootstrap")
        self.assertEqual(body["queued"], 2)
        self.assertEqual(db.get_gmail_watch()["history_id"], "300")

    def test_expired_history_cursor_recovers_from_unread(self):
        class _Err(Exception):
            class resp:
                status = 404

        db.save_gmail_watch("1", 999, "projects/x/topics/gmail-push")
        with self._valid_token(), \
                patch.object(webhook_gmail.gmail, "history_list", side_effect=_Err("not found")), \
                patch.object(webhook_gmail.gmail, "list_unread", return_value=[{"id": "u9"}]):
            status, body = webhook_gmail.handle_push_request(AUTH, _push("400"), service=object())
        self.assertEqual(status, 200)
        self.assertEqual(body["mode"], "recover")
        self.assertEqual(body["queued"], 1)
        self.assertEqual(db.get_gmail_watch()["history_id"], "400")

    def test_transient_error_is_retryable(self):
        db.save_gmail_watch("100", 999, "projects/x/topics/gmail-push")
        with self._valid_token(), \
                patch.object(webhook_gmail.gmail, "history_list", side_effect=RuntimeError("500 backend")):
            status, _ = webhook_gmail.handle_push_request(AUTH, _push(), service=object())
        self.assertEqual(status, 500)
        self.assertEqual(self._count("select count(*) from webhook_events where status='error'"), 1)
        with self._valid_token(), \
                patch.object(webhook_gmail.gmail, "history_list", return_value=(["m1"], "250")):
            retry_status, retry_body = webhook_gmail.handle_push_request(
                AUTH, _push(), service=object())
        self.assertEqual(retry_status, 200)
        self.assertEqual(retry_body["queued"], 1)


class QueueTests(_Base):
    def test_claim_finish_and_recovery(self):
        receive_queue.enqueue_ids(["q1", "q2"], source="test")
        first = db.claim_webhook_message()
        self.assertEqual(first["message_id"], "q1")
        self.assertEqual(self._status("q1"), "running")
        db.finish_webhook_message("q1", "done")
        second = db.claim_webhook_message()
        self.assertEqual(second["message_id"], "q2")
        db.finish_webhook_message("q2", "error", "boom")
        self.assertEqual(self._status("q2"), "error")
        self.assertEqual(db.enqueue_webhook_messages(["q2"]), 1)
        self.assertEqual(self._status("q2"), "queued")
        self.assertIsNotNone(db.claim_webhook_message())
        self.assertEqual(db.recover_webhook_queue(), 1)
        self.assertEqual(self._status("q2"), "queued")

    def test_done_message_is_not_reenqueued(self):
        db.enqueue_webhook_messages(["q3"])
        db.finish_webhook_message("q3", "done")
        self.assertEqual(db.enqueue_webhook_messages(["q3"]), 0)
        self.assertIsNone(db.claim_webhook_message())

    def test_process_one_success_marks_read(self):
        receive_queue.enqueue_ids(["q4"])
        row = {"subject": "Webhook article", "readyToFilter": "true"}
        with patch.object(receive_queue.creds, "gmail", return_value=object()), \
                patch.object(receive_queue.pipeline, "process_email", return_value=row), \
                patch.object(receive_queue, "save_checklist") as save, \
                patch.object(receive_queue.gmail, "mark_read") as mark:
            self.assertTrue(receive_queue.process_one())
        save.assert_called_once_with(row)
        mark.assert_called_once()
        self.assertEqual(self._status("q4"), "done")
        self.assertFalse(receive_queue.process_one())

    def test_process_one_failure_is_retryable(self):
        receive_queue.enqueue_ids(["q5"])
        with patch.object(receive_queue.creds, "gmail", return_value=object()), \
                patch.object(receive_queue.pipeline, "process_email",
                             side_effect=RuntimeError("pipeline boom")), \
                patch.object(receive_queue.gmail, "mark_read"):
            self.assertTrue(receive_queue.process_one())
        self.assertEqual(self._status("q5"), "error")
        self.assertEqual(db.enqueue_webhook_messages(["q5"]), 1)
        self.assertEqual(self._status("q5"), "queued")


class ToggleTests(_Base):
    """The Config-page on/off switch (T-055)."""

    def _settings(self, path):
        self.patch_settings = patch.object(receive_queue.settings_store, "SETTINGS_PATH", path)
        self.patch_settings.start()
        self.addCleanup(self.patch_settings.stop)

    def test_disabled_webhook_is_acknowledged_without_processing(self):
        with patch.object(webhook_gmail.receive_queue, "webhook_enabled", return_value=False), \
                self._valid_token():
            status, body = webhook_gmail.handle_push_request(AUTH, _push())
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "disabled")
        self.assertEqual(self._count("select count(*) from webhook_events"), 0)

    def test_apply_webhook_on_creates_and_stores_watch(self):
        self._settings(os.path.join(self.tmp.name, "settings.json"))
        with patch.object(receive_queue, "webhook_topic",
                          return_value="projects/x/topics/gmail-push"), \
                patch.object(receive_queue, "webhook_enabled", return_value=True), \
                patch.object(receive_queue.creds, "gmail", return_value=object()), \
                patch.object(receive_queue.gmail, "watch",
                             return_value={"historyId": "777", "expiration": 999}):
            result = receive_queue.apply_webhook(True)
        self.assertTrue(result["enabled"])
        self.assertEqual(result["watch"]["history_id"], "777")
        self.assertEqual(result["error"], "")
        self.assertEqual(db.get_gmail_watch()["history_id"], "777")

    def test_apply_webhook_off_stops_and_clears(self):
        self._settings(os.path.join(self.tmp.name, "settings.json"))
        db.save_gmail_watch("100", 999, "projects/x/topics/gmail-push")
        with patch.object(receive_queue.creds, "gmail", return_value=object()), \
                patch.object(receive_queue.gmail, "stop_watch") as stop:
            result = receive_queue.apply_webhook(False)
        self.assertFalse(result["enabled"])
        stop.assert_called_once()
        self.assertIsNone(db.get_gmail_watch())

    def test_apply_webhook_on_without_topic_reports_error(self):
        self._settings(os.path.join(self.tmp.name, "settings.json"))
        with patch.object(receive_queue, "webhook_topic", return_value=""):
            result = receive_queue.apply_webhook(True)
        self.assertTrue(result["enabled"])
        self.assertIn("GMAIL_PUBSUB_TOPIC", result["error"])


if __name__ == "__main__":
    unittest.main()
