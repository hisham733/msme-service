# =============================================================================
# FILE HEADER
# file    : tools/test_gmail_unread.py
# role    : Tests — unread-only Gmail query + single-run mark-read
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : prove list_unread appends is:unread, the reply thread lookup can opt out, and a
#           single successful/needs_human run marks the message read.
# pages   : n/a
# calls   : gmail, dashboard, main, checklist, db
# called  : developer / CI (python3 -m unittest tools.test_gmail_unread)
# amend   : no network, no live DB/mailbox; all services and pipeline calls are fake.
# =============================================================================
"""Unit tests for T-042 (unread-only refresh + mark-read).

Run:
    python3 -m unittest tools.test_gmail_unread -v
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import checklist
import dashboard
import gmail
import main


class _Req:
    def __init__(self, payload):
        self.payload = payload

    def execute(self):
        return self.payload


class _Messages:
    def __init__(self, captured):
        self.captured = captured

    def list(self, **kwargs):
        self.captured.update(kwargs)
        return _Req({"messages": []})


class _Users:
    def __init__(self, captured):
        self.captured = captured

    def messages(self):
        return _Messages(self.captured)


class _Service:
    def __init__(self):
        self.captured = {}

    def users(self):
        return _Users(self.captured)


class QueryTests(unittest.TestCase):
    def _q(self, query, unread_only=True):
        service = _Service()
        with patch.object(gmail, "_throttle", lambda: None):
            gmail.list_unread(service, query=query, unread_only=unread_only)
        return service.captured.get("q", "")

    def test_plain_query_gets_unread(self):
        q = self._q("in:inbox -category:promotions")
        self.assertIn("is:unread", q)

    def test_existing_unread_not_duplicated(self):
        q = self._q("in:inbox is:unread -category:promotions")
        self.assertEqual(q.lower().count("is:unread"), 1)

    def test_label_unread_not_duplicated(self):
        q = self._q("in:inbox label:unread -category:promotions")
        self.assertEqual(q.lower().count("label:unread"), 1)
        self.assertNotIn("is:unread", q.lower())

    def test_thread_lookup_can_keep_anywhere(self):
        q = self._q("thread:abc in:anywhere", unread_only=False)
        self.assertEqual(q, "thread:abc in:anywhere")

    def test_empty_query_uses_unread_default(self):
        q = self._q("")
        self.assertIn("is:unread", q)


class MarkReadTests(unittest.TestCase):
    def test_dashboard_single_run_marks_read(self):
        calls = []
        with patch.object(dashboard.creds, "gmail", return_value=object()), \
             patch.object(dashboard.pipeline, "process_email", return_value={"subject": "x"}), \
             patch.object(checklist, "save_checklist", return_value=None), \
             patch.object(dashboard.gmail, "mark_read",
                          side_effect=lambda svc, email_id: calls.append(email_id)):
            row = dashboard._process_one("msg-1", run_id="run-1")
        self.assertEqual(row["subject"], "x")
        self.assertEqual(calls, ["msg-1"])

    def test_dashboard_needs_human_marks_read(self):
        calls = []
        with patch.object(dashboard.creds, "gmail", return_value=object()), \
             patch.object(dashboard.pipeline, "process_email",
                          return_value={"subject": "x", "_status": "needs_human"}), \
             patch.object(checklist, "save_checklist", return_value=None), \
             patch.object(dashboard.gmail, "mark_read",
                          side_effect=lambda svc, email_id: calls.append(email_id)):
            dashboard._process_one("msg-2", run_id="run-2")
        self.assertEqual(calls, ["msg-2"])

    def test_main_single_run_marks_read(self):
        calls = []
        with patch.object(main.creds, "gmail", return_value=object()), \
             patch.object(main.db, "log_run_start", return_value="run-3"), \
             patch.object(main.pipeline, "process_email", return_value={"subject": "x"}), \
             patch.object(checklist, "save_checklist", return_value=None), \
             patch.object(main.gmail, "mark_read",
                          side_effect=lambda svc, email_id: calls.append(email_id)):
            row = main._process_one("msg-3")
        self.assertEqual(row["subject"], "x")
        self.assertEqual(calls, ["msg-3"])


if __name__ == "__main__":
    unittest.main()
