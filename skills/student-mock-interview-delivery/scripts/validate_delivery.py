#!/usr/bin/env python3
"""Validate evidence-grounded teacher and student mock-interview deliveries."""

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
QUESTION_RE = re.compile(r"^####\s+题目(\d+)｜(.+)$")
ANCHOR_RE = re.compile(
    r"^-\s+([A-Z]\d+)｜(Confirmed|Externally verified|Inferred|Knowledge supplement|Open)｜(.+)$"
)
MOBILE_RE = re.compile(r"(?<!\d)1[3-9]\d(?:[ -]?\d){8}(?!\d)")

TEACHER_SECTIONS = (
    "老师快速上手", "候选人业务主线", "三档匹配 JD", "JD逐条证据矩阵",
    "面试准备度与建议模式", "口述能力四级评分", "实习履历大白话拆解",
    "项目地图与必做产物", "数值反推", "职责边界", "事实账本",
    "个性化锚点清单", "故事证据与岗位补充", "核心经历深挖覆盖", "数值成果来源索引",
    "核心项目架构／图解", "模拟面试流程", "模拟面试问题与带教指引", "课后反馈模板",
)
STUDENT_SECTIONS = (
    "如何使用这份材料", "核心定位", "三档匹配 JD",
    "项目地图", "术语大白话卡", "指标口径扫盲", "岗位与行业知识", "故事证据与岗位补充",
    "核心项目架构／图解", "面试问题与个人逐字稿", "面试前任务",
)
QUESTION_CATEGORIES = (
    ("第一部分｜基础行为面", 6),
    ("第二部分｜宝洁八大问", 8),
    ("第三部分｜实习与项目深挖", 4),
    ("第四部分｜岗位专业题", 4),
)
TEACHER_FIELDS = (
    "考察目标", "表达类型", "合格回答要素", "候选人可用素材", "岗位场景补充", "参考回答方向",
    "继续追问", "常见问题", "反馈建议",
)
STUDENT_FIELDS = (
    "考察点", "表达类型", "你的答题主线", "事实或场景依据", "参考表达", "我的版本", "答题提示",
)
TIER_FIELDS = ("岗位日常", "匹配证据", "差距", "档位原因", "投递建议")
TIER_CARD_RE = re.compile(r"^###\s+(90%|80%|70%)｜(主投|稳妥拓展|进阶尝试)｜(.+)$")
CORE_EXPERIENCE_FIELDS = (
    "业务问题", "输入", "个人动作", "产物", "数字", "Bad Case", "职责边界", "对应题目",
)
TRACK_MARKERS = {
    "business": ("业务运营追问路线", "业务流程图", "指标与归因"),
    "product": ("AI 产品追问路线", "产品体验证据", "指标反推"),
    "technical": ("Agent 技术追问路线", "系统架构图", "异常与可观测"),
}
TRACK_MARKERS["mixed"] = TRACK_MARKERS["product"] + TRACK_MARKERS["technical"]
STUDENT_FORBIDDEN = (
    "**考察目标：**", "**合格回答要素：**", "**继续追问：**", "**常见问题：**",
    "**反馈建议：**", "评分表", "扣分规则", "内部事实核查", "面试官建议追问",
    "导师补充问题及使用说明", "面试官如何继续施压",
)
POST_SESSION_MARKERS = (
    "输入边界声明", "本轮实际问题", "答非所问与停顿", "稳定能力",
    "新增 Open", "简历调整", "下一轮重点问题", "学生任务卡",
)
MIN_QUESTIONS = 22
MAX_QUESTIONS = 32
EXPRESSION_TYPES = ("亲历表达", "迁移表达", "岗位知识", "场景推演")
MIN_STUDENT_REFERENCE = 24
MAX_STUDENT_REFERENCE = 450
STORY_FIELDS = (
    "来源", "场景／目标", "本人动作", "产物／结果", "职责边界", "失败／取舍", "学生原话／口述状态", "Open",
)
KNOWLEDGE_FIELDS = (
    "岗位通常怎么做", "为什么这样做", "常见例外／风险", "指标／验收", "与学生经历的连接", "表达边界",
)
VISUAL_SECTION_MARKERS = ("图解", "架构", "看图", "看懂")
METRIC_CARD_RE = re.compile(r"^###\s+指标(\d+)｜(.+)$")
METRIC_CARD_FIELDS = ("大白话", "怎么算／怎么看", "为什么重要", "容易误判", "候选人边界")
EXPLICIT_METRIC_RE = re.compile(r"【指标：([^】]+)】")
COMMON_METRIC_TERMS = tuple(sorted({
    "GMV", "ROI", "ROAS", "CTR", "CVR", "UV", "PV", "DAU", "MAU",
    "CAC", "LTV", "ARPU", "NPS",
    "推荐准确率", "商品信息问答准确率", "需求完成率", "委托转化率", "会话质量",
    "广告点击率", "商品点击率", "订单转化率", "加购率", "下单率", "转化率",
    "互动率", "完播率", "跳出率", "留存率", "复购率", "退款率", "取消率",
    "履约率", "完成率", "响应率", "召回率", "准确率", "采用率", "通过率",
    "流失率", "渗透率", "到店率", "核销率", "进店率", "收藏率", "缺货率",
    "毛利率", "库存周转率", "客单价", "获客成本", "成交额", "销售额", "订单量",
    "订单数", "曝光量", "点击量", "处理时效", "响应时长", "交付时长", "满意度",
}, key=len, reverse=True))
UNRESOLVED_VISUAL_MARKERS = (
    "待插入图片", "待补图", "图片生成中", "图片加载失败", "图片未生成",
)


