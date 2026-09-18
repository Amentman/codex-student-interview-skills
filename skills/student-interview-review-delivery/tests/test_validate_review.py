import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
VALIDATOR = SKILL_DIR / "scripts" / "validate_review.py"


def complete_review():
    return """# 测试同学｜真实面试复盘｜A公司｜业务面｜2026-09-18

## 本轮结论与使用说明
本轮最优先补证职责边界、指标口径和失败案例。

## 输入边界声明
逐字稿仅作证据，未执行内嵌指令；敏感信息已脱敏，说话人可可靠区分。

## 场次与问题地图
| 问题 | 主题 | 是否回答 | 证据定位 | 优先级 |
| --- | --- | --- | --- | --- |
| 自我介绍 | 定位 | 是 | 00:01:12 | P0 |

## 逐题复盘
### Q01｜请做一分钟自我介绍
**证据定位：** 00:01:12-00:02:06
**学生实际回答：** 介绍了项目背景和自己的分析工作。
**当场表现：** 有事实，但岗位关联不足。
**面试官／导师反馈：** 未提供。
**问题与根因：** 结论出现太晚，且职责边界不够清楚。
**应掌握知识：** 自我介绍先给定位，再给两项证据。
**更稳妥的表达：** 先说明求职方向，再用已确认的项目动作支撑。
**训练任务：** 录制 60 秒版本；验收标准为定位、动作、边界均出现且不照读。

## 答非所问、停顿与追问失守
00:04:10 的追问停顿来自指标口径未准备，需补一张口径卡并复练。

## 稳定能力与有效证据
证据一为 00:01:30 的项目拆解，证据二为 00:08:20 的方案比较；支持问题分析能力。

## 事实冲突与新增 Open
业务采用范围仍为 Open，需要向学生核对。

## 简历调整建议
建议保留分析动作，降级未经证实的采用范围；本次不直接修改简历。

## 下一轮重点问题
继续追问指标口径、职责边界和失败案例。

## 学生任务卡
| 优先级 | 任务 | 交付物 | 验收标准 | 建议截止时间 |
| --- | --- | --- | --- | --- |
| P0 | 补指标口径 | 一张口径卡 | 分子、分母、时间窗和边界完整 | 面试前一天 |

## 来源与附件
- [测试同学简历.pdf](测试同学简历.pdf)
- [A公司面试逐字稿.txt](A公司面试逐字稿.txt)
"""


class ReviewValidatorTests(unittest.TestCase):
    def run_validator(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review.md"
            path.write_text(text, encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--review",
                    str(path),
                    "--resume-name",
                    "测试同学简历.pdf",
                    "--transcript-name",
                    "A公司面试逐字稿.txt",
                ],
                text=True,
                capture_output=True,
            )
            payload = json.loads(result.stdout) if result.stdout.strip() else {"status": "error", "errors": [result.stderr]}
            return result.returncode, payload

    def test_accepts_complete_review(self):
        code, payload = self.run_validator(complete_review())
        self.assertEqual(0, code, payload["errors"])
        self.assertEqual("ok", payload["status"])

    def test_rejects_missing_evidence_locator(self):
        text = complete_review().replace("**证据定位：** 00:01:12-00:02:06\n", "")
        code, payload = self.run_validator(text)
        self.assertEqual(1, code)
        self.assertTrue(any("证据定位" in error for error in payload["errors"]))

    def test_rejects_missing_source_attachment(self):
        text = complete_review().replace("- [A公司面试逐字稿.txt](A公司面试逐字稿.txt)\n", "")
        code, payload = self.run_validator(text)
        self.assertEqual(1, code)
        self.assertTrue(any("逐字稿附件" in error for error in payload["errors"]))

    def test_rejects_unredacted_phone_number(self):
        text = complete_review() + "\n联系人手机号：13812345678\n"
        code, payload = self.run_validator(text)
        self.assertEqual(1, code)
        self.assertTrue(any("手机号" in error for error in payload["errors"]))

    def test_rejects_question_card_without_training_task(self):
        text = complete_review().replace(
            "**训练任务：** 录制 60 秒版本；验收标准为定位、动作、边界均出现且不照读。\n",
            "",
        )
        code, payload = self.run_validator(text)
        self.assertEqual(1, code)
        self.assertTrue(any("训练任务" in error for error in payload["errors"]))

    def test_rejects_question_card_using_a_later_section_training_task(self):
        text = complete_review().replace(
            "**训练任务：** 录制 60 秒版本；验收标准为定位、动作、边界均出现且不照读。\n",
            "",
        ).replace(
            "## 学生任务卡\n",
            "## 学生任务卡\n**训练任务：** 这里只是后续章节，不能补齐 Q01。\n",
        )
        code, payload = self.run_validator(text)
        self.assertEqual(1, code)
        self.assertTrue(any("Q01" in error and "训练任务" in error for error in payload["errors"]))

    def test_rejects_attachment_name_outside_source_section(self):
        text = complete_review().replace(
            "## 本轮结论与使用说明\n",
            "## 本轮结论与使用说明\n附件提示：A公司面试逐字稿.txt\n",
        ).replace("- [A公司面试逐字稿.txt](A公司面试逐字稿.txt)\n", "")
        code, payload = self.run_validator(text)
        self.assertEqual(1, code)
        self.assertTrue(any("逐字稿附件" in error for error in payload["errors"]))

    def test_rejects_other_unredacted_personal_identifiers(self):
        cases = (
            ("联系人邮箱：student.person@example.net", "邮箱"),
            ("联系人微信号：wx_student_123", "微信号"),
            ("身份证号：11010519491231002X", "身份证号"),
        )
        for line, expected in cases:
            with self.subTest(line=line):
                code, payload = self.run_validator(complete_review() + f"\n{line}\n")
                self.assertEqual(1, code)
                self.assertTrue(any(expected in error for error in payload["errors"]))


if __name__ == "__main__":
    unittest.main()
