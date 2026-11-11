"""Tests for the partner-handoff P0-1 schema, article timeline, and the repurpose backfill.

Run: python3 -m unittest tests.test_partner_p0 -v
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from msme import config, db
from tools import backfill_repurpose


class P0SchemaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "p0.sqlite3")
        self.patch = patch.object(config, "SQLITE_PATH", self.path)
        self.patch.start()
        db.init_db()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def _tables(self):
        c = db._connect()
        try:
            return {r[0] for r in c.execute("select name from sqlite_master where type='table'")}
        finally:
            c.close()

    def test_p0_tables_and_columns(self):
        tables = self._tables()
        for t in ("stage_runs", "article_events", "validation_results", "images"):
            self.assertIn(t, tables)
        c = db._connect()
        try:
            self.assertIn("article_hash", [r[1] for r in c.execute("pragma table_info(checklist)")])
            self.assertIn("article_id", [r[1] for r in c.execute("pragma table_info(repurpose_runs)")])
            self.assertIn("article_id", [r[1] for r in c.execute("pragma table_info(repurpose_events)")])
            self.assertEqual(c.execute("pragma busy_timeout").fetchone()[0], 5000)
        finally:
            c.close()

    def test_article_timeline_join(self):
        cid = db.save_checklist({"subject": "S", "messageId": "m1", "readyToFilter": "true"})
        db.save_filter_result(cid, "run-1", "t1", {"outcome": "ACCEPT", "weighted": 80,
                                                   "article_hash": "abc123"})
        db.upsert_repurpose_run("F1", checklist_id=cid, status="validated", model="deepseek-flash",
                                article_id=str(cid))
        db.add_stage_run("stage-1", cid, "repurpose", service="engine", status="done")
        db.add_article_event(cid, "repurpose", "validated", reason_code="OK")
        db.add_validation_results(cid, "F1", [{"code": "TITLE_PRESENT", "level": "fail", "ok": True}])
        tl = db.article_timeline(cid)
        self.assertIsNotNone(tl)
        self.assertEqual(tl["checklist"]["id"], cid)
        self.assertEqual(tl["filter"]["outcome"], "ACCEPT")
        self.assertEqual(tl["repurpose"]["status"], "validated")
        self.assertEqual(tl["validation"][0]["rule_code"], "TITLE_PRESENT")
        self.assertEqual(tl["events"][0]["stage"], "repurpose")


class BackfillTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.inbox = base / "repurpose_inbox"
        self.inbox.mkdir()
        self.manifest = base / "repurpose_export.json"
        self.patches = [
            patch.object(config, "SQLITE_PATH", str(base / "p0.sqlite3")),
            patch.object(backfill_repurpose, "INBOX", str(self.inbox)),
            patch.object(backfill_repurpose, "MANIFEST", str(self.manifest)),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def _folder(self, name, run):
        d = self.inbox / name
        d.mkdir()
        (d / "run.json").write_text(json.dumps(run), encoding="utf-8")
        return d

    def test_backfill_is_idempotent(self):
        folder = self._folder("F1", {
            "status": "validated", "model": "deepseek-flash",
            "usage": {"prompt": 10, "completion": 20, "total": 30, "calls": 1},
            "updated": "2026-11-07T00:00:00+00:00",
            "validator": {"ok": True, "results": [
                {"code": "TITLE_PRESENT", "level": "fail", "ok": True, "detail": "x"},
                {"code": "FEATURED_EXISTS", "level": "fail", "ok": True, "detail": "y"},
            ]},
            "image_file": "logo.png", "image_rung": "logo",
        })
        self.manifest.write_text(json.dumps({"exported": [
            {"checklist_id": 7, "filter_result_id": 9, "folder": "F1", "dest": str(folder),
             "article_hash": "abc", "config_hash": "c1", "weighted": 80, "status": "exported"},
        ]}), encoding="utf-8")

        backfill_repurpose.backfill(apply=True)
        backfill_repurpose.backfill(apply=True)  # idempotent

        exp = db.get_repurpose_export(7)
        self.assertIsNotNone(exp)
        self.assertEqual(exp["folder"], "F1")
        run = db.get_repurpose_run("F1")
        self.assertEqual(run["status"], "validated")
        self.assertEqual(run["article_id"], "7")
        c = db._connect()
        try:
            vals = c.execute("select count(*) from validation_results where article_id='7'").fetchone()[0]
            self.assertEqual(vals, 2)             # no duplicates on the second run
            self.assertEqual(c.execute("select count(*) from images").fetchone()[0], 1)
            self.assertEqual(c.execute("select count(*) from repurpose_events").fetchone()[0], 1)
        finally:
            c.close()


if __name__ == "__main__":
    unittest.main()
