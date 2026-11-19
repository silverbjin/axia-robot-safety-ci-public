#!/usr/bin/env python3
"""Read-only educational G07 demo verdict, never formal safety acceptance."""
import argparse
import json
import math
from pathlib import Path
import re

def measured(x):
    return type(x) in (float, int) and math.isfinite(x)

def classify(motion, shutdown, gui_windows, expected_source):
    if not isinstance(motion, dict) or not isinstance(shutdown, dict):
        raise ValueError("ORIGINAL_NATIVE_JSON_REQUIRED")
    c, s, t = (motion.get(k) for k in ("clear", "slow", "stop"))
    ok = (
        gui_windows == 2
        and motion.get("source_sha") == expected_source
        and re.fullmatch(r"[0-9a-f]{32}", str(motion.get("goal_uuid", ""))) is not None
        and motion.get("goal_sent") is True
        and motion.get("same_goal_executing_after_clear") is True
        and motion.get("slow_native_set_pose_ack") is True
        and motion.get("stop_native_set_pose_ack") is True
        and motion.get("goal_cancel_ack") is True
        and motion.get("goal_cancel_status") == 5
        and motion.get("status") == "CI_GAZEBO_MOVING_GOAL_CANDIDATE"
        and motion.get("first_timing_violation") is None
        and motion.get("guard_latched") is False
        and measured(motion.get("observed_odom_moved_m"))
        and motion["observed_odom_moved_m"] >= 0.05
        and measured(motion.get("odom_stopped_dwell_sec"))
        and motion["odom_stopped_dwell_sec"] >= 1.0
        and all(isinstance(x, dict) for x in (c, s, t))
        and all(measured(x.get(key)) for x in (c, s, t)
                for key in ("front_m", "supervised_vx", "cm_vx", "final_vx"))
        and c["front_m"] > 0.75 and c["cm_vx"] > 0.03 and c["final_vx"] > 0.03
        and 0.4 < s["front_m"] < 0.75
        and 0 < s["cm_vx"] <= 0.30 * s["supervised_vx"] + 0.01
        and 0 < s["final_vx"] <= 0.30 * s["supervised_vx"] + 0.01
        and 0.14 <= t["front_m"] < 0.4
        and abs(t["cm_vx"]) < 0.01 and abs(t["final_vx"]) < 0.01
        and shutdown.get("navigation_ack") is True
        and shutdown.get("localization_ack") is False
        and shutdown.get("localization_service_status") == "SERVICE_TIMEOUT"
    )
    return {
        "schema": "axia_g07_task04_mvp_educational_visual_verdict_v1",
        "status": ("MVP_VISUAL_L2_PASS_FORMAL_SHUTDOWN_HOLD" if ok else "HOLD"),
        "physical_demo_observed": bool(ok),
        "localization_shutdown_ack": False,
        "formal_l2_accepted": False,
        "owner_wsl2_l3_accepted": False,
        "certified_estop": False,
        "source_sha": expected_source,
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--motion", type=Path, required=True)
    p.add_argument("--shutdown", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--gui-windows", type=int, required=True)
    p.add_argument("--source-sha", required=True)
    args = p.parse_args()
    try:
        result = classify(json.loads(args.motion.read_text()),
                          json.loads(args.shutdown.read_text()),
                          args.gui_windows, args.source_sha)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print("AXIA_G07_MVP_VISUAL_REVIEW_HOLD:" + type(exc).__name__, flush=True)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("AXIA_G07_MVP_VISUAL_VERDICT " + json.dumps(result, sort_keys=True), flush=True)
    return 0 if result["physical_demo_observed"] else 2

if __name__ == "__main__":
    raise SystemExit(main())