def read_markdown(path, label, errors):
    if not path.is_file():
        errors.append(f"{label} 不存在: {path}")
        return None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        errors.append(f"{label} 不是 UTF-8 Markdown: {path}")
        return None


def exact_section(lines, level, title):
    target = "#" * level + " " + title
    for start, line in enumerate(lines):
        if line.strip() != target:
            continue
        for end in range(start + 1, len(lines)):
            match = HEADING_RE.match(lines[end].strip())
            if match and len(match.group(1)) <= level:
                return start, end
        return start, len(lines)
    return None


def visible_length(value):
    value = re.sub(r"\[[^]]+\]\([^)]+\)", "", value or "")
    value = re.sub(r"[`*_#>\-\s]", "", value)
    return len(value)


def field_value(block, field):
    match = re.search(
        rf"\*\*{re.escape(field)}：\*\*[ \t]*(.*?)(?=\n\*\*[^\n]+：\*\*|\Z)",
        block,
        re.S,
    )
    return match.group(1).strip() if match else None


def field_present(block, field):
    return bool(re.search(rf"\*\*{re.escape(field)}：\*\*", block))


def parse_question_cards(lines):
    starts = []
    for index, line in enumerate(lines):
        match = QUESTION_RE.match(line.strip())
        if match:
            starts.append((index, match))
    cards = []
    for position, (start, match) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        cards.append((match, "\n".join(lines[start:end])))
    return cards


def require_sections(text, sections, label, errors):
    lines = text.splitlines()
    for section in sections:
        if exact_section(lines, 2, section) is None:
            errors.append(f"{label}缺少精确标题: {section}")


def has_resume_link(text, resume_path, doc_path):
    first_lines = [line for line in text.splitlines() if line.strip()][:25]
    for target in re.findall(r"\[[^]\n]+\]\(([^)\n]+)\)", "\n".join(first_lines)):
        parsed = urlparse(target)
        target_path = Path(target)
        if parsed.scheme or parsed.netloc or target_path.is_absolute() or ".." in target_path.parts:
            continue
        if (doc_path.parent / target_path).resolve() == resume_path.resolve():
            return True
    return False


def markdown_data_rows(lines):
    rows = [
        line for line in lines
        if line.strip().startswith("|") and not re.match(r"^\|\s*[-:]", line.strip())
    ]
    return rows[1:] if rows else []


