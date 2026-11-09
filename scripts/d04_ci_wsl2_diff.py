#!/usr/bin/env python3
"""AXIA D04 forensic CI-vs-WSL2 diagnosis — evidence and host READ ONLY.

Reads the last owner evidence directory and captures bounded local host probes.
DOES NOT launch Gazebo, ROS nodes, a Goal, a Fault, or publish /cmd_vel.
Writes results to a *separate* diagnostic directory, not into signed evidence.
No upload, sudo, package installation, or Git modification.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

TWIST = "geometry_msgs/msg/Twist"
CMD_TOPICS = {
    "/cmd_vel_smoothed": ("velocity_smoother", "axia_safety_supervisor"),
    "/cmd_vel_supervised": ("axia_safety_supervisor", "collision_monitor"),
    "/cmd_vel": ("collision_monitor", "ros_gz_bridge"),
}
EVIDENCE_BASE = Path.home() / "axia_d04_evidence"
DIAG_BASE = Path.home() / "axia_d04_diagnostics"
PUBLIC_CI_RUN = "https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/42499547659"
P1_ORIGINAL_SHA = "caff1d1976f37a8be30ea2cbc4ea77261d3310d4"
P1_INSTRUCTOR_SHA = "c1b92d9dd3dd2cd038db16253102542d120ea87e"
PUBLIC_SOURCE_SHA = "f3ff2e1db9f37490c2d5965154d4c02898c43ea6"
ERROR_RE = re.compile(
    r"\b(ERROR|FATAL|Traceback|Exception|failed to|FileNotFound|No such file|"
    r"not found|not found:|No module named|invalid syntax|invalid.*SDF|"
    r"unexpected upstream|process has died|exit code -6|SIGABRT|"
    r"library not found|xcb|wayland|EGL|OGRE|could not find)\b",
    re.IGNORECASE,
)


def ci_scope_gap() -> dict:
    """Verified on the exact public CI run, NOT a runtime parity claim."""
    return {
        "reference": PUBLIC_CI_RUN,
        "head_sha": PUBLIC_SOURCE_SHA,
        "ci_python_contracts": True,           # 17/17
        "ci_jazzy_colcon": True,               # one ament_python package
        "ci_package_prefix": True,
        "ci_launch_show_args": True,
        "ci_real_p1_runtime": False,
        "ci_real_p1_command_graph": False,
        "ci_gazebo_gui": False,
        "ci_installed_package_yolo_inference": False,
        "ci_wslg": False,
        "ci_environment": "Ubuntu 24.04 hosted runner + ros:jazzy-ros-base-noble container; no WSLg",
        "reference_contract": "L0/L1 only; not equivalent to a full WSL2 D04 runtime check",
    }


def safe_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None


def safe_text(path: Path, max_chars: int = 2_000_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[-max_chars:]
    except OSError:
        return ""


def extract_error_lines(log: str, limit: int = 35) -> list[str]:
    """Capture grounded evidence strings, never assign causality from a regex."""
    lines = []
    for line in log.splitlines():
        if ERROR_RE.search(line):
            lines.append(line.strip()[:350])
    # Preserve earliest fatal messages and final error cluster.
    return (lines[:max(1, limit // 2)] +
            lines[-max(1, limit // 2):] if len(lines) > limit else lines)


def inspect_graph(graph: dict | None) -> dict:
    """Inspect only observer snapshots; never silently repair topology."""
    if not isinstance(graph, dict):
        return {"ready": False, "topics": {}, "blockers": ["P1_COMMAND_GRAPH_NO_SNAPSHOT"]}
    result = {}
    blockers = []
    for name, (expected_pub, expected_sub) in CMD_TOPICS.items():
        row = graph.get(name)
        if not isinstance(row, dict):
            row = {}
        pubs = row.get("publishers", []) or []
        subs = row.get("subscriptions", []) or []
        publisher_names = [x.get("node_name", "") for x in pubs if isinstance(x, dict)]
        subscriber_names = [x.get("node_name", "") for x in subs if isinstance(x, dict)]
        pub_ok = len(pubs) == 1 and publisher_names == [expected_pub]
        pub_type_ok = pub_ok and pubs[0].get("topic_type") == TWIST
        sub_ok = any(x.get("node_name") == expected_sub and
                     x.get("topic_type") == TWIST
                     for x in subs if isinstance(x, dict))
        if not (pub_ok and pub_type_ok and sub_ok):
            blockers.append("P1_COMMAND_GRAPH:" + name)
        result[name] = {
            "expected_publisher": expected_pub,
            "expected_subscriber": expected_sub,
            "publisher_names": publisher_names,
            "subscriber_names": subscriber_names,
            "publisher_types": [x.get("topic_type") for x in pubs if isinstance(x, dict)],
            "publisher_ok": pub_ok and pub_type_ok,
            "subscriber_ok": sub_ok,
            "endpoint_count": {"publishers": len(pubs), "subscriptions": len(subs)},
        }
    return {"ready": not blockers, "topics": result, "blockers": blockers}


def run_bounded(argv: list[str], timeout: float = 5.0, env: dict | None = None) -> dict:
    if shutil.which(argv[0]) is None:
        return {"status": "NOT_INSTALLED", "cmd": argv[:2]}
    try:
        p = subprocess.run(argv, capture_output=True, text=True,
                           timeout=timeout, check=False, env=env)
        return {
            "status": "PASS" if p.returncode == 0 else "FAIL",
            "return_code": p.returncode,
            "stdout": p.stdout[:2500],
            "stderr": p.stderr[:700],
        }
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT", "seconds": timeout}
    except OSError as exc:
        return {"status": "ERROR", "detail": type(exc).__name__}


def collect_host_facts() -> dict:
    """WSLg/GL, packages and ROS environment. No mutable ROS interaction."""
    os_release = safe_text(Path("/etc/os-release"), 4000)
    envnames = ("ROS_DISTRO", "ROS_DOMAIN_ID", "RMW_IMPLEMENTATION",
                "ROS_AUTOMATIC_DISCOVERY_RANGE", "DISPLAY", "WAYLAND_DISPLAY",
                "XDG_RUNTIME_DIR", "LIBGL_ALWAYS_SOFTWARE", "GALLIUM_DRIVER",
                "EGL_PLATFORM", "GZ_PARTITION", "GZ_SIM_RESOURCE_PATH")
    vars = {x: os.environ.get(x, "") for x in envnames}
    uname = safe_text(Path("/proc/sys/kernel/osrelease"), 500).strip()
    wsl_paths = {
        str(x): {"exists": x.exists(), "symlink": x.is_symlink()}
        for x in (Path("/mnt/wslg"), Path("/mnt/wslg/runtime-dir"),
                  Path("/tmp/.X11-unix"), Path("/tmp/.X11-unix/X0"))
    }
    pkg_names = [
        "ros-jazzy-nav2-bringup", "ros-jazzy-nav2-minimal-tb3-sim",
        "ros-jazzy-turtlebot3-gazebo", "ros-jazzy-ros-gz",
        "ros-jazzy-ros-gz-image", "ros-jazzy-xacro",
        "ros-jazzy-image-view", "ros-jazzy-rclpy",
        "gz-harmonic", "gz-sim8",
    ]
    packages = {}
    for name in pkg_names:
        r = run_bounded(["dpkg-query", "-W", "-f=${Version}", name], 2)
        packages[name] = r.get("stdout", "").strip() if r["status"] == "PASS" else "NOT_INSTALLED"
    disp = vars.get("DISPLAY", "")
    display_probe = (run_bounded(["xdpyinfo", "-display", disp], 5) if disp
                     else {"status": "BLOCKED", "detail": "DISPLAY unset"})
    gl_probe = (run_bounded(["glxinfo", "-B"], 7) if disp else
                {"status": "BLOCKED", "detail": "DISPLAY unset"})
    gz_probe = run_bounded(["gz", "sim", "--version"], 6)
    cache = Path.home() / ".cache/axia/d04"
    workspaces = [p for p in cache.glob("d04_package_ws_*/install/axia_d04_vision_demo")
                  if p.is_dir()] if cache.exists() else []
    return {
        "os_release": os_release,
        "kernel_release": uname,
        "wsl_detected": "microsoft" in uname.lower() or "wsl" in uname.lower(),
        "variables": vars, "wslg_paths": wsl_paths, "dpkg_versions": packages,
        "xdpyinfo": display_probe, "glxinfo": gl_probe, "gz_version": gz_probe,
        "package_install_candidates": [str(p) for p in workspaces][:8],
        "gui_probes_note": "xdpyinfo/glxinfo run with bounded timeouts, do not open GUI",
    }


def locate_latest(base: Path = EVIDENCE_BASE) -> Path:
    runs = [p for p in base.glob("d04-package-*") if p.is_dir() and
            (p / "owner_summary.json").is_file()]
    if not runs:
        raise FileNotFoundError(f"Existing owner evidence directory not found in {base}")
    return max(runs, key=lambda p: p.stat().st_mtime)


def build_report(evidence: Path, output: Path, *, collect_host: bool = True) -> dict:
    evidence = evidence.expanduser().resolve(strict=True)
    if not evidence.is_dir():
        raise NotADirectoryError(str(evidence))
    output = output.expanduser().resolve()
    if output == evidence or evidence in output.parents:
        raise ValueError("Forensic report must be OUTSIDE original evidence folder")
    output.mkdir(parents=True, exist_ok=True)
    live = evidence / "live"
    owner = safe_json(evidence / "owner_summary.json") or {}
    verdict = safe_json(live / "verdict.json") or {}
    graph_first_json = safe_json(live / "graph_first.json") or {}
    graph_second_json = safe_json(live / "graph_after_vision.json") or {}
    graph = inspect_graph(graph_first_json.get("graph"))
    log = safe_text(live / "package_launch.log")
    verifier_log = safe_text(evidence / "runtime.log")
    launch_args = safe_text(evidence / "launch_args.txt", 100_000)
    host = collect_host_facts() if collect_host else {"status": "SKIPPED_BY_TEST"}
    scope = ci_scope_gap()
    refs = {
        "private_sha": owner.get("private_sha"),
        "public_sha": owner.get("public_sha"),
        "runtime_status": verdict.get("status", "MISSING_VERDICT"),
        "wrapper_status": owner.get("status", "MISSING_OWNER_SUMMARY"),
        "gate_exit": owner.get("gate_exit"),
        "graph_oracle_reasons": (verdict.get("graph_first") or
                                  graph_first_json.get("verdict") or {}).get("reasons", []),
        "actual_live_person_verified": verdict.get("person_valid") is True,
        "actual_debug_image_verified": verdict.get("debug_image_saved") is True,
        "before_after_graph_present": bool(graph_second_json),
        "launched_cmd": (safe_json(live / "launch_command.json") or []),
    }
    clues = []
    if not graph["ready"]:
        clues.append({
            "id": "P1_COMMAND_GRAPH_NOT_READY", "level": "BLOCKED",
            "detail": "P1 publisher/subscriber topology never reached required state; independent of YOLO visibility",
            "action": "Review live/package_launch.log and live/graph_first.json; do not bypass graph gate",
        })
    if not log:
        clues.append({"id": "PACKAGE_LAUNCH_LOG_MISSING", "level": "INCONCLUSIVE",
                      "detail": "No package_launch.log available for early startup traceback"})
    if not refs["actual_live_person_verified"]:
        clues.append({"id": "YOLO_NOT_PROVEN", "level": "NOT_RUN_OR_FAILED",
                      "detail": "No actual person bbox/confidence proven by the submitted package run"})
    if scope["ci_gazebo_gui"] is False:
        clues.append({"id": "CI_GUI_NOT_TESTED", "level": "SCOPE_GAP",
                      "detail": "Public CI did not run Gazebo GUI/WSLg; environment equality is not proven"})
    if collect_host:
        vars = host.get("variables", {})
        if not vars.get("DISPLAY"):
            clues.append({"id": "WSLG_DISPLAY_UNSET", "level": "GUI_BLOCKED",
                          "detail": "DISPLAY absent from this diagnostic shell"})
        elif host.get("xdpyinfo", {}).get("status") != "PASS":
            clues.append({"id": "WSLG_DISPLAY_CONNECTIVITY_UNVERIFIED", "level": "GUI_SUSPECT",
                          "detail": "DISPLAY is set but xdpyinfo could not prove X11 connectivity"})
    bad_logs = extract_error_lines(log, limit=40)
    if bad_logs:
        clues.append({"id": "LAUNCH_LOG_ERRORS_PRESENT", "level": "CHECK_LOG",
                      "detail": "Excerpts are evidence, not a confirmed causal chain"})
    result = {
        "schema_version": 1,
        "case_status": "CASE_NOT_PROVEN" if refs["runtime_status"] !=
                       "PASS_P1_AND_YOLO_PACKAGE_RUNTIME" else "PACKAGE_RUNTIME_REPORTED_PASS",
        "evidence_directory": str(evidence),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "ci_scope_gap": scope,
        "scope_gap": scope,
        "verdict": verdict,
        "run_summary": refs,
        "graph": graph,
        "graph_after_vision": inspect_graph(graph_second_json.get("graph")),
        "launch_error_excerpts": bad_logs,
        "verifier_error_excerpts": extract_error_lines(verifier_log, limit=12),
        "launch_args_contains_p1": "p1_launch" in launch_args,
        "host": host,
        "diagnoses": clues,
        "no_commands_issued": True,
        "no_goal_or_fault_or_cmd_vel": True,
        "not_a_certified_estop_test": True,
    }
    path = output / "AXIA_D04_CI_WSL2_DIFF.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    md = [
        "# AXIA D04 — 공개 CI / WSL2 실제 실행 차이 분석",
        "",
        f"- Evidence: \`{evidence}\`",
        f"- Runtime: **{refs['runtime_status']}**, gate RC={refs['gate_exit']}",
        f"- P1 graph: **{'PASS' if graph['ready'] else 'BLOCKED'}**",
        f"- GUI: {'DISPLAY=' + host.get('variables',{}).get('DISPLAY','') if collect_host else 'not probed'}",
        "",
        "## 검증 수준 비교",
        "",
        "| 항목 | 공개 CI (기준 run) | WSL2 제출 증거 |",
        "|---|---|---|",
        "| Python 계약 | PASS 17/17 | 코드와 런타임 동등성 별도 |",
        "| Jazzy colcon / 패키지 인식 | PASS | PASS (사용자 로그) |",
        "| Launch --show-args | PASS | PASS (사용자 로그) |",
        "| 실제 P1 노드 제어 그래프 | **NOT_RUN** | **" +
          ("PASS" if graph["ready"] else "BLOCKED") + "** |",
        "| Gazebo GUI / WSLg | **NOT_RUN** | 화면 미표시 (사용자 관찰) |",
        "| 실제 새 패키지 YOLO 검출 | **NOT_RUN** | " +
          ("PASS" if refs["actual_live_person_verified"] else "NOT_PROVEN") + " |",
        "",
        f"CI 기준: {PUBLIC_CI_RUN} (source={PUBLIC_SOURCE_SHA})",
        "",
        "## P1 /cmd_vel 발행·구독 원본",
        "",
        "| 토픽 | 기대 발행자 | 실제 발행자 | 기대 구독자 | 실제 구독자 | 판정 |",
        "|---|---|---|---|---|---|",
    ]
    for topic, row in graph["topics"].items():
        ok = row["publisher_ok"] and row["subscriber_ok"]
        md.append("| " + " | ".join((topic, row["expected_publisher"],
             ", ".join(row["publisher_names"]) or "NONE",
             row["expected_subscriber"], ", ".join(row["subscriber_names"]) or "NONE",
             "PASS" if ok else "FAIL")) + " |")
    md += ["", "## 우선 확인해야 할 원인 후보 (확정 아님)", ""]
    for n, obj in enumerate(clues, 1):
        md.append(f"{n}. **{obj['id']}** [{obj['level']}]: {obj['detail']}")
    md += ["", "## 실제 Launch 로그의 오류 근거 (자동 추출)", ""]
    if bad_logs:
        md += ["\`\`\`text", *bad_logs[:35], "\`\`\`"]
    else:
        md.append("오류 정규식에 맞는 줄이 없거나 로그가 없습니다. 최초 오류의 부재를 증명하지 않습니다.")
    md += ["", "## 현재 환경 및 WSLg 점검", ""]
    if collect_host:
        for k in ("DISPLAY", "WAYLAND_DISPLAY", "ROS_DOMAIN_ID", "GZ_PARTITION",
                  "LIBGL_ALWAYS_SOFTWARE", "GALLIUM_DRIVER"):
            md.append(f"- \`{k}\`: \`{host['variables'].get(k,'')}\`")
        md.append(f"- X11 연결 검사: **{host['xdpyinfo'].get('status')}**")
        md.append(f"- OpenGL 검사: **{host['glxinfo'].get('status')}**")
        md.append(f"- WSL 감지: **{host['wsl_detected']}**")
        md.append("- ROS/Gazebo apt versions: 상세 JSON의 host.dpkg_versions 참고")
    else:
        md.append("호스트 점검을 생략했습니다.")
    md += [
        "", "## 후속 진단 순서",
        "",
        "1. \`live/package_launch.log\` 최초 ERROR/Traceback 및 xacro/Gazebo 실행 오류 확인",
        "2. \`live/graph_first.json\`의 세 토픽 발행자·구독자 / ROS_DOMAIN_ID 확인",
        "3. \`DISPLAY\`, \`xdpyinfo\`, \`glxinfo\`로 GUI 경로 분리 검사",
        "4. P1 기동을 수정해 실제 그래프 PASS 이후에만 /camera/image_raw와 YOLO person 판단",
        "5. 종료 중 planner_server SIGABRT는 독립 이슈로 취급",
        "",
        "**판정 경계:** 이 보고서는 제출된 과거 로그의 포렌식 비교다. "
        "실제 새 P1/Gazebo 실행이나 E-Stop 인증 시험을 수행하지 않는다.",
    ]
    (output / "AXIA_D04_CI_WSL2_DIFF.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({
        "case_status": result["case_status"],
        "evidence": str(evidence),
        "p1_graph_ready": graph["ready"],
        "graph_blockers": graph["blockers"],
        "launch_log_matches": len(bad_logs),
        "diag_json": str(path),
        "diag_md": str(output / "AXIA_D04_CI_WSL2_DIFF.md"),
    }, ensure_ascii=False))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--evidence", type=Path, help="Original owner evidence folder")
    p.add_argument("--out", type=Path, help="Separate output directory")
    p.add_argument("--no-host", action="store_true",
                   help="Skip local versions/WSLg read-only probes")
    a = p.parse_args()
    source = a.evidence or locate_latest()
    out = a.out or DIAG_BASE / source.name
    try:
        build_report(source, out, collect_host=not a.no_host)
        return 0
    except (OSError, ValueError) as exc:
        print(f"D04_DIAGNOSTIC_BLOCKED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
