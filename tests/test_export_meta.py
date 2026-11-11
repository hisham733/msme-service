"""Tests for the N-3/N-4 export handoff: repurpose_export writes meta.json + manifest.

Run: python3 -m unittest tests.test_export_meta -v
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from msme import config, db
from msme.repurpose import repurpose_export


class ExportMetaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.archive = base / "all_emails"
        self.archive.mkdir()
        self.inbox = base / "repurpose_inbox"
        self.manifest = base / "repurpose_export.json"
        self.patches = [
            patch.object(config, "SQLITE_PATH", str(base / "test.sqlite3")),
            patch.object(repurpose_export, "ARCHIVE_ROOT", self.archive),
            patch.object(repurpose_export, "INBOX", self.inbox),
            patch.object(repurpose_export, "MANIFEST", self.manifest),
        ]
        for p in self.patches:
            p.start()
        db.init_db()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def test_export_writes_meta_json_and_manifest(self):
        folder = self.archive / "Meltwater"
        folder.mkdir()
        (folder / "art.md").write_text("release text", encoding="utf-8")
        cid = db.save_checklist({"subject": "Meltwater report",
                                 "articleFile": "art.md", "messageId": "m-x"})
        db.save_filter_result(cid, "run-1", "t-x", {"outcome": "ACCEPT", "weighted": 80})
        db.save_email_link(cid, "m-x", "Meltwater report", {
            "linkType": "report", "url": "https://wearesocial.com/digital-2027",
            "source": "docx_rels"})

        plan = repurpose_export.export(apply=True)
        export = [p for p in plan if p.get("status") == "export"]
        self.assertEqual(len(export), 1)
        self.assertEqual(export[0]["reportUrl"], "https://wearesocial.com/digital-2027")

        dest = Path(export[0]["dest"])
        meta = json.loads((dest / "meta.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["articleType"], "report")
        self.assertEqual(meta["reportUrl"], "https://wearesocial.com/digital-2027")

        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        self.assertEqual(manifest["exported"][0]["reportUrl"],
                         "https://wearesocial.com/digital-2027")

    def test_existing_draft_still_gets_meta_json(self):
        folder = self.archive / "Meltwater 2"
        folder.mkdir()
        (folder / "art.md").write_text("release", encoding="utf-8")
        cid = db.save_checklist({"subject": "Meltwater 2",
                                 "articleFile": "art.md", "messageId": "m-y"})
        db.save_filter_result(cid, "run-2", "t-y", {"outcome": "ACCEPT", "weighted": 80})
        db.save_email_link(cid, "m-y", "Meltwater 2", {
            "linkType": "report", "url": "https://wearesocial.com/digital-2027"})
        # Pre-existing engine work in the destination.
        dest = self.inbox / "Meltwater 2"
        dest.mkdir(parents=True)
        (dest / "draft.md").write_text("old draft", encoding="utf-8")

        plan = repurpose_export.export(apply=True)
        entry = [p for p in plan if p.get("subject") == "Meltwater 2"][0]
        self.assertEqual(entry["status"], "skip")
        meta = json.loads((dest / "meta.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["reportUrl"], "https://wearesocial.com/digital-2027")
        self.assertEqual((dest / "draft.md").read_text(encoding="utf-8"), "old draft")

    def test_export_copies_table_media(self):
        folder = self.archive / "Meltwater 3"
        folder.mkdir()
        (folder / "art.md").write_text("release", encoding="utf-8")
        images = folder / "images"
        images.mkdir()
        logo = images / "xendit.png"
        logo.write_bytes(b"\x89PNG\r\n\x1a\nfake")
        cid = db.save_checklist({"subject": "Meltwater 3",
                                 "articleFile": "art.md", "messageId": "m-z"})
        db.save_filter_result(cid, "run-3", "t-z", {"outcome": "ACCEPT", "weighted": 80})
        db.save_email_media(cid, "m-z", [{"name": "xendit.png", "kind": "logo",
                                          "source": "gallery", "path": str(logo),
                                          "usable": True, "chosen": True}])

        plan = repurpose_export.export(apply=True)
        entry = [p for p in plan if p.get("subject") == "Meltwater 3"][0]
        dest = Path(entry["dest"])
        self.assertTrue((dest / "images" / "xendit.png").is_file())

    def test_skip_branch_adds_table_media(self):
        folder = self.archive / "Meltwater 4"
        folder.mkdir()
        (folder / "art.md").write_text("release", encoding="utf-8")
        images = folder / "images"
        images.mkdir()
        logo = images / "xendit.png"
        logo.write_bytes(b"\x89PNG\r\n\x1a\nfake")
        cid = db.save_checklist({"subject": "Meltwater 4",
                                 "articleFile": "art.md", "messageId": "m-w"})
        db.save_filter_result(cid, "run-4", "t-w", {"outcome": "ACCEPT", "weighted": 80})
        db.save_email_media(cid, "m-w", [{"name": "xendit.png", "kind": "logo",
                                          "source": "gallery", "path": str(logo),
                                          "usable": True, "chosen": True}])
        dest = self.inbox / "Meltwater 4"
        dest.mkdir(parents=True)
        (dest / "draft.md").write_text("old draft", encoding="utf-8")

        plan = repurpose_export.export(apply=True)
        entry = [p for p in plan if p.get("subject") == "Meltwater 4"][0]
        self.assertEqual(entry["status"], "skip")
        self.assertTrue((dest / "images" / "xendit.png").is_file())
        self.assertEqual((dest / "draft.md").read_text(encoding="utf-8"), "old draft")


if __name__ == "__main__":
    unittest.main()
