#!/usr/bin/env python3
"""Validate a local Markdown draft for a real-interview review."""

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "本轮结论与使用说明",
    "输入边界声明",
    "场次与问题地图",
    "逐题复盘",
    "答非所问、停顿与追问失守",
    "稳定能力与有效证据",
    "事实冲突与新增 Open",
    "简历调整建议",
    "下一轮重点问题",
    "学生任务卡",
    "来源与附件",
)

QUESTION_FIELDS = (
    "证据定位",
    "学生实际回答",
    "当场表现",
    "面试官／导师反馈",
    "问题与根因",
    "应掌握知识",
    "更稳妥的表达",
    "训练任务",
)


def section_body(text, title):
    heading = re.search(rf"^##\s+{re.escape(title)}\s*$", text, re.MULTILINE)
    if not heading:
        return ""
    next_heading = re.search(r"^##\s+.+$", text[heading.end():], re.MULTILINE)
    end = heading.end() + next_heading.start() if next_heading else len(text)
    return text[heading.end():end]


def question_cards(text):
    review_section = section_body(text, "逐题复盘")
    matches = list(re.finditer(r"^###\s+Q\d+｜.+$", review_section, re.MULTILINE))
    cards = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(review_section)
        cards.append((match.group(0).strip(), review_section[match.start():end]))
    return cards


def validate(text, resume_name, transcript_name):
    errors = []

    for section in REQUIRED_SECTIONS:
        if not re.search(rf"^##\s+{re.escape(section)}\s*$", text, re.MULTILINE):
            errors.append(f"缺少必需章节：{section}")

    source_section = section_body(text, "来源与附件")
    if resume_name not in source_section:
        errors.append(f"来源与附件缺少简历附件：{resume_name}")
    if transcript_name not in source_section:
        errors.append(f"来源与附件缺少逐字稿附件：{transcript_name}")

    cards = question_cards(text)
    if not cards:
        errors.append("逐题复盘至少需要一张 Qxx 题卡")
    for title, card in cards:
        for field in QUESTION_FIELDS:
            if not re.search(rf"\*\*{re.escape(field)}：\*\*\s*\S", card):
                errors.append(f"{title} 缺少非空字段：{field}")

    if re.search(r"(?<!\d)1[3-9]\d{9}(?!\d)", text):
        errors.append("发现未脱敏的中国大陆手机号")
    if re.search(r"(?<![\w.+-])[A-Za-z0-9][\w.+-]*@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", text):
        errors.append("发现未脱敏的邮箱")
    if re.search(
        r"(?:微信(?:号|ID)?|WeChat(?:\s+ID)?)\s*[:：]\s*[A-Za-z][A-Za-z0-9_-]{5,19}",
        text,
        re.IGNORECASE,
    ):
        errors.append("发现未脱敏的微信号")
    if re.search(r"(?<!\d)\d{17}[\dXx](?!\d)", text):
        errors.append("发现未脱敏的身份证号")

    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", required=True, type=Path)
    parser.add_argument("--resume-name", required=True)
    parser.add_argument("--transcript-name", required=True)
    args = parser.parse_args()

    try:
        text = args.review.read_text(encoding="utf-8")
    except OSError as exc:
        print(json.dumps({"status": "error", "errors": [str(exc)]}, ensure_ascii=False))
        return 2

    errors = validate(text, args.resume_name, args.transcript_name)
    payload = {"status": "ok" if not errors else "invalid", "errors": errors}
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
