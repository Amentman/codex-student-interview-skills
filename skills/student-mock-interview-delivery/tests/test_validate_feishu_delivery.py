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
SPACE_ID = "test-space-id"
ARCHIVE_ROOT = "archive-root-token"
OLD_MOCK_ROOT = "old-mock-root-token"

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
):
    attachment = '<figure><source name="测试同学简历.pdf" token="resume"/></figure>'
    intro = '<p>正文先出现了</p>'
    first_body = attachment if first_attachment else intro + attachment
    h1 = f"<h1>{title}</h1>" if duplicate_h1 else ""
    visual = "" if omit_visual else f'<whiteboard token="{"" if empty_visual_token else "board-1"}"/>'
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
):
    internal_title = f"{NAME}｜面试指导者版（内部）"
    student_title = f"{NAME}｜学生面试准备版"
    return {
        "profile": {
            "markdown": f"# {NAME}\n\n学员档案与服务记录。\n",
            "xml": (
                f"<title>{NAME}</title><p>学员档案与服务记录。</p>"
                '<h2>模拟面试交付入口</h2><p>'
                '<a href="https://example.invalid/wiki/internal">老师版</a>／'
                '<a href="https://example.invalid/wiki/student">学生版</a>'
                '</p>'
            ),
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
            ),
        },
        "student": {
            "markdown": full_student(),
            "xml": document_xml(student_title, "面试问题与个人逐字稿"),
        },
        "wiki_nodes": {
            "profile": {
                "node_token": "profile", "parent_node_token": ARCHIVE_ROOT,
                "title": NAME, "obj_token": "profile-doc", "obj_type": "docx",
                "space_id": SPACE_ID, "node_type": "origin", "has_child": True,
            },
            "internal": {
                "node_token": "internal", "parent_node_token": "profile",
                "title": internal_title, "obj_token": "internal-doc", "obj_type": "docx",
                "space_id": SPACE_ID, "node_type": "origin", "has_child": False,
            },
            "student": {
                "node_token": "student", "parent_node_token": "profile",
                "title": student_title, "obj_token": "student-doc", "obj_type": "docx",
                "space_id": SPACE_ID, "node_type": "origin", "has_child": False,
            },
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
snapshots = json.loads(Path(os.environ['FAKE_LARK_SNAPSHOTS']).read_text(encoding='utf-8'))
if args[:2] == ['docs', '+fetch']:
    doc = args[args.index('--doc') + 1]
    doc_format = args[args.index('--doc-format') + 1]
    content = snapshots[doc][doc_format]
    data = {'document': {'document_id': doc, 'revision_id': 17, 'content': content}}
elif args[:2] == ['wiki', '+node-get']:
    token = args[args.index('--node-token') + 1]
    data = snapshots['wiki_nodes'][token]
elif args[:2] == ['wiki', '+node-list']:
    parent = args[args.index('--parent-node-token') + 1]
    data = {'nodes': [node for node in snapshots['wiki_nodes'].values()
                      if node['parent_node_token'] == parent], 'has_more': False}
else:
    raise SystemExit('unexpected fake lark-cli command: ' + repr(args))
print(json.dumps({'ok': True, 'identity': 'user', 'data': data}, ensure_ascii=False))
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
                    "--profile",
                    "profile",
                    "--internal",
                    "internal",
                    "--student",
                    "student",
                    "--space-id",
                    SPACE_ID,
                    "--archive-root",
                    ARCHIVE_ROOT,
                    "--old-mock-root",
                    OLD_MOCK_ROOT,
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
            {"profile": 17, "internal": 17, "student": 17},
            result["revision_ids"],
        )

    def test_rejects_teacher_student_expression_type_mismatch(self):
        payload = snapshots()
        payload["student"]["markdown"] = payload["student"]["markdown"].replace(
            "**表达类型：** 迁移表达",
            "**表达类型：** 亲历表达",
            1,
        ).replace(
            "**事实或场景依据：** S01；K01",
            "**事实或场景依据：** S01",
            1,
        )
        code, result = self.run_validator(payload)
        self.assertEqual(1, code)
        self.assertTrue(any("表达类型不一致" in error for error in result["errors"]))

    def test_rejects_role_page_still_nested_under_same_name_homepage(self):
        payload = snapshots()
        payload["wiki_nodes"]["internal"]["parent_node_token"] = "legacy-homepage"
        code, result = self.run_validator(payload)
        self.assertEqual(1, code)
        self.assertTrue(any("直属子页" in error for error in result["errors"]))

    def test_rejects_redundant_same_name_child_under_profile(self):
        payload = snapshots()
        payload["wiki_nodes"]["legacy-homepage"] = {
            "node_token": "legacy-homepage", "parent_node_token": "profile",
            "title": NAME, "obj_token": "legacy-doc", "obj_type": "docx",
            "space_id": SPACE_ID, "node_type": "origin", "has_child": False,
        }
        code, result = self.run_validator(payload)
        self.assertEqual(1, code)
        self.assertTrue(any("同名中间页" in error for error in result["errors"]))

    def test_rejects_duplicate_student_archive(self):
        payload = snapshots()
        payload["wiki_nodes"]["duplicate-profile"] = {
            "node_token": "duplicate-profile",
            "parent_node_token": ARCHIVE_ROOT,
            "title": NAME, "obj_token": "duplicate-doc", "obj_type": "docx",
        }
        code, result = self.run_validator(payload)
        self.assertEqual(1, code)
        self.assertTrue(any("同名学员档案" in error for error in result["errors"]))

    def test_accepts_empty_historical_index(self):
        payload = snapshots()
        payload["wiki_nodes"]["historical-home"] = {
            "node_token": "historical-home",
            "parent_node_token": OLD_MOCK_ROOT,
            "title": NAME, "obj_token": "historical-doc", "obj_type": "docx",
        }
        code, result = self.run_validator(payload)
        self.assertEqual(0, code, result["errors"])

    def test_rejects_active_role_page_under_historical_index(self):
        payload = snapshots()
        payload["wiki_nodes"]["historical-home"] = {
            "node_token": "historical-home",
            "parent_node_token": OLD_MOCK_ROOT,
            "title": NAME, "obj_token": "historical-doc", "obj_type": "docx",
        }
        payload["wiki_nodes"]["legacy-role"] = {
            "node_token": "legacy-role",
            "parent_node_token": "historical-home",
            "title": f"{NAME}｜学生面试准备版", "obj_token": "legacy-role-doc", "obj_type": "docx",
        }
        code, result = self.run_validator(payload)
        self.assertEqual(1, code)
        self.assertTrue(any("旧目录仍有活跃同角色页" in error for error in result["errors"]))

    def test_rejects_missing_interview_footer_in_student_archive(self):
        payload = snapshots()
        payload["profile"]["xml"] = f"<title>{NAME}</title><p>学员档案与服务记录。</p>"
        code, result = self.run_validator(payload)
        self.assertEqual(1, code)
        self.assertTrue(any("模拟面试交付入口" in error for error in result["errors"]))

    def test_rejects_footer_pointing_to_wrong_role_pages(self):
        payload = snapshots()
        payload["profile"]["xml"] = payload["profile"]["xml"].replace(
            "/wiki/internal", "/wiki/someone-else"
        )
        code, result = self.run_validator(payload)
        self.assertEqual(1, code)
        self.assertTrue(any("老师版链接" in error for error in result["errors"]))

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

    def test_accepts_valid_image_src_from_feishu_xml(self):
        payload = snapshots()
        payload["internal"]["xml"] = payload["internal"]["xml"].replace(
            '<whiteboard token="board-1"/>', '<img src="image-file-token"/>'
        )
        code, result = self.run_validator(payload)
        self.assertEqual(0, code, result["errors"])

    def test_rejects_document_without_a_rendered_visual(self):
        code, result = self.run_validator(snapshots(omit_visual=True))
        self.assertEqual(1, code)
        self.assertTrue(any("至少一张可读项目图" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
