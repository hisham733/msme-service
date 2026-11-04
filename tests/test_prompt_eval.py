# =============================================================================
# FILE HEADER
# file    : tests/test_prompt_eval.py
# role    : Tests — versioned prompts + archive replay harness
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : prove v0/v1 prompt resolution, archive selection, message rebuilding and the fake
#           Gmail service without calling an AI provider.
# pages   : n/a
# calls   : config, prompt_eval, normalize, gmail
# called  : developer / CI (python3 -m unittest tests.test_prompt_eval)
# amend   : no network, no live DB/archive writes; temp paths only.
# =============================================================================
"""Unit tests for the prompt A/B harness.

Run:
    python3 -m unittest tests.test_prompt_eval -v
"""
import base64
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import prompt_eval

from msme import config
from msme.receive import gmail, normalize


class PromptVersionTests(unittest.TestCase):
    def test_v1_is_used_when_requested(self):
        base = config.load_prompt("extract_prompt.txt", version="")
        v1 = config.load_prompt("extract_prompt.txt", version="v1")
        self.assertNotEqual(base, v1)
        self.assertIn("chosenCandidate", v1)
        self.assertNotIn("HERE IS THE RAW EMAIL:", v1)

    def test_unknown_version_falls_back_to_base(self):
        base = config.load_prompt("decide_prompt.txt", version="")
        missing = config.load_prompt("decide_prompt.txt", version="v999")
        self.assertEqual(base, missing)

    def test_all_v1_packs_exist(self):
        for name in ("decide_prompt.txt", "extract_prompt.txt", "verify_prompt.txt"):
            self.assertTrue(os.path.exists(os.path.join(config.PROMPT_DIR, name.replace(".txt", ".v1.txt"))))


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.archive = self.root / "all_emails" / "received-2026-10-15-and-above"
        self.folder = self.archive / "Acme Robotics Hub"
        (self.folder / "originals").mkdir(parents=True)
        (self.folder / "images").mkdir()
        self.article = "FOR IMMEDIATE RELEASE\n\nAcme Robotics Opens a Hub\n\nPENANG, 20 Oct 2026 - Acme opened a hub."
        (self.folder / "article.md").write_text(self.article, encoding="utf-8")
        (self.folder / "originals" / "release.docx").write_bytes(b"PK\x03\x04fake-docx")
        (self.folder / "images" / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")
        self.db = self.root / "test.sqlite3"
        con = sqlite3.connect(self.db)
        con.execute("""CREATE TABLE checklist (
            id INTEGER PRIMARY KEY, subject TEXT, threadId TEXT, date TEXT, folderId TEXT,
            folderUrl TEXT, articleFile TEXT, hasArticle TEXT, hasPic TEXT, hasLogo TEXT,
            hasLogoInArticle TEXT, hasImageInArticle TEXT, subjectMatch TEXT,
            subjectScore TEXT, readyToFilter TEXT)""")
        con.execute("""INSERT INTO checklist
            (subject, articleFile, hasArticle, hasPic, hasLogo, hasLogoInArticle, hasImageInArticle,
             subjectMatch, subjectScore, readyToFilter, date)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            ("Fwd: [PRESS RELEASE] Acme Robotics Opens a Hub", "article.md", "true", "false",
             "true", "false", "false", "true", "88", "true", "2026-10-20"))
        con.commit()
        con.close()

    def tearDown(self):
        self.tmp.cleanup()

    def test_select_cases(self):
        cases = prompt_eval.select_cases(limit=2, db_path=str(self.db),
                                        archive_root=str(self.root / "all_emails"))
        self.assertEqual(len(cases), 1)
        case = cases[0]
        self.assertEqual(case["subject"], "Fwd: [PRESS RELEASE] Acme Robotics Opens a Hub")
        self.assertTrue(case["ready"])
        self.assertEqual(case["originals"], ["release.docx"])
        self.assertEqual(case["images"], ["logo.png"])

    def test_build_message_and_fake_service(self):
        cases = prompt_eval.select_cases(limit=1, db_path=str(self.db),
                                        archive_root=str(self.root / "all_emails"))
        message, blobs, article, has_docs = prompt_eval.build_message(cases[0])
        self.assertTrue(has_docs)
        self.assertEqual(article, self.article)
        raw = message["payload"]["parts"][0]["body"]["data"]
        body = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4)).decode("utf-8")
        self.assertIn("Please find the attached release", body)
        self.assertEqual(len(blobs), 2)  # release.docx + logo.png
        service = prompt_eval.FakeGmail(message, blobs)
        model = normalize.build_email_model(service, message["id"])
        self.assertIn("Acme Robotics", model["subject"])
        self.assertEqual(len(model["attachments"]), 2)
        first = next(iter(blobs))
        self.assertEqual(gmail.download_attachment(service, message["id"], first), blobs[first])

    def test_jaccard(self):
        self.assertEqual(prompt_eval._jaccard("a b c", "a b c"), 1.0)
        self.assertEqual(prompt_eval._jaccard("a b", "c d"), 0.0)
        self.assertGreater(prompt_eval._jaccard("a b c", "a b d"), 0.4)


if __name__ == "__main__":
    unittest.main()
