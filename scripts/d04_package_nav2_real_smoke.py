#!/usr/bin/env python3
"""REAL ROS 2 Jazzy packaged D04 + official Nav2 + Gazebo + yolo_ros smoke.

Public CI ONLY: a shim launches official upstream Nav2 Waffle, not private AXIA P1.
It exercises the *actual installed D04 package* with canonical headless=False,
the real Gazebo scene, image bridge and ONNX person bbox/confidence.

Never infer P1 Safety Supervisor/Collision Monitor acceptance from this test.
No synthetic ROS topics, publishers, Goal, Fault, direct motor commands.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from d04_waffle_pi_rgb_preflight import _start, _stop_all, sync_ros_discovery_environment
from d04_nav2_orderly_shutdown import request_nav2_shutdown
from d04_yolo_person_runtime import (
    _watch_detections_and_images, valid_rgb, valid_person,
    PINNED_ONNX_SHA256,
)

ACTOR_SHA256 = "49af0df3a319d1cb8ca2cebf02dbd00f625e5d5bec820bc5e109925b18b65c6e"
SHIM = '''"""CI-only official Nav2 simulation wrapper: NOT AXIA P1."""
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
from pathlib import Path

def generate_launch_description():
    upstream = Path(get_package_share_directory("nav2_bringup")) / "launch/tb3_simulation_launch.py"
    names = ("robot_sdf", "world", "headless", "use_rviz", "use_composition",
             "autostart", "use_sim_time")
    return LaunchDescription([IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(upstream)),
        launch_arguments={key: LaunchConfiguration(key) for key in names}.items(),
    )])
'''


def launch_command(shim: Path, onnx: Path, actor: Path) -> list[str]:
    if shim.name != "axia_tb3_p1.launch.py":
        raise ValueError("Shim must only be explicitly named for CI launch")
    return [
        "ros2", "launch", "axia_d04_vision_demo", "d04_p1_yolo.launch.py",
        "p1_launch:=" + str(shim.resolve()),
        "onnx_model:=" + str(onnx.resolve()),
        "actor_dae:=" + str(actor.resolve()),
        "headless:=False",  # Regression target! Official Nav2 PythonExpression
        "show_image:=False",  # no GUI provider on CI
        "use_rviz:=False",
        "cpu_renderer:=True",  # software OGRE under Xvfb
    ]


def run() -> int:
    out = Path(os.environ.get("D04_OUTPUT_DIR", "results/d04-packaged-nav2-live"))
    out.mkdir(parents=True, exist_ok=True)
    verdict = {
        "gate":"G-D04-PACKAGED-OFFICIAL-NAV2-RUNTIME",
        "status":"BLOCKED_OR_INCONCLUSIVE",
        "private_axia_p1_executed":False,
        "private_p1_graph_accepted":False,
        "goal_sent":False,"fault_injected":False,
        "cmd_vel_published_by_probe":False,
        "certified_estop_verified":False,
        "source_sha":os.environ.get("AXIA_TESTED_HEAD_SHA","NOT_PINNED"),
    }
    processes=[]
    env=os.environ.copy()
    env["ROS_DOMAIN_ID"]="40"
    env["ROS_AUTOMATIC_DISCOVERY_RANGE"]="LOCALHOST"
    env["GZ_PARTITION"]="axia_d04_pkg_nav2_"+str(os.getpid())
    env["GZ_SIM_RESOURCE_PATH"]=str(
        Path(os.environ.get("GZ_SIM_RESOURCE_PATH","/opt/ros/jazzy/share")))
    env["LIBGL_ALWAYS_SOFTWARE"]="1"
    env["GALLIUM_DRIVER"]="llvmpipe"
    env.pop("EGL_PLATFORM",None)
    sync_ros_discovery_environment(env)
    try:
        model=Path(os.environ["AXIA_ONNX_PATH"])
        actor=Path(os.environ["AXIA_ACTOR_DAE"])
        if hashlib.sha256(model.read_bytes()).hexdigest()!=PINNED_ONNX_SHA256:
            raise ValueError("Unpinned ONNX")
        if hashlib.sha256(actor.read_bytes()).hexdigest()!=ACTOR_SHA256:
            raise ValueError("Unpinned actor DAE")
        shim=out/"axia_tb3_p1.launch.py"
        shim.write_text(SHIM)
        cmd=launch_command(shim,model,actor)
        verdict["cli_boolean_arguments"]=[x for x in cmd if x.startswith("headless:=")]
        _start("installed_d04_package",cmd,env,out,processes)
        # Authentic rclpy subscriptions; only real Gazebo Image may satisfy the gate.
        print("[D04][L2] Executing installed D04 package / official Nav2 / real Gazebo + person ONNX",flush=True)
        seen=_watch_detections_and_images(out,duration_s=135,require_motion=True)
        verdict["ros_evidence"]=seen
        verdict["rgb_valid"]=bool(seen.get("first_image") and valid_rgb(seen["first_image"]))
        verdict["person_valid"]=bool(seen.get("person") and valid_person(seen["person"]))
        verdict["debug_saved"]=seen.get("debug_saved") is True
        verdict["motion_verified"]=seen["motion_evidence"]["passed"]
        if not all(verdict[k] for k in ("rgb_valid","person_valid","debug_saved","motion_verified")):
            raise RuntimeError("Real upstream Nav2 Waffle RGB/person/debug evidence absent")
        verdict["status"]="PASS_PACKAGED_OFFICIAL_NAV2_GAZEBO_PERSON"
    except Exception as exc:
        verdict["blocker"]=type(exc).__name__+": "+str(exc)[:500]
    finally:
        if verdict["status"]=="PASS_PACKAGED_OFFICIAL_NAV2_GAZEBO_PERSON" and processes:
            verdict["shutdown_service"]=request_nav2_shutdown(env,out,timeout_s=65)
        else:
            verdict["shutdown_service"]={"passed":False,"skipped":"VISION_NOT_ACCEPTED"}
        _stop_all(processes,verdict)
        logfile=out/"installed_d04_package.log"
        log=logfile.read_text(errors="replace") if logfile.is_file() else ""
        verdict["launch_no_lowercase_bool_nameerror"]="name 'false' is not defined" not in log
        verdict["launch_no_world_file_missing"]="No such file or directory: '/tmp/nav2_" not in log
        verdict["shutdown_quality"] = (
            "WARN_SIGABRT" if ("exit code -6" in log or "SIGABRT" in log)
            else "BLOCKED_NAV2_SHUTDOWN_SERVICE"
            if verdict["shutdown_service"].get("passed") is not True
            else "BLOCKED_TERMINATION_ESCALATION"
            if verdict.get("shutdown_escalated") else "PASS_NAV2_MANAGED_NO_SIGABRT"
        )
        if verdict["status"]=="PASS_PACKAGED_OFFICIAL_NAV2_GAZEBO_PERSON" and (
                verdict["shutdown_quality"]!="PASS_NAV2_MANAGED_NO_SIGABRT"):
            verdict["status"]="BLOCKED_SHUTDOWN_UNCLEAN"
            verdict["blocker"]="NAV2_SHUTDOWN_NOT_CLEAN"
        # Runtime must not silently PASS if Launch failed with a late NameError.
        if not verdict["launch_no_lowercase_bool_nameerror"] or not verdict["launch_no_world_file_missing"]:
            verdict["status"]="BLOCKED_OR_INCONCLUSIVE"
            verdict["blocker"]="NAV2_LAUNCH_REGRESSION"
        (out/"verdict.json").write_text(json.dumps(verdict,indent=2,ensure_ascii=False)+"\n")
        files=sorted(x for x in out.iterdir() if x.is_file() and x.name!="SHA256SUMS")
        (out/"SHA256SUMS").write_text("".join(
            hashlib.sha256(x.read_bytes()).hexdigest()+"  "+x.name+"\n" for x in files))
        print(json.dumps({k:verdict.get(k) for k in (
            "gate","status","blocker","rgb_valid","person_valid","debug_saved",
            "launch_no_lowercase_bool_nameerror","launch_no_world_file_missing",
            "motion_verified","shutdown_quality","shutdown_service"
        )},ensure_ascii=False),flush=True)
    return 0 if verdict["status"]=="PASS_PACKAGED_OFFICIAL_NAV2_GAZEBO_PERSON" else 2


if __name__=="__main__":
    raise SystemExit(run())
