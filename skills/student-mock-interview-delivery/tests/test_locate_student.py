import importlib.util
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
LOCATOR_PATH = SKILL_DIR / "scripts" / "locate_student.py"
SPEC = importlib.util.spec_from_file_location("locate_student", LOCATOR_PATH)
LOCATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LOCATOR)


class DeliveryRootResolutionTests(unittest.TestCase):
    def test_explicit_root_wins_even_when_auto_candidates_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            explicit = base / "explicit"
            explicit.mkdir()
            auto = base / "校招交付"
            auto.mkdir()

            result = LOCATOR.resolve_delivery_root(
                name="测试同学",
                explicit_root=explicit,
                candidates=[auto],
            )

            self.assertEqual("ok", result["status"])
            self.assertEqual(explicit.resolve(), result["root"])
            self.assertEqual("explicit", result["resolved_by"])

    def test_auto_selects_the_only_existing_delivery_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            missing = base / "旧目录" / "校招交付"
            existing = base / "新目录" / "校招交付"
            existing.mkdir(parents=True)

            result = LOCATOR.resolve_delivery_root(
                name="测试同学",
                candidates=[missing, existing],
            )

            self.assertEqual("ok", result["status"])
            self.assertEqual(existing.resolve(), result["root"])
            self.assertEqual("single_existing", result["resolved_by"])

    def test_auto_prefers_unique_root_containing_student_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            first = base / "第一处" / "校招交付"
            second = base / "第二处" / "校招交付"
            first.mkdir(parents=True)
            student_dir = second / "测试同学"
            student_dir.mkdir(parents=True)
            (student_dir / "测试同学简历.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")

            result = LOCATOR.resolve_delivery_root(
                name="测试同学",
                candidates=[first, second],
            )

            self.assertEqual("ok", result["status"])
            self.assertEqual(second.resolve(), result["root"])
            self.assertEqual("student_evidence", result["resolved_by"])

    def test_auto_stops_when_multiple_roots_contain_student_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            first = base / "第一处" / "校招交付"
            second = base / "第二处" / "校招交付"
            (first / "测试同学").mkdir(parents=True)
            (second / "测试同学").mkdir(parents=True)

            result = LOCATOR.resolve_delivery_root(
                name="测试同学",
                candidates=[first, second],
            )

            self.assertEqual("ambiguous_root", result["status"])
            self.assertIsNone(result["root"])
            self.assertEqual(
                [first.resolve(), second.resolve()],
                result["candidates"],
            )

    def test_auto_reports_missing_when_no_delivery_root_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)

            result = LOCATOR.resolve_delivery_root(
                name="测试同学",
                candidates=[base / "不存在" / "校招交付"],
            )

            self.assertEqual("missing_root", result["status"])
            self.assertIsNone(result["root"])


if __name__ == "__main__":
    unittest.main()