def validate_tiers(text, label, errors):
    lines = text.splitlines()
    if any(line.strip() in {"## 三档岗位画像", "## 主要岗位／JD卡"} for line in lines):
        errors.append(f"{label}三档匹配与三张 JD 不得拆分成两个章节")

    section_span = exact_section(lines, 2, "三档匹配 JD")
    if section_span is None:
        return []

    section = lines[section_span[0] + 1:section_span[1]]
    starts = [i for i, line in enumerate(section) if line.strip().startswith("### ")]
    if len(starts) != 3:
        errors.append(f"{label}三档匹配 JD 必须恰好包含 3 张 JD，实际 {len(starts)} 张")

    expected = (("90%", "主投"), ("80%", "稳妥拓展"), ("70%", "进阶尝试"))
    cards = []
    for position, start in enumerate(starts):
        heading = section[start].strip()
        match = TIER_CARD_RE.match(heading)
        if match is None:
            errors.append(
                f"{label}三档匹配 JD 标题格式错误: {heading}；"
                "应为 90%｜主投｜岗位名、80%｜稳妥拓展｜岗位名、70%｜进阶尝试｜岗位名"
            )
            continue
        score, tier_label, role = match.groups()
        cards.append((score, role.strip()))
        if position < len(expected) and (score, tier_label) != expected[position]:
            errors.append(f"{label}三档匹配 JD 必须按 90%、80%、70% 顺序排列")
        end = starts[position + 1] if position + 1 < len(starts) else len(section)
        block = "\n".join(section[start:end])
        missing = [field for field in TIER_FIELDS if not field_value(block, field)]
        if missing:
            errors.append(f"{label} {score} JD 卡缺少字段: {', '.join(missing)}")

    roles = [role for _, role in cards]
    if len(roles) != len(set(roles)):
        errors.append(f"{label}三档匹配 JD 的岗位名称不得重复")
    return cards


def validate_jd_matrix(text, errors):
    lines = text.splitlines()
    span = exact_section(lines, 2, "JD逐条证据矩阵")
    if span is None:
        return
    rows = markdown_data_rows(lines[span[0] + 1:span[1]])
    if len(rows) < 3:
        errors.append("老师版 JD逐条证据矩阵至少需要 3 条岗位要求")
    joined = "\n".join(rows)
    for grade in ("直接证据", "可迁移证据", "缺口"):
        if grade not in joined:
            errors.append(f"老师版 JD逐条证据矩阵缺少证据等级: {grade}")


def validate_anchors(text, errors):
    lines = text.splitlines()
    span = exact_section(lines, 2, "个性化锚点清单")
    if span is None:
        return
    anchors = [
        ANCHOR_RE.match(line.strip())
        for line in lines[span[0] + 1:span[1]]
        if ANCHOR_RE.match(line.strip())
    ]
    if len(anchors) < 3:
        errors.append("老师版 个性化锚点清单至少需要 3 条结构化锚点")
    if not any(match.group(2) == "Confirmed" for match in anchors):
        errors.append("老师版 个性化锚点清单至少需要 1 条 Confirmed 锚点")


def validate_story_knowledge_anchors(text, label, errors):
    """Validate reusable personal stories (S) and role knowledge (K)."""
    lines = text.splitlines()
    span = exact_section(lines, 2, "故事证据与岗位补充")
    if span is None:
        return set(), set()
    section = lines[span[0] + 1:span[1]]
    starts = [
        index for index, line in enumerate(section)
        if re.match(r"^###\s+[SK]\d+｜", line.strip())
    ]
    story_ids = set()
    knowledge_ids = set()
    for position, start in enumerate(starts):
        heading = section[start].strip()
        match = re.match(r"^###\s+([SK]\d+)｜(.+)$", heading)
        if match is None:
            continue
        anchor_id = match.group(1)
        target = story_ids if anchor_id.startswith("S") else knowledge_ids
        if anchor_id in target:
            errors.append(f"{label}故事证据与岗位补充存在重复锚点: {anchor_id}")
        target.add(anchor_id)
        end = starts[position + 1] if position + 1 < len(starts) else len(section)
        block = "\n".join(section[start:end])
        fields = STORY_FIELDS if anchor_id.startswith("S") else KNOWLEDGE_FIELDS
        missing = [field for field in fields if not field_value(block, field)]
        if missing:
            errors.append(f"{label} {anchor_id} 锚点缺少字段: {', '.join(missing)}")
    if not story_ids:
        errors.append(f"{label}故事证据与岗位补充至少需要 1 个 S 故事锚点")
    if not knowledge_ids:
        errors.append(f"{label}故事证据与岗位补充至少需要 1 个 K 岗位知识锚点")
    return story_ids, knowledge_ids


