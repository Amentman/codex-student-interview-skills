import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from enforce_company_cap import cap_rows, validate_company_cap


class CompanyCapTests(unittest.TestCase):
    def test_skill_contract_declares_and_routes_the_hard_cap(self):
        skill = (Path(__file__).resolve().parents[1] / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("同一学生 × 同一公司最多 3 个岗位", skill)
        self.assertIn("enforce_company_cap.py", skill)

    def test_caps_each_company_at_three_and_preserves_ranked_order(self):
        rows = [
            {"公司": "甲公司", "投递岗位": f"岗位{i}"} for i in range(1, 5)
        ] + [
            {"公司": "乙公司", "投递岗位": "岗位1"},
            {"公司": "甲公司", "投递岗位": "岗位5"},
        ]

        kept, dropped = cap_rows(rows, max_per_company=3)

        self.assertEqual(
            [(row["公司"], row["投递岗位"]) for row in kept],
            [("甲公司", "岗位1"), ("甲公司", "岗位2"), ("甲公司", "岗位3"),
             ("乙公司", "岗位1")],
        )
        self.assertEqual(
            [(row["公司"], row["投递岗位"]) for row in dropped],
            [("甲公司", "岗位4"), ("甲公司", "岗位5")],
        )

    def test_validator_reports_violations_without_silently_passing(self):
        rows = [{"公司": "甲公司"} for _ in range(4)]
        violations = validate_company_cap(rows, max_per_company=3)
        self.assertEqual(violations, {"甲公司": 4})


if __name__ == "__main__":
    unittest.main()
