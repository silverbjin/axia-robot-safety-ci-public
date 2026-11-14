#!/usr/bin/env python3
"""Read-only D06 G07 Owner staged-startup monitor. No ROS or Goal.

Reads only the original local Owner's existing staged_startup.log and
startup_verdict.json. Never starts, stops, fixes, or changes a ROS process.
The stage is the NEXT PENDING gate, NOT proof of a blocked underlying process.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

# Exact gates in p2_staged_no_goal.py, released G07 shared startup.
GATES = (
    "CLOCK_READY",
    "NAVIGATION_NOT_ACTIVE",
    "LOCALIZATION_START",
    "MAP_AMCL_ACTIVE",
    "INITIALPOSE_MAP_CHECKED",
    "AMCL_TF_READY",
    "NAVIGATION_START",
    "CM_ACTIVE",
    "P2_GRAPH_READY",
    "NAV2_ACTION_READY",
)


def _file_json(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (ValueError, OSError, UnicodeError):
        return {}


def inspect_run(g07: Path, *, now: float | None = None) -> dict:
    """Summarize one original Owner run; NO safety verdict is inferred."""
    g07 = Path(g07)
    log = g07 / "staged_startup.log"
    data = _file_json(g07 / "startup_verdict.json")
    result = {
        "schema": "axia.d06.owner_no_goal_startup_progress_v1",
        "status": "NO_OWNER_STAGED_LOG",
        "last_completed": None,
        "next_pending": None,
        "first_failed_gate": None,
        "last_stage_detail": None,
        "elapsed_since_start_log_sec": None,
        "last_verdict_update_age_sec": None,
        "goal_sent": False,
        "acceptance_pass": False,
        "no_ros_no_goal_readonly": True,
        "outer_startup_limit_sec": 480,
    }
    if log.is_symlink() or not log.is_file():
        return result
    current = time.time() if now is None else now
    result["status"] = "STARTUP_IN_PROGRESS_NO_GOAL"
    try:
        result["elapsed_since_start_log_sec"] = round(
            max(0., current - log.stat().st_mtime), 1)
        verdict_file = g07 / "startup_verdict.json"
        if verdict_file.is_file() and not verdict_file.is_symlink():
            result["last_verdict_update_age_sec"] = round(
                max(0., current - verdict_file.stat().st_mtime), 1)
    except OSError:
        pass
    stages = data.get("stages", [])
    if not isinstance(stages, list):
        stages = []
    completed = set()
    for stage in stages:
        if not isinstance(stage, dict):
            continue
        gate = stage.get("gate")
        if isinstance(gate, str):
            if stage.get("status") == "PASS":
                completed.add(gate)
                result["last_completed"] = gate
            elif stage.get("status") == "BLOCKED":
                if result["first_failed_gate"] is None:
                    result["first_failed_gate"] = gate
            result["last_stage_detail"] = str(stage.get("detail", ""))[:300]
    for gate in GATES:
        if gate not in completed:
            result["next_pending"] = gate
            break
    failure = data.get("failed_gate")
    if isinstance(failure, str) and failure:
        result["first_failed_gate"] = result["first_failed_gate"] or failure
    if result["first_failed_gate"]:
        result["status"] = "STARTUP_BLOCKED"
        result["next_pending"] = result["first_failed_gate"]
    elif data.get("status") == "SMOKE_READY" and data.get("goal_sent") is False:
        result["status"] = "STARTUP_READY_NO_GOAL"
        result["next_pending"] = None
    elif data.get("goal_sent") is True:
        result["status"] = "UNTRUSTED_GOAL_SENT_IN_NO_GOAL_STARTUP_VERDICT"
    elif data.get("status") == "ERROR":
        result["status"] = "STARTUP_ERROR"
    return result


def newest_owner(home: Path) -> Path | None:
    base = home / "axia_p2_private_evidence"
    if not base.is_dir() or base.is_symlink():
        return None
    candidates = []
    for folder in base.glob("p2-l3-owner-*/G07"):
        if folder.is_symlink() or not folder.is_dir() or folder.parent.is_symlink():
            continue
        log = folder / "staged_startup.log"
        if log.is_file() and not log.is_symlink():
            candidates.append((log.stat().st_mtime, folder))
    return max(candidates, default=(0., None), key=lambda item: item[0])[1]


def _last_log_lines(path: Path, count: int = 5) -> list[str]:
    if not path.is_file() or path.is_symlink():
        return []
    try:
        # The small diagnostic log is bounded by the G07 original startup path.
        return path.read_text(encoding="utf-8", errors="replace").splitlines()[-count:]
    except OSError:
        return []


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--owner-home", type=Path, default=Path.home())
    p.add_argument("--run-root", type=Path, help="Exact original G07 directory")
    p.add_argument("--json", action="store_true", help="Print JSON only")
    args = p.parse_args()
    g07 = args.run_root if args.run_root is not None else newest_owner(args.owner_home)
    result = inspect_run(g07 if g07 else Path("/__axia_missing__"))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result["status"] != "NO_OWNER_STAGED_LOG" else 3
    print("AXIA_D06_READONLY_STARTUP_DIAGNOSTIC_NO_ROS_NO_GOAL")
    print("OWNER_G07_DIR="+str(g07) if g07 else "OWNER_G07_DIR=NOT_LOCATED")
    for key in (
        "status", "last_completed", "next_pending", "first_failed_gate",
        "last_stage_detail", "elapsed_since_start_log_sec",
        "last_verdict_update_age_sec", "outer_startup_limit_sec"):
        print(f"{key.upper()}={result[key]}")
    if g07:
        for name in ("staged_startup.log",
                     "startup_verdict.localization_start.native.json",
                     "startup_verdict.navigation_start.native.json",
                     "startup_verdict.probe_clock.log"):
            path = g07 / name
            if path.is_file() and not path.is_symlink():
                if name.endswith(".native.json"):
                    v = _file_json(path)
                    print(name+"="+json.dumps({
                        k:v.get(k) for k in ("status","manager","command",
                                             "request_sent","elapsed_sec")},
                        sort_keys=True))
                else:
                    lines = _last_log_lines(path, 3)
                    print(name+" LAST_LINES="+repr(lines))
    print("INTERPRETATION=NEXT_PENDING_IS_NOT_PROVEN_ROOT_CAUSE")
    print("NOT_ACCEPTED_OWNER_L3_OR_PHYSICAL_ESTOP")
    return 0 if result["status"] != "NO_OWNER_STAGED_LOG" else 3


if __name__ == "__main__":
    raise SystemExit(main())
