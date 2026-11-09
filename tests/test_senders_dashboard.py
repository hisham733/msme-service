"""Tests for the by-sender dashboard queries.

Run: python3 -m unittest tests.test_senders_dashboard -v
"""
import os
import tempfile
import unittest
from unittest.mock import patch

from msme import db


class SenderDashboardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "senders.sqlite3")
        self.patch = patch.object(db.config, "SQLITE_PATH", self.db_path)
        self.patch.start()
        db.init_db()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def _email(self, mid, from_email, name="", when="2026-11-01T10:00:00+00:00", attachments=0):
        db.save_email(
            {
                "messageId": mid,
                "fromEmail": from_email,
                "fromName": name,
                "subject": "Subject " + mid,
                "linksFound": ["https://example.com/" + mid],
                "attachments": [{"filename": "a.pdf"}] * attachments,
            },
            received_at=when,
        )

    def test_summary_counts_and_last_received(self):
        self._email("m1", "a@example.com", "Alice", "2026-11-01T10:00:00+00:00")
        self._email("m2", "a@example.com", "Alice", "2026-11-03T10:00:00+00:00")
        self._email("m3", "b@example.com", "Bob", "2026-11-02T10:00:00+00:00")
        rows = {r["from_email"]: r for r in db.sender_summary()}
        self.assertEqual(rows["a@example.com"]["emails"], 2)
        self.assertEqual(rows["a@example.com"]["last_received"], "2026-11-03T10:00:00+00:00")
        self.assertEqual(rows["b@example.com"]["emails"], 1)
        self.assertEqual(rows["a@example.com"]["from_name"], "Alice")

    def test_rerun_does_not_double_count(self):
        self._email("m1", "a@example.com", "Alice")
        db.save_checklist({"subject": "S", "threadId": "t", "messageId": "m1", "readyToFilter": "false"})
        db.save_checklist({"subject": "S", "threadId": "t", "messageId": "m1", "readyToFilter": "true"})
        rows = db.sender_summary()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["emails"], 1, "the count comes from emails, not checklist")

    def test_detail_uses_latest_checklist_row(self):
        self._email("m1", "a@example.com", "Alice")
        self._email("m2", "a@example.com", "Alice")
        self._email("m3", "b@example.com", "Bob")
        first = db.save_checklist({"subject": "S1", "threadId": "t1", "messageId": "m1", "readyToFilter": "false"})
        second = db.save_checklist({"subject": "S1", "threadId": "t1", "messageId": "m1", "readyToFilter": "true"})
        rows = db.sender_emails("a@example.com")
        self.assertEqual(len(rows), 2)
        by_id = {r["message_id"]: r for r in rows}
        self.assertEqual(by_id["m1"]["checklistId"], second)
        self.assertEqual(by_id["m1"]["readyToFilter"], "true")
        self.assertNotIn("m3", by_id)

    def test_empty_table(self):
        self.assertEqual(db.sender_summary(), [])
        self.assertEqual(db.sender_emails("nobody@example.com"), [])

    def test_empty_sender_is_grouped_as_unknown(self):
        self._email("m1", "", "")
        rows = db.sender_summary()
        self.assertEqual(rows[0]["from_email"], "(unknown sender)")
        detail = db.sender_emails("(unknown sender)")
        self.assertEqual(len(detail), 1)

    def test_backfill_received_at_override(self):
        self._email("m1", "a@example.com", when="2026-10-01T00:00:00+00:00")
        self.assertEqual(db.get_email("m1")["received_at"], "2026-10-01T00:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
