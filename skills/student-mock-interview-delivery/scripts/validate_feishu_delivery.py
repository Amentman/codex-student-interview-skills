#!/usr/bin/env python3
"""Validate a mock-interview delivery by reading the current Feishu pages."""

import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET

from validate_delivery import (
    STUDENT_FORBIDDEN,
    STUDENT_SECTIONS,
    TEACHER_SECTIONS,
    TRACK_MARKERS,
    extract_and_validate_questions,
    require_sections,
    validate_anchors,
    validate_core_experiences,
    validate_jd_matrix,
    validate_metric_primer,
    validate_no_visual_placeholders,
    validate_tiers,
    validate_visual_order,
)


def local_name(tag):
    return tag.rsplit("}", 1)[-1]


def fetch_document(doc, doc_format, detail):
    command = [
        "lark-cli",
        "docs",
        "+fetch",
        "--doc",
        doc,
        "--doc-format",
        doc_format,
        "--detail",
        detail,
        "--as",
        "user",
        "--format",
        "json",
    ]
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "unknown lark-cli error"
        raise RuntimeError(message)
    try:
        payload = json.loads(result.stdout)
        if payload.get("ok") is False:
            raise RuntimeError(payload.get("message") or "lark-cli returned ok=false")
        document = payload["data"]["document"]
        return document["content"], document.get("revision_id")
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError("lark-cli returned an invalid document payload") from exc


def parse_document_xml(content, label, errors):
    fragment = content.strip()
    if fragment.startswith("<?xml"):
        fragment = fragment.split("?>", 1)[-1]
    try:
        wrapper = ET.fromstring(f"<root>{fragment}</root>")
    except ET.ParseError as exc:
        errors.append(f"{label} XML 无法解析: {exc}")
        return None, []

    children = list(wrapper)
    if len(children) == 1 and local_name(children[0].tag) in {"document", "fragment"}:
        children = list(children[0])
    title_node = next(
        (node for node in wrapper.iter() if local_name(node.tag) == "title"),
        None,
    )
    title = "" if title_node is None else "".join(title_node.itertext()).strip()
    body = [node for node in children if local_name(node.tag) != "title"]
    return title, body


def has_source(node):
    return any(local_name(child.tag) == "source" for child in node.iter())


def node_text(node):
    return "".join(node.itertext()).strip()


def visual_has_token(node):
    token_names = {"token", "file_token", "image_token", "src"}
    for current in node.iter():
        for key, value in current.attrib.items():
            if local_name(key) in token_names and str(value).strip():
                return True
    return False


def validate_page_structure(xml, label, expected_title, visual_boundary_title, errors):
    title, body = parse_document_xml(xml, label, errors)
    if title != expected_title:
        errors.append(f"{label}页面标题应为 {expected_title}，实际为 {title or '缺失'}")
    if not body or not has_source(body[0]):
        errors.append(f"{label}标题后的第一个正文块必须是原始简历附件")

    ordered_nodes = [node for block in body for node in block.iter()]
    if any(local_name(node.tag) == "h1" for node in ordered_nodes):
        errors.append(f"{label}正文不得包含 H1；页面原生标题是唯一 H1")

    visual_nodes = [
        node for node in ordered_nodes
        if local_name(node.tag) in {"whiteboard", "image", "img"}
    ]
    if not visual_nodes:
        errors.append(f"{label}至少一张可读项目图缺失")
    for node in visual_nodes:
        if not visual_has_token(node):
            errors.append(f"{label}包含空图片或画板 token")

    boundary_index = next(
        (
            index
            for index, node in enumerate(ordered_nodes)
            if local_name(node.tag) == "h2" and node_text(node) == visual_boundary_title
        ),
        None,
    )
    if boundary_index is not None and any(
        local_name(node.tag) in {"whiteboard", "image", "img"}
        for node in ordered_nodes[boundary_index + 1 :]
    ):
        errors.append(f"{label}项目图片或画板必须位于{visual_boundary_title}之前")


