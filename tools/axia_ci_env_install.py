#!/usr/bin/env python3
"""Pin a small, allowlisted ROS/Nav2/Gazebo CI core to owner apt versions.

NEVER changes WSL2. --apply is CI-container only; subprocess argv, no shell.
Rejects unavailable versions instead of silently using latest packages.
This does not reproduce WSL2 kernel, GUI/GPU or Gazebo Goal behavior.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from axia_ci_env_compare import CRITICAL, MIN_REQUIRED, read_profile


def selected_versions(owner):
    packages = owner["apt_packages"]
    if owner.get("profile_kind") != "wsl2_owner" or owner.get("wsl2_detected") is not True:
        raise ValueError("NOT_WSL_OWNER_PROFILE")
    if owner.get("os", {}).get("version_id") != "24.04" or owner.get("ros", {}).get("distro") != "jazzy":
        raise ValueError("WRONG_OWNER_OS_OR_ROS")
    for key in MIN_REQUIRED:
        if key not in packages:
            raise ValueError("OWNER_MISSING_REQUIRED_" + key)
    selected = {key: packages[key] for key in CRITICAL if key in packages}
    for key, version in selected.items():
        if not re.fullmatch(r"[a-z0-9+.-]+", key) or not re.fullmatch(r"[a-zA-Z0-9.+:~_+-]+", version):
            raise ValueError("UNSAFE_APT_PACKAGE_OR_VERSION")
    return selected


def available_versions(package):
    try:
        p = subprocess.run(["apt-cache", "madison", package], capture_output=True,
                           text=True, timeout=15, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return set()
    if p.returncode:
        return set()
    return {parts[1].strip() for line in p.stdout.splitlines()
            if len(parts := line.split("|")) >= 3}


def installed_version(package):
    try:
        p = subprocess.run(["dpkg-query", "-W", "-f=" + chr(36) + "{Version}",
                            package], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return p.stdout.strip() if p.returncode == 0 else ""


def make_plan(owner):
    target = selected_versions(owner)
    todo = []
    unavailable = []
    already = []
    for name, version in target.items():
        if installed_version(name) == version:
            already.append(name)
        elif version in available_versions(name):
            todo.append(name + "=" + version)
        else:
            unavailable.append(name + "=" + version)
    return {"schema": "axia_ci_apt_pinning_v1",
            "status": "VERSION_UNAVAILABLE" if unavailable else "READY_TO_PIN",
            "exact_install_specs": todo,
            "already_matched": already,
            "unavailable_versions": unavailable,
            "pin_count": len(target),
            "wsl2_kernel_parity": False,
            "gazebo_goal_verified": False}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--owner", type=Path, required=True)
    p.add_argument("--plan-output", type=Path, required=True)
    p.add_argument("--apply", action="store_true")
    args = p.parse_args(argv)
    try:
        plan = make_plan(read_profile(args.owner))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("AXIA_CI_PINNING_BLOCKED " + str(exc), file=sys.stderr)
        return 3
    args.plan_output.parent.mkdir(parents=True, exist_ok=True)
    args.plan_output.write_text(json.dumps(plan, indent=2, sort_keys=True)+"\n")
    print("AXIA_CI_APT_PIN_PLAN=" + plan["status"])
    print("AXIA_CI_APT_PIN_COUNT=" + str(plan["pin_count"]))
    if plan["unavailable_versions"]:
        for value in plan["unavailable_versions"][:30]:
            print("AXIA_CI_APT_PIN_UNAVAILABLE_PACKAGE=" + value.split("=", 1)[0])
        return 2
    if not args.apply or not plan["exact_install_specs"]:
        print("AXIA_CI_APT_PIN_APPLY=" + ("NO_CHANGES" if args.apply else "DRY_RUN"))
        return 0
    if os.geteuid() != 0:
        print("AXIA_CI_APT_PIN_BLOCKED_NEEDS_CONTAINER_ROOT", file=sys.stderr)
        return 3
    specs = plan["exact_install_specs"]
    env = dict(os.environ, DEBIAN_FRONTEND="noninteractive")
    simulation = subprocess.run(["apt-get", "--simulate", "--allow-downgrades",
                                 "--no-install-recommends", "install", *specs],
                                env=env, timeout=180, check=False,
                                capture_output=True, text=True)
    if simulation.returncode:
        print("AXIA_CI_APT_PIN_DEPENDENCY_CONFLICT_SIMULATION", file=sys.stderr)
        return 2
    if any(line.lstrip().startswith("Remv ") for line in simulation.stdout.splitlines()):
        print("AXIA_CI_APT_PIN_BLOCKED_WOULD_REMOVE_PACKAGES", file=sys.stderr)
        return 2
    install = subprocess.run(["apt-get", "-y", "--allow-downgrades",
                              "--no-install-recommends", "install", *specs],
                             env=env, timeout=600, check=False,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if install.returncode:
        print("AXIA_CI_APT_PIN_INSTALL_BLOCKED", file=sys.stderr)
        return 2
    if any(installed_version(name) != version
           for name, version in selected_versions(read_profile(args.owner)).items()):
        print("AXIA_CI_APT_PIN_POSTVERIFY_MISMATCH", file=sys.stderr)
        return 2
    print("AXIA_CI_APT_PIN_POSTVERIFY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
