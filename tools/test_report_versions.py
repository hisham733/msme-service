# =============================================================================
# FILE HEADER
# file    : tools/test_report_versions.py
# role    : Tests — archive version grouping + received-date parsing
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : unit-test the report's one-version-per-group rule without touching the
#           live archive or calling Jev.
# pages   : n/a
# calls   : archive_layout
# called  : developer / CI (python3 -m unittest tools.test_report_versions)
# amend   : no network, no writes outside a temp dir.
# =============================================================================
"""Unit tests for archive_layout (report input + versions).

Run:
    python3 -m unittest tools.test_report_versions -v
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import archive_layout as AL


def _make(path, article="body", mtime=None):
    os.makedirs(path, exist_ok=True)
    if article is not None:
        with open(os.path.join(path, "article.md"), "w", encoding="utf-8") as f:
            f.write(article)
    if mtime is not None:
        os.utime(path, (mtime, mtime))


class VersionNameTests(unittest.TestCase):
    def test_suffixes_are_stripped(self):
        self.assertEqual(AL.version_base("ACCA Five Priorities"), "ACCA Five Priorities")
        self.assertEqual(AL.version_base("ACCA Five Priorities_1"), "ACCA Five Priorities")
        self.assertEqual(AL.version_base("i-City Press Release _4"), "i-City Press Release")
        self.assertEqual(AL.version_base("Name_12"), "Name")


class DateTests(unittest.TestCase):
    def test_iso_and_rfc(self):
        self.assertEqual(AL.parse_date("2026-10-16"), "2026-10-16")
        self.assertEqual(AL.parse_date("Thu, 22 Oct 2026 16:48:08 +0800"), "2026-10-22")

    def test_truncated_month(self):
        self.assertEqual(AL.parse_date("Fri, 16 Oc"), "2026-10-16")
        self.assertEqual(AL.parse_date("Tue, 22 Se"), "2026-09-22")
        self.assertEqual(AL.parse_date("Mon, 5 Oct"), "2026-10-05")

    def test_invalid(self):
        self.assertEqual(AL.parse_date(""), "")
        self.assertEqual(AL.parse_date("nonsense"), "")


class GroupingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def test_flat_and_bucket_layouts_are_both_read(self):
        _make(os.path.join(self.root, "Flat article"), mtime=100)
        _make(os.path.join(self.root, "bucket", "Bucketed article"), mtime=200)
        rels = [i["rel"] for i in AL.iter_article_dirs(self.root)]
        self.assertIn("Flat article", rels)
        self.assertIn("bucket/Bucketed article", rels)

    def test_skip_folders_are_ignored(self):
        _make(os.path.join(self.root, "_duplicates", "Old", "article"))
        _make(os.path.join(self.root, "_no_article", "Empty"))
        _make(os.path.join(self.root, "Keep me"), mtime=100)
        rels = [i["rel"] for i in AL.iter_article_dirs(self.root)]
        self.assertEqual(rels, ["Keep me"])

    def test_newest_complete_version_wins(self):
        _make(os.path.join(self.root, "Story"), "old", mtime=100)
        _make(os.path.join(self.root, "Story_1"), None, mtime=300)
        _make(os.path.join(self.root, "Story_2"), "newer", mtime=200)
        groups = AL.group_versions(self.root)
        pick = AL.choose_version(groups["Story"])
        self.assertEqual(pick["name"], "Story_2")

    def test_keepmap_overrides_newest(self):
        _make(os.path.join(self.root, "Story"), "old", mtime=100)
        _make(os.path.join(self.root, "Story_1"), "new", mtime=200)
        groups = AL.group_versions(self.root)
        pick = AL.choose_version(groups["Story"], keep={"Story": "Story"})
        self.assertEqual(pick["name"], "Story")

    def test_empty_group_has_no_pick(self):
        _make(os.path.join(self.root, "Empty"), None, mtime=100)
        groups = AL.group_versions(self.root)
        self.assertIsNone(AL.choose_version(groups.get("Empty", [])))


class ReceivedDateTests(unittest.TestCase):
    def test_exact_and_fuzzy_lookup(self):
        dmap = {
            AL.norm_subject("Fwd: [PRESS RELEASE] Company Launches Product"): ("2026-10-16", "sqlite"),
        }
        date, source = AL.received_date("Company Launches Product", "Company-Launches.md", dmap)
        self.assertEqual(date, "2026-10-16")
        self.assertEqual(source, "sqlite")


class FolderFilterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        _make(os.path.join(self.root, "received-15-and-above", "A"), mtime=100)
        _make(os.path.join(self.root, "received-15-and-above", "B"), mtime=100)
        _make(os.path.join(self.root, "received-14-and-below", "C"), mtime=100)
        _make(os.path.join(self.root, "flat"), mtime=100)

    def tearDown(self):
        self.tmp.cleanup()

    def test_filter_by_folder(self):
        items = AL.iter_article_dirs(self.root)
        above = AL.filter_by_folder(items, "received-15-and-above")
        below = AL.filter_by_folder(items, "received-14-and-below")
        self.assertEqual(len(above), 2)
        self.assertEqual(len(below), 1)
        self.assertEqual(len(AL.filter_by_folder(items, "")), 4)

    def test_top_folders_counts(self):
        found = {f["name"]: f["count"] for f in AL.top_folders(self.root)}
        self.assertEqual(found["received-15-and-above"], 2)
        self.assertEqual(found["received-14-and-below"], 1)
        self.assertNotIn("", found)


if __name__ == "__main__":
    unittest.main()
