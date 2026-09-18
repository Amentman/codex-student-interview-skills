#!/usr/bin/env python3
"""Locate one student's existing resume and mock-interview master without mutation."""

import argparse
import json
import os
import sys
from pathlib import Path


SUPPORTED_SUFFIXES = {".pdf", ".docx"}
DELIVERY_DIR_NAME = "校招交付"


def default_delivery_root_candidates(home=None):
    home = Path(home).expanduser().resolve() if home is not None else Path.home().resolve()
    desktop = home / "Desktop"
    candidates = [
        desktop / DELIVERY_DIR_NAME,
        desktop / "01_公司与客户" / DELIVERY_DIR_NAME,
    ]
    for pattern in (f"*/{DELIVERY_DIR_NAME}", f"*/*/{DELIVERY_DIR_NAME}"):
        candidates.extend(desktop.glob(pattern))
    return list(dict.fromkeys(path.resolve() for path in candidates))


def root_has_student_evidence(root, name):
    exact_dir = root / name
    if exact_dir.is_dir():
        return True
    return any(
        path.is_file() and name in path.name and path.suffix.lower() in SUPPORTED_SUFFIXES
        for path in root.rglob("*")
    )


def resolve_delivery_root(name, explicit_root=None, candidates=None):
    if explicit_root is not None:
        root = Path(explicit_root).expanduser().resolve()
        return {
            "status": "ok",
            "root": root,
            "candidates": [root],
            "resolved_by": "explicit",
        }

    candidates = candidates if candidates is not None else default_delivery_root_candidates()
    existing = sorted(
        {Path(path).expanduser().resolve() for path in candidates if Path(path).expanduser().is_dir()},
        key=str,
    )
    if not existing:
        return {
            "status": "missing_root",
            "root": None,
            "candidates": [],
            "resolved_by": None,
        }
    if len(existing) == 1:
        return {
            "status": "ok",
            "root": existing[0],
            "candidates": existing,
            "resolved_by": "single_existing",
        }

    evidence_roots = [root for root in existing if root_has_student_evidence(root, name)]
    if len(evidence_roots) == 1:
        return {
            "status": "ok",
            "root": evidence_roots[0],
            "candidates": existing,
            "resolved_by": "student_evidence",
        }
    return {
        "status": "ambiguous_root",
        "root": None,
        "candidates": evidence_roots or existing,
        "resolved_by": None,
    }


def supported_documents(directory):
    return sorted(
        (path.resolve() for path in directory.rglob("*")
         if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES),
        key=lambda path: str(path),
    )


def choose_resume(candidates):
    resume_named = [path for path in candidates if "简历" in path.name]
    preferred = resume_named or candidates
    return preferred[0] if len(preferred) == 1 else None


def safe_student_name(name):
    separators = {os.sep}
    if os.altsep:
        separators.add(os.altsep)
    return name not in {".", ".."} and not Path(name).is_absolute() and not any(
        separator in name for separator in separators
    )


def payload(
    status,
    name,
    student_dir,
    candidates,
    primary_resume,
    delivery_root=None,
    root_candidates=None,
    root_resolved_by=None,
):
    interview = None
    if student_dir is not None:
        master = student_dir / f"{name}_模拟面试.md"
        if master.is_file():
            interview = str(master.resolve())
    return {
        "status": status,
        "student_name": name,
        "delivery_root": str(delivery_root) if delivery_root is not None else None,
        "root_candidates": [str(path) for path in (root_candidates or [])],
        "root_resolved_by": root_resolved_by,
        "student_dir": str(student_dir.resolve()) if student_dir is not None else None,
        "resume_candidates": [str(path) for path in candidates],
        "primary_resume": str(primary_resume) if primary_resume is not None else None,
        "interview_markdown": interview,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        help="Explicit delivery root; omit to discover a unique 校招交付 directory",
    )
    parser.add_argument("--name", required=True, help="Student name")
    args = parser.parse_args()
    if not safe_student_name(args.name):
        print(json.dumps(payload("invalid_name", args.name, None, [], None), ensure_ascii=False))
        return 4

    root_result = resolve_delivery_root(args.name, explicit_root=args.root)
    if root_result["status"] != "ok":
        print(json.dumps(payload(
            root_result["status"],
            args.name,
            None,
            [],
            None,
            root_candidates=root_result["candidates"],
        ), ensure_ascii=False))
        return {"missing_root": 5, "ambiguous_root": 6}[root_result["status"]]

    root = root_result["root"]
    exact_dir = root / args.name

    if exact_dir.is_dir():
        student_dir = exact_dir
        candidates = supported_documents(student_dir)
    elif root.is_dir():
        candidates = sorted(
            (path.resolve() for path in root.rglob("*")
             if path.is_file() and args.name in path.name
             and path.suffix.lower() in SUPPORTED_SUFFIXES),
            key=lambda path: str(path),
        )
        student_dir = candidates[0].parent if len(candidates) == 1 else None
    else:
        candidates = []
        student_dir = None

    primary_resume = choose_resume(candidates)
    status = "ok" if primary_resume else ("ambiguous" if candidates else "missing")
    exit_code = {"ok": 0, "ambiguous": 2, "missing": 3}[status]
    print(json.dumps(payload(
        status,
        args.name,
        student_dir,
        candidates,
        primary_resume,
        delivery_root=root,
        root_candidates=root_result["candidates"],
        root_resolved_by=root_result["resolved_by"],
    ), ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
