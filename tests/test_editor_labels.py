# =============================================================================
# FILE HEADER
# file    : tests/test_editor_labels.py
# role    : Tests — plain-language editor labels (receive / filter / publish)
# owner   : Hisham (human owner) · AI coding sessions may amend under his review
# purpose : prove the editor shows no article / no media, fail 3R / not relevant, and the
#           publish labels, using the live accept threshold convention.
# pages   : n/a
# calls   : editor_data
# called  : developer / CI (python3 -m unittest tests.test_editor_labels -v)
# amend   : pure data tests; no DB, no network.
# =============================================================================
"""Unit tests for the T-047-era editor wording changes."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from msme.receive import editor_data as ed


class FilterLabelTests(unittest.TestCase):
    def test_three_r_gate(self):
        label, reason = ed._filter_state(
            {"filterOutcome": "REJECT", "filterGate": "ROYAL_RESPECT", "filterWeighted": 80},
            {"gate_labels": {"royal_respect": "Royal institution respect"}}, accept=62)
        self.assertEqual(label, "fail 3R")
        self.assertIn("3R", reason)

    def test_low_score_is_not_relevant(self):
        label, reason = ed._filter_state(
            {"filterOutcome": "REJECT", "filterGate": "LOW_WEIGHTED_SCORE", "filterWeighted": 50},
            {}, accept=62)
        self.assertEqual(label, "not relevant")
        self.assertIn("62", reason)

    def test_borderline_below_limit_is_not_relevant(self):
        label, _ = ed._filter_state(
            {"filterOutcome": "EDITOR REVIEW", "filterGate": "BORDERLINE", "filterWeighted": 60},
            {}, accept=62)
        self.assertEqual(label, "not relevant")

    def test_ambiguous_above_limit_needs_review(self):
        label, _ = ed._filter_state(
            {"filterOutcome": "EDITOR REVIEW", "filterGate": "AMBIGUOUS_ROYAL_RESPECT",
             "filterWeighted": 80}, {}, accept=62)
        self.assertEqual(label, "needs review")

    def test_accept_and_error(self):
        self.assertEqual(ed._filter_state({"filterOutcome": "ACCEPT"}, {}, accept=62)[0], "accepted")
        self.assertEqual(ed._filter_state({"filterOutcome": "ERROR"}, {}, accept=62)[0], "check failed")

    def test_readiness_wording(self):
        self.assertEqual(ed._reason_for_readiness({"hasArticle": "false"}, {}), "No article.")
        row = {"hasArticle": "true", "hasPic": "false", "hasLogo": "false", "hasImageInArticle": "false"}
        self.assertEqual(ed._reason_for_readiness(row, {}), "No media.")

    def test_item_has_filter_label(self):
        row = {"id": 1, "threadId": "t1", "subject": "x", "date": "2026-10-28",
               "readyToFilter": "true", "hasArticle": "true", "hasPic": "true",
               "filterOutcome": "EDITOR REVIEW", "filterGate": "BORDERLINE",
               "filterStatus": "", "filterWeighted": 60}
        item = ed._item_for(row, {}, {}, {}, 1, accept=62)
        self.assertEqual(item["filterLabel"], "not relevant")
        self.assertEqual(item["stage"], "filter")


if __name__ == "__main__":
    unittest.main()
