#!/usr/bin/env python3
"""D04 read-only child process-group shutdown, Linux/WSL2, stdlib only.

Upstream starts ros2 launch with start_new_session=True. Its previous helper
checked proc.poll() alone: dead parent could leave image_view/Gazebo children
alive. This audits the OWNED process group even if parent is already gone.
No process-name pkill, user-wide killall or other ROS sessions.
"""
from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import time


def _members(session_id: int) -> list[dict]:
    """Live /proc processes whose both process group AND session equal D04 ID."""
    found = []
    for item in Path("/proc").iterdir():
        if not item.name.isdigit():
            continue
        try:
            # comm may contain spaces/parentheses; split after last ')'.
            rest = (item / "stat").read_text().rsplit(")", 1)[1].split()
            state, pgrp, sid = rest[0], int(rest[2]), int(rest[3])
            if state not in ("Z", "X") and pgrp == session_id and sid == session_id:
                found.append({"pid": int(item.name), "state": state})
        except (OSError, ValueError, IndexError):
            continue
    return sorted(found, key=lambda x: x["pid"])


def _wait_empty(session_id: int, timeout_s: float) -> list[dict]:
    until = time.monotonic() + timeout_s
    while True:
        live = _members(session_id)
        if not live or time.monotonic() >= until:
            return live
        time.sleep(min(0.1, max(0.01, until - time.monotonic())))


def _signal_owned(session_id: int, which: signal.Signals) -> bool:
    if not _members(session_id):
        return False
    try:
        os.killpg(session_id, which)
        return True
    except ProcessLookupError:
        return False


def stop_owned(processes: list, evidence: dict, *,
               interrupt_timeout: float = 18.0,
               terminate_timeout: float = 8.0,
               kill_timeout: float = 3.0) -> None:
    """Stop owned process groups and fail clean-shutdown audit on survivors."""
    audit = evidence.setdefault("shutdown_group_audit", {})
    for label, proc in reversed(processes):
        sid = int(proc.pid)  # _start uses start_new_session=True
        parent_already_exited = proc.poll() is not None
        original = _members(sid)
        row = {
            "session_id": sid, "parent_already_exited": parent_already_exited,
            "initial_count": len(original),
            "initial_pids": [member["pid"] for member in original],
            "sigint_sent": False, "sigterm_sent": False,
            "sigkill_sent": False, "residual_count": 0, "residual_pids": [],
        }
        audit[label] = row
        if original and parent_already_exited:
            evidence.setdefault("shutdown_orphaned_group_detected", []).append(label)
        if original:
            row["sigint_sent"] = _signal_owned(sid, signal.SIGINT)
            after = _wait_empty(sid, interrupt_timeout)
            if after:
                evidence.setdefault("shutdown_escalated", []).append(label)
                row["sigterm_sent"] = _signal_owned(sid, signal.SIGTERM)
                after = _wait_empty(sid, terminate_timeout)
            if after:
                row["sigkill_sent"] = _signal_owned(sid, signal.SIGKILL)
                after = _wait_empty(sid, kill_timeout)
            row["residual_count"] = len(after)
            row["residual_pids"] = [member["pid"] for member in after]
            if after:
                evidence.setdefault("shutdown_residual_groups", []).append(label)
        try:
            proc.wait(timeout=0.3)
        except subprocess.TimeoutExpired:
            pass
        evidence.setdefault("process_exit", {})[label] = proc.poll()
