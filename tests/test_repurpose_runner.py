"""Tests for the in-process repurpose runner (T-050 / D40)."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from msme import config, db, paths
from msme.repurpose import runner
from msme.repurpose.engine import manifest


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.inbox = root / "inbox"
        self.site = root / "site"
        self.inbox.mkdir()
        self.site.mkdir()
        folder = self.inbox / "A"
        folder.mkdir()
        (folder / "release.md").write_text(
            "Acme launched Widget Pro on 16 October 2026. " * 8, encoding="utf-8")
        (folder / "images").mkdir()
        self.patches = [
            patch.object(config, "SQLITE_PATH", str(root / "db.sqlite3")),
            patch.object(paths, "REPURPOSE_INBOX", self.inbox),
            patch.object(paths, "REPURPOSE_SITE", self.site),
        ]
        for p in self.patches:
            p.start()
        db.init_db()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def test_run_folder_mirrors_run_json_and_events(self):
        def fake_run_one(cfg, item, call=None):
            manifest.write(item["path"], status="validated", validator={"ok": True})
            return {"ok": True, "results": []}, "validated"

        with patch("msme.repurpose.engine.run.run_one", side_effect=fake_run_one):
            out = runner.run_folder("A")

        self.assertEqual(out["status"], "validated")
        run = db.get_repurpose_run("A")
        self.assertEqual(run["status"], "validated")
        self.assertIn("validated", run["run_json"])
        events = db.list_repurpose_events("A")
        self.assertTrue(any(e["stage"] == "run" and e["status"] == "started" for e in events))
        self.assertTrue(any(e["stage"] == "run" and e["status"] == "validated" for e in events))

    def test_pending_folder_is_the_one_without_a_draft(self):
        self.assertEqual([i["folder"] for i in runner.pending_folders()], ["A"])
        (self.inbox / "A" / "draft.md").write_text("## Title\n\nDraft.\n", encoding="utf-8")
        self.assertEqual(runner.pending_folders(), [])


if __name__ == "__main__":
    unittest.main()
