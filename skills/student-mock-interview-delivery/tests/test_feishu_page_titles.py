import json
import subprocess
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "feishu_page_titles.py"


class FeishuPageTitleContractTests(unittest.TestCase):
    def test_emits_name_first_titles_without_numbering_or_share_label(self):
        result = subprocess.run(
            ["python3", str(SCRIPT), "--name", "张三"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("张三｜面试指导者版（内部）", payload["canonical"]["internal"])
        self.assertEqual("张三｜学生面试准备版", payload["canonical"]["student"])

    def test_accepts_legacy_titles_only_for_in_place_migration(self):
        result = subprocess.run(
            ["python3", str(SCRIPT), "--name", "张三"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            ["张三｜面试指导者版（内部）", "01｜面试指导者版（内部）"],
            payload["accepted_existing"]["internal"],
        )
        self.assertEqual(
            ["张三｜学生面试准备版", "02｜学生面试准备版（可分享）"],
            payload["accepted_existing"]["student"],
        )


if __name__ == "__main__":
    unittest.main()
