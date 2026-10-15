#!/usr/bin/env python3
"""Enforce the per-company role cap for one student's job list.

The input order is treated as the upstream ranking. The first N rows for each
non-empty company are kept; later rows are returned as dropped so a caller can
record the reason instead of silently writing an over-cap list.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


DEFAULT_MAX_PER_COMPANY = 3


def _company_value(row: dict[str, Any], company_key: str) -> str:
    value = row.get(company_key, "")
    if isinstance(value, list):
        value = value[0] if value else ""
    return str(value).strip()


def validate_company_cap(
    rows: Iterable[dict[str, Any]],
    max_per_company: int = DEFAULT_MAX_PER_COMPANY,
    company_key: str = "公司",
) -> dict[str, int]:
    """Return company counts that exceed the cap, without changing rows."""

    if max_per_company < 1:
        raise ValueError("max_per_company must be at least 1")
    counts = Counter(
        company for row in rows if (company := _company_value(row, company_key))
    )
    return {
        company: count
        for company, count in counts.items()
        if count > max_per_company
    }


def cap_rows(
    rows: Iterable[dict[str, Any]],
    max_per_company: int = DEFAULT_MAX_PER_COMPANY,
    company_key: str = "公司",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Keep the ranked prefix up to N rows per company.

    Rows without a company value are preserved and reported to the caller's
    normal data-quality checks; they are not grouped into one fake company.
    """

    if max_per_company < 1:
        raise ValueError("max_per_company must be at least 1")

    kept: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for row in rows:
        company = _company_value(row, company_key)
        if not company or counts[company] < max_per_company:
            kept.append(row)
            if company:
                counts[company] += 1
        else:
            dropped.append(row)
    return kept, dropped


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Keep at most N ranked roles for each company in a JSON list."
    )
    parser.add_argument("input_json", type=Path)
    parser.add_argument("output_json", type=Path)
    parser.add_argument(
        "--max-per-company", type=int, default=DEFAULT_MAX_PER_COMPANY
    )
    parser.add_argument("--company-key", default="公司")
    args = parser.parse_args()

    rows = json.loads(args.input_json.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        parser.error("input_json must contain a JSON list of objects")

    kept, dropped = cap_rows(rows, args.max_per_company, args.company_key)
    args.output_json.write_text(
        json.dumps(kept, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report = {
        "max_per_company": args.max_per_company,
        "input_count": len(rows),
        "kept_count": len(kept),
        "dropped_count": len(dropped),
        "dropped": dropped,
        "violations_before_cap": validate_company_cap(
            rows, args.max_per_company, args.company_key
        ),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
