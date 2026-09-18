import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
VALIDATOR = SKILL_DIR / "scripts" / "validate_feishu_delivery.py"
NAME = "测试同学"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_validate_delivery import full_student, full_teacher  # noqa: E402


def document_xml(
    title,
    question_title,
    *,
    first_attachment=True,
    duplicate_h1=False,
    empty_visual_token=False,
    omit_visual=False,
    visual_uses_src=False,
):
    attachment = '<figure><source name="测试同学简历.pdf" token="resume"/></figure>'
    intro = '<p>正文先出现了</p>'
    first_body = attachment if first_attachment else intro + attachment
    h1 = f"<h1>{title}</h1>" if duplicate_h1 else ""
    if omit_visual:
        visual = ""
    elif visual_uses_src:
        visual = '<image src="https://example.invalid/rendered.png"/>'
    else:
        visual = f'<whiteboard token="{"" if empty_visual_token else "board-1"}"/>'
    return (
        f"<title>{title}</title>{first_body}{h1}"
        "<h2>核心项目架构／图解</h2>"
        f"{visual}"
        f"<h2>{question_title}</h2>"
    )


def snapshots(
    *,
    first_attachment=True,
    duplicate_h1=False,
    empty_visual_token=False,
    omit_visual=False,
    visual_uses_src=False,
):
    internal_title = f"{NAME}｜面试指导者版（内部）"
    student_title = f"{NAME}｜学生面试准备版"
    return {
        "homepage": {
            "markdown": f"# {NAME}\n\n{internal_title}\n\n{student_title}\n",
            "xml": f"<title>{NAME}</title><p>{internal_title}</p><p>{student_title}</p>",
        },
        "internal": {
            "markdown": full_teacher(),
            "xml": document_xml(
                internal_title,
                "模拟面试问题与带教指引",
                first_attachment=first_attachment,
                duplicate_h1=duplicate_h1,
                empty_visual_token=empty_visual_token,
                omit_visual=omit_visual,
                visual_uses_src=visual_uses_src,
            ),
        },
        "student": {
            "markdown": full_student(),
            "xml": document_xml(student_title, "面试问题与个人逐字稿"),
        },
    }


class FeishuDeliveryValidationTests(unittest.TestCase):
    def run_validator(self, payload):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot_path = root / "snapshots.json"
            snapshot_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            fake_cli = root / "lark-cli"
            fake_cli.write_text(
                """#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

args = sys.argv[1:]
doc = args[args.index('--doc') + 1]
doc_format = args[args.index('--doc-format') + 1]
snapshots = json.loads(Path(os.environ['FAKE_LARK_SNAPSHOTS']).read_text(encoding='utf-8'))
content = snapshots[doc][doc_format]
print(json.dumps({
    'ok': True,
    'identity': 'user',
    'data': {'document': {'document_id': doc, 'revision_id': 17, 'content': content}},
}, ensure_ascii=False))
""",
                encoding="utf-8",
            )
            fake_cli.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = str(root) + os.pathsep + env.get("PATH", "")
            env["FAKE_LARK_SNAPSHOTS"] = str(snapshot_path)
            result = subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    "--name",
                    NAME,
                    "--homepage",
                    "homepage",
                    "--internal",
                    "internal",
                    "--student",
                    "student",
                    "--track",
                    "business",
                ],
                text=True,
                capture_output=True,
                env=env,
            )
            payload = (
                json.loads(result.stdout)
                if result.stdout.strip()
                else {"status": "missing-validator", "errors": [result.stderr], "revision_ids": {}}
            )
            return result.returncode, payload

    def test_accepts_complete_documents_fetched_directly_from_feishu(self):
        code, result = self.run_validator(snapshots())
        self.assertEqual(0, code, result["errors"])
        self.assertEqual("ok", result["status"])
        self.assertEqual(
            {"homepage": 17, "internal": 17, "student": 17},
            result["revision_ids"],
        )

    def test_rejects_when_resume_is_not_first_body_block(self):
        code, result = self.run_validator(snapshots(first_attachment=False))
        self.assertEqual(1, code)
        self.assertTrue(any("第一个正文块" in error for error in result["errors"]))

    def test_rejects_duplicate_body_h1(self):
        code, result = self.run_validator(snapshots(duplicate_h1=True))
        self.assertEqual(1, code)
        self.assertTrue(any("正文不得包含 H1" in error for error in result["errors"]))

    def test_rejects_empty_visual_token(self):
        code, result = self.run_validator(snapshots(empty_visual_token=True))
        self.assertEqual(1, code)
        self.assertTrue(any("空图片或画板 token" in error for error in result["errors"]))

    def test_rejects_document_without_a_rendered_visual(self):
        code, result = self.run_validator(snapshots(omit_visual=True))
        self.assertEqual(1, code)
        self.assertTrue(any("至少一张可读项目图" in error for error in result["errors"]))

    def test_accepts_a_rendered_image_with_nonempty_src(self):
        code, result = self.run_validator(snapshots(visual_uses_src=True))
        self.assertEqual(0, code, result["errors"])


if __name__ == "__main__":
    unittest.main()
