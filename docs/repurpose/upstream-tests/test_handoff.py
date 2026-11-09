"""Handoff tests — the multi-machine contract (D-015), the intake contract (D-016) and the export (D-017).

These are the checks that make the partner handoff a build, not a hope:
* `config.local.json` overrides the shared config and never writes the shared file;
* `intake.*` can describe a foreign folder shape without editing code;
* `preflight` PASSes the synthetic demo and FAILs the two deliberate bad shapes;
* `build_export` produces a tree with no secret, no client folder, and every required file.
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline import config, preflight, scan

try:  # `tools\` is deliberately not exported; the builder test only runs in the source repository
    import tools.build_export as export
except ImportError:  # pragma: no cover - exercised by running the goldens inside the export
    export = None

DEMO = config.ROOT / "partner_handoff" / "demo_releases"
BAD = config.ROOT / "partner_handoff" / "demo_releases_bad"

MINI_CONFIG = {
    "email_articles_root": "Files_from_MSME/Email_Articles",
    "dlw_root": "DLW",
    "queue_mode": "one",
    "skills": {"repurpose": ".claude/skills/msme-repurpose/SKILL.md",
               "image_select": ".claude/skills/msme-image-select/SKILL.md"},
    "llm": {"provider": "deepseek", "model": "deepseek-flash", "base_url": "https://example.invalid",
            "api_key_env": "DEEPSEEK_API_KEY", "temperature": 0.2, "retry_limit": 2},
    "dashboard": {"host": "127.0.0.1", "port": 8765},
}


class ConfigLayerTest(unittest.TestCase):
    def test_deep_merge_keeps_untouched_keys_and_replaces_lists(self):
        merged = config.deep_merge({"llm": {"model": "a", "retry_limit": 2},
                                    "image_dirs": ["images"]},
                                   {"llm": {"model": "b"}, "image_dirs": ["photos"]})
        self.assertEqual(merged["llm"], {"model": "b", "retry_limit": 2})
        self.assertEqual(merged["image_dirs"], ["photos"])

    def test_local_overrides_shared_and_shared_file_is_not_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config.json").write_text(json.dumps(MINI_CONFIG), encoding="utf-8")
            local = root / "config.local.json"
            with mock.patch.object(config, "ROOT", root), mock.patch.object(config, "LOCAL", local):
                self.assertEqual(config.load_config()["email_articles_root"],
                                 "Files_from_MSME/Email_Articles")
                config.save_local({"email_articles_root": "D:/Partner/Email_Articles",
                                   "llm": {"model": "a-local-model"}})
                cfg = config.load_config()
                self.assertEqual(cfg["email_articles_root"], "D:/Partner/Email_Articles")
                self.assertEqual(cfg["llm"]["model"], "a-local-model")
                self.assertEqual(cfg["llm"]["retry_limit"], 2)          # untouched shared key survives
                self.assertEqual(json.loads((root / "config.json").read_text())["email_articles_root"],
                                 "Files_from_MSME/Email_Articles")   # shared file untouched

    def test_intake_defaults_apply_without_mutating_cfg(self):
        cfg = {"intake": {"image_dirs": ["photos"]}}
        rules = config.intake_cfg(cfg)
        self.assertEqual(rules["image_dirs"], ["photos"])
        self.assertEqual(rules["link_names"], config.DEFAULT_INTAKE["link_names"])
        self.assertNotIn("link_names", cfg["intake"])


class IntakeShapeTest(unittest.TestCase):
    def test_scan_reads_a_foreign_shape_via_config_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "RELEASE_ONE"
            (folder / "photos").mkdir(parents=True)
            (folder / "press release.txt").write_text("x" * 300, encoding="utf-8")
            (folder / "photos" / "a.jpg").write_bytes(b"fake")
            rules = config.deep_merge(config.DEFAULT_INTAKE, {
                "release_text_glob": "*.txt", "release_text_exclude": [],
                "image_dirs": ["photos"], "link_names": ["url.txt"]})
            row = scan.scan_folder(folder, rules)
            self.assertEqual(row["n_release_texts"], 1)
            self.assertEqual(row["release"], "press release.txt")
            self.assertEqual(row["n_images"], 1)
            self.assertFalse(row["has_link"])

    def test_ambiguous_folder_is_visible_not_silently_first(self):
        row = scan.scan_folder(BAD / "DEMO_Ambiguous_Two_Releases")
        self.assertEqual(row["n_release_texts"], 2)
        self.assertTrue(row["ambiguous"])


class PreflightTest(unittest.TestCase):
    def test_demo_passes_with_no_warning(self):
        report = preflight.check_root(DEMO)
        self.assertEqual(report["summary"]["fail"], 0)
        self.assertEqual(report["summary"]["warn"], 0)
        self.assertEqual(report["summary"]["pass"], 2)

    def test_bad_shapes_fail_for_the_right_reason(self):
        report = preflight.check_root(BAD)
        self.assertEqual(report["summary"]["fail"], 2)
        rows = {r["folder"]: r for r in report["folders"]}
        self.assertIn("ambiguous", " ".join(rows["DEMO_Ambiguous_Two_Releases"]["errors"]))
        self.assertIn("no release text", " ".join(rows["DEMO_No_Release_Text"]["errors"]))

    def test_flat_root_is_a_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "one.md").write_text("x" * 300, encoding="utf-8")
            report = preflight.check_root(root)
            self.assertTrue(report["flat_release_texts"])

    def test_batch_indexes_at_the_root_are_not_release_texts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "INDEX.md").write_text("# index", encoding="utf-8")
            (root / "_LINKS.md").write_text("| folder | url |", encoding="utf-8")
            release = root / "RELEASE_ONE"
            release.mkdir()
            (release / "release.md").write_text("x" * 300, encoding="utf-8")
            report = preflight.check_root(root)
            self.assertEqual(report["flat_release_texts"], [])
            self.assertEqual(report["summary"]["folders"], 1)

    def test_missing_root_is_reported_not_crashed(self):
        report = preflight.check_root("Z:/definitely/not/here")
        self.assertFalse(report["exists"])
        self.assertIn("does not exist", report["error"])


class SkillHashTest(unittest.TestCase):
    def test_skill_hash_ignores_line_endings(self):
        from pipeline.manifest import skill_hash
        with tempfile.TemporaryDirectory() as tmp:
            crlf = Path(tmp) / "crlf.md"
            lf = Path(tmp) / "lf.md"
            crlf.write_bytes(b"rule one\r\nrule two\r\n")
            lf.write_bytes(b"rule one\nrule two\n")
            self.assertEqual(skill_hash(crlf), skill_hash(lf))
            lf.write_bytes(b"rule one\nrule three\n")
            self.assertNotEqual(skill_hash(crlf), skill_hash(lf))


@unittest.skipIf(export is None, "export builder not present (running inside the handoff export)")
class ExportTest(unittest.TestCase):
    def test_export_tree_is_clean_and_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = export.build(Path(tmp) / "tree", clean=False)
            tree = Path(result["out"])
            self.assertEqual(export.verify(tree), [])
            for rel in export.REQUIRED:
                self.assertTrue((tree / rel).is_file(), rel)
            self.assertFalse((tree / "Files_from_MSME").exists())
            self.assertFalse((tree / "DLW" / "images").exists())
            self.assertTrue((tree / "analysis" / "repurpose" / "cold-run"
                             / "N-01_semiconductor_draft.md").is_file())
            self.assertFalse((tree / "analysis" / "imageeval").exists())
            self.assertIn("DLW_ARTICLES", (tree / "DLW" / "data" / "articles.js").read_text())
            self.assertEqual((tree / "DLW" / "data" / "articles.js").read_text().count("["), 1)

    def test_export_never_carries_a_key_or_the_local_config(self):
        self.assertTrue(export.skip("config.local.json"))
        self.assertTrue(export.skip(".env"))
        self.assertTrue(export.skip("Files_from_MSME/x.md"))
        self.assertTrue(export.skip("DLW/images/a.jpg"))
        self.assertFalse(export.skip("partner_handoff/demo_releases/x/images/a.png"))


if __name__ == "__main__":
    unittest.main()
