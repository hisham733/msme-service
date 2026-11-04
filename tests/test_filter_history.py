"""Tests for per-result rubric snapshots and filter history."""
import os
import tempfile
import unittest
from unittest.mock import patch

from msme import db
from msme.filtering import filter as filter_judge


class TestFilterHistoryStorage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "history.sqlite3")
        self.patch = patch.object(db.config, "SQLITE_PATH", self.db_path)
        self.patch.start()
        db.init_db()
        self.cid = db.save_checklist({
            "subject": "History article", "threadId": "t-history",
            "date": "2026-10-26", "articleFile": "history.md",
            "hasArticle": "true", "hasPic": "true", "readyToFilter": "true",
        })

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def _result(self, outcome="ACCEPT", weighted=80, cfg="aaa111"):
        return {
            "outcome": outcome, "weighted": weighted, "gate": None,
            "confidence": 0.9, "model": "jev-test",
            "gates": {"royal_respect": 0.01},
            "scores": {"sme_relevance": {"norm": 0.9}},
            "battery": {"gates": {"royal_respect": {"threshold": 0.1}}, "scores": {}},
            "config_hash": cfg, "article_hash": "art123",
            "article_text": "Stored article text", "article_len": 19,
        }

    def test_snapshot_and_history_roundtrip(self):
        rid = db.save_filter_result(self.cid, "run-1", "t-history", self._result())
        versions = db.list_filter_history(checklist_id=self.cid)
        self.assertEqual(len(versions), 1)
        v = versions[0]
        self.assertEqual(v["id"], rid)
        self.assertEqual(v["config_hash"], "aaa111")
        self.assertEqual(v["battery"]["gates"]["royal_respect"]["threshold"], 0.1)
        self.assertEqual(v["article_text"], "Stored article text")
        self.assertEqual(v["subject"], "History article")

    def test_two_versions_newest_first(self):
        db.save_filter_result(self.cid, "run-1", "t-history", self._result(cfg="old111"))
        db.save_filter_result(self.cid, "run-1", "t-history", self._result("REJECT", 50, "new222"))
        versions = db.list_filter_history(checklist_id=self.cid)
        self.assertEqual([v["config_hash"] for v in versions], ["new222", "old111"])
        self.assertEqual(versions[0]["outcome"], "REJECT")

    def test_versions_are_scoped_to_one_email_row(self):
        cid2 = db.save_checklist({
            "subject": "Second email in same thread", "threadId": "t-history",
            "date": "2026-10-27", "articleFile": "second.md",
        })
        db.save_filter_result(self.cid, "run-1", "t-history", self._result(cfg="one111"))
        db.save_filter_result(cid2, "run-2", "t-history", self._result(cfg="two222"))
        self.assertEqual(len(db.list_filter_history(checklist_id=self.cid)), 1)
        self.assertEqual(len(db.list_filter_history(checklist_id=cid2)), 1)

    def test_legacy_rows_have_no_snapshot(self):
        db.save_filter_result(self.cid, "run-1", "t-history", {"outcome": "ACCEPT", "weighted": 70})
        v = db.list_filter_history(checklist_id=self.cid)[0]
        self.assertEqual(v["battery"], {})
        self.assertEqual(v["article_text"], "")


class TestBatterySnapshot(unittest.TestCase):
    def test_snapshot_has_gates_scores_and_hash(self):
        snap, h = filter_judge.battery_snapshot()
        self.assertEqual(len(snap["gates"]), 3)
        self.assertEqual(len(snap["scores"]), 11)
        self.assertIn("accept_threshold", snap)
        self.assertEqual(len(h), 12)

    def test_hash_changes_with_weight(self):
        base = {"gates": {}, "scores": {"x": {"weight": 10}}, "accept_threshold": 60,
                "llm_assist": False, "jev_model": "jev"}
        h1 = filter_judge._config_hash(base)
        changed = {"gates": {}, "scores": {"x": {"weight": 11}}, "accept_threshold": 60,
                   "llm_assist": False, "jev_model": "jev"}
        self.assertNotEqual(h1, filter_judge._config_hash(changed))


if __name__ == "__main__":
    unittest.main()
