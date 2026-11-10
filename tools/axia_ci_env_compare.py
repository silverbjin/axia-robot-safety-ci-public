#!/usr/bin/env python3
"""Compare owner WSL2 user-space with CI Ubuntu. Never treats WSLg/kernel as equal.

Expected exit: 0=PARITY_READY, 2=USERSPACE_DRIFT, 3=invalid/missing evidence.
This checks selected core ROS/Nav2/Gazebo versions and official source hashes,
not full machine identity or ROS/Gazebo physical execution success.
"""
import argparse
import json
from pathlib import Path
import re
import sys

SCHEMA = "axia_ros_jazzy_harmonic_env_v1"
CRITICAL = (
    "ros-jazzy-nav2-bringup",
    "ros-jazzy-nav2-minimal-tb3-sim",
    "ros-jazzy-navigation2",
    "ros-jazzy-nav2-amcl",
    "ros-jazzy-nav2-controller",
    "ros-jazzy-nav2-planner",
    "ros-jazzy-nav2-bt-navigator",
    "ros-jazzy-nav2-collision-monitor",
    "ros-jazzy-ros-gz",
    "ros-jazzy-rclpy",
    "ros-jazzy-rmw-fastrtps-cpp",
    "ros-jazzy-rmw-cyclonedds-cpp",
    "gz-harmonic",
    "gz-sim8",
    "libgz-sim8",
    "libsdformat14",
    "python3-colcon-common-extensions",
    "python3-yaml",
)
MIN_REQUIRED = (
    "ros-jazzy-nav2-bringup",
    "ros-jazzy-nav2-minimal-tb3-sim",
    "ros-jazzy-navigation2",
    "ros-jazzy-ros-gz",
)
OFFICIAL_REQUIRED = (
    "nav2_bringup/launch/tb3_simulation_launch.py",
    "nav2_minimal_tb3_sim/worlds/tb3_sandbox.sdf.xacro",
)


def read_profile(path):
    p = Path(path)
    if not p.is_file() or p.stat().st_size > 2_000_000:
        raise ValueError("PROFILE_MISSING_OR_TOO_LARGE")
    value = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise ValueError("PROFILE_SCHEMA_MISMATCH")
    apt = value.get("apt_packages")
    if not isinstance(apt, dict) or len(apt) > 2000:
        raise ValueError("INVALID_PACKAGE_MAP")
    for key, version in apt.items():
        if (not isinstance(key, str) or
            re.fullmatch(r"[a-z0-9+.-]+", key) is None or
            not isinstance(version, str) or len(version) > 120 or
            re.fullmatch(r"[a-zA-Z0-9.+:~_+-]+", version) is None):
            raise ValueError("INVALID_PACKAGE_OR_VERSION")
    return value


def compare(owner, ci):
    issues = []
    def mismatch(path, expected, actual):
        issues.append({"field": path, "owner": expected, "ci": actual})
    if owner.get("profile_kind") != "wsl2_owner" or owner.get("wsl2_detected") is not True:
        mismatch("owner.wsl2_confirmed", True, owner.get("wsl2_detected"))
    for key in ("id", "version_id"):
        if owner.get("os", {}).get(key) != ci.get("os", {}).get(key):
            mismatch("os." + key, owner.get("os", {}).get(key), ci.get("os", {}).get(key))
    if owner.get("os", {}).get("id") != "ubuntu" or owner.get("os", {}).get("version_id") != "24.04":
        mismatch("expected_owner_ubuntu_24_04", True, False)
    for field in ("architecture",):
        if owner.get(field) != ci.get(field):
            mismatch(field, owner.get(field), ci.get(field))
    for section, key in (("python", "major_minor"), ("ros", "distro")):
        if owner.get(section, {}).get(key) != ci.get(section, {}).get(key):
            mismatch(section + "." + key, owner.get(section, {}).get(key), ci.get(section, {}).get(key))
    if owner.get("ros", {}).get("distro") != "jazzy":
        mismatch("owner.jazzy", "jazzy", owner.get("ros", {}).get("distro"))
    for key in ("rmw_implementation", "discovery_range"):
        owner_value = owner.get("env_allowlist", {}).get(key, "")
        ci_value = ci.get("env_allowlist", {}).get(key, "")
        if owner_value not in ("", None) and owner_value != ci_value:
            mismatch("env_allowlist." + key, owner_value, ci_value)

    packages = owner["apt_packages"]
    installed = ci["apt_packages"]
    for key in MIN_REQUIRED:
        if key not in packages:
            mismatch("owner_missing." + key, "installed", "missing")
    for key in CRITICAL:
        if key not in packages:
            continue
        if installed.get(key) != packages[key]:
            mismatch("package." + key, packages[key], installed.get(key))

    before = owner.get("ros", {}).get("official_file_sha256", {})
    after = ci.get("ros", {}).get("official_file_sha256", {})
    for key in OFFICIAL_REQUIRED:
        if key not in before:
            mismatch("owner_official_sha256." + key, "sha256", None)
        elif before[key] != after.get(key):
            mismatch("official_sha256." + key, before[key], after.get(key))
    result = {
        "schema": "axia_ci_owner_userspace_parity_v1",
        "status": "PARITY_READY" if not issues else "USERSPACE_DRIFT",
        "critical_issues": issues,
        "compared_core_packages": [k for k in CRITICAL if k in packages],
        "nonblocking_differences": [
            "WSL2 kernel and WSLg GPU cannot be reproduced by a Linux CI container",
            "Real ROS/Gazebo timing/Goal remains WSL2 Owner-only evidence",
        ],
        "certified_estop": False,
        "gazebo_goal_test_passed": False,
    }
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--owner", type=Path, required=True)
    p.add_argument("--ci", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        result = compare(read_profile(args.owner), read_profile(args.ci))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("AXIA_CI_ENV_PROFILE_INVALID " + str(exc), file=sys.stderr)
        return 3
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print("AXIA_CI_ENV_PARITY_STATUS=" + result["status"])
    print("AXIA_CI_ENV_CRITICAL_DRIFT_COUNT=" + str(len(result["critical_issues"])))
    for change in result["critical_issues"][:30]:
        print("AXIA_CI_ENV_DRIFT=" + change["field"])
    print("AXIA_CI_ENV_NO_GOAL_NO_ESTOP_CERTIFICATION")
    return 0 if result["status"] == "PARITY_READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