def validate_core_experiences(text, errors):
    lines = text.splitlines()
    span = exact_section(lines, 2, "核心经历深挖覆盖")
    if span is None:
        return
    section = lines[span[0] + 1:span[1]]
    starts = [i for i, line in enumerate(section) if re.match(r"^###\s+P\d+｜", line.strip())]
    if not starts:
        errors.append("老师版 核心经历深挖覆盖至少需要 1 张 Pxx 经历卡")
        return
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(section)
        block = "\n".join(section[start:end])
        missing = []
        for field in CORE_EXPERIENCE_FIELDS:
            match = re.search(rf"^-\s+{re.escape(field)}：[ \t]*(.+)$", block, re.M)
            if not match or visible_length(match.group(1)) < 2:
                missing.append(field)
        if missing:
            errors.append(f"老师版 {section[start].strip()} 缺少经历字段: {', '.join(missing)}")


def strip_metric_primer(text):
    """Remove the primer itself so metric cards do not satisfy their own references."""
    lines = text.splitlines()
    span = exact_section(lines, 2, "指标口径扫盲")
    if span is None:
        return text
    return "\n".join(lines[:span[0]] + lines[span[1]:])


def normalize_metric_name(value):
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]", "", value or "").lower()


def metric_card_aliases(card_name):
    aliases = {normalize_metric_name(card_name)}
    upper_name = card_name.upper()
    for term in COMMON_METRIC_TERMS:
        haystack = upper_name if term.isascii() else card_name
        needle = term.upper() if term.isascii() else term
        if needle in haystack:
            aliases.add(normalize_metric_name(term))
    return aliases


def extract_metric_references(reference_texts):
    """Collect common or explicitly marked metrics used outside the primer section."""
    found = []
    for text in reference_texts:
        if not text:
            continue
        source = strip_metric_primer(text)
        for group in EXPLICIT_METRIC_RE.findall(source):
            for name in re.split(r"[、,，/|]+", group):
                if normalize_metric_name(name):
                    found.append(name.strip())
        upper_source = source.upper()
        for term in COMMON_METRIC_TERMS:
            haystack = upper_source if term.isascii() else source
            needle = term.upper() if term.isascii() else term
            if needle in haystack:
                found.append(term)
    unique = []
    seen = set()
    for name in found:
        normalized = normalize_metric_name(name)
        if normalized not in seen:
            seen.add(normalized)
            unique.append(name)
    return unique


def validate_metric_primer(text, errors, reference_texts=()):
    """Require plain-language metric cards that explain both calculation and limits."""
    lines = text.splitlines()
    span = exact_section(lines, 2, "指标口径扫盲")
    if span is None:
        return
    section = lines[span[0] + 1:span[1]]
    starts = [i for i, line in enumerate(section) if METRIC_CARD_RE.match(line.strip())]
    if len(starts) < 3:
        errors.append(f"学生版 指标口径扫盲至少需要 3 张指标卡，实际 {len(starts)} 张")
    aliases = set()
    for position, start in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(section)
        block = "\n".join(section[start:end])
        match = METRIC_CARD_RE.match(section[start].strip())
        card_name = f"指标{match.group(1)}｜{match.group(2).strip()}"
        aliases.update(metric_card_aliases(match.group(2).strip()))
        missing = [field for field in METRIC_CARD_FIELDS if not field_value(block, field)]
        if missing:
            errors.append(f"学生版 {card_name} 缺少小白口径字段: {', '.join(missing)}")
    missing_references = [
        name for name in extract_metric_references(reference_texts)
        if normalize_metric_name(name) not in aliases
    ]
    if missing_references:
        errors.append(
            "学生版 指标口径扫盲缺少对应卡: " + "、".join(missing_references)
        )


