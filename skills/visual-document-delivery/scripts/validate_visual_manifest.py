#!/usr/bin/env python3
"""Validate deterministic fields in a visual-document delivery manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ALLOWED_TYPES = {
    "flowchart",
    "architecture",
    "swimlane",
    "timeline",
    "matrix",
    "chart",
    "relationship",
}
ALLOWED_FACT_BOUNDARIES = {
    "Confirmed",
    "Externally verified",
    "Inferred",
    "Knowledge supplement",
    "Open",
}
REQUIRED_VISUAL_FIELDS = {
    "id",
    "type",
    "reason",
    "section",
    "fact_boundary",
    "caption",
    "source_note",
}


def validate_manifest(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    contract = data.get("visual_contract")
    if not isinstance(contract, dict):
        return ["missing visual_contract"]

    substantial = contract.get("substantial") is True
    signals = contract.get("complexity_signals")
    plan = contract.get("visual_plan")
    if not isinstance(signals, list):
        errors.append("complexity_signals must be a list")
        signals = []
    if not isinstance(plan, list):
        errors.append("visual_plan must be a list")
        plan = []
    if substantial and signals and not plan:
        errors.append(
            "substantial document with complex relationships needs a visual plan"
        )
    if (
        not substantial
        and not plan
        and not str(contract.get("no_visual_reason", "")).strip()
    ):
        errors.append("simple document without visuals needs no_visual_reason")

    ids: set[str] = set()
    for item in plan:
        if not isinstance(item, dict):
            errors.append("visual_plan entries must be objects")
            continue
        missing = sorted(REQUIRED_VISUAL_FIELDS - item.keys())
        if missing:
            errors.append(f"visual entry missing fields: {', '.join(missing)}")
        visual_id = str(item.get("id", "")).strip()
        if not visual_id or visual_id in ids:
            errors.append(f"visual id is missing or duplicated: {visual_id}")
        ids.add(visual_id)
        if item.get("type") not in ALLOWED_TYPES:
            errors.append(f"unsupported visual type: {item.get('type')}")
        if item.get("fact_boundary") not in ALLOWED_FACT_BOUNDARIES:
            errors.append(
                f"unsupported fact boundary: {item.get('fact_boundary')}"
            )
        for field in ("reason", "section", "caption", "source_note"):
            if not str(item.get(field, "")).strip():
                errors.append(f"visual field is empty: {visual_id}.{field}")
        if item.get("type") == "chart":
            chart_metadata = item.get("chart_metadata")
            if not isinstance(chart_metadata, dict):
                errors.append(f"chart metadata missing or invalid: {visual_id}")
            else:
                for field in (
                    "source_identity",
                    "metric_definition",
                    "time_range",
                    "unit_or_denominator",
                ):
                    if not str(chart_metadata.get(field, "")).strip():
                        errors.append(
                            f"chart metadata field is empty: {visual_id}.{field}"
                        )

    required_ids = contract.get("required_visual_ids", [])
    if not isinstance(required_ids, list):
        errors.append("required_visual_ids must be a list")
        required_ids = []
    for visual_id in required_ids:
        if visual_id not in ids:
            errors.append(f"required visual missing from plan: {visual_id}")

    readback = contract.get("readback", {})
    media_blocks = (
        readback.get("media_blocks", []) if isinstance(readback, dict) else []
    )
    media_by_id = {
        str(item.get("visual_id", "")): item
        for item in media_blocks
        if isinstance(item, dict)
    }
    for visual_id in required_ids:
        media = media_by_id.get(str(visual_id))
        if not media:
            errors.append(f"required visual missing from readback: {visual_id}")
        elif not str(media.get("token", "")).strip():
            errors.append(f"media token is empty: {visual_id}")

    render_qa = contract.get("render_qa", {})
    if not isinstance(render_qa, dict):
        errors.append("render_qa must be an object")
        return errors
    page_count = render_qa.get("page_count", 0)
    checked_pages = render_qa.get("checked_pages", [])
    if substantial:
        if not isinstance(page_count, int) or page_count < 1:
            errors.append("substantial document needs a positive rendered page count")
        elif checked_pages != list(range(1, page_count + 1)):
            errors.append("render QA does not cover every page")
        required_checks = {"clipping", "readability", "layout", "caption"}
        if not required_checks.issubset(set(render_qa.get("checked_items", []))):
            errors.append("render QA is missing required checked items")
        if render_qa.get("issues"):
            errors.append("render QA still has unresolved issues")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Visual manifest JSON file")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors = [f"cannot read valid JSON ({exc})"]
    else:
        errors = (
            validate_manifest(data)
            if isinstance(data, dict)
            else ["manifest root must be an object"]
        )
    print(
        json.dumps(
            {"status": "invalid" if errors else "ok", "errors": errors},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
