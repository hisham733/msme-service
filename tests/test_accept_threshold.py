"""Tests for the live ACCEPT threshold (D33)."""
import unittest
from unittest.mock import patch

from msme import settings_store
from msme.filtering import filter as filter_judge


class TestAcceptThreshold(unittest.TestCase):
    def test_saved_value_used(self):
        with patch.object(filter_judge.settings_store, "get", return_value=72):
            self.assertEqual(filter_judge.accept_threshold(), 72.0)

    def test_fallback_and_clamp(self):
        with patch.object(filter_judge.settings_store, "get", return_value=None), \
             patch.object(filter_judge.config, "ACCEPT_THRESHOLD", 60):
            self.assertEqual(filter_judge.accept_threshold(), 60.0)
        with patch.object(filter_judge.settings_store, "get", return_value=150):
            self.assertEqual(filter_judge.accept_threshold(), 100.0)
        with patch.object(filter_judge.settings_store, "get", return_value=-5):
            self.assertEqual(filter_judge.accept_threshold(), 0.0)

    def test_setting_field_exists(self):
        self.assertIn("ACCEPT_THRESHOLD", [k for k, _, _ in settings_store.FIELDS])

    def test_decide_uses_live_cutoff(self):
        answers = {"x": {"noul": 0.75}}
        with patch.object(filter_judge, "gates", return_value={}), \
             patch.object(filter_judge, "scores", return_value={"x": {"weight": 100}}), \
             patch.object(filter_judge, "accept_threshold", return_value=70):
            self.assertEqual(filter_judge.decide(answers)[0], "ACCEPT")
        with patch.object(filter_judge, "gates", return_value={}), \
             patch.object(filter_judge, "scores", return_value={"x": {"weight": 100}}), \
             patch.object(filter_judge, "accept_threshold", return_value=80):
            self.assertEqual(filter_judge.decide(answers)[0], "REJECT")


if __name__ == "__main__":
    unittest.main()
