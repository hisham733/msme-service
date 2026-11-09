"""Tests for repurpose engine usage capture and the runtime engine config.

Run: python3 -m unittest tests.test_repurpose_usage -v
"""
import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from msme import db, settings_store
from msme.repurpose.engine import config as engine_config
from msme.repurpose.engine import llm_step, usage, vision


class _FakeResponse:
    def __init__(self, body):
        self._body = body

    def __enter__(self):
        return io.BytesIO(self._body)

    def __exit__(self, *exc):
        return False


def _completion(content="ok", prompt=10, completion=5):
    return json.dumps({
        "model": "deepseek-flash",
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": prompt, "completion_tokens": completion,
                  "total_tokens": prompt + completion},
    }).encode()


class UsageAccumulatorTests(unittest.TestCase):
    def tearDown(self):
        usage.reset()

    def test_add_and_reset(self):
        usage.reset()
        usage.add({"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}, "m")
        usage.add({"prompt": 2, "completion": 3, "total": 5}, "m")
        total = usage.get()
        self.assertEqual(total["prompt"], 12)
        self.assertEqual(total["completion"], 8)
        self.assertEqual(total["total"], 20)
        self.assertEqual(total["calls"], 2)
        self.assertEqual(total["model"], "m")
        usage.reset()
        self.assertEqual(usage.get()["total"], 0)

    def test_calls_without_usage_are_ignored(self):
        usage.reset()
        usage.add({}, "m")
        usage.add(None, "m")
        self.assertEqual(usage.get()["calls"], 0)


class EngineCallTests(unittest.TestCase):
    def tearDown(self):
        usage.reset()

    def _cfg(self):
        return {"llm": {"model": "deepseek-flash", "base_url": "https://api.example/chat",
                        "temperature": 0.2, "api_key_env": "DEEPSEEK_API_KEY"}}

    def test_call_llm_records_usage(self):
        usage.reset()
        with patch.object(llm_step, "api_key", return_value="k"), \
                patch.object(llm_step.urllib.request, "urlopen",
                             return_value=_FakeResponse(_completion())):
            text = llm_step.call_llm([{"role": "user", "content": "hi"}], self._cfg())
        self.assertEqual(text, "ok")
        self.assertEqual(usage.get()["total"], 15)
        self.assertEqual(usage.get()["model"], "deepseek-flash")

    def test_vision_post_records_usage(self):
        usage.reset()
        with patch.object(vision, "api_key", return_value="k"), \
                patch("urllib.request.urlopen",
                      return_value=_FakeResponse(_completion('{"images": []}', 20, 4))):
            vision._post(self._cfg(), [{"role": "user", "content": "look"}])
        self.assertEqual(usage.get()["total"], 24)


class EngineConfigTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patch = patch.object(settings_store, "SETTINGS_PATH",
                                  os.path.join(self.tmp.name, "settings.json"))
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_runtime_settings_win(self):
        settings_store.save({
            "REPURPOSE_MODEL": "test-model",
            "REPURPOSE_TEMPERATURE": 0.7,
            "REPURPOSE_RETRY_LIMIT": 4,
        })
        cfg = engine_config.load_config()
        self.assertEqual(cfg["llm"]["model"], "test-model")
        self.assertAlmostEqual(cfg["llm"]["temperature"], 0.7)
        self.assertEqual(cfg["llm"]["retry_limit"], 4)

    def test_defaults_without_settings(self):
        cfg = engine_config.load_config()
        self.assertTrue(cfg["llm"]["model"])
        self.assertAlmostEqual(cfg["llm"]["temperature"], 0.2)


class RepurposeRunStorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.patch = patch.object(db.config, "SQLITE_PATH",
                                  os.path.join(self.tmp.name, "usage.sqlite3"))
        self.patch.start()
        db.init_db()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def test_usage_json_is_stored_and_read(self):
        payload = {"prompt": 100, "completion": 50, "total": 150, "calls": 2}
        db.upsert_repurpose_run("folder-x", status="validated", model="deepseek-flash",
                                usage_json=json.dumps(payload))
        rows = db.cost_repurpose_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["usage"]["total"], 150)


if __name__ == "__main__":
    unittest.main()
