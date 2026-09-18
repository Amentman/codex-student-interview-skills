import json
import hashlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


class RepositoryContractTests(unittest.TestCase):
    def test_plugin_contains_complete_interview_skill_suite(self):
        expected = {
            "building-resume-interview-stories",
            "recording-processing",
            "student-mock-interview-delivery",
            "student-role-interview-prep",
            "student-interview-review-delivery",
            "visual-document-delivery",
        }
        actual = {path.name for path in SKILLS.iterdir() if (path / "SKILL.md").is_file()}
        self.assertEqual(expected, actual)

    def test_skill_names_match_their_directories(self):
        for skill_dir in SKILLS.iterdir():
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.is_file():
                continue
            text = skill_file.read_text(encoding="utf-8")
            match = re.search(r"^name:\s*([^\n]+)$", text, re.MULTILINE)
            self.assertIsNotNone(match, skill_file)
            self.assertEqual(skill_dir.name, match.group(1).strip())

    def test_markdown_references_are_local_and_resolvable(self):
        link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+\.md)\)")
        for markdown in SKILLS.rglob("*.md"):
            text = markdown.read_text(encoding="utf-8")
            for target in link_pattern.findall(text):
                self.assertFalse(target.startswith("/"), f"absolute link in {markdown}: {target}")
                self.assertTrue((markdown.parent / target).resolve().is_file(), f"missing link in {markdown}: {target}")

    def test_interview_review_requests_route_to_the_dedicated_skill(self):
        mock_text = (SKILLS / "student-mock-interview-delivery" / "SKILL.md").read_text(encoding="utf-8")
        role_text = (SKILLS / "student-role-interview-prep" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("student-interview-review-delivery", mock_text)
        self.assertIn("student-interview-review-delivery", role_text)

    def test_discovery_metadata_keeps_the_three_core_routes_distinct(self):
        mock_ui = (SKILLS / "student-mock-interview-delivery" / "agents" / "openai.yaml").read_text(encoding="utf-8")
        recording = (SKILLS / "recording-processing" / "SKILL.md").read_text(encoding="utf-8")
        stories = (SKILLS / "building-resume-interview-stories" / "SKILL.md").read_text(encoding="utf-8")
        mock_contract = (SKILLS / "student-mock-interview-delivery" / "references" / "interview-content-contract.md").read_text(encoding="utf-8")

        self.assertNotIn("实际面试转写稿", mock_ui)
        self.assertNotIn("可选复盘", mock_ui)
        self.assertIn("student-interview-review-delivery", recording)
        self.assertIn("student-role-interview-prep", stories)
        self.assertIn("student-mock-interview-delivery", stories)
        self.assertNotIn("有真实公司与 JD 时才增加", mock_contract)

    def test_distributed_skills_do_not_embed_private_feishu_targets(self):
        text_suffixes = {".md", ".py", ".yaml", ".yml", ".json", ".toml", ".txt"}
        corpus = "\n".join(
            path.read_text(encoding="utf-8")
            for path in SKILLS.rglob("*")
            if path.is_file() and path.suffix in text_suffixes
        )
        self.assertIsNone(re.search(r"space_id`?:\s*`?\d{10,}", corpus))
        self.assertNotIn("旧分类父节点", corpus)
        self.assertNotIn("/" + "Users" + "/", corpus)

    def test_repository_does_not_embed_secret_like_values_or_private_feishu_urls(self):
        text_suffixes = {".md", ".py", ".yaml", ".yml", ".json", ".toml", ".txt"}
        files = [
            path
            for path in ROOT.rglob("*")
            if path.is_file() and ".git" not in path.parts and path.suffix in text_suffixes
        ]
        corpus = "\n".join(path.read_text(encoding="utf-8") for path in files)
        forbidden = (
            r"sk-[A-Za-z0-9_-]{16,}",
            r"AKIA[0-9A-Z]{16}",
            r"gh[pousr]_[A-Za-z0-9]{20,}",
            r"xox[baprs]-[A-Za-z0-9-]{10,}",
            r"Bearer\s+[A-Za-z0-9._-]{20,}",
            r"https://[^\s)]+(?:feishu\.cn|larksuite\.com)/(?:wiki|docx|docs|base|drive)/[^\s)]+",
        )
        for pattern in forbidden:
            self.assertIsNone(re.search(pattern, corpus, re.IGNORECASE), pattern)

    def test_absolute_user_paths_are_limited_to_audited_prompt_provenance(self):
        allowed = {
            ROOT / "prompts" / "global-AGENTS.md",
            ROOT / "prompts" / "project-AGENTS.md",
            ROOT / "docs" / "PROVENANCE.md",
        }
        offenders = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts or path in allowed:
                continue
            if path.suffix not in {".md", ".py", ".yaml", ".yml", ".json", ".toml", ".txt"}:
                continue
            absolute_user_prefix = "/" + "Users" + "/"
            if absolute_user_prefix in path.read_text(encoding="utf-8"):
                offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual([], offenders)

    def test_plugin_manifest_points_to_skills_directory(self):
        manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual("codex-student-interview-skills", manifest["name"])
        self.assertEqual("./skills/", manifest["skills"])

        portable = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual("https://agent-plugins.org/schemas/1.0.0/plugin.schema.json", portable["$schema"])
        self.assertEqual(manifest["name"], portable["name"])
        self.assertEqual(
            portable["extensions"]["com.openai"]["interface"]["capabilities"],
            manifest["interface"]["capabilities"],
        )

        marketplace = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
        entry = marketplace["plugins"][0]
        self.assertEqual(portable["name"], entry["name"])
        self.assertEqual(
            "https://github.com/Amentman/codex-student-interview-skills.git",
            entry["source"]["url"],
        )

    def test_source_prompt_snapshots_are_present(self):
        expected = {
            "global-AGENTS.md": "4510de771fbf41d65ff6601c5d0f2b82fee991bafde4e675c869cc19de3f0bf4",
            "project-AGENTS.md": "66aa549c7573a8b000c5b233f73f40fce980c57ce60ca4ce996e43920a520e35",
        }
        for filename, digest in expected.items():
            content = (ROOT / "prompts" / filename).read_bytes()
            self.assertEqual(digest, hashlib.sha256(content).hexdigest())


if __name__ == "__main__":
    unittest.main()
