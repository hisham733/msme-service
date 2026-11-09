"""Tests for the cost estimator and the /api/costs.json shape.

Run: python3 -m unittest tests.test_cost -v
"""
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from msme import cost, db, settings_store


class CostTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patches = [
            patch.object(db.config, "SQLITE_PATH", os.path.join(self.tmp.name, "cost.sqlite3")),
            patch.object(settings_store, "SETTINGS_PATH", os.path.join(self.tmp.name, "settings.json")),
        ]
        for p in self.patches:
            p.start()
        db.init_db()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def _receive(self, email_id, run_id, total, model="deepseek/deepseek-flash", when="2026-11-01T10:00:00+00:00"):
        db.save_pipeline_result(
            run_id, email_id, "S " + email_id,
            {"tokens": {"detail": {"prompt": total * 2 // 3, "completion": total // 3,
                                   "total": total, "model": model}}},
            {"subject": "S " + email_id}, "success",
        )
        # save_pipeline_result does not carry created_at; patch it for the latest-run tests.
        c = db._connect()
        c.execute("update pipeline_results set created_at=? where run_id=?", (when, run_id))
        c.commit(); c.close()

    def _checklist(self, message_id, subject="S"):
        return db.save_checklist({"subject": subject, "threadId": "t", "messageId": message_id,
                                  "readyToFilter": "true"})

    def _filter(self, checklist_id, message_id, outcome="ACCEPT", inp=2000, out=200,
                model="jev-1.14.0", when="2026-11-01T10:05:00+00:00"):
        db.save_filter_result(checklist_id, "r-" + message_id, message_id, {
            "outcome": outcome, "weighted": 80, "gate": None, "confidence": 0.5,
            "gates": {}, "scores": {}, "usage": {"input_tokens": inp, "output_tokens": out},
            "model": model,
        })
        c = db._connect()
        c.execute("update filter_results set created_at=? where checklist_id=?", (when, checklist_id))
        c.commit(); c.close()

    def test_rates_default_to_the_measured_values(self):
        p = cost.prices()
        self.assertAlmostEqual(p["deepseek_per_m"], 0.65)
        self.assertAlmostEqual(p["jev_input_per_m"], 0.042)
        self.assertEqual(p["currency"], "USD")

    def test_receive_and_filter_math(self):
        # 1M total DeepSeek tokens at $0.65/M = $0.65
        self.assertAlmostEqual(cost.receive_cost({"total": 1_000_000}), 0.65, places=6)
        # 1M Jev input at $0.042/M = $0.042 (output free)
        self.assertAlmostEqual(cost.filter_cost({"input_tokens": 1_000_000, "output_tokens": 999999},
                                                "jev-1.14.0"), 0.042, places=6)

    def test_chain_uses_the_latest_run_per_email(self):
        self._receive("m1", "r1", 1000, when="2026-11-01T10:00:00+00:00")
        self._receive("m1", "r2", 3000, when="2026-11-02T10:00:00+00:00")
        cid = self._checklist("m1")
        self._filter(cid, "m1")
        rows = cost.build_rows(db.cost_receive_rows(), db.cost_filter_rows(), db.cost_repurpose_rows())
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]["receive_cost"], 3000 / 1_000_000 * 0.65, places=6)

    def test_all_runs_spend_includes_retries(self):
        self._receive("m1", "r1", 1000, when="2026-11-01T10:00:00+00:00")
        self._receive("m1", "r2", 3000, when="2026-11-02T10:00:00+00:00")
        s = cost.build_summary(db.cost_receive_rows(), db.cost_filter_rows(), db.cost_repurpose_rows())
        self.assertAlmostEqual(s["chain"]["receive"], 3000 / 1_000_000 * 0.65, places=6)
        self.assertAlmostEqual(s["all_runs"]["receive"], 4000 / 1_000_000 * 0.65, places=6)

    def test_repurpose_usage_and_published(self):
        self._checklist("m1")
        db.upsert_repurpose_run(
            "folder-1", checklist_id=1, status="validated", model="deepseek-flash",
            finished_at="2026-11-03T10:00:00+00:00",
            usage_json=json.dumps({"prompt": 1000, "completion": 1000, "total": 2000}),
        )
        rows = cost.build_rows([], [], db.cost_repurpose_rows())
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["published"])
        self.assertTrue(rows[0]["repurpose_priced"])
        self.assertAlmostEqual(rows[0]["repurpose_cost"], 2000 / 1_000_000 * 0.65, places=6)

    def test_budget_and_emails_left(self):
        settings_store.save({"COST_BUDGET_USD": 1.0})
        self._receive("m1", "r1", 1_000_000)  # $0.65
        s = cost.build_summary(db.cost_receive_rows(), [], [])
        self.assertAlmostEqual(s["budget"]["remaining"], 0.35, places=6)
        self.assertEqual(s["budget"]["emails_left"], 0)

    def test_empty_db(self):
        s = cost.build_summary([], [], [])
        self.assertEqual(s["all_runs"]["total"], 0)
        self.assertEqual(s["emails"], 0)
        self.assertEqual(len(s["daily"]), 14)

    def test_dashboard_endpoint_shape(self):
        from msme.receive import dashboard
        self._receive("m1", "r1", 1500)
        body = dashboard.api_costs()
        self.assertIn("summary", body)
        self.assertIn("rows", body)
        self.assertIn("pricing", body)
        self.assertEqual(body["rows"][0]["email_id"], "m1")
        self.assertIn("emailUrl", body["rows"][0])
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["page_size"], 20)

    def test_pagination_returns_only_20_rows(self):
        from msme.receive import dashboard
        for i in range(25):
            self._receive("m%02d" % i, "r%02d" % i, 1000 + i)
        first = dashboard.api_costs(page=1, page_size=20)
        self.assertEqual(len(first["rows"]), 20)
        self.assertEqual(first["total"], 25)
        self.assertEqual(first["pages"], 2)
        second = dashboard.api_costs(page=2, page_size=20)
        self.assertEqual(len(second["rows"]), 5)
        self.assertEqual(second["page"], 2)
        ids = {r["email_id"] for r in first["rows"]} | {r["email_id"] for r in second["rows"]}
        self.assertEqual(len(ids), 25, "pages must not overlap and must cover every email")

    def test_pagination_search_is_server_side(self):
        from msme.receive import dashboard
        for i in range(5):
            self._receive("m%02d" % i, "r%02d" % i, 1000)
        body = dashboard.api_costs(page=1, page_size=20, q="m03")
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["rows"][0]["email_id"], "m03")


if __name__ == "__main__":
    unittest.main()
