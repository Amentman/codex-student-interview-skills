import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "skills" / "campus-job-matching"


class CampusJobMatchingContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        cls.matching = (ROOT / "references" / "campus-matching.md").read_text(
            encoding="utf-8"
        )
        cls.feishu = (ROOT / "references" / "feishu-delivery.md").read_text(
            encoding="utf-8"
        )

    def test_direction_and_link_guards_are_explicit(self):
        for phrase in (
            "方向硬过滤",
            "白名单",
            "严禁",
            "疑似研发宁可剔除",
            "点开必须能投递",
            "公司主页/聚合页冒充详情",
        ):
            self.assertIn(phrase, self.skill + self.matching)

    def test_freshness_batch_dedup_and_csv_contract_is_explicit(self):
        for phrase in (
            "已过截止",
            "已下架",
            "限生源",
            "分批",
            "零重叠",
            "CSV",
            "utf-8-sig",
            "2026-10-15",
        ):
            self.assertIn(phrase, self.skill + self.matching)

    def test_feishu_write_scope_and_readback_are_explicit(self):
        for phrase in (
            "tenant token",
            "只填主字段列",
            "勿碰重复列",
            "单批≤200",
            "串行",
            "独立回读",
        ):
            self.assertIn(phrase, self.feishu + self.skill)

    def test_variable_count_is_not_hardcoded_to_23(self):
        self.assertNotIn("23 条非空记录", self.feishu)

    def test_existing_table_full_audit_mode_is_explicit(self):
        for phrase in (
            "全量复核",
            "逐条问题清单",
            "直接在表内",
            "删除/改链接",
            "record_id",
            "删除需用户明确授权",
        ):
            self.assertIn(phrase, self.skill + self.matching + self.feishu)

    def test_company_cap_counts_existing_records(self):
        for phrase in (
            "已有记录计入公司上限",
            "已有 3 条",
            "历史超额记录只报告",
        ):
            self.assertIn(phrase, self.skill + self.matching + self.feishu)


if __name__ == "__main__":
    unittest.main()
