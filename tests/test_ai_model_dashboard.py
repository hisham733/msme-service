"""Tests for the AI Model page data (Receive + Jev tabs).

Run: python3 -m unittest tests.test_ai_model_dashboard -v
"""
import os
import tempfile
import unittest
from unittest.mock import patch

from msme import db


class AIModelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patch_db = patch.object(db.config, "SQLITE_PATH",
                                     os.path.join(self.tmp.name, "ai-model.sqlite3"))
        self.patch_db.start()
        db.init_db()

    def tearDown(self):
        self.patch_db.stop()
        self.tmp.cleanup()

    def _run(self, email_id, model="deepseek/deepseek-flash", status="success", subject=None):
        run_id = db.log_run_start(email_id, subject or ("S " + email_id), model=model)
        db.log_run_end(run_id, status, model=model)
        return run_id

    def _email(self, mid, sender="a@example.com", name="Alice"):
        db.save_email({"messageId": mid, "fromEmail": sender, "fromName": name,
                       "subject": "S " + mid}, received_at="2026-11-01T10:00:00+00:00")

    def _checklist(self, mid, ready="true"):
        return db.save_checklist({"subject": "S " + mid, "threadId": "t",
                                  "messageId": mid, "readyToFilter": ready})

    def _filter(self, cid, mid, outcome="ACCEPT", weighted=80, gate=None):
        db.save_filter_result(cid, "r-" + mid, mid, {
            "outcome": outcome, "weighted": weighted, "gate": gate, "confidence": 0.5,
            "gates": {}, "scores": {}, "usage": {"input_tokens": 1000, "output_tokens": 100},
            "model": "jev-1.14.0",
        })

    def test_receive_latest_run_and_run_count(self):
        self._run("m1")
        self._run("m1", status="error")
        rows = db.model_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["email_id"], "m1")
        self.assertEqual(rows[0]["run_count"], 2)
        self.assertEqual(rows[0]["status"], "error")

    def test_sender_fills_from_emails(self):
        self._run("m1")
        self._email("m1", "b@example.com", "Bob")
        row = db.model_rows()[0]
        self.assertEqual(row["from_email"], "b@example.com")
        self.assertEqual(row["from_name"], "Bob")

    def test_ready_comes_from_the_latest_checklist_row(self):
        self._run("m1")
        self._checklist("m1", "false")
        self._checklist("m1", "true")
        self.assertEqual(db.model_rows()[0]["readyToFilter"], "true")

    def test_model_summary_counts(self):
        self._run("m1")
        self._run("m2")
        self._run("m2")
        summary = {s["model"]: s for s in db.model_summary()}
        self.assertEqual(summary["deepseek/deepseek-flash"]["emails"], 2)
        self.assertEqual(summary["deepseek/deepseek-flash"]["runs"], 3)

    def test_jev_latest_verdict_and_summary(self):
        cid1 = self._checklist("m1")
        cid2 = self._checklist("m2")
        self._filter(cid1, "m1", "ACCEPT", 80)
        self._filter(cid1, "m1", "REJECT", 20)
        self._filter(cid2, "m2", "EDITOR REVIEW", 60, "BORDERLINE")
        rows = {r["messageId"]: r for r in db.jev_rows()}
        self.assertEqual(rows["m1"]["outcome"], "REJECT", "the latest verdict wins")
        self.assertEqual(rows["m2"]["gate"], "BORDERLINE")
        summary = {s["outcome"]: s["n"] for s in db.jev_summary()}
        self.assertEqual(summary["REJECT"], 1)
        self.assertEqual(summary["EDITOR REVIEW"], 1)
        self.assertNotIn("ACCEPT", summary)

    def test_api_shapes(self):
        from msme.receive import dashboard
        self._run("m1")
        self._checklist("m1")
        body = dashboard.api_models("receive")
        self.assertEqual(body["stage"], "receive")
        self.assertEqual(body["rows"][0]["email_id"], "m1")
        self.assertIn("emailUrl", body["rows"][0])
        jev = dashboard.api_models("jev")
        self.assertEqual(jev["stage"], "jev")
        self.assertEqual(jev["rows"], [])

    def test_empty(self):
        self.assertEqual(db.model_rows(), [])
        self.assertEqual(db.model_summary(), [])
        self.assertEqual(db.jev_rows(), [])
        self.assertEqual(db.jev_summary(), [])


if __name__ == "__main__":
    unittest.main()
