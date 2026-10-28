"""D29 tests: the checklist is written to SQLite only (no Google Sheet path).

Run: python3 -m unittest tools.test_checklist_sqlite -v
"""
import unittest
from unittest.mock import patch

import checklist
import repurpose_export


class TestChecklistSqlite(unittest.TestCase):
    def test_save_only_calls_sqlite(self):
        row = {"subject": "Example", "threadId": "abc", "hasArticle": "true"}
        with patch.object(checklist.db, "save_checklist") as save:
            checklist.save_checklist(row)
        save.assert_called_once_with(row)

    def test_no_sheet_writer_remains(self):
        self.assertFalse(hasattr(checklist, "append_to_sheet"))
        self.assertFalse(hasattr(checklist, "creds"))
        self.assertFalse(hasattr(checklist, "config"))

    def test_accept_triggers_repurpose_export(self):
        row = {"subject": "Accepted", "threadId": "t", "hasArticle": "true",
               "_filter": {"outcome": "ACCEPT"}}
        with patch.object(checklist.db, "save_checklist", return_value=11), \
             patch.object(checklist.db, "save_filter_result"), \
             patch.object(checklist.settings_store, "get", return_value=True), \
             patch.object(repurpose_export, "export") as exp:
            checklist.save_checklist(row)
        exp.assert_called_once_with(apply=True)

    def test_reject_does_not_trigger_repurpose(self):
        row = {"subject": "Rejected", "threadId": "t", "_filter": {"outcome": "REJECT"}}
        with patch.object(checklist.db, "save_checklist", return_value=12), \
             patch.object(checklist.db, "save_filter_result"), \
             patch.object(checklist.settings_store, "get", return_value=True), \
             patch.object(repurpose_export, "export") as exp:
            checklist.save_checklist(row)
        exp.assert_not_called()

    def test_build_row_order(self):
        row = {"hasArticle": "true", "subject": "Example"}
        built = checklist.build_row(row)
        self.assertEqual(len(built), len(checklist.COLUMNS))
        self.assertEqual(built[0], "Example")
        self.assertEqual(built[checklist.COLUMNS.index("hasArticle")], "true")


if __name__ == "__main__":
    unittest.main()
