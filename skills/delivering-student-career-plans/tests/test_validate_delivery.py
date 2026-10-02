import copy
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from validate_delivery import validate_manifest  # noqa: E402


WHITEPAPER_PARENT = "whitepaper-parent-token"
CAREER_PLAN_PARENT = "career-plan-parent-token"


def write_minimal_pdf(path: Path, page_count: int) -> None:
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        (
            f"<< /Type /Pages /Count {page_count} /Kids ["
            + " ".join(f"{index} 0 R" for index in range(3, 3 + page_count))
            + "] >>"
        ).encode("ascii"),
    ]
    objects.extend(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 596 842] >>"
        for _ in range(page_count)
    )
    payload = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for object_number, body in enumerate(objects, start=1):
        offsets.append(len(payload))
        payload.extend(f"{object_number} 0 obj\n".encode("ascii"))
        payload.extend(body)
        payload.extend(b"\nendobj\n")
    xref_offset = len(payload)
    payload.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    payload.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        payload.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    payload.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    path.write_bytes(payload)


def make_png(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        )

    row = b"\x00" + bytes(rgb) * width
    raw = row * height
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw))
        + chunk(b"IEND", b"")
    )


def complete_career_visual_manifest(page_count: int = 12):
    specs = (
        (
            "industry-value-chain",
            "flowchart",
            "Industry overview",
            "Externally verified",
            "Explain where the target roles sit in the industry.",
        ),
        (
            "career-route-map",
            "matrix",
            "Route priorities",
            "Inferred",
            "Compare main, steady, and conditional routes without hiding gaps.",
        ),
        (
            "timeline",
            "timeline",
            "Action timeline",
            "Open",
            "Make the 90-day and graduation milestones visible.",
        ),
    )
    visual_plan = [
        {
            "id": visual_id,
            "type": visual_type,
            "reason": reason,
            "section": section,
            "fact_boundary": fact_boundary,
            "caption": "Evidence status is shown in the figure.",
            "source_note": "Career-plan evidence ledger and verified public sources.",
        }
        for visual_id, visual_type, section, fact_boundary, reason in specs
    ]
    return {
        "skill": "delivering-student-career-plans",
        "visual_contract": {
            "substantial": True,
            "complexity_signals": ["multi_route_comparison", "time_stages"],
            "required_visual_ids": [item[0] for item in specs],
            "visual_plan": visual_plan,
            "readback": {
                "media_blocks": [
                    {"visual_id": item[0], "token": f"image-{index}"}
                    for index, item in enumerate(specs, start=1)
                ]
            },
            "render_qa": {
                "page_count": page_count,
                "checked_pages": list(range(1, page_count + 1)),
                "checked_items": ["clipping", "readability", "layout", "caption"],
                "issues": [],
            },
        },
    }


class ValidateDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        fixture_dir = Path(__file__).parent / "fixtures"
        self.whitepaper_text = (fixture_dir / "complete_whitepaper.txt").read_text(encoding="utf-8")
        self.plan_text = (fixture_dir / "complete_plan.txt").read_text(encoding="utf-8")
        self.plan_text += "\n" + (
            "每项行动均需对应真实任务、本人动作、可核实产出、截止时间和复盘结果。" * 500
        )
        self.whitepaper_path = self.root / "whitepaper.txt"
        self.plan_path = self.root / "plan.txt"
        self.whitepaper_path.write_text(self.whitepaper_text, encoding="utf-8")
        self.plan_path.write_text(self.plan_text, encoding="utf-8")
        self.resume_path = self.root / "示例候选人简历.pdf"
        self.resume_path.write_bytes(b"%PDF-1.4\noriginal resume fixture\n%%EOF\n")
        self.resume_sha256 = hashlib.sha256(self.resume_path.read_bytes()).hexdigest()
        self.rendered_pdf_path = self.root / "career-plan.pdf"
        write_minimal_pdf(self.rendered_pdf_path, 12)
        self.rendered_pdf_sha256 = hashlib.sha256(
            self.rendered_pdf_path.read_bytes()
        ).hexdigest()
        self.visual_manifest_path = self.root / "visual-manifest.json"
        self.visual_manifest_path.write_text(
            json.dumps(complete_career_visual_manifest(), ensure_ascii=False),
            encoding="utf-8",
        )
        self.rendered_pages_dir = self.root / "rendered-pages"
        self.rendered_pages_dir.mkdir()
        pdftoppm = shutil.which("pdftoppm")
        if pdftoppm is None:
            self.fail("pdftoppm is required for delivery validator tests")
        subprocess.run(
            [
                pdftoppm,
                "-png",
                "-r",
                "90",
                str(self.rendered_pdf_path),
                str(self.rendered_pages_dir / "page"),
            ],
            check=True,
            capture_output=True,
        )
        self.readback_path = self.root / "feishu-readback.json"
        self.readback = {
            "method": "browser",
            "read_at": "2026-09-04T17:30:00+08:00",
            "whitepaper": {
                "url": "https://example.invalid/wiki/whitepaper",
                "title": "AI 赛道｜行业与岗位白皮书（2026版）",
                "parent_node_token": WHITEPAPER_PARENT,
                "observed_parent_node_token": WHITEPAPER_PARENT,
                "observed_parent_title": "行业白皮书与岗位科普",
                "parent_relation_source": "sidebar-tree",
                "observed_node_level": 4,
                "observed_node_pos": "4,2,0,1",
                "observed_parent_level": 3,
                "observed_parent_node_pos": "4,2,0",
                "direct_parent_verified": True,
                "duplicate_page_count": 1,
                "unexpected_blank_sibling_count": 0,
                "source_first_marker_present": True,
                "source_last_marker_present": True,
                "source_count_observed": 10,
                "required_sections_present": 10,
                "required_sections_total": 10,
            },
            "career_plan": {
                "url": "https://example.invalid/wiki/career-plan",
                "title": "示例候选人｜AI 职业规划",
                "parent_node_token": CAREER_PLAN_PARENT,
                "observed_parent_node_token": CAREER_PLAN_PARENT,
                "observed_parent_title": "职业规划",
                "parent_relation_source": "sidebar-tree",
                "observed_node_level": 3,
                "observed_node_pos": "4,8,1",
                "observed_parent_level": 2,
                "observed_parent_node_pos": "4,8",
                "direct_parent_verified": True,
                "duplicate_page_count": 1,
                "unexpected_blank_sibling_count": 0,
                "whitepaper_url": "https://example.invalid/wiki/whitepaper",
                "required_sections_present": 9,
                "required_sections_total": 9,
                "original_resume_attachment_count": 1,
                "full_plan_checks": {
                    "main_section_count": 15,
                    "jd_count_observed": 8,
                    "project_count_observed": 2,
                    "resume_version_count_observed": 3,
                    "internship_stage_count_observed": 3,
                    "has_90_day_plan": True,
                    "has_graduation_timeline": True,
                    "route_coverage": {
                        "technical_ai_product": {
                            "label": "高匹配岗位",
                            "jd_count_observed": 4,
                            "project_count_observed": 1,
                            "resume_version_count_observed": 1,
                            "adjustment_conditions_present": True,
                            "jd_markers": [
                                "产品岗 JD1",
                                "产品岗 JD2",
                                "产品岗 JD3",
                                "产品岗 JD4",
                            ],
                            "project_markers": ["项目一：岗位对口项目"],
                            "resume_markers": ["V1 产品版"],
                            "adjustment_markers": ["转为高匹配岗位单主线"],
                        },
                        "agent_application_development": {
                            "label": "保稳方向",
                            "jd_count_observed": 4,
                            "project_count_observed": 1,
                            "resume_version_count_observed": 1,
                            "adjustment_conditions_present": True,
                            "jd_markers": [
                                "Agent 岗 JD1",
                                "Agent 岗 JD2",
                                "Agent 岗 JD3",
                                "Agent 岗 JD4",
                            ],
                            "project_markers": ["项目二：综合能力项目"],
                            "resume_markers": ["V2 Agent 版"],
                            "adjustment_markers": ["转为保稳方向单主线"],
                        },
                    },
                },
                "rendered_pdf_pages": 12,
                "rendered_pdf_sha256": self.rendered_pdf_sha256,
                "rendered_page_image_count": 12,
                "visual_qa_pass": True,
                "markdown_sha256": hashlib.sha256(
                    self.plan_path.read_bytes()
                ).hexdigest(),
                "visual_qa_pages": [
                    {
                        "page": page_number,
                        "status": "passed",
                        "image_sha256": hashlib.sha256(
                            (self.rendered_pages_dir / f"page-{page_number:02d}.png").read_bytes()
                        ).hexdigest(),
                        "checked_items": ["clipping", "readability", "layout"],
                        "issues": [],
                    }
                    for page_number in range(1, 13)
                ],
                "attachment": {
                    "block_type": "file",
                    "filename": self.resume_path.name,
                    "position": "first_page",
                    "preview_opened": True,
                },
            },
        }
        self.manifest = {
            "visual_manifest_path": str(self.visual_manifest_path),
            "whitepaper": {
                "title": "AI 赛道｜行业与岗位白皮书（2026版）",
                "text_path": str(self.whitepaper_path),
                "parent_node_token": WHITEPAPER_PARENT,
                "source_count": 10,
                "url": "https://example.invalid/wiki/whitepaper",
            },
            "career_plan": {
                "text_path": str(self.plan_path),
                "parent_node_token": CAREER_PLAN_PARENT,
                "student_name": "示例候选人",
                "title": "示例候选人｜AI 职业规划",
                "url": "https://example.invalid/wiki/career-plan",
                "source_files": [str(self.resume_path)],
                "original_resume": {
                    "path": str(self.resume_path),
                    "filename": self.resume_path.name,
                    "size_bytes": self.resume_path.stat().st_size,
                    "sha256": self.resume_sha256,
                },
                "whitepaper_url": "https://example.invalid/wiki/whitepaper",
                "delivery_mode": "full",
                "required_route_keys": [
                    "technical_ai_product",
                    "agent_application_development",
                ],
                "jd_official_domains": ["jobs.example.com"],
                "rendered_pdf_path": str(self.rendered_pdf_path),
                "rendered_pages_dir": str(self.rendered_pages_dir),
            },
            "expected": {
                "whitepaper_parent_node_token": WHITEPAPER_PARENT,
                "career_plan_parent_node_token": CAREER_PLAN_PARENT,
                "career_plan_delivery_mode": "full",
            },
            "readback_path": str(self.readback_path),
        }

    def tearDown(self):
        self.temp_dir.cleanup()

    def validate(self, manifest=None):
        self.readback_path.write_text(
            json.dumps(self.readback, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        manifest_path = self.root / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest or self.manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return validate_manifest(manifest_path)

    def configure_standard_mode(self):
        supplement = """

# 核心方向薪资与公司补充
薪资参考核验日：2026-09-29。产品/应用方向薪资样本为上海税前年包 25—42 万；Agent 方向薪资样本为上海税前年包 30—55 万，均为岗位样本而非市场承诺。

# 行业与公司选择
当前岗位样本：字节跳动、携程、华为。长期研究池：智谱、MiniMax。
AI Agent 大厂池包括字节跳动、华为；中小型 AI/垂直场景公司池包括智谱、MiniMax。主投应用开发、平台和评测，核心算法与后训练只做选择性冲刺。
项目达到最小可演示状态并通过复盘后，再进入对应简历版本和正式投递。
受保护证据链标记：项目证据 → 简历版本 → 正式投递 → 面试反馈。
"""
        plan_text = self.plan_text + supplement
        self.plan_path.write_text(plan_text, encoding="utf-8")
        authoritative_text_path = self.root / "authoritative-plan.txt"
        authoritative_text_path.write_text(plan_text, encoding="utf-8")
        self.manifest["career_plan"]["delivery_mode"] = "standard"
        self.manifest["career_plan"]["required_route_keys"] = [
            "product_application",
            "agent_application",
        ]
        self.manifest["career_plan"]["expected_project_count"] = 2
        self.manifest["career_plan"]["requires_agent_company_split"] = True
        self.manifest["career_plan"]["source_fidelity"] = {
            "authoritative_artifact_path": str(self.rendered_pdf_path),
            "authoritative_artifact_sha256": self.rendered_pdf_sha256,
            "authoritative_text_path": str(authoritative_text_path),
            "protected_marker_groups": [
                {
                    "label": "evidence chain",
                    "markers": [
                        "受保护证据链标记：项目证据 → 简历版本 → 正式投递 → 面试反馈。"
                    ],
                },
                {
                    "label": "company names",
                    "markers": ["字节跳动", "携程", "智谱", "MiniMax"],
                },
            ],
            "required_visual_ids": [
                "industry-value-chain",
                "career-route-map",
                "timeline",
            ],
        }
        self.manifest["expected"]["career_plan_delivery_mode"] = "standard"
        self.manifest["expected"]["require_source_fidelity"] = True
        self.readback["career_plan"].pop("full_plan_checks")
        self.readback["career_plan"]["markdown_sha256"] = hashlib.sha256(
            plan_text.encode("utf-8")
        ).hexdigest()
        self.readback["career_plan"]["standard_plan_checks"] = {
            "direction_count_observed": 2,
            "salary_reference_date": "2026-09-29",
            "route_coverage": {
                "product_application": {
                    "label": "高匹配岗位",
                    "daily_work_markers": ["用户调研和需求文档"],
                    "fit_markers": ["数据背景"],
                    "role_markers": ["产品岗 JD1"],
                    "salary_markers": ["产品/应用方向薪资样本"],
                    "company_markers": ["字节跳动", "携程"],
                },
                "agent_application": {
                    "label": "保稳方向",
                    "daily_work_markers": ["RAG 后端与评测"],
                    "fit_markers": ["Python 基础"],
                    "role_markers": ["Agent 岗 JD1"],
                    "salary_markers": ["Agent 方向薪资样本"],
                    "company_markers": ["智谱", "MiniMax"],
                },
            },
            "company_pool": {
                "current_samples_separated_from_research_pool": True,
            },
            "agent_company_split": {
                "bigtech_markers": ["字节跳动", "华为"],
                "sme_markers": ["智谱", "MiniMax"],
                "role_tier_boundary_present": True,
            },
        }
        self.readback["career_plan"]["source_fidelity_checks"] = {
            "visual_media_blocks": [
                {"visual_id": "industry-value-chain", "token": "image-1"},
                {"visual_id": "career-route-map", "token": "image-2"},
                {"visual_id": "timeline", "token": "image-3"},
            ]
        }

    def test_rejects_whitepaper_without_sources_and_limitations(self):
        self.whitepaper_path.write_text(
            self.whitepaper_text.replace("## 局限、时效与更新时间", "## 备注")
            .replace("## 来源与证据台账", "## 附录"),
            encoding="utf-8",
        )
        manifest = copy.deepcopy(self.manifest)
        manifest["whitepaper"]["source_count"] = 0
        errors = self.validate(manifest)
        self.assertIn("whitepaper: missing sources", errors)
        self.assertIn("whitepaper: missing limitations or update date", errors)

    def test_rejects_full_plan_when_required_visual_is_missing(self):
        visual_manifest = complete_career_visual_manifest()
        contract = visual_manifest["visual_contract"]
        contract["visual_plan"] = [
            item
            for item in contract["visual_plan"]
            if item["id"] != "career-route-map"
        ]
        contract["readback"]["media_blocks"] = [
            item
            for item in contract["readback"]["media_blocks"]
            if item["visual_id"] != "career-route-map"
        ]
        self.visual_manifest_path.write_text(
            json.dumps(visual_manifest, ensure_ascii=False), encoding="utf-8"
        )
        errors = self.validate()
        self.assertIn(
            "career_plan visual: required visual missing from plan: career-route-map",
            errors,
        )

    def test_rejects_plan_without_original_resume_attachment(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["career_plan"]["source_files"] = ["questionnaire.png"]
        manifest["career_plan"].pop("original_resume")
        errors = self.validate(manifest)
        self.assertIn("career_plan: missing original resume attachment", errors)

    def test_rejects_resume_path_that_does_not_exist(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["career_plan"]["original_resume"]["path"] = str(
            self.root / "missing-resume.pdf"
        )
        errors = self.validate(manifest)
        self.assertIn("career_plan: original resume file does not exist", errors)

    def test_rejects_resume_with_mismatched_sha256(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["career_plan"]["original_resume"]["sha256"] = "0" * 64
        errors = self.validate(manifest)
        self.assertIn("career_plan: original resume sha256 mismatch", errors)

    def test_rejects_text_only_feishu_attachment_readback(self):
        self.readback["career_plan"]["attachment"]["block_type"] = "text"
        errors = self.validate()
        self.assertIn(
            "career_plan readback: attachment is not a file/source block", errors
        )

    def test_rejects_resume_attachment_at_document_end(self):
        self.readback["career_plan"]["attachment"]["position"] = "document_end"
        errors = self.validate()
        self.assertIn(
            "career_plan readback: original resume is not on first page", errors
        )

    def test_rejects_unopened_attachment_preview(self):
        self.readback["career_plan"]["attachment"]["preview_opened"] = False
        errors = self.validate()
        self.assertIn(
            "career_plan readback: attachment preview was not verified", errors
        )

    def test_rejects_incomplete_live_plan_sections(self):
        self.readback["career_plan"]["required_sections_present"] = 8
        errors = self.validate()
        self.assertIn("career_plan readback: required sections incomplete", errors)

    def test_rejects_full_plan_that_is_only_a_short_outline(self):
        self.readback["career_plan"]["full_plan_checks"]["main_section_count"] = 5
        errors = self.validate()
        self.assertIn("career_plan readback: full plan must have 12-18 main sections", errors)

    def test_rejects_full_plan_without_required_depth(self):
        checks = self.readback["career_plan"]["full_plan_checks"]
        checks["jd_count_observed"] = 5
        checks["project_count_observed"] = 1
        checks["resume_version_count_observed"] = 1
        checks["internship_stage_count_observed"] = 2
        checks["has_90_day_plan"] = False
        checks["has_graduation_timeline"] = False
        errors = self.validate()
        self.assertIn("career_plan readback: full plan must contain 6-10 verified JDs", errors)
        self.assertIn("career_plan readback: full plan must contain at least two projects", errors)
        self.assertIn("career_plan readback: full plan must contain 2-3 resume versions", errors)
        self.assertIn("career_plan readback: full plan must contain three internship stages", errors)
        self.assertIn("career_plan readback: missing 90-day plan", errors)
        self.assertIn("career_plan readback: missing graduation timeline", errors)

    def test_rejects_full_plan_when_one_route_has_no_evidence_chain(self):
        coverage = self.readback["career_plan"]["full_plan_checks"]["route_coverage"]
        coverage["agent_application_development"]["project_count_observed"] = 0
        errors = self.validate()
        self.assertIn(
            "career_plan readback: route agent_application_development missing project coverage",
            errors,
        )

    def test_rejects_duplicate_required_route_keys(self):
        self.manifest["career_plan"]["required_route_keys"] = [
            "technical_ai_product",
            "technical_ai_product",
        ]
        errors = self.validate()
        self.assertIn("career_plan: required route keys must be unique", errors)

    def test_rejects_route_markers_not_found_in_live_text(self):
        coverage = self.readback["career_plan"]["full_plan_checks"]["route_coverage"]
        coverage["technical_ai_product"]["project_markers"] = ["不存在的项目"]
        errors = self.validate()
        self.assertIn(
            "career_plan readback: route technical_ai_product project markers not found",
            errors,
        )

    def test_rejects_route_marker_reused_by_two_routes(self):
        coverage = self.readback["career_plan"]["full_plan_checks"]["route_coverage"]
        coverage["agent_application_development"]["project_markers"] = [
            "项目一：岗位对口项目"
        ]
        errors = self.validate()
        self.assertIn("career_plan readback: route project markers must be unique", errors)

    def test_rejects_claimed_full_counts_that_do_not_match_live_text(self):
        self.plan_path.write_text("# 示例候选人｜职业规划\n\n## 核心定位\n短提纲", encoding="utf-8")
        errors = self.validate()
        self.assertIn("career_plan readback: main section count does not match live text", errors)
        self.assertIn("career_plan readback: JD count does not match live text", errors)

    def test_rejects_keyword_stuffed_short_outline(self):
        short_plan = "\n".join(
            [f"# 章节 {index}" for index in range(1, 13)]
            + [
                "代表性真实 JD（2026-09-10 访问） https://jobs.example.com/1",
                "项目一：A 项目 项目二：B 项目 V1 V2",
                "第一段实习 第二段实习 第三段实习 前 90 天 毕业前时间线",
                "核心定位 方向优先级 公司池 投递策略 面试策略 风险 执行分工与验收",
            ]
        )
        self.plan_path.write_text(short_plan, encoding="utf-8")
        self.readback["career_plan"]["markdown_sha256"] = hashlib.sha256(
            short_plan.encode("utf-8")
        ).hexdigest()
        errors = self.validate()
        self.assertIn("career_plan readback: full plan is too short", errors)

    def test_rejects_project_without_required_detail(self):
        shallow_plan = self.plan_text.replace("个人必须完成的工作", "学生行动")
        self.plan_path.write_text(shallow_plan, encoding="utf-8")
        self.readback["career_plan"]["markdown_sha256"] = hashlib.sha256(
            shallow_plan.encode("utf-8")
        ).hexdigest()
        errors = self.validate()
        self.assertIn("career_plan readback: project sections missing personal work", errors)

    def test_rejects_concise_mode_when_full_delivery_is_expected(self):
        self.manifest["career_plan"]["delivery_mode"] = "concise"
        errors = self.validate()
        self.assertIn("career_plan: delivery_mode does not match expected mode", errors)

    def test_accepts_standard_plan_with_salary_company_split_and_correct_sequence(self):
        self.configure_standard_mode()
        self.assertEqual([], self.validate())

    def test_rejects_standard_plan_when_live_text_hash_is_stale(self):
        self.configure_standard_mode()
        self.readback["career_plan"]["markdown_sha256"] = "0" * 64
        errors = self.validate()
        self.assertIn("career_plan readback: live text sha256 mismatch", errors)

    def test_rejects_standard_plan_when_protected_source_marker_is_missing(self):
        self.configure_standard_mode()
        protected = "受保护证据链标记：项目证据 → 简历版本 → 正式投递 → 面试反馈。"
        plan_text = self.plan_path.read_text(encoding="utf-8").replace(protected, "")
        self.plan_path.write_text(plan_text, encoding="utf-8")
        self.readback["career_plan"]["markdown_sha256"] = hashlib.sha256(
            plan_text.encode("utf-8")
        ).hexdigest()
        errors = self.validate()
        self.assertIn(
            "career_plan source fidelity: protected marker missing from live text (evidence chain: 受保护证据链标记：项目证据 → 简历版本 → 正式投递 → 面试反馈。)",
            errors,
        )

    def test_rejects_standard_plan_when_required_feishu_visual_is_missing(self):
        self.configure_standard_mode()
        blocks = self.readback["career_plan"]["source_fidelity_checks"][
            "visual_media_blocks"
        ]
        self.readback["career_plan"]["source_fidelity_checks"][
            "visual_media_blocks"
        ] = [item for item in blocks if item["visual_id"] != "career-route-map"]
        errors = self.validate()
        self.assertIn(
            "career_plan source fidelity: required Feishu visual missing (career-route-map)",
            errors,
        )

    def test_rejects_standard_plan_without_salary_evidence(self):
        self.configure_standard_mode()
        coverage = self.readback["career_plan"]["standard_plan_checks"][
            "route_coverage"
        ]
        coverage["agent_application"]["salary_markers"] = ["不存在的薪资样本"]
        errors = self.validate()
        self.assertIn(
            "career_plan readback: route agent_application salary markers not found",
            errors,
        )

    def test_rejects_standard_agent_plan_without_bigtech_company_list(self):
        self.configure_standard_mode()
        split = self.readback["career_plan"]["standard_plan_checks"][
            "agent_company_split"
        ]
        split["bigtech_markers"] = ["不存在的大厂 A", "不存在的大厂 B"]
        errors = self.validate()
        self.assertIn(
            "career_plan readback: Agent big-tech company markers not found",
            errors,
        )

    def test_rejects_standard_plan_when_resume_precedes_projects(self):
        self.configure_standard_mode()
        plan_text = "# 简历版本预览\n先做简历。\n\n" + self.plan_path.read_text(
            encoding="utf-8"
        )
        self.plan_path.write_text(plan_text, encoding="utf-8")
        self.readback["career_plan"]["markdown_sha256"] = hashlib.sha256(
            plan_text.encode("utf-8")
        ).hexdigest()
        errors = self.validate()
        self.assertIn(
            "career_plan readback: project-resume-application sequence is wrong",
            errors,
        )

    def test_rejects_full_plan_without_verified_page_by_page_pdf_qa(self):
        self.readback["career_plan"]["visual_qa_pass"] = False
        self.readback["career_plan"]["rendered_page_image_count"] = 11
        errors = self.validate()
        self.assertIn("career_plan readback: PDF visual QA not verified", errors)
        self.assertIn("career_plan readback: rendered page image count mismatch", errors)

    def test_rejects_invalid_png_and_incomplete_per_page_qa(self):
        (self.rendered_pages_dir / "page-01.png").write_bytes(b"not an image")
        self.readback["career_plan"]["visual_qa_pages"] = [
            {"page": 1, "status": "passed"}
        ]
        errors = self.validate()
        self.assertIn("career_plan readback: invalid rendered PNG page-01.png", errors)
        self.assertIn("career_plan readback: per-page visual QA is incomplete", errors)

    def test_rejects_valid_png_that_does_not_match_pdf_page(self):
        page_one = self.rendered_pages_dir / "page-01.png"
        page_one.write_bytes(make_png(800, 1000, (10, 20, 30)))
        self.readback["career_plan"]["visual_qa_pages"][0]["image_sha256"] = hashlib.sha256(
            page_one.read_bytes()
        ).hexdigest()
        errors = self.validate()
        self.assertIn("career_plan readback: rendered page images do not match PDF", errors)

    def test_rejects_pdf_page_count_mismatch(self):
        write_minimal_pdf(self.rendered_pdf_path, 11)
        self.readback["career_plan"]["rendered_pdf_sha256"] = hashlib.sha256(
            self.rendered_pdf_path.read_bytes()
        ).hexdigest()
        errors = self.validate()
        self.assertIn("career_plan readback: PDF page count mismatch", errors)

    def test_rejects_whitepaper_source_count_mismatch(self):
        self.readback["whitepaper"]["source_count_observed"] = 9
        errors = self.validate()
        self.assertIn("whitepaper readback: source count mismatch", errors)

    def test_rejects_duplicate_original_resume_attachments(self):
        self.readback["career_plan"]["original_resume_attachment_count"] = 2
        errors = self.validate()
        self.assertIn(
            "career_plan readback: original resume attachment count is not one",
            errors,
        )

    def test_rejects_unexpected_blank_sibling_page(self):
        self.readback["whitepaper"]["unexpected_blank_sibling_count"] = 1
        errors = self.validate()
        self.assertIn("whitepaper readback: unexpected blank sibling page", errors)

    def test_rejects_missing_feishu_readback(self):
        manifest = copy.deepcopy(self.manifest)
        manifest.pop("readback_path")
        errors = self.validate(manifest)
        self.assertIn("manifest: missing readback_path", errors)

    def test_rejects_plan_without_whitepaper_link(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["career_plan"]["whitepaper_url"] = ""
        self.plan_path.write_text(
            self.plan_text.replace("https://example.invalid/wiki/whitepaper", ""),
            encoding="utf-8",
        )
        errors = self.validate(manifest)
        self.assertIn("career_plan: missing whitepaper link", errors)

    def test_accepts_complete_career_plan_without_whitepaper(self):
        manifest = copy.deepcopy(self.manifest)
        manifest.pop("whitepaper")
        manifest["expected"].pop("whitepaper_parent_node_token")
        manifest["career_plan"].pop("whitepaper_url")
        self.readback.pop("whitepaper")
        self.readback["career_plan"].pop("whitepaper_url")
        plan_text = self.plan_text.replace(
            "https://example.invalid/wiki/whitepaper", ""
        )
        self.plan_path.write_text(plan_text, encoding="utf-8")
        self.readback["career_plan"]["markdown_sha256"] = hashlib.sha256(
            plan_text.encode("utf-8")
        ).hexdigest()
        self.assertEqual([], self.validate(manifest))

    def test_accepts_feishu_markdown_with_h1_title_and_h2_chapters(self):
        plan_text = "# 示例候选人｜职业规划\n\n" + re.sub(
            r"(?m)^# ", "## ", self.plan_text
        )
        self.plan_path.write_text(plan_text, encoding="utf-8")
        self.readback["career_plan"]["markdown_sha256"] = hashlib.sha256(
            plan_text.encode("utf-8")
        ).hexdigest()
        self.assertEqual([], self.validate())

    def test_accepts_student_facing_equivalent_section_names(self):
        plan_text = self.plan_text.replace(
            "# 核心定位与当前卡点", "# 一、先看结论：你该投什么"
        ).replace(
            "核心定位：", "方向结论："
        ).replace(
            "# 前 90 天计划", "# 十、30 天行动计划\n\n完整复盘窗口为 90 天。"
        ).replace(
            "# 风险与待确认项", "# 十一、还需要本人确认的事项"
        ).replace(
            "后续确认信息", "仍需本人补充的事项"
        )
        self.plan_path.write_text(plan_text, encoding="utf-8")
        self.readback["career_plan"]["markdown_sha256"] = hashlib.sha256(
            plan_text.encode("utf-8")
        ).hexdigest()
        self.assertEqual([], self.validate())

    def test_accepts_structured_jd_cards_with_chinese_access_date(self):
        cards = ["# 代表性岗位参考（2026年9月10日查阅）"]
        for index in range(1, 9):
            name = "产品岗 JD" if index <= 4 else "Agent 岗 JD"
            number = index if index <= 4 else index - 4
            slug = "product" if index <= 4 else "agent"
            cards.extend(
                [
                    f"### {name}{number}",
                    f"类型与地点：当前岗位；上海。https://jobs.example.com/{slug}-{number}",
                    "主要任务：客户与项目推进。门槛与加分项：本科、沟通与数据能力。",
                    "匹配与差距：已有基础但缺岗位闭环。投递判断：补齐项目后投递。",
                ]
            )
        plan_text = re.sub(
            r"(?ms)^# 代表性真实 JD 对照.*?(?=^# 项目一：)",
            "\n\n".join(cards) + "\n\n",
            self.plan_text,
        )
        self.plan_path.write_text(plan_text, encoding="utf-8")
        self.readback["career_plan"]["markdown_sha256"] = hashlib.sha256(
            plan_text.encode("utf-8")
        ).hexdigest()
        self.assertEqual([], self.validate())

    def test_accepts_plan_without_product_service_map_when_not_requested(self):
        plan_text = re.sub(
            r"(?ms)^# 产品与服务 Map\n.*?(?=^# 前 90 天计划)",
            "",
            self.plan_text,
        )
        self.plan_path.write_text(plan_text, encoding="utf-8")
        self.readback["career_plan"]["markdown_sha256"] = hashlib.sha256(
            plan_text.encode("utf-8")
        ).hexdigest()
        self.readback["career_plan"]["full_plan_checks"]["main_section_count"] = 14
        self.assertEqual([], self.validate())

    def test_rejects_internal_working_language_in_external_plan(self):
        leaked_plan = self.plan_text + "\n" + (
            "文档定位：外企优先补充版。原始资料与事实底稿。"
            "该图为顾问判断（Inferred），不代表当前 HC。"
            "资料边界：项目计划中，不包装成真实经历，不得使用虚构结果。"
        )
        self.plan_path.write_text(leaked_plan, encoding="utf-8")
        self.readback["career_plan"]["markdown_sha256"] = hashlib.sha256(
            leaked_plan.encode("utf-8")
        ).hexdigest()
        errors = self.validate()
        self.assertIn("career_plan: external copy contains internal working language (文档定位)", errors)
        self.assertIn("career_plan: external copy contains internal working language (事实底稿)", errors)
        self.assertIn("career_plan: external copy contains internal working language (顾问判断)", errors)
        self.assertIn("career_plan: external copy contains internal working language (Inferred)", errors)
        self.assertIn("career_plan: external copy contains internal working language (HC)", errors)
        self.assertIn("career_plan: external copy contains internal working language (资料边界)", errors)
        self.assertIn("career_plan: external copy contains internal working language (不包装成)", errors)
        self.assertIn("career_plan: external copy contains internal working language (不得使用虚构)", errors)

    def test_rejects_wrong_feishu_parent_tokens(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["whitepaper"]["parent_node_token"] = "wrong-whitepaper-parent"
        manifest["career_plan"]["parent_node_token"] = "wrong-career-plan-parent"
        errors = self.validate(manifest)
        self.assertIn("whitepaper: wrong Feishu parent token", errors)
        self.assertIn("career_plan: wrong Feishu parent token", errors)

    def test_rejects_claimed_parent_when_live_tree_observes_another_parent(self):
        self.readback["career_plan"]["observed_parent_node_token"] = (
            "HlKhwHet9iskqbkgD6ecOXthnxd"
        )
        self.readback["career_plan"]["observed_parent_title"] = "校招岗位数据库"
        self.readback["career_plan"]["observed_node_pos"] = "4,7,0"
        self.readback["career_plan"]["observed_parent_node_pos"] = "4,7"
        errors = self.validate()
        self.assertIn("career_plan readback: observed parent mismatch", errors)

    def test_accepts_complete_two_document_delivery(self):
        self.assertEqual([], self.validate())


if __name__ == "__main__":
    unittest.main()
