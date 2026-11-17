"""G07 C32: read-only localization native service vs server log first-stage join.

Only original wall-clock stamped Nav2 launch messages and native ACK payload.
Never equate rcl preshutdown, clean child exit, or missing log with a service ACK.
No ROS, Gazebo, Goal, subprocess or safety code here.
"""
from __future__ import annotations

import re

_LOG = re.compile(
    r"\[lifecycle_manager-\d+\]\s+\[[A-Z]+\]\s+"
    r"\[(\d+\.\d+)\]\s+\[lifecycle_manager_localization\]:\s*(.*)"
)
_ANSI = re.compile(r"\x1b\[[0-9;]*m")

def _hold(status, **details):
    return dict(schema="axia.g07.c32.localization_native_stage_v1",
                status=status, native_ack=False,
                server_callback_entry_observed=False,
                root_cause_proven=False, release_pass=False,
                owner_accepted=False, certified_estop=False, **details)

def assess_native_shutdown(native: dict, launch_text: str) -> dict:
    """Time-scoped server message observations, never native ACK inference."""
    if not isinstance(native, dict) or not isinstance(launch_text, str):
        return _hold("NATIVE_REQUEST_WALL_ALIGNMENT_UNVERIFIED")
    start = native.get("request_wall_ns")
    end = native.get("response_wall_ns")
    elapsed = native.get("response_wait_sec")
    if (type(start) is not int or type(end) is not int
            or type(elapsed) not in (int, float)
            or start <= 0 or end <= start or elapsed < 0
            or abs((end - start) / 1e9 - elapsed) > 0.15):
        return _hold("NATIVE_REQUEST_WALL_ALIGNMENT_UNVERIFIED")
    if native.get("status") == "ACK" and native.get("ack_response_received") is True:
        x = _hold("NATIVE_ACK_OBSERVED_REQUIRES_SEPARATE_SAFETY_GATES")
        x["native_ack"] = True
        return x
    if native.get("request_sent") is not True:
        return _hold("NATIVE_REQUEST_NOT_SENT")
    if native.get("ack_response_received") is True:
        return _hold("NATIVE_RESPONSE_CONTRADICTORY_HOLD")
    start_s = start / 1e9
    end_s = end / 1e9
    observed = []
    for raw in launch_text.splitlines():
        m = _LOG.search(_ANSI.sub("", raw))
        if not m:
            continue
        at = float(m.group(1))
        # Don't claim a later SIGINT/preshutdown corresponds to this native call.
        if start_s <= at <= end_s:
            observed.append(m.group(2).strip())
    enter = any("Shutting down managed nodes" in s for s in observed)
    complete = any("Managed nodes have been shut down" in s for s in observed)
    transitions = [s for s in observed if
                   s.startswith(("Deactivating ", "Cleaning up ", "Shutting down "))]
    if complete and enter:
        status = "SERVER_COMPLETED_BUT_CLIENT_ACK_MISSING"
    elif enter:
        status = "SERVER_CALLBACK_ENTERED_ACK_MISSING"
    else:
        status = "SERVICE_CALLBACK_NOT_OBSERVED_CAUSE_UNPROVEN"
    x = _hold(status, stage_messages_count=len(observed),
              managed_transition_messages=transitions[:10],
              native_status=native.get("status"),
              request_wall_start_ns=start, response_wall_end_ns=end)
    x["server_callback_entry_observed"] = enter
    x["server_shutdown_complete_log_observed"] = complete
    return x
