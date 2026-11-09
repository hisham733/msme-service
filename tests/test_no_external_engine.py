"""Cut-the-cord guard (T-050 / D40): the engine must not need MSME_AI_News."""
import unittest
from pathlib import Path

from msme import paths
from msme.repurpose.engine import config

ROOT = Path(__file__).resolve().parent.parent


class NoExternalEngineTests(unittest.TestCase):
    def test_engine_paths_are_inside_this_repo(self):
        cfg = config.load_config()
        repo = paths.ROOT.resolve()
        for key in ("email_articles_root", "dlw_root"):
            p = Path(cfg[key]).resolve()
            self.assertTrue(str(p).startswith(str(repo)), f"{key} escapes the repo: {p}")

    def test_no_source_references_the_external_engine(self):
        bad = []
        for path in (ROOT / "msme").rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for needle in ("MSME_AI_News", "REPURPOSE_ENGINE_ROOT"):
                if needle in text:
                    bad.append(f"{path.relative_to(ROOT)}: {needle}")
        self.assertEqual(bad, [])

    def test_skills_are_vendored(self):
        for rel in ("skills/msme-repurpose/SKILL.md",
                    "skills/msme-image-select/SKILL.md"):
            self.assertTrue((config.ROOT / rel).is_file(), rel)


if __name__ == "__main__":
    unittest.main()
