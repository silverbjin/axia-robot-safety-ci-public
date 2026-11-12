#!/usr/bin/env python3
"""D04 read-only child process-group shutdown, Linux/WSL2, stdlib only.

Upstream starts ros2 launch with start_new_session=True. Its previous helper
checked proc.poll() alone: dead parent could leave image_view/Gazebo children
alive. This audits the OWNED process group even if parent is already gone.
No process-name signal filtering or targeting unrelated ROS sessions.
"""
from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import time


def _members(session_id: int) -> list[dict]:
    """Live /proc processes in one D04-owned Linux session (any child PGID)."""
    found = []
    for item in Path("/proc").iterdir():
        if not item.name.isdigit():
            continue
        try:
            # comm may contain spaces/parentheses; split after last ')'.
            rest = (item / "stat").read_text().rsplit(")", 1)[1].split()
            state, pgrp, sid = rest[0], int(rest[2]), int(rest[3])
            if state not in ("Z", "X") and sid == session_id:
                found.append({"pid": int(item.name), "state": state, "pgrp": pgrp})
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
    members = _members(session_id)
    if not members:
        return False
    any_sent = False
    # ROS launch descendants can open a different PROCESS group but stay
    # in the same owned SESSION. Signal their unique groups, not other apps.
    for group in sorted({row["pgrp"] for row in members}):
        try:
            os.killpg(group, which)
            any_sent = True
        except ProcessLookupError:
            pass
    return any_sent


def _gazebo_gui_pids(session_id: int) -> set[int]:
    """Best-effort WSLg/Gazebo GUI process identity; no external X11 dependency."""
    result = set()
    for row in _members(session_id):
        try:
            raw = Path(f"/proc/{row['pid']}/cmdline").read_bytes()
            args = [x.decode(errors="replace") for x in raw.split(b"\0") if x]
            # Inspect the actual executable/script, not embedded Python -c
            # source code, which can contain a GUI filename as a literal.
            candidates = args[:1]
            if len(args) > 1 and args[1] not in ("-c", "-m"):
                candidates.append(args[1])
            gui_binary = any("gz-sim-gui" in Path(x).name for x in candidates)
            gz_cli = ("-g" in args and "sim" in args and
                      any(Path(x).name == "gz" for x in args[:3]))
            if gui_binary or gz_cli:
                result.add(row["pid"])
        except OSError:
            pass
    return result


def wait_for_gui_hold(session_id: int, seconds: float, *,
                      poll_interval: float = 0.4) -> dict:
    """Return early if a Gazebo GUI observed during HOLD is closed/restarted.

    If no owned Gazebo GUI is discoverable, retain the original fixed-duration
    hold rather than claiming a false GUI-close event. No ROS/Qt dependencies.
    """
    end = time.monotonic() + max(0.0, seconds)
    first_pids: set[int] = set()
    while time.monotonic() < end:
        current = _gazebo_gui_pids(session_id)
        if not first_pids and current:
            first_pids = current
        elif first_pids and not (first_pids & current):
            return {
                "reason": "GAZEBO_GUI_EXITED_OR_RESTARTED",
                "observed_gazebo_gui": True, "original_pids": sorted(first_pids),
                "last_gui_pids": sorted(current),
                "held_seconds_requested": seconds,
            }
        time.sleep(min(poll_interval, max(0.01, end - time.monotonic())))
    return {
        "reason": "HOLD_COMPLETE",
        "observed_gazebo_gui": bool(first_pids),
        "original_pids": sorted(first_pids),
        "held_seconds_requested": seconds,
    }


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
