#!/usr/bin/env python3
"""Deterministic quality gate for two-document student career-plan deliveries."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


VISUAL_VALIDATOR_PATH = (
    Path(__file__).resolve().parents[2]
    / "visual-document-delivery"
    / "scripts"
    / "validate_visual_manifest.py"
)


def contains_any(text: str, terms: tuple[str, ...]) -> bool:
    normalized = " ".join(text.lower().split())
    return any(term.lower() in normalized for term in terms)


def _resolve_text(payload: dict[str, Any], manifest_dir: Path, label: str) -> tuple[str, list[str]]:
    raw_path = payload.get("text_path")
    if not raw_path:
        return "", [f"{label}: missing text_path"]
    path = Path(str(raw_path))
    if not path.is_absolute():
        path = manifest_dir / path
    try:
        return path.read_text(encoding="utf-8"), []
    except (OSError, UnicodeError) as exc:
        return "", [f"{label}: cannot read text_path ({exc})"]


def _missing_group(text: str, groups: tuple[tuple[str, tuple[str, ...]], ...], label: str) -> list[str]:
    return [f"{label}: missing {name}" for name, terms in groups if not contains_any(text, terms)]


def validate_whitepaper(text: str, payload: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("parent_node_token") != expected.get("whitepaper_parent_node_token"):
        errors.append("whitepaper: wrong Feishu parent token")

    groups = (
        ("research scope or method", ("研究范围", "研究方法", "资料范围")),
        ("industry value chain", ("行业价值链", "产业链", "上游", "中游", "下游")),
        ("role map", ("岗位地图", "岗位簇", "部门与岗位", "岗位族谱")),
        ("trends or risks", ("趋势", "风险", "招聘变化", "行业周期")),
    )
    errors.extend(_missing_group(text, groups, "whitepaper"))

    source_count = payload.get("source_count", 0)
    if not isinstance(source_count, int) or source_count < 1 or not contains_any(
        text, ("来源与证据", "参考来源", "资料来源", "来源台账")
    ):
        errors.append("whitepaper: missing sources")

    if not contains_any(
        text,
        ("局限、时效与更新时间", "局限与时效", "限制与更新时间", "局限性说明"),
    ):
        errors.append("whitepaper: missing limitations or update date")

    url = str(payload.get("url", ""))
    if not url.startswith(("https://", "http://")):
        errors.append("whitepaper: missing valid URL")
    return errors


def _resolve_local_path(raw_path: Any, manifest_dir: Path) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    path = Path(raw_path)
    return path if path.is_absolute() else manifest_dir / path


def _validate_visual_manifest(
    manifest: dict[str, Any], manifest_dir: Path
) -> list[str]:
    raw_path = manifest.get("visual_manifest_path")
    path = _resolve_local_path(raw_path, manifest_dir)
    if path is None:
        return ["manifest: missing visual_manifest_path"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"career_plan visual: cannot read valid JSON ({exc})"]

    if not VISUAL_VALIDATOR_PATH.is_file():
        return ["career_plan visual: shared validator cannot be loaded"]
    spec = importlib.util.spec_from_file_location(
        "visual_document_delivery_validator", VISUAL_VALIDATOR_PATH
    )
    if spec is None or spec.loader is None:
        return ["career_plan visual: shared validator cannot be loaded"]
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return [
        f"career_plan visual: {error}"
        for error in module.validate_manifest(data)
    ]


def _validate_original_resume(
    payload: dict[str, Any], manifest_dir: Path
) -> tuple[list[str], dict[str, Any] | None]:
    errors: list[str] = []
    resume = payload.get("original_resume")
    if not isinstance(resume, dict):
        return ["career_plan: missing original resume attachment"], None

    path = _resolve_local_path(resume.get("path"), manifest_dir)
    if path is None or not path.is_file():
        return ["career_plan: original resume file does not exist"], resume

    filename = str(resume.get("filename", ""))
    if filename != path.name:
        errors.append("career_plan: original resume filename mismatch")

    actual_size = path.stat().st_size
    if actual_size < 1 or resume.get("size_bytes") != actual_size:
        errors.append("career_plan: original resume size mismatch")

    actual_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    if resume.get("sha256") != actual_sha256:
        errors.append("career_plan: original resume sha256 mismatch")
    return errors, resume


def validate_career_plan(
    text: str,
    payload: dict[str, Any],
    expected: dict[str, Any],
    manifest_dir: Path,
    require_whitepaper: bool = True,
) -> list[str]:
    errors: list[str] = []
    if payload.get("parent_node_token") != expected.get("career_plan_parent_node_token"):
        errors.append("career_plan: wrong Feishu parent token")

    student_name = str(payload.get("student_name", "")).strip()
    if not student_name or student_name not in text:
        errors.append("career_plan: missing student name")

    groups = (
        (
            "core positioning",
            ("核心定位", "一句话定位", "求职定位", "先看结论", "方向结论"),
        ),
        (
            "direction priorities",
            ("核心求职方向", "方向优先级", "主攻方向", "保稳方向", "岗位比较"),
        ),
        (
            "company-pool boundary",
            ("行业与公司选择", "公司池", "目标企业", "岗位边界"),
        ),
        ("projects", ("项目一", "项目 1", "补充项目", "岗位对口项目")),
        ("resume versions", ("简历版本", "定向简历", "简历规划", "简历与求职材料")),
        ("application and interview", ("投递与面试", "投递策略", "面试策略")),
        (
            "timeline",
            (
                "阶段时间线",
                "行动时间线",
                "阶段计划",
                "毕业前时间线",
                "30 天行动计划",
                "30天行动计划",
                "90 天计划",
                "90天行动计划",
                "校招路径",
            ),
        ),
        (
            "risks",
            (
                "风险与待确认",
                "风险",
                "待确认项",
                "后续确认信息",
                "还需要本人确认",
                "本人确认的事项",
            ),
        ),
    )
    errors.extend(_missing_group(text, groups, "career_plan"))
    if payload.get("require_product_service_mapping") is True and not contains_any(
        text,
        ("产品与服务 map", "服务与资源 map", "服务模块", "产出验收", "执行分工与验收"),
    ):
        errors.append("career_plan: missing product-service mapping")

    resume_errors, _ = _validate_original_resume(payload, manifest_dir)
    errors.extend(resume_errors)

    if require_whitepaper:
        whitepaper_url = str(payload.get("whitepaper_url", "")).strip()
        if not whitepaper_url.startswith(("https://", "http://")) or whitepaper_url not in text:
            errors.append("career_plan: missing whitepaper link")

    unsafe_claims = (
        "保证录用",
        "保证 offer",
        "百分百上岸",
        "项目已盈利",
    )
    for claim in unsafe_claims:
        if claim.lower() in text.lower():
            errors.append(f"career_plan: high-risk unsupported claim ({claim})")

    # Student/parent-facing plans must not expose the team's working vocabulary.
    # These concepts may remain in the internal ledger/manifest, but the external
    # copy must translate them into natural, useful language.
    internal_working_patterns = (
        ("文档定位", r"文档定位\s*[：:]"),
        ("版本", r"(?:^|[\n。；])\s*版本\s*[：:]"),
        ("配套资料", r"配套资料\s*[：:]"),
        ("事实底稿", r"事实底稿"),
        ("顾问判断", r"顾问判断"),
        ("Confirmed", r"(?<![A-Za-z])Confirmed(?![A-Za-z])"),
        ("Externally verified", r"(?<![A-Za-z])Externally\s+verified(?![A-Za-z])"),
        ("Inferred", r"(?<![A-Za-z])Inferred(?![A-Za-z])"),
        ("Open", r"(?<![A-Za-z])Open(?![A-Za-z])"),
        ("HC", r"(?<![A-Za-z])HC(?![A-Za-z])"),
        ("非已获机会", r"非已获机会"),
        ("资料边界", r"资料边界"),
        ("不包装成", r"不包装成"),
        ("不得使用虚构", r"不得使用虚构"),
    )
    for label, pattern in internal_working_patterns:
        if re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
            errors.append(
                f"career_plan: external copy contains internal working language ({label})"
            )
    return errors


def _validate_full_plan_readback(
    payload: dict[str, Any],
    career_plan: dict[str, Any],
    manifest_dir: Path,
    text: str,
) -> list[str]:
    """Require observable evidence that a full plan is not a short outline."""
    errors: list[str] = []
    checks = payload.get("full_plan_checks")
    if not isinstance(checks, dict):
        return ["career_plan readback: missing full plan checks"]

    text_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    if payload.get("markdown_sha256") != text_sha256:
        errors.append("career_plan readback: live text sha256 mismatch")
    if len(re.sub(r"\s+", "", text)) < 12000:
        errors.append("career_plan readback: full plan is too short")

    # Feishu Markdown exports use H1 for the document title and H2 for main
    # chapters, while plain authoring fixtures may use H1 chapters directly.
    # Anchor the chapter level to the core-positioning heading instead of
    # assuming a fixed Markdown level.
    main_level_match = re.search(
        r"(?m)^(#{1,3})(?!#)\s+[^\n]*(?:核心定位|求职定位)[^\n]*$",
        text,
    )
    main_level = len(main_level_match.group(1)) if main_level_match else 1
    main_hashes = "#" * main_level
    main_heading_pattern = rf"(?m)^{re.escape(main_hashes)}(?!#)\s+"

    section_count = checks.get("main_section_count")
    if not isinstance(section_count, int) or not 12 <= section_count <= 18:
        errors.append("career_plan readback: full plan must have 12-18 main sections")
    observed_section_count = len(re.findall(main_heading_pattern, text))
    if section_count != observed_section_count:
        errors.append("career_plan readback: main section count does not match live text")

    jd_section_match = re.search(
        rf"(?ms)^{re.escape(main_hashes)}(?!#)[^\n]*(?:代表性真实\s*JD|真实\s*JD\s*对照|代表性岗位参考)[^\n]*\n(.*?)(?=^{re.escape(main_hashes)}(?!#)\s+|\Z)",
        text,
    )
    jd_section = jd_section_match.group(1) if jd_section_match else ""
    observed_jd_urls = {
        url.rstrip(".,;，。；>)")
        for url in re.findall(r"https?://[^\s)<>]+", jd_section)
    }

    jd_count = checks.get("jd_count_observed")
    if not isinstance(jd_count, int) or not 6 <= jd_count <= 10:
        errors.append("career_plan readback: full plan must contain 6-10 verified JDs")
    if jd_count != len(observed_jd_urls):
        errors.append("career_plan readback: JD count does not match live text")
    jd_heading = jd_section_match.group(0).splitlines()[0] if jd_section_match else ""
    if not re.search(r"20\d{2}(?:-\d{2}-\d{2}|年\d{1,2}月\d{1,2}日)", jd_heading):
        errors.append("career_plan readback: JD section missing access date")
    jd_rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in jd_section.splitlines()
        if "http://" in line or "https://" in line
    ]
    table_rows_complete = len(jd_rows) == len(observed_jd_urls) and not any(
        len(row) < 5 or any(len(re.sub(r"\s+", "", cell)) < 2 for cell in row[:5])
        for row in jd_rows
    )
    card_heading_pattern = re.compile(
        rf"(?m)^#{{{main_level + 1},6}}(?!#)\s+[^\n]+$"
    )
    card_matches = list(card_heading_pattern.finditer(jd_section))
    jd_cards: list[str] = []
    for index, match in enumerate(card_matches):
        end = card_matches[index + 1].start() if index + 1 < len(card_matches) else len(jd_section)
        card = jd_section[match.start():end]
        if re.search(r"https?://[^\s)<>]+", card):
            jd_cards.append(card)
    card_rows_complete = len(jd_cards) == len(observed_jd_urls) and all(
        contains_any(card, terms)
        for card in jd_cards
        for terms in (
            ("类型与地点", "岗位类型", "地点"),
            ("主要任务", "核心工作", "培养重点"),
            ("门槛与加分项", "硬门槛", "任职要求"),
            ("匹配与差距", "匹配点"),
            ("投递判断", "申请判断"),
        )
    )
    if not table_rows_complete and not card_rows_complete:
        errors.append("career_plan readback: JD rows missing task, match, gap, and decision detail")
    approved_domains = career_plan.get("jd_official_domains")
    if not isinstance(approved_domains, list) or not approved_domains or not all(
        isinstance(domain, str) and domain.strip() for domain in approved_domains
    ):
        errors.append("career_plan: missing official JD domains")
    else:
        normalized_domains = [domain.lower().strip(".") for domain in approved_domains]
        for url in observed_jd_urls:
            hostname = (urlparse(url).hostname or "").lower()
            if not any(
                hostname == domain or hostname.endswith(f".{domain}")
                for domain in normalized_domains
            ):
                errors.append(f"career_plan readback: JD URL outside official domains ({hostname})")

    observed_project_count = len(
        re.findall(r"(?m)^#{1,3}\s+[^\n]*项目\s*[一二三四1234](?:[：:]|\b)", text)
    )

    project_count = checks.get("project_count_observed")
    if not isinstance(project_count, int) or project_count < 2:
        errors.append("career_plan readback: full plan must contain at least two projects")
    if project_count != observed_project_count:
        errors.append("career_plan readback: project count does not match live text")
    project_heading_pattern = re.compile(
        r"(?m)^(#{1,3})\s+[^\n]*项目\s*[一二三四1234](?:[：:]|\b)[^\n]*$"
    )
    project_matches = list(project_heading_pattern.finditer(text))
    project_sections: list[str] = []
    for index, match in enumerate(project_matches):
        level = len(match.group(1))
        boundary = re.search(
            rf"(?m)^#{{1,{level}}}\s+",
            text[match.end():],
        )
        end = match.end() + boundary.start() if boundary else len(text)
        project_sections.append(text[match.start():end])
    project_depth_groups = (
        ("status", ("项目状态", "当前状态", "建议完成周期")),
        ("target role", ("对应岗位", "目标岗位", "优先服务于")),
        ("scenario", ("场景", "用户任务", "业务问题", "科研问题")),
        ("modules", ("核心模块", "系统模块")),
        (
            "personal work",
            ("个人必须完成", "本人必须完成", "学生必须完成", "个人需要完成"),
        ),
        ("deliverables", ("交付物与验收", "产出与验收", "交付与验收")),
        (
            "resume expression",
            ("完成后简历表达", "简历表达模板", "简历表达方向"),
        ),
        (
            "interview use",
            ("面试用途", "产品面", "技术面", "面试追问", "面试可回答"),
        ),
    )
    for group_name, terms in project_depth_groups:
        if not project_sections or any(not contains_any(section, terms) for section in project_sections):
            errors.append(f"career_plan readback: project sections missing {group_name}")

    observed_resume_versions = set(re.findall(r"\bV[1-9]\b", text, flags=re.IGNORECASE))

    resume_count = checks.get("resume_version_count_observed")
    if not isinstance(resume_count, int) or not 2 <= resume_count <= 3:
        errors.append("career_plan readback: full plan must contain 2-3 resume versions")
    if resume_count != len(observed_resume_versions):
        errors.append("career_plan readback: resume version count does not match live text")
    resume_section_match = re.search(
        rf"(?ms)^{re.escape(main_hashes)}(?!#)[^\n]*(?:简历版本|简历与求职材料)[^\n]*\n(.*?)(?=^{re.escape(main_hashes)}(?!#)\s+|\Z)",
        text,
    )
    resume_section = resume_section_match.group(1) if resume_section_match else ""
    if not all(
        contains_any(resume_section, terms)
        for terms in (
            ("主投岗位", "目标岗位"),
            ("重点突出", "重点内容"),
            ("经历排序", "材料排序", "前置"),
            ("弱化内容", "弱化", "减少"),
        )
    ):
        errors.append("career_plan readback: resume versions missing role-emphasis-order-boundary detail")

    observed_internship_stages = sum(
        bool(re.search(pattern, text))
        for pattern in (
            r"第一段实习|第一阶段",
            r"第二段实习|第二阶段",
            r"第三段(?:\s*/\s*暑期)?实习|第三阶段",
        )
    )

    internship_count = checks.get("internship_stage_count_observed")
    if not isinstance(internship_count, int) or internship_count < 3:
        errors.append("career_plan readback: full plan must contain three internship stages")
    if internship_count != observed_internship_stages:
        errors.append("career_plan readback: internship stage count does not match live text")
    internship_section_match = re.search(
        rf"(?ms)^{re.escape(main_hashes)}(?!#)[^\n]*(?:三段实习|实习与校招路径|经历积累与校招路径)[^\n]*\n(.*?)(?=^{re.escape(main_hashes)}(?!#)\s+|\Z)",
        text,
    )
    internship_section = internship_section_match.group(1) if internship_section_match else ""
    if not all(
        contains_any(internship_section, terms)
        for terms in (
            ("时间", "阶段时间"),
            ("目标岗位", "岗位"),
            ("公司层级", "公司类型", "目标岗位与公司"),
            ("必须获得的证据", "岗位证据"),
            ("退出条件", "转段条件"),
        )
    ):
        errors.append("career_plan readback: internship path missing time-role-company-evidence-exit detail")

    has_90_day_plan = bool(re.search(r"90\s*天", text))
    if checks.get("has_90_day_plan") is not True or not has_90_day_plan:
        errors.append("career_plan readback: missing 90-day plan")
    has_graduation_timeline = bool(
        re.search(
            rf"(?m)^{re.escape(main_hashes)}(?!#)[^\n]*(?:(?:毕业前|20\d{{2}}\s*[—–-]\s*20\d{{2}})[^\n]*时间线|20\d{{2}}\s*[—–-]\s*20\d{{2}}[^\n]*校招路径)",
            text,
        )
    )
    if checks.get("has_graduation_timeline") is not True or not has_graduation_timeline:
        errors.append("career_plan readback: missing graduation timeline")

    route_keys = career_plan.get("required_route_keys")
    if not isinstance(route_keys, list) or len(route_keys) < 2 or not all(
        isinstance(key, str) and key.strip() for key in route_keys
    ):
        errors.append("career_plan: full plan requires at least two route keys")
    elif len(set(route_keys)) != len(route_keys):
        errors.append("career_plan: required route keys must be unique")
    else:
        coverage = checks.get("route_coverage")
        if not isinstance(coverage, dict):
            errors.append("career_plan readback: missing route coverage")
        else:
            route_requirements = (
                ("jd_count_observed", "JD coverage"),
                ("project_count_observed", "project coverage"),
                ("resume_version_count_observed", "resume coverage"),
            )
            marker_sets: dict[str, set[str]] = {
                "JD": set(),
                "project": set(),
                "resume": set(),
                "adjustment": set(),
            }
            duplicate_marker_types: set[str] = set()
            for key in route_keys:
                route = coverage.get(key)
                if not isinstance(route, dict):
                    errors.append(f"career_plan readback: route {key} missing coverage")
                    continue
                route_label = route.get("label")
                if not isinstance(route_label, str) or not route_label.strip() or route_label not in text:
                    errors.append(f"career_plan readback: route {key} label not found")
                marker_requirements = (
                    ("jd_markers", "JD", jd_section),
                    ("project_markers", "project", text),
                    ("resume_markers", "resume", text),
                    ("adjustment_markers", "adjustment", text),
                )
                for marker_field, marker_label, marker_text in marker_requirements:
                    markers = route.get(marker_field)
                    if not isinstance(markers, list) or not markers or not all(
                        isinstance(marker, str) and marker.strip() for marker in markers
                    ):
                        errors.append(
                            f"career_plan readback: route {key} missing {marker_label} markers"
                        )
                        continue
                    if not all(marker in marker_text for marker in markers):
                        errors.append(
                            f"career_plan readback: route {key} {marker_label} markers not found"
                        )
                    normalized_markers = set(markers)
                    if marker_sets[marker_label].intersection(normalized_markers):
                        duplicate_marker_types.add(marker_label)
                    marker_sets[marker_label].update(normalized_markers)
                for field, label in route_requirements:
                    value = route.get(field)
                    if not isinstance(value, int) or value < 1:
                        errors.append(
                            f"career_plan readback: route {key} missing {label}"
                        )
                    marker_field = {
                        "jd_count_observed": "jd_markers",
                        "project_count_observed": "project_markers",
                        "resume_version_count_observed": "resume_markers",
                    }[field]
                    markers = route.get(marker_field)
                    if isinstance(value, int) and isinstance(markers, list) and value != len(set(markers)):
                        errors.append(
                            f"career_plan readback: route {key} {label} count mismatch"
                        )
                if route.get("adjustment_conditions_present") is not True:
                    errors.append(
                        f"career_plan readback: route {key} missing adjustment conditions"
                    )
            for marker_label in sorted(duplicate_marker_types):
                errors.append(
                    f"career_plan readback: route {marker_label.lower()} markers must be unique"
                )

    pdf_path = _resolve_local_path(career_plan.get("rendered_pdf_path"), manifest_dir)
    pages_dir = _resolve_local_path(career_plan.get("rendered_pages_dir"), manifest_dir)
    rendered_pages = payload.get("rendered_pdf_pages")
    reported_images = payload.get("rendered_page_image_count")
    actual_pdf_pages: int | None = None
    if pdf_path is None or not pdf_path.is_file():
        errors.append("career_plan readback: rendered PDF is missing")
    else:
        actual_pdf_sha256 = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
        if payload.get("rendered_pdf_sha256") != actual_pdf_sha256:
            errors.append("career_plan readback: rendered PDF sha256 mismatch")
        pdfinfo = shutil.which("pdfinfo")
        if pdfinfo is None:
            errors.append("career_plan readback: pdfinfo is unavailable")
        else:
            completed = subprocess.run(
                [pdfinfo, str(pdf_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            match = re.search(r"(?m)^Pages:\s*(\d+)\s*$", completed.stdout)
            if completed.returncode != 0 or match is None:
                errors.append("career_plan readback: rendered PDF is invalid")
            else:
                actual_pdf_pages = int(match.group(1))
                if actual_pdf_pages != rendered_pages:
                    errors.append("career_plan readback: PDF page count mismatch")
    image_sha256_by_page: dict[int, str] = {}
    if pages_dir is None or not pages_dir.is_dir():
        errors.append("career_plan readback: rendered page images are missing")
    else:
        def page_number(path: Path) -> int:
            match = re.search(r"(\d+)(?=\.png$)", path.name)
            return int(match.group(1)) if match else 0

        png_paths = sorted(pages_dir.glob("*.png"), key=page_number)
        actual_images = len(png_paths)
        if (
            not isinstance(rendered_pages, int)
            or rendered_pages < 1
            or reported_images != rendered_pages
            or actual_images != rendered_pages
        ):
            errors.append("career_plan readback: rendered page image count mismatch")
        for png_path in png_paths:
            header = png_path.read_bytes()[:24]
            width = int.from_bytes(header[16:20], "big") if len(header) >= 24 else 0
            height = int.from_bytes(header[20:24], "big") if len(header) >= 24 else 0
            is_valid_png = (
                len(header) == 24
                and header[:8] == b"\x89PNG\r\n\x1a\n"
                and header[12:16] == b"IHDR"
                and width >= 600
                and height >= 800
            )
            if not is_valid_png:
                errors.append(
                    f"career_plan readback: invalid rendered PNG {png_path.name}"
                )
            else:
                image_sha256_by_page[page_number(png_path)] = hashlib.sha256(
                    png_path.read_bytes()
                ).hexdigest()

        pdftoppm = shutil.which("pdftoppm")
        if pdf_path is not None and pdf_path.is_file():
            if pdftoppm is None:
                errors.append("career_plan readback: pdftoppm is unavailable")
            else:
                with tempfile.TemporaryDirectory() as temp_dir:
                    render_prefix = Path(temp_dir) / "page"
                    completed = subprocess.run(
                        [pdftoppm, "-png", "-r", "90", str(pdf_path), str(render_prefix)],
                        check=False,
                        capture_output=True,
                    )
                    rerendered = sorted(Path(temp_dir).glob("page-*.png"), key=page_number)
                    rerendered_hashes = [
                        hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in rerendered
                    ]
                    saved_hashes = [
                        hashlib.sha256(path.read_bytes()).hexdigest()
                        for path in png_paths
                    ]
                    if completed.returncode != 0 or rerendered_hashes != saved_hashes:
                        errors.append("career_plan readback: rendered page images do not match PDF")
    if payload.get("visual_qa_pass") is not True:
        errors.append("career_plan readback: PDF visual QA not verified")
    page_checks = payload.get("visual_qa_pages")
    expected_page_numbers = set(range(1, rendered_pages + 1)) if isinstance(rendered_pages, int) else set()
    observed_page_numbers = set()
    per_page_valid = isinstance(page_checks, list) and len(page_checks) == len(expected_page_numbers)
    if isinstance(page_checks, list):
        for item in page_checks:
            if not isinstance(item, dict) or item.get("status") != "passed" or not isinstance(item.get("page"), int):
                per_page_valid = False
                continue
            page = item["page"]
            observed_page_numbers.add(page)
            required_checks = {"clipping", "readability", "layout"}
            checked_items = item.get("checked_items")
            issues = item.get("issues")
            if (
                item.get("image_sha256") != image_sha256_by_page.get(page)
                or not isinstance(checked_items, list)
                or not required_checks.issubset(set(checked_items))
                or not isinstance(issues, list)
            ):
                per_page_valid = False
    if not per_page_valid or observed_page_numbers != expected_page_numbers:
        errors.append("career_plan readback: per-page visual QA is incomplete")
    return errors


def _validate_standard_plan_readback(
    payload: dict[str, Any],
    career_plan: dict[str, Any],
    text: str,
) -> list[str]:
    """Validate the decision-focused default plan without forcing deep-report length."""
    errors: list[str] = []
    checks = payload.get("standard_plan_checks")
    if not isinstance(checks, dict):
        return ["career_plan readback: missing standard plan checks"]

    route_keys = career_plan.get("required_route_keys")
    if not isinstance(route_keys, list) or not 1 <= len(route_keys) <= 3 or not all(
        isinstance(key, str) and key.strip() for key in route_keys
    ):
        errors.append("career_plan: standard plan requires 1-3 route keys")
        route_keys = []
    elif len(set(route_keys)) != len(route_keys):
        errors.append("career_plan: required route keys must be unique")

    direction_count = checks.get("direction_count_observed")
    if direction_count != len(route_keys):
        errors.append("career_plan readback: direction count does not match route keys")

    coverage = checks.get("route_coverage")
    marker_requirements = (
        ("daily_work_markers", "daily work", 1),
        ("fit_markers", "fit reason", 1),
        ("role_markers", "representative roles", 1),
        ("salary_markers", "salary", 1),
        ("company_markers", "company pool", 2),
    )
    if not isinstance(coverage, dict):
        errors.append("career_plan readback: missing standard route coverage")
    else:
        for key in route_keys:
            route = coverage.get(key)
            if not isinstance(route, dict):
                errors.append(f"career_plan readback: route {key} missing coverage")
                continue
            label = route.get("label")
            if not isinstance(label, str) or not label.strip() or label not in text:
                errors.append(f"career_plan readback: route {key} label not found")
            for field, label_name, minimum_count in marker_requirements:
                markers = route.get(field)
                if (
                    not isinstance(markers, list)
                    or len(set(markers)) < minimum_count
                    or not all(isinstance(marker, str) and marker.strip() for marker in markers)
                ):
                    errors.append(
                        f"career_plan readback: route {key} missing {label_name} markers"
                    )
                    continue
                if not all(marker in text for marker in markers):
                    errors.append(
                        f"career_plan readback: route {key} {label_name} markers not found"
                    )

    salary_reference_date = checks.get("salary_reference_date")
    if (
        not isinstance(salary_reference_date, str)
        or not salary_reference_date.strip()
        or salary_reference_date not in text
    ):
        errors.append("career_plan readback: salary reference date not found")

    company_pool = checks.get("company_pool")
    if not isinstance(company_pool, dict):
        errors.append("career_plan readback: missing company pool checks")
    else:
        if company_pool.get("current_samples_separated_from_research_pool") is not True:
            errors.append(
                "career_plan readback: current samples and research pool are not separated"
            )
        if not contains_any(text, ("岗位样本", "近期样本", "当前样本")) or not contains_any(
            text, ("长期研究池", "长期关注", "持续关注")
        ):
            errors.append(
                "career_plan readback: company pool boundary not found in live text"
            )

    if career_plan.get("requires_agent_company_split") is True:
        split = checks.get("agent_company_split")
        if not isinstance(split, dict):
            errors.append("career_plan readback: missing Agent company split")
        else:
            for field, label_name in (
                ("bigtech_markers", "big-tech"),
                ("sme_markers", "small-and-medium or vertical"),
            ):
                markers = split.get(field)
                if (
                    not isinstance(markers, list)
                    or len(set(markers)) < 2
                    or not all(isinstance(marker, str) and marker.strip() for marker in markers)
                ):
                    errors.append(
                        f"career_plan readback: Agent {label_name} company markers missing"
                    )
                elif not all(marker in text for marker in markers):
                    errors.append(
                        f"career_plan readback: Agent {label_name} company markers not found"
                    )
            if split.get("role_tier_boundary_present") is not True:
                errors.append("career_plan readback: Agent role-tier boundary missing")

    expected_project_count = career_plan.get("expected_project_count")
    observed_project_count = len(
        re.findall(r"(?m)^#{1,4}\s+[^\n]*项目\s*[一二三四1234](?:[：:]|\b)", text)
    )
    if not isinstance(expected_project_count, int) or expected_project_count < 0:
        errors.append("career_plan: standard plan missing expected project count")
    elif observed_project_count != expected_project_count:
        errors.append("career_plan readback: project count does not match live text")

    headings = [
        (match.start(), match.group(1).strip())
        for match in re.finditer(r"(?m)^#{1,4}\s+([^\n]+)$", text)
    ]

    def first_heading(*terms: str) -> int | None:
        return next(
            (position for position, heading in headings if any(term in heading for term in terms)),
            None,
        )

    project_pos = first_heading("补强项目", "项目一", "项目 1", "项目规划")
    resume_pos = first_heading("简历版本", "定向简历", "简历规划")
    application_pos = first_heading("投递策略", "投递与面试", "正式投递")
    if expected_project_count and (
        project_pos is None
        or resume_pos is None
        or application_pos is None
        or not project_pos < resume_pos < application_pos
    ):
        errors.append(
            "career_plan readback: project-resume-application sequence is wrong"
        )
    if expected_project_count and not contains_any(
        text, ("最小可演示", "进入简历条件", "通过复盘后", "达到可演示")
    ):
        errors.append("career_plan readback: project-to-resume gate is missing")
    return errors


def _validate_source_fidelity(
    payload: dict[str, Any],
    career_plan: dict[str, Any],
    expected: dict[str, Any],
    manifest_dir: Path,
    live_text: str,
) -> list[str]:
    """Protect an approved local artifact from being summarized during Feishu delivery."""
    errors: list[str] = []
    fidelity = career_plan.get("source_fidelity")
    required = expected.get("require_source_fidelity") is True
    if not isinstance(fidelity, dict):
        return (
            ["career_plan source fidelity: missing protected source contract"]
            if required
            else []
        )

    artifact_path = _resolve_local_path(
        fidelity.get("authoritative_artifact_path"), manifest_dir
    )
    if artifact_path is None or not artifact_path.is_file():
        errors.append("career_plan source fidelity: authoritative artifact is missing")
    else:
        artifact_sha256 = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
        if fidelity.get("authoritative_artifact_sha256") != artifact_sha256:
            errors.append(
                "career_plan source fidelity: authoritative artifact sha256 mismatch"
            )

    source_path = _resolve_local_path(
        fidelity.get("authoritative_text_path"), manifest_dir
    )
    authoritative_text = ""
    if source_path is None or not source_path.is_file():
        errors.append("career_plan source fidelity: authoritative text is missing")
    else:
        try:
            authoritative_text = source_path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            errors.append("career_plan source fidelity: authoritative text is unreadable")

    marker_groups = fidelity.get("protected_marker_groups")
    if not isinstance(marker_groups, list) or not marker_groups:
        errors.append("career_plan source fidelity: protected marker groups are missing")
    else:
        for group in marker_groups:
            if not isinstance(group, dict):
                errors.append("career_plan source fidelity: invalid protected marker group")
                continue
            label = str(group.get("label", "unnamed")).strip() or "unnamed"
            markers = group.get("markers")
            if (
                not isinstance(markers, list)
                or not markers
                or not all(isinstance(marker, str) and marker.strip() for marker in markers)
            ):
                errors.append(
                    f"career_plan source fidelity: invalid protected markers ({label})"
                )
                continue
            for marker in markers:
                if authoritative_text and marker not in authoritative_text:
                    errors.append(
                        "career_plan source fidelity: protected marker missing from "
                        f"authoritative text ({label}: {marker})"
                    )
                if marker not in live_text:
                    errors.append(
                        "career_plan source fidelity: protected marker missing from "
                        f"live text ({label}: {marker})"
                    )

    required_visual_ids = fidelity.get("required_visual_ids")
    if not isinstance(required_visual_ids, list) or not required_visual_ids or not all(
        isinstance(visual_id, str) and visual_id.strip()
        for visual_id in required_visual_ids
    ):
        errors.append("career_plan source fidelity: required visual IDs are missing")
    else:
        checks = payload.get("source_fidelity_checks")
        blocks = checks.get("visual_media_blocks") if isinstance(checks, dict) else None
        observed = {
            item.get("visual_id")
            for item in blocks
            if isinstance(item, dict)
            and isinstance(item.get("visual_id"), str)
            and isinstance(item.get("token"), str)
            and item["token"].strip()
        } if isinstance(blocks, list) else set()
        for visual_id in required_visual_ids:
            if visual_id not in observed:
                errors.append(
                    "career_plan source fidelity: required Feishu visual missing "
                    f"({visual_id})"
                )
    return errors


def _load_readback(manifest: dict[str, Any], manifest_dir: Path) -> tuple[dict[str, Any] | None, list[str]]:
    raw_path = manifest.get("readback_path")
    if not raw_path:
        return None, ["manifest: missing readback_path"]
    path = _resolve_local_path(raw_path, manifest_dir)
    if path is None:
        return None, ["manifest: missing readback_path"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, [f"manifest: cannot read valid Feishu readback ({exc})"]
    if not isinstance(payload, dict):
        return None, ["manifest: Feishu readback root must be an object"]
    return payload, []


def _validate_parent_observation(
    payload: dict[str, Any], expected_parent_token: Any, label: str
) -> list[str]:
    """Validate evidence read from Feishu, not a copied manifest assertion."""
    errors: list[str] = []
    source = payload.get("parent_relation_source")
    if source not in {"wiki-node-get", "sidebar-tree"}:
        return [f"{label} readback: missing independent parent observation"]

    if payload.get("observed_parent_node_token") != expected_parent_token:
        errors.append(f"{label} readback: observed parent mismatch")
    if not isinstance(payload.get("observed_parent_title"), str) or not payload[
        "observed_parent_title"
    ].strip():
        errors.append(f"{label} readback: observed parent title missing")

    if source == "sidebar-tree":
        node_level = payload.get("observed_node_level")
        parent_level = payload.get("observed_parent_level")
        node_pos = payload.get("observed_node_pos")
        parent_pos = payload.get("observed_parent_node_pos")
        positions_are_strings = isinstance(node_pos, str) and isinstance(
            parent_pos, str
        )
        if (
            not isinstance(node_level, int)
            or not isinstance(parent_level, int)
            or node_level != parent_level + 1
            or not positions_are_strings
        ):
            errors.append(f"{label} readback: sidebar tree does not prove direct parent")
        else:
            node_parts = [part.strip() for part in node_pos.split(",") if part.strip()]
            parent_parts = [
                part.strip() for part in parent_pos.split(",") if part.strip()
            ]
            if (
                len(node_parts) != len(parent_parts) + 1
                or node_parts[: len(parent_parts)] != parent_parts
            ):
                errors.append(
                    f"{label} readback: sidebar tree does not prove direct parent"
                )
    return errors


def _validate_feishu_readback(
    readback: dict[str, Any],
    whitepaper: dict[str, Any] | None,
    career_plan: dict[str, Any],
    expected: dict[str, Any],
    manifest_dir: Path,
    career_plan_text: str,
) -> list[str]:
    errors: list[str] = []
    if readback.get("method") not in {"lark-cli", "browser"}:
        errors.append("readback: missing supported verification method")
    if not isinstance(readback.get("read_at"), str) or not readback["read_at"].strip():
        errors.append("readback: missing verification timestamp")

    whitepaper_rb = readback.get("whitepaper")
    if whitepaper is not None and not isinstance(whitepaper_rb, dict):
        errors.append("whitepaper readback: missing object")
    elif whitepaper is not None:
        if whitepaper_rb.get("url") != whitepaper.get("url"):
            errors.append("whitepaper readback: URL mismatch")
        if whitepaper_rb.get("title") != whitepaper.get("title"):
            errors.append("whitepaper readback: title mismatch")
        if whitepaper_rb.get("parent_node_token") != expected.get("whitepaper_parent_node_token"):
            errors.append("whitepaper readback: wrong direct parent")
        if whitepaper_rb.get("direct_parent_verified") is not True:
            errors.append("whitepaper readback: direct parent was not verified")
        errors.extend(
            _validate_parent_observation(
                whitepaper_rb,
                expected.get("whitepaper_parent_node_token"),
                "whitepaper",
            )
        )
        if whitepaper_rb.get("duplicate_page_count") != 1:
            errors.append("whitepaper readback: duplicate or missing page")
        if whitepaper_rb.get("unexpected_blank_sibling_count") != 0:
            errors.append("whitepaper readback: unexpected blank sibling page")
        if whitepaper_rb.get("source_first_marker_present") is not True or whitepaper_rb.get(
            "source_last_marker_present"
        ) is not True:
            errors.append("whitepaper readback: source range was not verified")
        if whitepaper_rb.get("source_count_observed") != whitepaper.get("source_count"):
            errors.append("whitepaper readback: source count mismatch")
        whitepaper_sections_present = whitepaper_rb.get("required_sections_present")
        whitepaper_sections_total = whitepaper_rb.get("required_sections_total")
        if (
            not isinstance(whitepaper_sections_present, int)
            or not isinstance(whitepaper_sections_total, int)
            or whitepaper_sections_total < 4
            or whitepaper_sections_present != whitepaper_sections_total
        ):
            errors.append("whitepaper readback: required sections incomplete")

    career_plan_rb = readback.get("career_plan")
    if not isinstance(career_plan_rb, dict):
        errors.append("career_plan readback: missing object")
        return errors

    if career_plan_rb.get("url") != career_plan.get("url"):
        errors.append("career_plan readback: URL mismatch")
    if career_plan_rb.get("title") != career_plan.get("title"):
        errors.append("career_plan readback: title mismatch")
    if career_plan_rb.get("parent_node_token") != expected.get("career_plan_parent_node_token"):
        errors.append("career_plan readback: wrong direct parent")
    if career_plan_rb.get("direct_parent_verified") is not True:
        errors.append("career_plan readback: direct parent was not verified")
    errors.extend(
        _validate_parent_observation(
            career_plan_rb,
            expected.get("career_plan_parent_node_token"),
            "career_plan",
        )
    )
    if career_plan_rb.get("duplicate_page_count") != 1:
        errors.append("career_plan readback: duplicate or missing page")
    if career_plan_rb.get("unexpected_blank_sibling_count") != 0:
        errors.append("career_plan readback: unexpected blank sibling page")
    if whitepaper is not None and career_plan_rb.get("whitepaper_url") != career_plan.get(
        "whitepaper_url"
    ):
        errors.append("career_plan readback: whitepaper link mismatch")
    if career_plan_rb.get("original_resume_attachment_count") != 1:
        errors.append(
            "career_plan readback: original resume attachment count is not one"
        )

    text_sha256 = hashlib.sha256(career_plan_text.encode("utf-8")).hexdigest()
    if career_plan_rb.get("markdown_sha256") != text_sha256:
        errors.append("career_plan readback: live text sha256 mismatch")

    errors.extend(
        _validate_source_fidelity(
            career_plan_rb,
            career_plan,
            expected,
            manifest_dir,
            career_plan_text,
        )
    )
    delivery_mode = career_plan.get("delivery_mode")
    expected_delivery_mode = expected.get("career_plan_delivery_mode")
    allowed_delivery_modes = {"full", "standard", "concise"}
    if delivery_mode not in allowed_delivery_modes:
        errors.append("career_plan: delivery_mode must be full, standard, or concise")
    elif expected_delivery_mode not in allowed_delivery_modes:
        errors.append("career_plan: missing expected delivery mode")
    elif delivery_mode != expected_delivery_mode:
        errors.append("career_plan: delivery_mode does not match expected mode")

    career_sections_present = career_plan_rb.get("required_sections_present")
    career_sections_total = career_plan_rb.get("required_sections_total")
    minimum_sections = {"full": 9, "standard": 8, "concise": 5}.get(
        delivery_mode, 9
    )
    if (
        not isinstance(career_sections_present, int)
        or not isinstance(career_sections_total, int)
        or career_sections_total < minimum_sections
        or career_sections_present != career_sections_total
    ):
        errors.append("career_plan readback: required sections incomplete")

    if delivery_mode == expected_delivery_mode == "full":
        errors.extend(
            _validate_full_plan_readback(
                career_plan_rb,
                career_plan,
                manifest_dir,
                career_plan_text,
            )
        )
    elif delivery_mode == expected_delivery_mode == "standard":
        errors.extend(
            _validate_standard_plan_readback(
                career_plan_rb,
                career_plan,
                career_plan_text,
            )
        )

    attachment = career_plan_rb.get("attachment")
    if not isinstance(attachment, dict):
        errors.append("career_plan readback: missing original resume file block")
        return errors
    if attachment.get("block_type") not in {"file", "source"}:
        errors.append("career_plan readback: attachment is not a file/source block")
    resume = career_plan.get("original_resume")
    expected_filename = resume.get("filename") if isinstance(resume, dict) else None
    if attachment.get("filename") != expected_filename:
        errors.append("career_plan readback: attachment filename mismatch")
    if attachment.get("position") != "first_page":
        errors.append("career_plan readback: original resume is not on first page")
    if attachment.get("preview_opened") is not True:
        errors.append("career_plan readback: attachment preview was not verified")
    return errors


def validate_manifest(manifest_path: Path) -> list[str]:
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"manifest: cannot read valid JSON ({exc})"]

    if not isinstance(manifest, dict):
        return ["manifest: root must be an object"]

    whitepaper = manifest.get("whitepaper")
    career_plan = manifest.get("career_plan")
    expected = manifest.get("expected")
    errors: list[str] = []
    if "whitepaper" in manifest and not isinstance(whitepaper, dict):
        errors.append("manifest: whitepaper must be an object when provided")
    if not isinstance(career_plan, dict):
        errors.append("manifest: missing career_plan object")
    if not isinstance(expected, dict):
        errors.append("manifest: missing expected object")
    if errors:
        return errors

    errors.extend(_validate_visual_manifest(manifest, manifest_path.parent))

    whitepaper_text = ""
    if isinstance(whitepaper, dict):
        whitepaper_text, text_errors = _resolve_text(
            whitepaper, manifest_path.parent, "whitepaper"
        )
        errors.extend(text_errors)
    career_plan_text, text_errors = _resolve_text(
        career_plan, manifest_path.parent, "career_plan"
    )
    errors.extend(text_errors)
    if errors:
        return errors

    if isinstance(whitepaper, dict):
        errors.extend(validate_whitepaper(whitepaper_text, whitepaper, expected))
    errors.extend(
        validate_career_plan(
            career_plan_text,
            career_plan,
            expected,
            manifest_path.parent,
            require_whitepaper=isinstance(whitepaper, dict),
        )
    )
    if isinstance(whitepaper, dict) and whitepaper.get("url") != career_plan.get(
        "whitepaper_url"
    ):
        errors.append("delivery: career plan links a different whitepaper URL")
    readback, readback_errors = _load_readback(manifest, manifest_path.parent)
    errors.extend(readback_errors)
    if readback is not None:
        errors.extend(
            _validate_feishu_readback(
                readback,
                whitepaper if isinstance(whitepaper, dict) else None,
                career_plan,
                expected,
                manifest_path.parent,
                career_plan_text,
            )
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Path to delivery manifest JSON")
    args = parser.parse_args(argv)
    errors = validate_manifest(args.manifest)
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
