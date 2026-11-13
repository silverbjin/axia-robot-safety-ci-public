#!/usr/bin/env python3
"""AXIA P4 G12 D03-only release gate: structure and receipts, no actual release.

Real student RED / sealed private GREEN must run in public CI separately.
Never upgrades G11, G13 or baseline-wide formal acceptance.
"""
from __future__ import annotations

from pathlib import Path
import re

SHA40 = re.compile(r"^[0-9a-f]{40}$")
FORBIDDEN_PATH_COMPONENTS = frozenset({
    "instructor", "instructor_solution", "solutions", "solution",
    "hidden_tests", "secrets", "private_keys", ".ssh",
})
FORBIDDEN_FILE_SUFFIXES = (".pem", ".key", ".p12", ".pfx")


def scan_student_tree(root: Path) -> list[str]:
    """Only path-name screening; do not read or print private sources."""
    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        return ["STUDENT_ROOT_MISSING_OR_UNSAFE"]
    hits = []
    for entry in root.rglob("*"):
        relative = entry.relative_to(root)
        parts = tuple(x.lower() for x in relative.parts)
        if entry.is_symlink() or any(p in FORBIDDEN_PATH_COMPONENTS for p in parts) or (
            entry.is_file() and entry.name.lower().endswith(FORBIDDEN_FILE_SUFFIXES)
        ):
            hits.append(relative.as_posix())
    return sorted(hits)


def evaluate_receipt(receipt: dict, *, forbidden_files: list[str]) -> dict:
    """Fail closed; GREEN means one D03 educational module, not P4 accepted."""
    result = {
        "schema": "axia_p4_g12_d03_scoped_v1",
        "status": "BLOCKED",
        "formal_accepted": False,
        "student_release_approved": False,
        "G11": "NOT_ACCEPTED",
        "G12": "NOT_ACCEPTED",
        "G13": "NOT_RUN",
        "certified_estop": False,
        "ros_gazebo_run": False,
        "scope": "D03_PURE_PYTHON_ONLY",
    }
    if not isinstance(receipt, dict) or not isinstance(forbidden_files, list):
        return result
    a = receipt.get("student_sha")
    b = receipt.get("instructor_sha")
    if (not isinstance(a, str) or not SHA40.fullmatch(a)
            or not isinstance(b, str) or not SHA40.fullmatch(b)
            or a == b or forbidden_files):
        return result
    if (receipt.get("student_red_rc") != 1
            or type(receipt.get("student_failures")) is not int
            or receipt["student_failures"] < 1
            or receipt.get("instructor_public_green_rc") != 0
            or receipt.get("instructor_hidden_green_rc") != 0
            or receipt.get("protected_checkout") is not True):
        return result
    result["status"] = "G12_D03_TODO_RED_REFERENCE_GREEN_SCOPED"
    result["G12"] = "D03_SCOPED_CANDIDATE"
    return result
