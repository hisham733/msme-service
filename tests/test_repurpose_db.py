"""Tests for the repurpose tables added by T-050/D40 (one DB)."""
import os
import tempfile
import unittest
from unittest.mock import patch

from msme import config, db


class RepurposeDbTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "msme.sqlite3")
        self.patch = patch.object(config, "SQLITE_PATH", self.db_path)
        self.patch.start()
        db.init_db()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_export_is_upserted_by_checklist_id(self):
        db.save_repurpose_export(11, 101, folder="A", dest="/inbox/A",
                                 article_hash="h1", config_hash="c1", weighted=80)
        db.save_repurpose_export(11, 102, folder="A2", dest="/inbox/A2",
                                 article_hash="h2", config_hash="c2", weighted=81)
        rows = db.list_repurpose_exports()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["filter_result_id"], 102)
        self.assertEqual(rows[0]["folder"], "A2")
        self.assertEqual(db.get_repurpose_export(11)["weighted"], 81)

    def test_run_upsert_keeps_one_row_per_folder(self):
        db.upsert_repurpose_run("A", status="drafting", model="deepseek-flash")
        db.upsert_repurpose_run("A", status="validated", run_json='{"ok": true}',
                                draft_path="A/draft.md")
        rows = db.list_repurpose_runs()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "validated")
        self.assertEqual(rows[0]["model"], "deepseek-flash")
        self.assertIn("ok", rows[0]["run_json"])

    def test_events_are_append_only_and_filterable(self):
        db.add_repurpose_event("A", "draft", "done", "1.2k chars")
        db.add_repurpose_event("B", "draft", "error", "no key")
        self.assertEqual(len(db.list_repurpose_events()), 2)
        a = db.list_repurpose_events("A")
        self.assertEqual(len(a), 1)
        self.assertEqual(a[0]["stage"], "draft")
        self.assertEqual(a[0]["detail"], "1.2k chars")


if __name__ == "__main__":
    unittest.main()
