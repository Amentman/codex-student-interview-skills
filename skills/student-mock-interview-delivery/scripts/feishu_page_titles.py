#!/usr/bin/env python3
"""Emit canonical and legacy Feishu child-page titles for one student."""

import argparse
import json


def build_title_contract(student_name: str) -> dict:
    name = student_name.strip()
    if not name:
        raise ValueError("student name must not be empty")

    canonical = {
        "internal": f"{name}｜面试指导者版（内部）",
        "student": f"{name}｜学生面试准备版",
    }
    return {
        "student_name": name,
        "canonical": canonical,
        "accepted_existing": {
            "internal": [canonical["internal"], "01｜面试指导者版（内部）"],
            "student": [canonical["student"], "02｜学生面试准备版（可分享）"],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    args = parser.parse_args()
    try:
        payload = build_title_contract(args.name)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
