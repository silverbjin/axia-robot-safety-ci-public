#!/usr/bin/env python3
"""AXIA D04 packaged ROS2 launch actual P1+YOLO acceptance (read-only).

Distinct from the previous verified-script runner: starts *the installed
axia_d04_vision_demo ROS2 package*. Fails closed unless the exact P1 command
graph and real person bbox/confidence/debug PNG all exist.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import threading
import hashlib
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import time

from d04_waffle_pi_rgb_preflight import _start, sync_ros_discovery_environment
from d04_owned_gui_shutdown import stop_owned, wait_for_gui_hold
from d04_p1_yolo_live import graph_oracle, core_chain, sensor_sample
from d04_yolo_person_runtime import _watch_detections_and_images, valid_person, valid_rgb
from d04_nav2_orderly_shutdown import request_nav2_shutdown
from d04_nav2_initialpose_ready import request_initialpose_ready

EXPECTED_P1 = "653ef49c30973c57a9fcc34b7b2fcc185bc84d95"
EXPECTED_MODEL = "4f44c33cea12d4b5785e5e7c0a20c13d0c62a77de607ce96a40d6036c7d7bbcf"
EXPECTED_ACTOR = "49af0df3a319d1cb8ca2cebf02dbd00f625e5d5bec820bc5e109925b18b65c6e"

@contextmanager
def visible_stage(name: str, interval_s: float = 8):
    """Emit progress during blocking ROS/Gazebo checks without claiming success."""
    finished = threading.Event()
    start = time.monotonic()
    print(f"[D04][{name}] START", flush=True)
    def heartbeat():
        while not finished.wait(interval_s):
            print(f"[D04][{name}] RUNNING elapsed={time.monotonic()-start:.0f}s", flush=True)
    worker = threading.Thread(target=heartbeat, daemon=True)
    worker.start()
    try:
        yield
    finally:
        finished.set()
        worker.join(timeout=1)
        print(f"[D04][{name}] DONE elapsed={time.monotonic()-start:.0f}s", flush=True)


def graph_oracle_while_launch_alive(root: Path, env: dict, out: Path,
                                   label: str, live_launch, timeout: int = 150):
    """Read real P1 graph; abort promptly if actual ROS launch exits beforehand.

    The original P1 oracle and topology criteria are unchanged. No shortcut to
    ACCEPTED is possible. This only avoids a useless 150s wait after a crash.
    """
    graph_path = out / ("graph_" + label + ".json")
    log_path = out / ("graph_" + label + ".log")
    args = [
        sys.executable, str(root / "tools/p1_t05_graph_oracle.py"),
        "--output", str(graph_path), "--timeout", str(timeout),
    ]
    deadline = time.monotonic() + timeout + 10
    with log_path.open("w", encoding="utf-8") as stream:
        oracle = subprocess.Popen(args, cwd=root, env=env,
                                  stdout=stream, stderr=subprocess.STDOUT)
        try:
            while oracle.poll() is None:
                if live_launch.poll() is not None:
                    raise RuntimeError(
                        "D04_PACKAGE_LAUNCH_EXITED_EARLY: rc=" +
                        str(live_launch.returncode) +
                        "; review live/package_launch.log first"
                    )
                if time.monotonic() >= deadline:
                    raise TimeoutError("P1_ORACLE_TIMEOUT")
                time.sleep(0.4)
        finally:
            if oracle.poll() is None:
                oracle.terminate()
                try:
                    oracle.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    oracle.kill()
                    oracle.wait(timeout=3)
    if not graph_path.is_file():
        return {"passed": False, "graph": {},
                "verdict": {"passed": False, "reasons": ["NO_GRAPH_JSON"]}}
    data = json.loads(graph_path.read_text(encoding="utf-8"))
    return {"passed": oracle.returncode == 0 and
            data.get("verdict", {}).get("passed") is True,
            "graph": data.get("graph", {}),
            "verdict": data.get("verdict", {})}


def build_launch_command(p1: Path, model: Path, actor: Path, *, gui: bool = False):
    if p1.name != "axia_tb3_p1.launch.py":
        raise ValueError("Only original AXIA P1 launch is accepted")
    return [
        "ros2", "launch", "axia_d04_vision_demo", "d04_p1_yolo.launch.py",
        "p1_launch:=" + str(p1.resolve()),
        "onnx_model:=" + str(model.resolve()),
        "actor_dae:=" + str(actor.resolve()),
        "use_rviz:=false",
        "headless:=" + ("False" if gui else "True"),
        "show_image:=" + ("true" if gui else "false"),
        "cpu_renderer:=" + ("false" if gui else "true"),
    ]


def run(a) -> int:
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    verdict = {
        "gate": "G-D04-PACKAGE-P1-YOLO",
        "status": "BLOCKED_OR_INCONCLUSIVE",
        "p1_expected_sha": EXPECTED_P1,
        "goal_sent": False, "fault_injected": False,
        "cmd_vel_published_by_demo": False,
        "certified_estop_verified": False,
        "p1_g00_g04_accepted": False,
        "shutdown_quality": "NOT_EVALUATED",
        "shutdown_service": None,
        "motion_verified": False,
    }
    env = os.environ.copy()
    env["ROS_DOMAIN_ID"] = "40"
    env["ROS_AUTOMATIC_DISCOVERY_RANGE"] = "LOCALHOST"
    env["GZ_PARTITION"] = "axia_d04_pkg_" + str(os.getpid())
    env["AXIA_P0_SIM_ONLY"] = "1"
    # WSLg GUI: allow host-accelerated GL when available. Forcing llvmpipe
    # on the instructor laptop can prevent the 6-s actor cycle advancing in
    # observable wall time. Preserve the proven CPU fallback for headless CI.
    if a.gui:
        env.pop("LIBGL_ALWAYS_SOFTWARE", None)
        env.pop("GALLIUM_DRIVER", None)
        verdict["render_policy"] = "WSLG_HOST_OPENGL"
    else:
        env["LIBGL_ALWAYS_SOFTWARE"] = "1"
        env["GALLIUM_DRIVER"] = "llvmpipe"
        verdict["render_policy"] = "HEADLESS_LLVMPIPE"
    env.pop("EGL_PLATFORM", None)
    sync_ros_discovery_environment(env)
    proc = []
    owner_stop_signal = {"name": None}
    def _owner_stop(signum, _frame):
        owner_stop_signal["name"] = signal.Signals(signum).name
        raise RuntimeError("D04_OWNER_STOP_REQUESTED_" + owner_stop_signal["name"])
    signal.signal(signal.SIGINT, _owner_stop)
    signal.signal(signal.SIGTERM, _owner_stop)
    try:
        p1root = a.instructor.resolve()
        sha = subprocess.check_output(
            ["git", "-C", str(p1root), "rev-parse", "HEAD"], text=True).strip()
        if sha != EXPECTED_P1 and sha != a.d04_private_sha:
            raise ValueError("Private instructor source SHA not approved")
        p1 = p1root / "ros2_ws/src/axia_safety_bringup/launch/axia_tb3_p1.launch.py"
        if not p1.is_file():
            raise FileNotFoundError(p1)
        if hashlib.sha256(a.model.read_bytes()).hexdigest() != EXPECTED_MODEL:
            raise ValueError("Model SHA mismatch")
        if hashlib.sha256(a.actor.read_bytes()).hexdigest() != EXPECTED_ACTOR:
            raise ValueError("Actor SHA mismatch")
        verdict["instructor_sha"] = sha
        cmd = build_launch_command(p1, a.model, a.actor, gui=a.gui)
        (out / "launch_command.json").write_text(json.dumps(cmd, indent=2) + "\n")
        print(f"[D04][LAUNCH] Starting installed ROS2 package; GUI={'ON' if a.gui else 'OFF'}; no Goal/Fault/cmd_vel", flush=True)
        launch_process = _start("package_launch", cmd, env, out, proc)
        with visible_stage("P1_GRAPH_BEFORE"):
            first = graph_oracle_while_launch_alive(
                p1root, env, out, "first", launch_process, timeout=150)
        verdict["graph_first"] = first.get("verdict")
        if not first["passed"]:
            raise RuntimeError("P1 original graph was not ready")
        with visible_stage("NAV2_INITIALPOSE_READY"):
            verdict["nav2_initialpose_ready"]=request_initialpose_ready(env,out,timeout_s=70)
        if verdict["nav2_initialpose_ready"].get("passed") is not True:
            raise RuntimeError("Nav2 planner/localization not ACTIVE after simulation initialpose")
        with visible_stage("P1_SENSOR_INPUTS"):
            verdict["clock_samples"] = sensor_sample("/clock", "clock")
            verdict["scan_samples"] = sensor_sample("/scan", "scan")
            verdict["odom_samples"] = sensor_sample("/odom", "odom")
        print(f"[D04][SENSORS] /clock={verdict['clock_samples']} /scan={verdict['scan_samples']} /odom={verdict['odom_samples']}", flush=True)
        if not all(verdict[k] > 0 for k in ("clock_samples", "scan_samples", "odom_samples")):
            raise RuntimeError("P1 sensors not active")
        print("[D04][YOLO] Waiting for real Gazebo RGB -> ONNX person bbox + debug image", flush=True)
        with visible_stage("RGB_YOLO_PERSON", interval_s=5):
            evidence = _watch_detections_and_images(out, duration_s=130, require_motion=True)
        person = evidence.get("person")
        print(
            f"[D04][PERSON] class={person.get('class_name') if person else 'NOT_DETECTED'} "
            f"confidence={person.get('score',0):.3f} "
            f"bbox={[(person or {}).get(k) for k in ('center_x','center_y','size_x','size_y')]} "
            f"frames(rgb/det/debug)={evidence.get('camera_frames',0)}/"
            f"{evidence.get('detection_frames',0)}/{evidence.get('debug_frames',0)}",
            flush=True)
        verdict["vision"] = evidence
        verdict["motion_verified"] = evidence["motion_evidence"]["passed"]
        print("[D04][MOTION] "+json.dumps(evidence["motion_evidence"],ensure_ascii=False)[:850],flush=True)
        verdict["person_valid"] = bool(
            evidence.get("person") and valid_person(evidence["person"]))
        verdict["rgb_valid"] = bool(
            evidence.get("first_image") and valid_rgb(evidence["first_image"]))
        verdict["debug_image_saved"] = evidence.get("debug_saved") is True
        with visible_stage("P1_GRAPH_AFTER"):
            after = graph_oracle(p1root, env, out, "after_vision", timeout=50)
        verdict["graph_after_vision"] = after.get("verdict")
        verdict["graph_stable"] = bool(
            after["passed"] and core_chain(first["graph"]) == core_chain(after["graph"]))
        if not all(verdict.get(x) for x in (
            "person_valid", "rgb_valid", "debug_image_saved", "graph_stable",
            "motion_verified"
        )):
            raise RuntimeError("Package vision or P1 graph gate failed")
        verdict["status"] = "PASS_P1_AND_YOLO_PACKAGE_RUNTIME"
        print("[D04][PASS] Real person detection + unchanged P1 velocity graph verified", flush=True)
        if a.gui:
            print("[D04][GUI] Check Gazebo and 'axia_d04_yolo_preview' video windows; "
                  "human actor is VISUAL-ONLY and robot stays stationary.", flush=True)
            with visible_stage("GUI_DEMO_HOLD", interval_s=10):
                verdict["gui_hold"] = wait_for_gui_hold(
                    launch_process.pid, min(max(a.hold_seconds, 0), 120))
                if verdict["gui_hold"]["reason"] == "GAZEBO_GUI_EXITED_OR_RESTARTED":
                    print("[D04][GUI] First Gazebo GUI exit/restart detected; "
                          "closing owned preview and launch group now", flush=True)
    except Exception as exc:
        verdict["blocker"] = type(exc).__name__ + ":" + str(exc)[:500]
        print(f"[D04][BLOCKED] {verdict['blocker']}", flush=True)
    finally:
        # Prevent a second Ctrl+C/SIGTERM from aborting owned-group cleanup.
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
        if owner_stop_signal["name"]:
            verdict["owner_stop_signal"] = owner_stop_signal["name"]
            verdict["status"] = "BLOCKED_OWNER_INTERRUPTED"
        print("[D04][SHUTDOWN] Requesting Nav2 managed lifecycle Shutdown before SIGINT",flush=True)
        if verdict["status"]=="PASS_P1_AND_YOLO_PACKAGE_RUNTIME" and proc:
            verdict["shutdown_service"] = request_nav2_shutdown(env,out,timeout_s=65)
        else:
            verdict["shutdown_service"] = {"passed":False,"skipped":"NOT_RUNTIME_ACCEPTED"}
        print("[D04][SHUTDOWN] Stopping launch process group",flush=True)
        if owner_stop_signal["name"]:
            stop_owned(proc, verdict, interrupt_timeout=4.0,
                       terminate_timeout=3.0, kill_timeout=2.0)
        else:
            stop_owned(proc, verdict)
        verdict["gui_cleanup_contract"] = "D04_OWNED_ROS_SESSION_V1"
        group_audit = verdict.get("shutdown_group_audit", {})
        group_clean = bool(group_audit) and all(
            row.get("residual_count") == 0 for row in group_audit.values()
        )
        print("[D04][GUI_SHUTDOWN_AUDIT] " + json.dumps({
            "owned_session_clean": group_clean,
            "groups": group_audit,
            "orphaned_groups": verdict.get("shutdown_orphaned_group_detected", []),
            "signal": verdict.get("owner_stop_signal"),
        }, ensure_ascii=False), flush=True)
        log=out/"package_launch.log"
        lines=log.read_text(errors="replace") if log.exists() else ""
        sigabrt=bool("exit code -6" in lines or "SIGABRT" in lines)
        if sigabrt:
            verdict["shutdown_quality"]="WARN_SIGABRT"
        elif verdict.get("shutdown_residual_groups") or any(
            row.get("residual_count", 0) > 0
            for row in verdict.get("shutdown_group_audit", {}).values()
        ):
            verdict["shutdown_quality"]="BLOCKED_RESIDUAL_GUI_PROCESSES"
        elif verdict.get("shutdown_orphaned_group_detected"):
            verdict["shutdown_quality"]="BLOCKED_PREMATURE_LAUNCH_EXIT_WITH_ORPHANS"
        elif verdict["shutdown_service"].get("passed") is not True:
            verdict["shutdown_quality"]="BLOCKED_NAV2_SHUTDOWN_SERVICE"
        elif verdict.get("shutdown_escalated"):
            verdict["shutdown_quality"]="BLOCKED_TERMINATION_ESCALATION"
        else:
            verdict["shutdown_quality"]="PASS_NAV2_MANAGED_NO_SIGABRT"
        if verdict["status"]=="PASS_P1_AND_YOLO_PACKAGE_RUNTIME":
            if verdict["shutdown_quality"]=="PASS_NAV2_MANAGED_NO_SIGABRT":
                verdict["status"]="PASS_P1_AND_YOLO_PACKAGE_CLEAN_EXIT"
            else:
                verdict["status"]="BLOCKED_SHUTDOWN_UNCLEAN"
        (out / "verdict.json").write_text(
            json.dumps(verdict, indent=2, ensure_ascii=False) + "\n")
        files = sorted(f for f in out.rglob("*") if f.is_file() and f.name != "SHA256SUMS")
        (out / "SHA256SUMS").write_text("".join(
            hashlib.sha256(f.read_bytes()).hexdigest() + "  " +
            f.relative_to(out).as_posix() + "\n" for f in files))
        print(json.dumps({k:verdict.get(k) for k in (
            "gate", "status", "blocker", "graph_first", "graph_after_vision",
            "graph_stable", "person_valid", "rgb_valid", "debug_image_saved",
            "shutdown_quality")}, ensure_ascii=False))
    return 0 if verdict["status"] == "PASS_P1_AND_YOLO_PACKAGE_CLEAN_EXIT" else 2


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for name in ("instructor", "model", "actor", "out"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--d04-private-sha", required=True)
    p.add_argument("--gui", action="store_true")
    p.add_argument("--hold-seconds", type=int, default=90)
    raise SystemExit(run(p.parse_args()))