def validate_remote_documents(
    name,
    homepage_markdown,
    homepage_xml,
    teacher_markdown,
    teacher_xml,
    student_markdown,
    student_xml,
    track,
    forbid_names=(),
):
    errors = []
    internal_title = f"{name}｜面试指导者版（内部）"
    student_title = f"{name}｜学生面试准备版"

    homepage_title, _ = parse_document_xml(homepage_xml, "学生主页", errors)
    if homepage_title != name:
        errors.append(f"学生主页标题应为 {name}，实际为 {homepage_title or '缺失'}")
    for required_title in (internal_title, student_title):
        if required_title not in homepage_markdown and required_title not in homepage_xml:
            errors.append(f"学生主页缺少子页用途或入口: {required_title}")

    for label, text in (("老师版", teacher_markdown), ("学生版", student_markdown)):
        if name not in text:
            errors.append(f"{label}未包含学生姓名: {name}")
        for forbidden in forbid_names:
            if forbidden in text:
                errors.append(f"{label}包含禁止姓名: {forbidden}")

    require_sections(teacher_markdown, TEACHER_SECTIONS, "老师版", errors)
    teacher_tiers = validate_tiers(teacher_markdown, "老师版", errors)
    validate_jd_matrix(teacher_markdown, errors)
    validate_anchors(teacher_markdown, errors)
    validate_core_experiences(teacher_markdown, errors)
    for marker in TRACK_MARKERS[track]:
        if marker not in teacher_markdown:
            errors.append(f"老师版缺少 {track} 路线标记: {marker}")
    teacher_questions = extract_and_validate_questions(
        teacher_markdown, "模拟面试问题与带教指引", "老师版", errors
    )
    validate_visual_order(
        teacher_markdown, "模拟面试流程", "老师版", errors
    )
    validate_no_visual_placeholders(teacher_markdown, "老师版", errors)

    require_sections(student_markdown, STUDENT_SECTIONS, "学生版", errors)
    student_tiers = validate_tiers(student_markdown, "学生版", errors)
    validate_metric_primer(
        student_markdown,
        errors,
        reference_texts=(teacher_markdown, student_markdown),
    )
    student_questions = extract_and_validate_questions(
        student_markdown, "面试问题与个人逐字稿", "学生版", errors
    )
    validate_visual_order(
        student_markdown, "面试问题与个人逐字稿", "学生版", errors
    )
    validate_no_visual_placeholders(student_markdown, "学生版", errors)
    for marker in STUDENT_FORBIDDEN:
        if marker in student_markdown:
            errors.append(f"学生版包含内部禁用标记: {marker}")

    if teacher_questions and student_questions and teacher_questions != student_questions:
        errors.append("老师版与学生版的题目标题或顺序不一致")
    if teacher_tiers and student_tiers and teacher_tiers != student_tiers:
        errors.append("老师版与学生版三档匹配 JD 的岗位或顺序不一致")

    validate_page_structure(
        teacher_xml,
        "老师版",
        internal_title,
        "模拟面试流程",
        errors,
    )
    validate_page_structure(
        student_xml,
        "学生版",
        student_title,
        "面试问题与个人逐字稿",
        errors,
    )
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--homepage", required=True)
    parser.add_argument("--internal", required=True)
    parser.add_argument("--student", required=True)
    parser.add_argument("--track", required=True, choices=tuple(TRACK_MARKERS))
    parser.add_argument("--forbid-name", action="append", default=[])
    args = parser.parse_args()

    errors = []
    documents = {
        "homepage": args.homepage,
        "internal": args.internal,
        "student": args.student,
    }
    snapshots = {}
    revision_ids = {}
    for label, doc in documents.items():
        snapshots[label] = {}
        for doc_format, detail in (("markdown", "simple"), ("xml", "full")):
            try:
                content, revision_id = fetch_document(doc, doc_format, detail)
                snapshots[label][doc_format] = content
                revision_ids[label] = revision_id
            except RuntimeError as exc:
                errors.append(f"{label} 飞书读回失败: {exc}")
                break

    if not errors:
        errors.extend(
            validate_remote_documents(
                args.name,
                snapshots["homepage"]["markdown"],
                snapshots["homepage"]["xml"],
                snapshots["internal"]["markdown"],
                snapshots["internal"]["xml"],
                snapshots["student"]["markdown"],
                snapshots["student"]["xml"],
                args.track,
                args.forbid_name,
            )
        )

    result = {
        "status": "ok" if not errors else "invalid",
        "errors": errors,
        "revision_ids": revision_ids,
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
