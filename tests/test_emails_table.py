"""Tests for the compact `emails` table (received-email envelope).

Run: python3 -m unittest tests.test_emails_table -v
"""
import json
import os
import tempfile
import time
import unittest
from unittest.mock import patch

from msme import db


class EmailsTableTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "emails.sqlite3")
        self.patch = patch.object(db.config, "SQLITE_PATH", self.db_path)
        self.patch.start()
        db.init_db()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def _model(self, **over):
        model = {
            "messageId": "msg-1",
            "fromName": "Editor MSME",
            "fromEmail": "editor@example.com",
            "subject": "Example release",
            "linksFound": ["https://example.com/release", "https://example.com/report"],
            "attachments": [{"filename": "a.pdf"}, {"filename": "b.docx"}],
        }
        model.update(over)
        return model

    def test_save_round_trip(self):
        self.assertTrue(db.save_email(self._model()))
        row = db.get_email("msg-1")
        self.assertEqual(row["from_name"], "Editor MSME")
        self.assertEqual(row["from_email"], "editor@example.com")
        self.assertEqual(row["subject"], "Example release")
        self.assertEqual(row["attachment_count"], 2)
        self.assertEqual(row["links"], ["https://example.com/release", "https://example.com/report"])
        self.assertTrue(row["received_at"])

    def test_repeat_keeps_first_received_at(self):
        db.save_email(self._model())
        first = db.get_email("msg-1")["received_at"]
        time.sleep(0.01)
        db.save_email(self._model(linksFound=["https://example.com/new"], attachments=[]))
        row = db.get_email("msg-1")
        self.assertEqual(row["received_at"], first)
        self.assertEqual(row["attachment_count"], 0)
        self.assertEqual(row["links"], ["https://example.com/new"])
        self.assertEqual(len(db.list_emails()), 1)

    def test_missing_message_id_writes_nothing(self):
        self.assertFalse(db.save_email({"fromName": "No id"}))
        self.assertEqual(db.list_emails(), [])

    def test_checklist_join_exposes_email_fields(self):
        db.save_email(self._model())
        db.save_checklist({"subject": "Example release", "threadId": "t-1", "messageId": "msg-1"})
        rows = db.list_checklist()
        self.assertEqual(rows[0]["emailFrom"], "editor@example.com")
        self.assertEqual(rows[0]["emailFromName"], "Editor MSME")
        self.assertEqual(rows[0]["emailAttachments"], 2)
        self.assertEqual(json.loads(rows[0]["emailLinks"]),
                         ["https://example.com/release", "https://example.com/report"])


if __name__ == "__main__":
    unittest.main()
