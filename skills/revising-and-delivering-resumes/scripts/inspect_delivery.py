#!/usr/bin/env python3
"""Inspect a resume Word review copy and clean application PDF."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
import zipfile
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

import pdfplumber
from lxml import etree
from pypdf import PdfReader
from pypdf.generic import ContentStream


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"


def normalize(text: str) -> str:
    return (
        re.sub(r"\s+", "", text)
        .replace("（", "(")
        .replace("）", ")")
        .replace("，", ",")
        .replace("：", ":")
    )


def strip_normalized_fragments(text: str, fragments: list[str]) -> str:
    result = normalize(text)
    for fragment in fragments:
        normalized_fragment = normalize(fragment)
        if normalized_fragment:
            result = result.replace(normalized_fragment, "")
    return result


def is_visible_text_character(value: str) -> bool:
    return bool(value) and not value.isspace() and unicodedata.category(value) not in {
        "Cc",
        "Cf",
        "Co",
    }


def normalize_font_family(value: str) -> str:
    family = re.sub(r"^[A-Z]{6}\+", "", value)
    family = re.sub(r"[^a-z0-9]", "", family.lower())
    for suffix in ("semibold", "regular", "medium", "light", "bold", "italic"):
        if family.endswith(suffix):
            family = family[: -len(suffix)]
            break
    return family


def inspect_docx(path: Path) -> dict[str, object]:
    comment_ids: set[str] = set()
    with zipfile.ZipFile(path) as archive:
        bad_member = archive.testzip()
        if bad_member:
            raise ValueError(f"Corrupt DOCX member: {bad_member}")
        names = set(archive.namelist())
        document = etree.fromstring(archive.read("word/document.xml"))
        body_text = "".join(document.itertext())
        header_parts: list[str] = []
        footer_parts: list[str] = []
        for name in sorted(names):
            if re.fullmatch(r"word/header\d+\.xml", name):
                header_parts.append("".join(etree.fromstring(archive.read(name)).itertext()))
            elif re.fullmatch(r"word/footer\d+\.xml", name):
                footer_parts.append("".join(etree.fromstring(archive.read(name)).itertext()))
        header_footer_fragments = [
            part for part in header_parts + footer_parts if normalize(part)
        ]
        text = "".join(header_parts + [body_text] + footer_parts)
        comments = 0
        if "word/comments.xml" in names:
            comments_xml = etree.fromstring(archive.read("word/comments.xml"))
            comment_nodes = comments_xml.findall(f".//{W}comment")
            comments = len(comment_nodes)
            comment_ids = {
                value
                for node in comment_nodes
                if (value := node.get(f"{W}id")) is not None
            }

    start_ids = {
        value
        for node in document.findall(f".//{W}commentRangeStart")
        if (value := node.get(f"{W}id")) is not None
    }
    end_ids = {
        value
        for node in document.findall(f".//{W}commentRangeEnd")
        if (value := node.get(f"{W}id")) is not None
    }
    reference_ids = {
        value
        for node in document.findall(f".//{W}commentReference")
        if (value := node.get(f"{W}id")) is not None
    }
    missing_anchor_ids = sorted(comment_ids - (start_ids & end_ids & reference_ids))

    red_runs = 0
    active_italics = 0
    fonts: Counter[str] = Counter()
    font_character_counts: Counter[str] = Counter()
    font_size_character_counts: Counter[float] = Counter()
    paragraph_font_sizes: list[dict[str, object]] = []
    for paragraph in document.findall(f".//{W}p"):
        size_groups: Counter[float] = Counter()
        paragraph_text = "".join(paragraph.itertext())
        for run in paragraph.findall(f"./{W}r"):
            run_text = "".join(run.itertext())
            visible_characters = sum(is_visible_text_character(char) for char in run_text)
            size = run.find(f"./{W}rPr/{W}sz")
            if size is not None and (value := size.get(f"{W}val")) and visible_characters:
                size_groups[float(value) / 2] += visible_characters
        paragraph_font_sizes.append(
            {
                "text": paragraph_text,
                "size_groups": {str(key): value for key, value in sorted(size_groups.items())},
            }
        )
    for run in document.findall(f".//{W}r"):
        run_text = "".join(run.itertext())
        visible_characters = sum(is_visible_text_character(char) for char in run_text)
        color = run.find(f".//{W}color")
        if color is not None and (color.get(f"{W}val") or "").upper() in {
            "C00000",
            "FF0000",
        }:
            red_runs += 1
        italic = run.find(f".//{W}i")
        if italic is not None and italic.get(f"{W}val") not in {
            "0",
            "false",
            "off",
        }:
            active_italics += 1
        run_fonts = run.find(f".//{W}rFonts")
        if run_fonts is not None:
            preferred_font = None
            for attr in ("ascii", "hAnsi", "eastAsia"):
                value = run_fonts.get(f"{W}{attr}")
                if value:
                    fonts[value] += 1
                    if preferred_font is None or attr == "eastAsia":
                        preferred_font = value
            if preferred_font and visible_characters:
                font_character_counts[preferred_font] += visible_characters
        size = run.find(f".//{W}sz")
        if size is not None and (value := size.get(f"{W}val")) and visible_characters:
            font_size_character_counts[float(value) / 2] += visible_characters

    return {
        "path": str(path),
        "text": text,
        "body_text": body_text,
        "header_footer_fragments": header_footer_fragments,
        "characters": len(normalize(text)),
        "comments": comments,
        "comment_range_starts": len(start_ids),
        "comment_range_ends": len(end_ids),
        "comment_references": len(reference_ids),
        "missing_anchor_ids": missing_anchor_ids,
        "red_runs": red_runs,
        "active_italics": active_italics,
        "fonts": dict(fonts.most_common()),
        "font_character_counts": dict(font_character_counts.most_common()),
        "font_size_character_counts": {
            str(key): value for key, value in sorted(font_size_character_counts.items())
        },
        "paragraph_font_sizes": paragraph_font_sizes,
    }


def inspect_pdf(path: Path) -> dict[str, object]:
    typography_groups: dict[tuple[str, float], dict[str, object]] = {}
    with pdfplumber.open(path) as document:
        pages = len(document.pages)
        if pages == 0:
            raise ValueError("PDF has no pages")
        page_metrics = []
        for index, page in enumerate(document.pages, 1):
            words = page.extract_words()
            bottom = max((word["bottom"] for word in words), default=0.0)
            width, height = float(page.width), float(page.height)
            page_metrics.append(
                {
                    "page": index,
                    "width_pt": round(width, 2),
                    "height_pt": round(height, 2),
                    "a4": abs(width - 595.28) <= 3 and abs(height - 841.89) <= 3,
                    "bottom_blank_pt": round(height - bottom, 2),
                }
            )
            for char in page.chars:
                value = str(char.get("text", ""))
                if not value or unicodedata.category(value) in {"Cc", "Cf", "Co"}:
                    continue
                font = str(char.get("fontname", ""))
                size = round(float(char.get("size", 0.0)), 2)
                group = typography_groups.setdefault(
                    (font, size),
                    {"font": font, "size_pt": size, "characters": 0, "sample": ""},
                )
                if is_visible_text_character(value):
                    group["characters"] = int(group["characters"]) + 1
                if len(str(group["sample"])) < 120:
                    group["sample"] = str(group["sample"]) + value
        text = "\n".join(current.extract_text() or "" for current in document.pages)

    reader = PdfReader(path)
    review_annotations = 0
    link_annotations = 0
    red_color_ops = 0
    for current_page in reader.pages:
        for annotation in current_page.get("/Annots", []):
            subtype = str(annotation.get_object().get("/Subtype"))
            if subtype == "/Link":
                link_annotations += 1
            else:
                review_annotations += 1
        contents = current_page.get_contents()
        if contents is not None:
            stream = ContentStream(contents, reader)
            for operands, operator in stream.operations:
                if operator in (b"rg", b"RG") and len(operands) == 3:
                    red, green, blue = (float(value) for value in operands)
                    if red >= 0.5 and green <= 0.25 and blue <= 0.25:
                        red_color_ops += 1
                elif operator in (b"k", b"K") and len(operands) == 4:
                    cyan, magenta, yellow, black = (float(value) for value in operands)
                    if cyan <= 0.25 and magenta >= 0.5 and yellow >= 0.5 and black <= 0.25:
                        red_color_ops += 1

    return {
        "path": str(path),
        "text": text,
        "characters": len(normalize(text)),
        "pages": pages,
        "page_metrics": page_metrics,
        "a4_all_pages": all(bool(metric["a4"]) for metric in page_metrics),
        "last_page_bottom_blank_pt": page_metrics[-1]["bottom_blank_pt"],
        "review_annotations": review_annotations,
        "link_annotations": link_annotations,
        "red_color_ops": red_color_ops,
        "typography_groups": sorted(
            typography_groups.values(),
            key=lambda item: (-int(item["characters"]), str(item["font"]), float(item["size_pt"])),
        ),
    }


def find_pdf_typography_drift(
    word: dict[str, object],
    pdf: dict[str, object],
    *,
    size_tolerance: float,
    min_characters: int,
) -> list[dict[str, object]]:
    word_sizes = [float(value) for value in dict(word["font_size_character_counts"]).keys()]
    word_fonts = {
        normalize_font_family(value)
        for value in dict(word["font_character_counts"]).keys()
        if normalize_font_family(value)
    }
    issues: list[dict[str, object]] = []
    for group in list(pdf["typography_groups"]):
        characters = int(group["characters"])
        if characters < min_characters:
            continue
        font = str(group["font"])
        size = float(group["size_pt"])
        normalized_font = normalize_font_family(font)
        reasons = []
        if word_sizes and not any(abs(size - expected) <= size_tolerance for expected in word_sizes):
            reasons.append(f"size {size:g}pt not present in Word")
        if word_fonts and normalized_font and normalized_font not in word_fonts:
            reasons.append(f"font {font} not present in Word")
        if reasons:
            issues.append(
                {
                    "font": font,
                    "size_pt": size,
                    "characters": characters,
                    "reasons": reasons,
                    "sample": str(group["sample"]),
                }
            )
    return issues


def find_word_mixed_font_sizes(
    word: dict[str, object], *, spread_tolerance: float, min_characters_per_size: int = 2
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    for paragraph in list(word["paragraph_font_sizes"]):
        groups = {
            float(size): int(characters)
            for size, characters in dict(paragraph["size_groups"]).items()
            if int(characters) >= min_characters_per_size
        }
        if len(groups) < 2 or max(groups) - min(groups) <= spread_tolerance:
            continue
        issues.append(
            {
                "size_groups": {str(key): value for key, value in sorted(groups.items())},
                "sample": str(paragraph["text"])[:160],
            }
        )
    return issues


def add_check(checks: list[dict[str, object]], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "passed": passed, "detail": detail})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review-docx", required=True, type=Path)
    parser.add_argument("--application-pdf", required=True, type=Path)
    parser.add_argument("--clean-docx", type=Path)
    parser.add_argument("--expect-comments", action="store_true")
    parser.add_argument("--expect-red", action="store_true")
    parser.add_argument("--forbid-active-italics", action="store_true")
    parser.add_argument("--forbid-pdf-red", action="store_true")
    parser.add_argument("--forbid-pdf-typography-drift", action="store_true")
    parser.add_argument("--forbid-word-mixed-font-sizes", action="store_true")
    parser.add_argument("--pdf-font-size-tolerance", type=float, default=0.35)
    parser.add_argument("--min-pdf-typography-outlier-characters", type=int, default=8)
    parser.add_argument("--word-font-size-spread-tolerance", type=float, default=0.75)
    parser.add_argument("--require-font")
    parser.add_argument("--max-bottom-blank", type=float)
    parser.add_argument("--min-text-similarity", type=float, default=0.97)
    parser.add_argument("--expected-pages", type=int)
    parser.add_argument("--paper", choices=("any", "a4"), default="any")
    args = parser.parse_args()

    review = inspect_docx(args.review_docx)
    clean = inspect_docx(args.clean_docx) if args.clean_docx else None
    pdf = inspect_pdf(args.application_pdf)
    checks: list[dict[str, object]] = []

    if args.expected_pages is not None:
        add_check(
            checks,
            "pdf_pages",
            pdf["pages"] == args.expected_pages,
            f'{pdf["pages"]} == {args.expected_pages}',
        )
    if args.paper == "a4":
        add_check(
            checks,
            "pdf_a4_all_pages",
            bool(pdf["a4_all_pages"]),
            json.dumps(pdf["page_metrics"], ensure_ascii=False),
        )
    add_check(checks, "pdf_clean_annotations", pdf["review_annotations"] == 0, f'{pdf["review_annotations"]}')
    if args.expect_comments:
        add_check(checks, "word_comments", review["comments"] > 0, f'{review["comments"]}')
        anchors_complete = review["comments"] > 0 and not review["missing_anchor_ids"]
        add_check(
            checks,
            "word_comment_anchors",
            anchors_complete,
            (
                f'comments={review["comments"]}, starts={review["comment_range_starts"]}, '
                f'ends={review["comment_range_ends"]}, refs={review["comment_references"]}, '
                f'missing={review["missing_anchor_ids"]}'
            ),
        )
    if args.expect_red:
        add_check(checks, "word_red_runs", review["red_runs"] > 0, f'{review["red_runs"]}')
    if args.forbid_active_italics:
        add_check(checks, "no_active_italics", review["active_italics"] == 0, f'{review["active_italics"]}')
    if args.forbid_pdf_red:
        add_check(checks, "no_pdf_red", pdf["red_color_ops"] == 0, f'{pdf["red_color_ops"]}')
    if args.forbid_word_mixed_font_sizes:
        mixed_font_size_paragraphs = find_word_mixed_font_sizes(
            review, spread_tolerance=args.word_font_size_spread_tolerance
        )
        add_check(
            checks,
            "word_paragraph_font_sizes_consistent",
            not mixed_font_size_paragraphs,
            json.dumps(mixed_font_size_paragraphs, ensure_ascii=False),
        )
    if args.require_font:
        add_check(checks, "required_font", args.require_font in review["fonts"], args.require_font)
    if args.max_bottom_blank is not None:
        add_check(
            checks,
            "bottom_blank",
            float(pdf["last_page_bottom_blank_pt"]) <= args.max_bottom_blank,
            f'{pdf["last_page_bottom_blank_pt"]} <= {args.max_bottom_blank}',
        )

    reference = clean if clean else review
    if args.forbid_pdf_typography_drift:
        typography_issues = find_pdf_typography_drift(
            reference,
            pdf,
            size_tolerance=args.pdf_font_size_tolerance,
            min_characters=args.min_pdf_typography_outlier_characters,
        )
        add_check(
            checks,
            "pdf_typography_matches_word",
            not typography_issues,
            json.dumps(typography_issues, ensure_ascii=False),
        )
    fragments = list(reference["header_footer_fragments"])
    similarity = SequenceMatcher(
        None,
        normalize(reference["body_text"]),
        strip_normalized_fragments(pdf["text"], fragments),
    ).ratio()
    add_check(
        checks,
        "word_pdf_text_similarity",
        similarity >= args.min_text_similarity,
        f"{similarity:.4f} >= {args.min_text_similarity:.4f}",
    )
    if fragments:
        normalized_pdf = normalize(pdf["text"])
        missing_fragments = [
            fragment for fragment in fragments if normalize(fragment) not in normalized_pdf
        ]
        add_check(
            checks,
            "word_pdf_header_footer_present",
            not missing_fragments,
            f"missing={len(missing_fragments)} of {len(fragments)}",
        )
    if clean:
        same_text = normalize(clean["text"]) == normalize(review["text"])
        add_check(checks, "review_clean_text_equal", same_text, str(same_text))

    passed = all(bool(check["passed"]) for check in checks)
    report = {
        "passed": passed,
        "review_docx": {
            key: value
            for key, value in review.items()
            if key not in {"text", "body_text", "header_footer_fragments", "paragraph_font_sizes"}
        },
        "clean_docx": None
        if clean is None
        else {
            key: value
            for key, value in clean.items()
            if key not in {"text", "body_text", "header_footer_fragments", "paragraph_font_sizes"}
        },
        "application_pdf": {
            key: value for key, value in pdf.items() if key not in {"text", "typography_groups"}
        },
        "checks": checks,
        "visual_inspection_required": True,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, KeyError, ValueError, zipfile.BadZipFile) as error:
        print(json.dumps({"passed": False, "error": str(error)}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
