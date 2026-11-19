#!/usr/bin/env python3
"""D08 pre-Goal read-only LIVE check in the already-running G07 world.

Reuses existing official D07 ComputePathToPose and D04/D05 live ROS
DetectionArray + registered Gazebo RGB-D. NO Gazebo launch, no
NavigateToPose, no /cmd_vel publisher or safety authority. Expects the
upstream yolo_ros node to be running already; if not, HOLD.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "d08" / "harness"))

EXPECTED_ROI = "D08_REAL_LIVE_PERSON_RANGE_2VALID_UNKNOWN_L2_PASS_NO_GOAL"
EXPECTED_PATH = "D08_REAL_THREE_OFFICIAL_NAV2_PATH_PHASES_L2_PASS_NO_GOAL"
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def validate_sources(world: Path, robot: Path, public_sha: str,
                     student_sha: str) -> dict:
    if not all(SHA40.fullmatch(x or "") for x in (public_sha, student_sha)):
        raise ValueError("D08_G07_READONLY_SOURCE_SHA_MISSING")
    cp = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                        capture_output=True, text=True, timeout=6)
    if cp.returncode != 0 or cp.stdout.strip() != public_sha:
        raise ValueError("D08_G07_READONLY_EXACT_PUBLIC_SOURCE_MISMATCH")
    for p in (world, robot):
        if not p.is_file() or p.is_symlink():
            raise ValueError("D08_G07_READONLY_SOURCE_NOT_REGULAR")
    w, r = ET.parse(world).getroot(), ET.parse(robot).getroot()
    sensor = r.findall(".//sensor[@name='axia_d08_registered_rgbd']")
    if (len(w.findall("./world")) != 1 or
        len(w.findall(".//model[@name='axia_p2_g07_obstacle']")) != 1 or
        len(sensor) != 1 or sensor[0].get("type") != "rgbd_camera" or
        sensor[0].findtext("./camera/image/width") != "640" or
        sensor[0].findtext("./camera/image/height") != "480" or
        len(r.findall(".//sensor[@name='hls_lfcd_lds']")) != 1 or
        r.findtext(".//sensor[@name='hls_lfcd_lds']/update_rate") != "10"):
        raise ValueError("D08_G07_READONLY_ONE_WORLD_RGBD_10HZ_SOURCE_INVALID")
    return {
        "public_sha": public_sha, "student_sha": student_sha,
        "world_sha256": hashlib.sha256(world.read_bytes()).hexdigest(),
        "robot_sha256": hashlib.sha256(robot.read_bytes()).hexdigest(),
    }


def verify_readonly_results(person: dict, official: dict) -> dict:
    if person.get("status") != EXPECTED_ROI or person.get("goal_sent") is not False or person.get("cmd_vel_published") is not False:
        raise ValueError("D08_G07_REAL_D04_D05_LIVE_ROI_UNVERIFIED")
    if (official.get("status") != EXPECTED_PATH or
        official.get("robot_moving_goal_sent") is not False or
        official.get("actual_cm_safety_ttl_proven") is not False):
        raise ValueError("D08_G07_REAL_D07_OFFICIAL_PATH_UNVERIFIED")
    return {
        "status": "D08_G07_REAL_READONLY_D04_D05_D07_PREGOAL_PASS_NOT_MOVING",
        "d04_person_detected_from_live_yolo": True,
        "d05_actual_registered_rgbd_two_valid_one_unknown": True,
        "d07_official_path_three_phases": True,
        "moving_goal_sent": False,
        "cm_guard_150ms_verified": False,
        "certified_estop": False,
    }


def run(out: Path, world: Path, robot: Path,
        public_sha: str, student_sha: str) -> int:
    if out.exists() or out.is_symlink():
        raise ValueError("D08_G07_READONLY_EVIDENCE_OUTPUT_EXISTS")
    out.mkdir(parents=True)
    result = {
        "status": "HOLD", "first_boundary": "NOT_RUN",
        "source": "existing_G07_Gazebo_without_new_launch",
        "moving_goal_sent": False, "certified_estop": False,
        "cm_guard_150ms_verified": False, "student_sha": student_sha,
        "public_sha": public_sha,
        "ros_domain_id": os.environ.get("ROS_DOMAIN_ID"),
        "gz_partition": os.environ.get("GZ_PARTITION"),
    }
    try:
        result["source_contract"] = validate_sources(
            world, robot, public_sha, student_sha)
        # No second Gazebo, no new node that can send a robot command.
        # The existing C++ yolo_ros is an external precondition.
        from d08_live_person_range_session import run_session
        from d08_public_gazebo_l2 import observe_real_front_scan
        from d08_same_world_replan import run as path_run
        live_dir = out / "actual_person_range"
        roi_rc = run_session(live_dir, dict(os.environ), public_sha,
                             robot, observe_real_front_scan)
        person = json.loads((live_dir / "verdict.json").read_text())
        result["actual_person_status"] = person.get("status")
        if roi_rc != 0:
            raise RuntimeError("D08_G07_FIRST_REAL_YOLO_D05_BOUNDARY:"
                               + str(person.get("first_boundary", "HOLD"))[:180])
        path_dir = out / "official_three_phase_path"
        path_rc = path_run(path_dir, dict(os.environ), public_sha)
        official = json.loads((path_dir / "verdict.json").read_text())
        result["official_path_status"] = official.get("status")
        if path_rc != 0:
            raise RuntimeError("D08_G07_FIRST_OFFICIAL_D07_PATH_BOUNDARY:"
                               + str(official.get("first_boundary", "HOLD"))[:180])
        result.update(verify_readonly_results(person, official))
        result["first_boundary"] = "NONE"
        print("D08_G07_REAL_READONLY_PREGOAL_D04_D05_D07_L2_PASS_NO_GOAL",
              flush=True)
    except Exception as exc:
        result["status"] = "HOLD"
        result["first_boundary"] = type(exc).__name__ + ":" + str(exc)[:260]
        print("D08_G07_READONLY_PREGOAL_HOLD_NO_GOAL "
              + result["first_boundary"], flush=True)
    finally:
        (out / "verdict.json").write_text(
            json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        (out / "SHA256SUMS").write_text(
            hashlib.sha256((out / "verdict.json").read_bytes()).hexdigest()
            + "  verdict.json\n", encoding="utf-8")
    return 0 if result["status"].endswith("_PASS_NOT_MOVING") else 2


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for field in ("out", "world", "robot"):
        p.add_argument("--" + field, required=True, type=Path)
    p.add_argument("--public-sha", required=True)
    p.add_argument("--student-sha", required=True)
    a = p.parse_args()
    return run(a.out, a.world, a.robot, a.public_sha, a.student_sha)


if __name__ == "__main__":
    raise SystemExit(main())
