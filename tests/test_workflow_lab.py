# =============================================================================
# FILE HEADER
# file    : tests/test_workflow_lab.py
# role    : Tests — interactive receive workflow lab
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : prove the lab stages/code map work and that every sandbox run is write-free.
# pages   : n/a
# calls   : workflow_lab, pipeline, config, archive, reply
# called  : developer / CI (python3 -m unittest tests.test_workflow_lab)
# amend   : no network, no live DB/archive writes; temp paths only.
# =============================================================================
"""Unit tests for the Workflow Lab.

Run:
    python3 -m unittest tests.test_workflow_lab -v
"""
import io
import os
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from msme import config
from msme.receive import archive, reply, workflow_lab


def _png(width, height):
    sig = b"\x89PNG\r\n\x1a\n"

    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\x00\x00\x00" * width for _ in range(height))
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def _docx_bytes():
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w") as z:
        z.writestr("word/media/image1.png", _png(520, 300))
        z.writestr("word/media/image2.png", _png(80, 77))
    return bio.getvalue()


class StageMetadataTests(unittest.TestCase):
    def test_all_stages_are_complete(self):
        self.assertEqual(len(workflow_lab.STAGES), 9)
        ids = [s["id"] for s in workflow_lab.STAGES]
        self.assertEqual(ids, ["receive", "normalize", "decide", "fetch",
                               "extract", "media", "verify", "filter", "save"])
        for stage in workflow_lab.STAGES:
            for key in ("title", "type", "summary", "why", "risk", "inputs", "outputs", "code"):
                self.assertTrue(stage.get(key), f"{stage['id']} missing {key}")


class CodeTests(unittest.TestCase):
    def test_code_excerpt_for_normalize(self):
        d = workflow_lab.api_code("normalize")
        self.assertEqual(d["stage"], "normalize")
        self.assertTrue(any("build_email_model" in e.get("code", "") for e in d["excerpts"]))

    def test_unknown_stage_is_rejected(self):
        from fastapi import HTTPException

        with self.assertRaises(HTTPException):
            workflow_lab.api_code("no-such-stage")


class FileMapTests(unittest.TestCase):
    def test_runtime_and_one_off_are_distinguished(self):
        fm = workflow_lab.file_map()
        by_name = {os.path.basename(f["file"]): f for f in fm["files"]}
        self.assertEqual(by_name["pipeline.py"]["status"], "core")
        self.assertTrue(by_name["pipeline.py"]["needed"])
        self.assertEqual(by_name["check_deepseek_key.py"]["status"], "one-off")
        self.assertFalse(by_name["check_deepseek_key.py"]["needed"])
        self.assertIn("pipeline.py", by_name["archive.py"]["imported_by"])
        self.assertEqual(by_name["workflow_lab.py"]["status"], "feature")

    def test_every_file_has_a_purpose(self):
        fm = workflow_lab.file_map()
        self.assertGreater(fm["total"], 30)
        for item in fm["files"]:
            self.assertTrue(item["role"], item["file"])
            self.assertTrue(item["purpose"], item["file"])


class ExampleRunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_sql = config.SQLITE_PATH
        self.old_archive = config.LOCAL_ARCHIVE_DIR
        config.SQLITE_PATH = os.path.join(self.tmp.name, "lab.sqlite3")
        config.LOCAL_ARCHIVE_DIR = os.path.join(self.tmp.name, "archive")
        self.old_archive_fn = archive.archive_email
        self.old_reply_fn = reply.send_reply_for_row

        def _boom(*args, **kwargs):
            raise AssertionError("sandbox must not write")

        archive.archive_email = _boom
        reply.send_reply_for_row = _boom

    def tearDown(self):
        archive.archive_email = self.old_archive_fn
        reply.send_reply_for_row = self.old_reply_fn
        config.SQLITE_PATH = self.old_sql
        config.LOCAL_ARCHIVE_DIR = self.old_archive
        self.tmp.cleanup()

    def test_simple_release_is_not_ready(self):
        run = workflow_lab._run_example("simple_release", lambda *a: None)
        row = run["row"]
        self.assertEqual(row["hasArticle"], "true")
        self.assertEqual(row["hasLogo"], "false")
        self.assertEqual(row["readyToFilter"], "false")
        self.assertTrue(run["simulated"])

    def test_ready_release_is_ready(self):
        run = workflow_lab._run_example("ready_release", lambda *a: None)
        self.assertEqual(run["row"]["hasLogo"], "true")
        self.assertEqual(run["row"]["readyToFilter"], "true")

    def test_no_article(self):
        run = workflow_lab._run_example("no_article", lambda *a: None)
        self.assertEqual(run["row"]["hasArticle"], "false")
        self.assertEqual(run["row"]["readyToFilter"], "false")

    def test_no_db_or_archive_write(self):
        workflow_lab._run_example("ready_release", lambda *a: None)
        self.assertFalse(os.path.exists(config.SQLITE_PATH))
        self.assertFalse(os.path.isdir(config.LOCAL_ARCHIVE_DIR)
                         and os.listdir(config.LOCAL_ARCHIVE_DIR))


class StageRunTests(unittest.TestCase):
    def test_stage_runs(self):
        for stage in ("normalize", "decide", "extract", "verify", "save"):
            out = workflow_lab._run_stage(stage, {}, "sim", lambda *a: None)
            self.assertEqual(out["stage"], stage)
            self.assertIsInstance(out["output"], dict)


class MediaScanTests(unittest.TestCase):
    def test_docx_images_are_classified(self):
        from msme.receive import extract

        info = extract.classify_doc_images(_docx_bytes(), "sample.docx")
        self.assertTrue(info["has_image"])
        self.assertTrue(info["has_logo"])
        self.assertTrue(info["has_photo"])


if __name__ == "__main__":
    unittest.main()
