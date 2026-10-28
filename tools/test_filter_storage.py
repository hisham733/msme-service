"""Tests for filter_results storage, checklist linkage and one-port routing."""
import os
import tempfile
import unittest
from unittest.mock import patch

import checklist
import combined
import db
import filter_log


class TestFilterStorage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test.sqlite3")
        self.patch = patch.object(db.config, "SQLITE_PATH", self.db_path)
        self.patch.start()
        self.auto = patch.object(checklist.settings_store, "get", return_value=False)
        self.auto.start()
        db.init_db()

    def tearDown(self):
        self.auto.stop()
        self.patch.stop()
        self.tmp.cleanup()

    def _row(self, **extra):
        row = {
            "subject": "Example release", "threadId": "t1", "date": "2026-10-26",
            "hasArticle": "true", "hasPic": "true", "hasLogo": "false",
            "hasLogoInArticle": "false", "hasImageInArticle": "false",
            "subjectMatch": "true", "subjectScore": "100", "readyToFilter": "true",
            "_runId": "run-1",
            "_filter": {
                "outcome": "ACCEPT", "weighted": 78, "gate": None,
                "confidence": 0.91, "model": "jev-latest",
                "gates": {"royal_respect": 0.01},
                "scores": {"sme_relevance": {"raw": 0.9, "norm": 0.9, "confidence": 0.9}},
                "gate_thresholds": {"royal_respect": 0.85},
                "gate_labels": {"royal_respect": "Royal institution respect"},
                "reasons": [],
            },
        }
        row.update(extra)
        return row

    def test_checklist_id(self):
        cid = db.save_checklist(self._row())
        self.assertIsInstance(cid, int)
        self.assertGreater(cid, 0)

    def test_checklist_save_writes_linked_filter(self):
        checklist.save_checklist(self._row())
        rows = db.list_checklist()
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual(r["filterStatus"], "ok")
        self.assertEqual(r["filterOutcome"], "ACCEPT")
        self.assertEqual(r["filterWeighted"], 78)
        self.assertEqual(r["filterVerdict"]["gate_thresholds"]["royal_respect"], 0.85)

    def test_filter_error_is_linked(self):
        row = self._row(_filter={"outcome": "ERROR", "error": "Jev down"})
        checklist.save_checklist(row)
        r = db.list_checklist()[0]
        self.assertEqual(r["filterStatus"], "error")
        self.assertEqual(r["filterError"], "Jev down")

    def test_no_filter_result_is_allowed(self):
        row = self._row()
        row.pop("_filter")
        checklist.save_checklist(row)
        r = db.list_checklist()[0]
        self.assertIsNone(r["filterStatus"])
        self.assertEqual(r["filterOutcome"], None)


class TestFilterLog(unittest.TestCase):
    def test_receive_source_written(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "verdicts.jsonl")
            with patch.object(filter_log, "VERDICT_LOG", path):
                filter_log.log_verdict({"subject": "S", "_source": "receive"},
                                       {"outcome": "ACCEPT", "weighted": 70}, source="receive")
            with open(path, encoding="utf-8") as f:
                self.assertIn('"source": "receive"', f.read())


class TestCombinedRouting(unittest.TestCase):
    def test_filter_paths(self):
        for p in ("/filter", "/filter.html", "/config.json", "/verdicts", "/lab/ask",
                  "/report/files", "/testfilter/articles", "/logs.html"):
            app, path = combined._target(p)
            self.assertIs(app, combined.filter_service.app, p)
            self.assertEqual(path, p)

    def test_receive_and_legacy_paths(self):
        for p in ("/", "/checklist.html", "/config.html", "/api/run", "/filter-config.html"):
            app, path = combined._target(p)
            self.assertIs(app, combined.dashboard.app, p)
        app, path = combined._target("/run")
        self.assertIs(app, combined.dashboard.app)
        self.assertEqual(path, "/api/run")
        app, path = combined._target("/health")
        self.assertEqual(path, "/api/health")


if __name__ == "__main__":
    unittest.main()
