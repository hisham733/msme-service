"""N-6 tests: Gmail links and checklist identity storage.

Run: python3 -m unittest tests.test_email_link -v
"""
import os
import tempfile
import unittest
from unittest.mock import patch

from msme import db
from msme.receive import email_link


class GmailUrlTests(unittest.TestCase):
    def test_direct_link_from_message_id(self):
        urls = email_link.gmail_urls("1a162cc0b30af0e7", "")
        self.assertEqual(
            urls["emailUrl"],
            "https://mail.google.com/mail/u/0/#all/1a162cc0b30af0e7",
        )
        self.assertEqual(urls["emailSearchUrl"], "")

    def test_search_link_strips_brackets_and_encodes(self):
        urls = email_link.gmail_urls("", "<CAM123@mail.gmail.com>")
        self.assertEqual(urls["emailUrl"], "")
        self.assertIn("#search/rfc822msgid:CAM123%40mail.gmail.com", urls["emailSearchUrl"])

    def test_invalid_message_id_is_rejected(self):
        urls = email_link.gmail_urls("abc/def", "")
        self.assertEqual(urls["emailUrl"], "")

    def test_missing_ids_return_empty_links(self):
        urls = email_link.gmail_urls("", "")
        self.assertEqual(urls, {"emailUrl": "", "emailSearchUrl": ""})

    def test_account_setting_is_used(self):
        with patch.object(email_link.settings_store, "get", return_value="editor@example.com"):
            urls = email_link.gmail_urls("abc123", "")
        self.assertIn("/u/editor@example.com/#all/abc123", urls["emailUrl"])

    def test_enrich_row_adds_both_links(self):
        row = {"messageId": "abc123", "rfc822MessageId": "<x@y>"}
        email_link.enrich_row(row)
        self.assertTrue(row["emailUrl"])
        self.assertTrue(row["emailSearchUrl"])


class ChecklistStorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "email-link.sqlite3")
        self.patch = patch.object(db.config, "SQLITE_PATH", self.db_path)
        self.patch.start()
        db.init_db()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_message_ids_round_trip(self):
        db.save_checklist({
            "subject": "Example",
            "threadId": "thread-1",
            "messageId": "msg-1",
            "rfc822MessageId": "<cam@example.com>",
        })
        rows = db.list_checklist()
        self.assertEqual(rows[0]["messageId"], "msg-1")
        self.assertEqual(rows[0]["rfc822MessageId"], "<cam@example.com>")

    def test_row_without_ids_does_not_break(self):
        db.save_checklist({"subject": "No ids", "threadId": "thread-2"})
        rows = db.list_checklist()
        self.assertEqual(rows[0]["messageId"], "")
        email_link.enrich_row(rows[0])
        self.assertEqual(rows[0]["emailUrl"], "")


if __name__ == "__main__":
    unittest.main()
