#!/usr/bin/env python3
"""AXIA Jazzy/Harmonic WSL2 -> CI read-only inventory. No Goal, Fault or Gazebo launch.

Output "owner_profile.json" intentionally implements the existing
axia_ros_jazzy_harmonic_env_v1 contract used by axia_ci_env_compare.py.
No usernames, home paths, hostnames, network addresses, raw environment,
ROS message contents, tokens or private source contents are collected.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import stat
import subprocess
import sys

SCHEMA = "axia_ros_jazzy_harmonic_env_v1"
EXTRA_SCHEMA = "axia_p2_g07_owner_ci_runtime_inventory_v1"
PACKAGE_RE = re.compile(
    r"^(ros-jazzy-|gz-|libgz-|libignition-|libsdformat|python3-colcon"
    r"|python3-ament|python3-rosdep|python3-yaml$|python3-empy$"
    r"|python3-vcstool$|python3-rosinstall)"
)
PACKAGE_NAME_RE = re.compile(r"^[a-z0-9+.-]+$")
VERSION_RE = re.compile(r"^[a-zA-Z0-9.+:~_+-]{1,120}$")
RMW_ALLOW = {"", "rmw_fastrtps_cpp", "rmw_cyclonedds_cpp", "rmw_connextdds"}
DISCOVERY_ALLOW = {"", "LOCALHOST", "SUBNET", "OFF", "SYSTEM_DEFAULT"}
OFFICIAL = {
    "nav2_bringup": (
        "launch/tb3_simulation_launch.py",
        "params/nav2_params.yaml",
        "maps/tb3_sandbox.yaml",
        "maps/tb3_sandbox.pgm",
    ),
    "nav2_minimal_tb3_sim": ("worlds/tb3_sandbox.sdf.xacro",),
}
CORE = (
    "ros-jazzy-nav2-bringup",
    "ros-jazzy-nav2-minimal-tb3-sim",
    "ros-jazzy-navigation2",
    "ros-jazzy-nav2-collision-monitor",
    "ros-jazzy-ros-gz",
    "ros-jazzy-ros-gz-bridge",
    "ros-jazzy-rclpy",
    "gz-sim8-cli",
    "libgz-sim8",
    "libsdformat14",
)


def command(argv: list[str], timeout: int = 8) -> str:
    """Fixed argv only, never shell. Untrusted stderr/stdout is not retained."""
    try:
        result = subprocess.run(
            argv, capture_output=True, text=True, stdin=subprocess.DEVNULL,
            check=False, timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout if result.returncode == 0 else ""


def package_versions() -> dict[str, str]:
    fmt = chr(36) + "{Package}\t" + chr(36) + "{Version}\t" + chr(36) + "{db:Status-Abbrev}\n"
    output = command(["dpkg-query", "-W", "-f=" + fmt], timeout=20)
    packages = {}
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        name, version, status = parts
        if (status.startswith("ii") and PACKAGE_RE.match(name)
                and PACKAGE_NAME_RE.fullmatch(name)
                and VERSION_RE.fullmatch(version)):
            packages[name] = version
    return dict(sorted(packages.items()))


def package_holds() -> list[str]:
    output = command(["apt-mark", "showhold"], timeout=8)
    names = [
        item.strip() for item in output.splitlines()
        if PACKAGE_RE.match(item.strip()) and PACKAGE_NAME_RE.fullmatch(item.strip())
    ]
    return sorted(set(names))[:120]


def os_info() -> dict[str, str]:
    mapping = {}
    try:
        lines = Path("/etc/os-release").read_text(encoding="utf-8").splitlines()
        for line in lines:
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key in ("ID", "VERSION_ID", "VERSION_CODENAME"):
                mapping[key.lower()] = value.strip().strip('"')
    except OSError:
        pass
    return mapping


def official_hashes() -> dict[str, str]:
    try:
        from ament_index_python.packages import get_package_share_directory
    except ImportError:
        return {}
    hashes = {}
    for package, files in OFFICIAL.items():
        try:
            root = Path(get_package_share_directory(package))
        except (LookupError, OSError, ValueError):
            continue
        for rel in files:
            path = root / rel
            try:
                if path.is_file() and 0 < path.stat().st_size <= 8_000_000:
                    hashes[package + "/" + rel] = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError:
                continue
    return dict(sorted(hashes.items()))


def safe_env(env: dict[str, str]) -> dict:
    rmw = env.get("RMW_IMPLEMENTATION", "")
    discovery = env.get("ROS_AUTOMATIC_DISCOVERY_RANGE", "")
    domain = env.get("ROS_DOMAIN_ID", "")
    return {
        "rmw_implementation": rmw if rmw in RMW_ALLOW else "CUSTOM_REDACTED",
        "discovery_range": discovery if discovery in DISCOVERY_ALLOW else "CUSTOM_REDACTED",
        "domain_id": int(domain) if domain.isascii() and domain.isdecimal() and 0 <= int(domain) <= 232 else None,
        "gz_sim_resource_path_set": bool(env.get("GZ_SIM_RESOURCE_PATH")),
        "gz_partition_set": bool(env.get("GZ_PARTITION")),
    }


def safe_version(args: list[str]) -> str:
    # Some CLI tools include filesystem paths in warnings. Only extract a
    # known numeric version; never persist arbitrary captured stdout.
    raw = command(args)
    match = re.search(r"\b(?:version\s*)?(\d+\.\d+(?:\.\d+)?)\b", raw, re.I)
    return match.group(1) if match else ""


def mem_total_mib() -> int | None:
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) // 1024
    except (OSError, ValueError, IndexError):
        pass
    return None


def create_profile(env: dict[str, str] | None = None, *, mode: str = "owner") -> dict:
    env = os.environ if env is None else env
    if mode not in ("owner", "ci"):
        raise ValueError("INVALID_COLLECTION_MODE")
    kernel = platform.release()
    wsl = "microsoft" in kernel.lower() or "wsl" in kernel.lower()
    pkgs = package_versions()
    checks = official_hashes()
    source_sha = env.get("AXIA_P2_OWNER_PINNED_SHA", "")
    if not re.fullmatch(r"[a-f0-9]{40}", source_sha):
        source_sha = None
    return {
        "schema": SCHEMA,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "profile_kind": "wsl2_owner" if wsl else "ci_linux",
        "os": os_info(),
        "architecture": platform.machine()[:48],
        "kernel_release": kernel[:120],
        "wsl2_detected": wsl,
        "wslg": {
            "dev_dxg_exists": Path("/dev/dxg").exists(),
            "wayland_display_set": bool(env.get("WAYLAND_DISPLAY")),
            "display_set": bool(env.get("DISPLAY")),
        },
        "python": {
            "major_minor": f"{sys.version_info.major}.{sys.version_info.minor}",
            "full_version": platform.python_version(),
        },
        "ros": {
            "distro": env.get("ROS_DISTRO", "") if env.get("ROS_DISTRO", "") in ("", "jazzy") else "OTHER",
            "version": env.get("ROS_VERSION", "") if env.get("ROS_VERSION", "") in ("", "2") else "OTHER",
            "official_file_sha256": checks,
        },
        "commands": {
            "gz": safe_version(["gz", "--version"]),
            "gz_sim": safe_version(["gz", "sim", "--version"]),
            "colcon": safe_version(["colcon", "version-check"]),
        },
        "apt_packages": pkgs,
        "apt_held_packages": package_holds(),
        "env_allowlist": safe_env(env),
        "package_count": len(pkgs),
        "runtime_details": {
            "schema": EXTRA_SCHEMA,
            "collector_mode": mode,
            "cpu_logical_count": os.cpu_count(),
            "ram_total_mib": mem_total_mib(),
            "wsl2_kernel_present": wsl,
            "wslg_gpu_device_present": Path("/dev/dxg").exists(),
            "native_wsl2_scheduler_equivalent_to_linux_ci": False,
            "source_commit_sha_if_explicitly_set": source_sha,
            "goal_sent": False,
            "fault_injected": False,
            "gazebo_started_by_collector": False,
            "certified_estop": False,
            "ci_parity_compared": False,
            "ci_user_space_parity_proven": False,
            "physical_g07_l3_verified": False,
        },
        "privacy": {
            "only_allowlisted_fields": True,
            "hostname_username_paths_addresses_tokens_excluded": True,
            "raw_environment_exported": False,
            "raw_ros_message_payloads_exported": False,
            "raw_apt_source_urls_exported": False,
        },
    }


def summary(profile: dict) -> dict:
    keys = ("ros-jazzy-nav2-bringup", "ros-jazzy-navigation2",
            "ros-jazzy-nav2-minimal-tb3-sim", "ros-jazzy-ros-gz")
    missing = [name for name in keys if name not in profile["apt_packages"]]
    missing_files = [key for key in (
        "nav2_bringup/launch/tb3_simulation_launch.py",
        "nav2_bringup/params/nav2_params.yaml",
        "nav2_minimal_tb3_sim/worlds/tb3_sandbox.sdf.xacro",
    ) if key not in profile["ros"]["official_file_sha256"]]
    ready = (
        profile["os"].get("id") == "ubuntu"
        and profile["os"].get("version_id") == "24.04"
        and profile["ros"]["distro"] == "jazzy"
        and bool(profile["commands"]["gz_sim"])
        and not missing and not missing_files
    )
    return {
        "schema": "axia_wsl2_ci_sync_inventory_summary_v1",
        "status": "COLLECTED_READY_FOR_CI_COMPARISON" if ready else "COLLECTED_WITH_MISSING_ITEMS",
        "captured_utc": profile["captured_utc"],
        "wsl2_detected": profile["wsl2_detected"],
        "ros_distro": profile["ros"]["distro"],
        "gz_sim_version": profile["commands"]["gz_sim"],
        "package_count": profile["package_count"],
        "critical_packages": {k: profile["apt_packages"].get(k) for k in CORE},
        "missing_required_packages": missing,
        "missing_official_sha256": missing_files,
        "official_file_sha256": profile["ros"]["official_file_sha256"],
        "discovery_range_at_capture": profile["env_allowlist"]["discovery_range"],
        "expected_owner_g07_runner_discovery": "LOCALHOST",
        "domain_id_at_capture": profile["env_allowlist"]["domain_id"],
        "domain_and_partition_renumbered_for_isolated_run": True,
        "source_commit_sha_if_explicitly_set": profile["runtime_details"]["source_commit_sha_if_explicitly_set"],
        "wsl2_kernel_equal_to_ci": False,
        "scheduler_equal_to_ci": False,
        "goal_sent": False,
        "gazebo_started_by_collector": False,
        "ci_sync_applied": False,
        "ci_parity_compared": False,
        "formal_g07_accepted": False,
        "certified_estop": False,
    }


def write_exclusive(path: Path, value: str) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(str(path), flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fp:
        fp.write(value)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--mode", choices=("owner", "ci"), default="owner")
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)
    if args.self_check:
        print("AXIA_WSL2_CI_SYNC_COLLECTOR_STATIC_OK NO_GOAL_NO_MUTATION")
        return 0
    if args.out_dir is None:
        parser.error("--out-dir is required unless --self-check")
    outdir = args.out_dir.resolve(strict=True)
    if not outdir.is_dir() or outdir.is_symlink():
        print("AXIA_WSL2_CI_INVENTORY_BLOCKED_NOT_PRIVATE_DIR", file=sys.stderr)
        return 2
    if outdir.stat().st_mode & 0o077:
        print("AXIA_WSL2_CI_INVENTORY_BLOCKED_UNSAFE_MODE", file=sys.stderr)
        return 2
    if args.mode == "owner" and not outdir.is_relative_to(Path.home().resolve()):
        print("AXIA_WSL2_CI_INVENTORY_BLOCKED_OUTSIDE_HOME", file=sys.stderr)
        return 2
    profile = create_profile(mode=args.mode)
    if args.mode == "owner" and not profile["wsl2_detected"]:
        print("AXIA_WSL2_CI_INVENTORY_BLOCKED_NOT_WSL2", file=sys.stderr)
        return 2
    if args.mode == "ci" and profile["wsl2_detected"]:
        print("AXIA_WSL2_CI_INVENTORY_BLOCKED_NOT_CI_LINUX", file=sys.stderr)
        return 2
    brief = summary(profile)
    profile_payload = json.dumps(profile, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    brief_payload = json.dumps(brief, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    write_exclusive(outdir / "owner_profile.json", profile_payload)
    write_exclusive(outdir / "owner_summary.json", brief_payload)
    digest_profile = hashlib.sha256(profile_payload.encode()).hexdigest()
    digest_summary = hashlib.sha256(brief_payload.encode()).hexdigest()
    write_exclusive(outdir / "SHA256SUMS",
                    digest_profile + "  owner_profile.json\n" +
                    digest_summary + "  owner_summary.json\n")
    print("AXIA_WSL2_CI_SYNC_INVENTORY_CREATED_NO_GOAL_NO_GAZEBO")
    print("AXIA_WSL2_CI_SYNC_STATUS=" + brief["status"])
    print("AXIA_WSL2_CI_SYNC_CRITICAL_MISSING=" + ",".join(brief["missing_required_packages"]))
    print("AXIA_WSL2_CI_SYNC_PACKAGE_COUNT=" + str(profile["package_count"]))
    print("PRIVATE_OUTPUT_DIR=" + str(outdir))
    print("AXIA_WSL2_CI_SYNC_NOT_APPLIED_PARITY_NOT_PROVEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