def validate_no_visual_placeholders(text, label, errors):
    matches = [marker for marker in UNRESOLVED_VISUAL_MARKERS if marker in text]
    if matches:
        errors.append(f"{label}包含未解决的图片占位: {', '.join(matches)}")


def validate_question_categories(section_lines, label, errors):
    category_counts = {}
    current = None
    for line in section_lines:
        if line.startswith("### "):
            current = line.removeprefix("### ").strip()
            category_counts.setdefault(current, 0)
        elif QUESTION_RE.match(line.strip()) and current:
            category_counts[current] += 1
    for category, minimum in QUESTION_CATEGORIES:
        count = category_counts.get(category)
        if count is None:
            errors.append(f"{label}问题目录缺少分类: {category}")
        elif count < minimum:
            errors.append(f"{label}{category}至少需要 {minimum} 题，实际 {count}")


def validate_visual_order(text, boundary_section_title, label, errors):
    """Keep project teaching visuals before interview execution begins."""
    lines = text.splitlines()
    boundary_span = exact_section(lines, 2, boundary_section_title)
    if boundary_span is None:
        return
    boundary_start = boundary_span[0]
    late_visual_heading = any(
        line.strip().startswith("## ")
        and any(marker in line for marker in VISUAL_SECTION_MARKERS)
        for line in lines[boundary_start + 1:]
    )
    late_mermaid = any(
        line.strip().startswith("```mermaid")
        for line in lines[boundary_start + 1:]
    )
    if late_visual_heading or late_mermaid:
        boundary_label = "模拟面试流程" if boundary_section_title == "模拟面试流程" else "面试问题"
        errors.append(f"{label}项目图解必须位于{boundary_label}之前，不能在面试开始后补图")


