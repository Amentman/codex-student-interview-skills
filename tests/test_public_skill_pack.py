import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"


EXPECTED_SKILLS = {
    "auditing-candidate-resumes",
    "building-resume-interview-stories",
    "campus-job-matching",
    "campus-recommend",
    "delivering-student-career-plans",
    "designing-student-portfolio-products",
    "recording-processing",
    "revising-and-delivering-resumes",
    "student-interview-review-delivery",
    "student-job-content",
    "student-mock-interview-delivery",
    "student-role-interview-prep",
    "visual-document-delivery",
}


class PublicSkillPackTests(unittest.TestCase):
    def test_complete_catalog_is_present(self):
        actual = {p.name for p in SKILLS.iterdir() if (p / "SKILL.md").is_file()}
        self.assertEqual(EXPECTED_SKILLS, actual)

    def test_every_skill_has_portable_frontmatter(self):
        for name in EXPECTED_SKILLS:
            path = SKILLS / name / "SKILL.md"
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), path)
            header = text.split("---\n", 2)[1]
            self.assertRegex(header, r"(?m)^name:\s*" + re.escape(name) + r"\s*$")
            self.assertRegex(header, r"(?m)^description:\s*.+")

    def test_skill_links_resolve(self):
        pattern = re.compile(r"\]\(([^)#]+)(?:#[^)]+)?\)")
        for path in SKILLS.rglob("*.md"):
            for target in pattern.findall(path.read_text(encoding="utf-8")):
                if "://" in target or target.startswith("mailto:"):
                    continue
                self.assertTrue((path.parent / target).exists(), f"{path}: {target}")

    def test_public_pack_has_no_machine_specific_paths_or_build_artifacts(self):
        files = [
            p
            for p in ROOT.rglob("*")
            if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts
        ]
        self.assertFalse(any(p.suffix == ".pyc" for p in files))
        user_prefix = "/" + "Users" + "/"
        home_prefix = "/" + "home" + "/"
        forbidden = re.compile(
            re.escape(user_prefix)
            + "|"
            + re.escape(home_prefix)
            + r"|[A-Za-z]:\\\\"
        )
        for path in files:
            if path.suffix not in {".md", ".yaml", ".yml", ".json", ".py", ".toml"}:
                continue
            self.assertIsNone(forbidden.search(path.read_text(encoding="utf-8")), path)

    def test_catalog_routes_every_skill_once(self):
        catalog = (ROOT / "docs" / "SKILL_CATALOG.md").read_text(encoding="utf-8")
        for name in EXPECTED_SKILLS:
            self.assertEqual(catalog.count(f"`{name}`"), 1, name)


if __name__ == "__main__":
    unittest.main()
