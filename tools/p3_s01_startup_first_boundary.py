"""Read-only, sanitized first Nav2 startup error classifier for public CI.

The original exact-SHA P3 S01 L2 #43423047000 failed BEFORE any Goal:
NAVIGATION_START: G07_NATIVE_LIFECYCLE_STARTUP_REJECTED.
A later empty CM rosbag was secondary. Never disclose private ROS log content;
emit stage, line number, component and an allowlisted failure classification.
"""
import argparse
import json
import re
from pathlib import Path


def summarize(launch_text, native):
    if not isinstance(launch_text, str):
        launch_text = ""
    if not isinstance(native, dict):
        native = {}
    status = native.get("status", "UNKNOWN")
    if status not in ("ACK", "REJECTED", "SERVICE_TIMEOUT",
                      "SERVICE_MISSING", "BLOCKED_LIFECYCLE_EXCEPTION"):
        status = "UNKNOWN"
    first = None
    first_line = None
    first_node = None
    cleanup_seen = False
    cleanup_before_error = False
    for index, line in enumerate(launch_text.splitlines(), 1):
        if any(x in line for x in ("signal_handler(SIGINT/SIGTERM)",
                                   "rcl preshutdown", "Destroying lifecycle_manager")):
            cleanup_seen = True
        match = re.search(r"\[(?:ERROR|FATAL)\]\s*\[([A-Za-z0-9_]+)\]", line)
        if not match:
            continue
        if cleanup_seen:
            cleanup_before_error = first is None
            continue
        first = line.lower()
        first_line = index
        first_node = match.group(1)
        break
    cls = "UNKNOWN_FIRST_NAV_ERROR"
    if first is not None:
        if "failed to configure" in first or "configure failed" in first:
            cls = "NODE_CONFIGURE_FAILURE"
        elif "failed to activate" in first or "activate failed" in first:
            cls = "NODE_ACTIVATION_FAILURE"
        elif "failed to bring up" in first:
            cls = "LIFECYCLE_BRINGUP_FAILURE"
        elif "bond" in first:
            cls = "LIFECYCLE_BOND_FAILURE"
        elif "parameter" in first or "param" in first:
            cls = "NAV_PARAM_FAILURE"
        else:
            cls = "NAV_STARTUP_OTHER_ERROR"
    return {
        "schema": "axia_p3_s01_first_nav_startup_boundary_v1",
        "first_failure_stage": "NO_NAV_FAILURE_CONFIRMED" if status == "ACK"
                               else "NAVIGATION_START",
        "native_status": status,
        "native_request_sent": native.get("request_sent") is True,
        "first_error_class": cls,
        "first_error_line": first_line,
        "first_error_node": first_node,
        "cleanup_started_before_error": cleanup_before_error,
        "goal_sent": False,
        "fault_injected": False,
        "raw_safety_behavior_accepted": False,
        "formal_accepted": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--launch-log", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # Never echo the unredacted ROS log or any private source/paths.
    try:
        native = json.loads(args.native.read_text(encoding="utf8"))
    except (OSError, ValueError):
        native = {}
    try:
        data = args.launch_log.read_text(encoding="utf8", errors="replace")
    except OSError:
        data = ""
    result = summarize(data, native)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print("AXIA_P3_S01_FIRST_NAV_STARTUP_BOUNDARY " +
          json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