def extract_and_validate_questions(
    text, section_title, side, errors, story_ids=None, knowledge_ids=None
):
    story_ids = story_ids or set()
    knowledge_ids = knowledge_ids or set()
    lines = text.splitlines()
    span = exact_section(lines, 2, section_title)
    if span is None:
        return []
    section_lines = lines[span[0] + 1:span[1]]
    validate_question_categories(section_lines, side, errors)
    cards = parse_question_cards(section_lines)
    count = len(cards)
    if count < MIN_QUESTIONS or count > MAX_QUESTIONS:
        errors.append(f"{side}问题数量应在 {MIN_QUESTIONS}-{MAX_QUESTIONS} 之间，实际 {count}")
    numbers = [int(match.group(1)) for match, _ in cards]
    if numbers and numbers != list(range(1, count + 1)):
        errors.append(f"{side}题目编号必须从题目1开始连续且不重复")

    missing_fields = []
    short_references = []
    long_references = []
    duplicate_references = {}
    for match, block in cards:
        qid = f"题目{match.group(1)}"
        fields = TEACHER_FIELDS if side == "老师版" else STUDENT_FIELDS
        missing = []
        for field in fields:
            if side == "学生版" and field == "我的版本":
                if not field_present(block, field):
                    missing.append(field)
            elif not field_value(block, field):
                missing.append(field)
        if missing:
            missing_fields.append(f"{qid}({','.join(missing)})")

        expression_type = field_value(block, "表达类型") or ""
        if expression_type and expression_type not in EXPRESSION_TYPES:
            errors.append(
                f"{side} {qid} 表达类型无效: {expression_type}；"
                f"只能使用 {'、'.join(EXPRESSION_TYPES)}"
            )

        if side == "老师版":
            basis = "\n".join((
                field_value(block, "候选人可用素材") or "",
                field_value(block, "岗位场景补充") or "",
            ))
        else:
            basis = field_value(block, "事实或场景依据") or ""
        referenced_stories = set(re.findall(r"\bS\d+\b", basis))
        referenced_knowledge = set(re.findall(r"\bK\d+\b", basis))
        unknown_stories = referenced_stories - story_ids
        unknown_knowledge = referenced_knowledge - knowledge_ids
        if unknown_stories:
            errors.append(f"{side} {qid} 引用了不存在的 S 锚点: {', '.join(sorted(unknown_stories))}")
        if unknown_knowledge:
            errors.append(f"{side} {qid} 引用了不存在的 K 锚点: {', '.join(sorted(unknown_knowledge))}")
        if expression_type == "亲历表达" and not referenced_stories:
            errors.append(f"{side} {qid} 亲历表达必须引用至少 1 个 S 锚点")
        elif expression_type == "迁移表达":
            if not referenced_stories:
                errors.append(f"{side} {qid} 迁移表达必须引用至少 1 个 S 锚点")
            if not referenced_knowledge:
                errors.append(f"{side} {qid} 迁移表达必须引用至少 1 个 K 锚点")
        elif expression_type in {"岗位知识", "场景推演"} and not referenced_knowledge:
            errors.append(f"{side} {qid} {expression_type}必须引用至少 1 个 K 锚点")

        if side == "老师版":
            followup = field_value(block, "继续追问") or ""
            if "第一层" not in followup or "第二层" not in followup:
                errors.append(f"老师版 {qid} 的继续追问必须包含第一层和第二层")
            if visible_length(field_value(block, "参考回答方向") or "") < 24:
                errors.append(f"老师版 {qid} 的参考回答方向过短")
        else:
            reference = field_value(block, "参考表达") or ""
            length = visible_length(reference)
            if length < MIN_STUDENT_REFERENCE:
                short_references.append(qid)
            if length > MAX_STUDENT_REFERENCE:
                long_references.append(qid)
            normalized = re.sub(r"[\W_]", "", reference).lower()
            if normalized:
                duplicate_references.setdefault(normalized, []).append(qid)
            if visible_length(field_value(block, "事实或场景依据") or "") < 8:
                errors.append(f"学生版 {qid} 的事实或场景依据过短，必须指向 S/K 锚点")
            if visible_length(field_value(block, "答题提示") or "") < 20:
                errors.append(f"学生版 {qid} 的答题提示过短，必须说明如何改写和验收")
            if expression_type == "岗位知识" and re.search(r"我(?:当时|曾经|负责|主导|完成)", reference):
                errors.append(f"学生版 {qid} 的岗位知识不得伪装成个人经历")
            if expression_type == "场景推演" and not re.search(r"如果|假设|场景|面对", reference):
                errors.append(f"学生版 {qid} 的场景推演必须明确假设条件")

    if missing_fields:
        errors.append(f"{side}问题卡字段不完整: " + ", ".join(missing_fields[:8]))
    if short_references:
        errors.append(
            f"学生版参考表达过短（少于 {MIN_STUDENT_REFERENCE} 个可见字符）: "
            + ", ".join(short_references[:8])
        )
    if long_references:
        errors.append(
            f"学生版参考表达过长（超过 {MAX_STUDENT_REFERENCE} 个可见字符）: "
            + ", ".join(long_references[:8])
        )
    duplicates = [ids for ids in duplicate_references.values() if len(ids) > 2]
    if duplicates:
        errors.append("学生版参考表达重复超过 2 次: " + ", ".join(duplicates[0][:8]))
    return [
        (
            int(match.group(1)),
            match.group(2).strip(),
            field_value(block, "表达类型") or "",
        )
        for match, block in cards
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--resume", required=True)
    parser.add_argument("--master", required=True)
    parser.add_argument("--internal")
    parser.add_argument("--student")
    parser.add_argument("--track", choices=tuple(TRACK_MARKERS))
    parser.add_argument("--post-session")
    parser.add_argument("--forbid-name", action="append", default=[])
    args = parser.parse_args()

    errors = []
    resume = Path(args.resume)
    if not resume.is_file():
        errors.append(f"简历不存在: {resume}")

    paths = {"母稿": Path(args.master)}
    if args.internal:
        paths["老师版"] = Path(args.internal)
    if args.student:
        paths["学生版"] = Path(args.student)
    if args.post_session:
        paths["复盘"] = Path(args.post_session)

    texts = {}
    for label, path in paths.items():
        text = read_markdown(path, label, errors)
        if text is None:
            continue
        texts[label] = text
        if args.name not in text:
            errors.append(f"{label}未包含学生姓名: {args.name}")
        for forbidden in args.forbid_name:
            if forbidden in text:
                errors.append(f"{label}包含禁止姓名: {forbidden}")

    teacher_text = texts.get("老师版") or texts.get("母稿")
    teacher_path = paths.get("老师版") or paths["母稿"]
    teacher_questions = []
    teacher_tiers = []
    if teacher_text:
        require_sections(teacher_text, TEACHER_SECTIONS, "老师版", errors)
        teacher_tiers = validate_tiers(teacher_text, "老师版", errors)
        validate_jd_matrix(teacher_text, errors)
        validate_anchors(teacher_text, errors)
        teacher_story_ids, teacher_knowledge_ids = validate_story_knowledge_anchors(
            teacher_text, "老师版", errors
        )
        validate_core_experiences(teacher_text, errors)
        if not has_resume_link(teacher_text, resume, teacher_path):
            errors.append(f"老师版前 25 个非空行未包含简历 Markdown 链接: {resume.name}")
        if args.track:
            for marker in TRACK_MARKERS[args.track]:
                if marker not in teacher_text:
                    errors.append(f"老师版缺少 {args.track} 路线标记: {marker}")
        teacher_questions = extract_and_validate_questions(
            teacher_text, "模拟面试问题与带教指引", "老师版", errors,
            teacher_story_ids, teacher_knowledge_ids,
        )
        validate_visual_order(
            teacher_text, "模拟面试流程", "老师版", errors
        )
        validate_no_visual_placeholders(teacher_text, "老师版", errors)

    student_text = texts.get("学生版")
    student_questions = []
    student_tiers = []
    if student_text:
        require_sections(student_text, STUDENT_SECTIONS, "学生版", errors)
        student_tiers = validate_tiers(student_text, "学生版", errors)
        student_story_ids, student_knowledge_ids = validate_story_knowledge_anchors(
            student_text, "学生版", errors
        )
        validate_metric_primer(
            student_text,
            errors,
            reference_texts=(teacher_text, student_text),
        )
        student_questions = extract_and_validate_questions(
            student_text, "面试问题与个人逐字稿", "学生版", errors,
            student_story_ids, student_knowledge_ids,
        )
        validate_visual_order(
            student_text, "面试问题与个人逐字稿", "学生版", errors
        )
        validate_no_visual_placeholders(student_text, "学生版", errors)
        for marker in STUDENT_FORBIDDEN:
            if marker in student_text:
                errors.append(f"学生版包含内部禁用标记: {marker}")

    if teacher_questions and student_questions:
        teacher_titles = [(number, title) for number, title, _ in teacher_questions]
        student_titles = [(number, title) for number, title, _ in student_questions]
        if teacher_titles != student_titles:
            errors.append("老师版与学生版的题目标题或顺序不一致")
        elif [mode for _, _, mode in teacher_questions] != [mode for _, _, mode in student_questions]:
            errors.append("老师版与学生版的表达类型不一致")
    if teacher_tiers and student_tiers and teacher_tiers != student_tiers:
        errors.append("老师版与学生版三档匹配 JD 的岗位或顺序不一致")

    review = texts.get("复盘")
    if review:
        for marker in POST_SESSION_MARKERS:
            if marker not in review:
                errors.append(f"复盘缺少必需标记: {marker}")
        if MOBILE_RE.search(review):
            errors.append("复盘包含未脱敏的中国大陆手机号")

    result = {"status": "ok" if not errors else "invalid", "errors": errors}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
