#!/usr/bin/env python3
"""AXIA WSL2/Jazzy/Harmonic user-space fingerprint (allowlist, no secrets).

Never collects usernames, hostnames, home paths, IP/MAC, credentials,
private repo contents, ROS message payloads or the complete environment.
Stdlib only; also runs inside an Ubuntu 24.04 CI image.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone

SCHEMA = "axia_ros_jazzy_harmonic_env_v1"
PACKAGE_RE = re.compile(
    r"^(ros-jazzy-|gz-|libgz-|libignition-|libsdformat|python3-colcon"
    r"|python3-ament|python3-rosdep|python3-yaml$|python3-empy$"
    r"|python3-vcstool$|python3-rosinstall)"
)
RMW_ALLOWED = {"", "rmw_fastrtps_cpp", "rmw_cyclonedds_cpp", "rmw_connextdds"}
DISCOVERY_ALLOWED = {"", "LOCALHOST", "SUBNET", "OFF", "SYSTEM_DEFAULT"}
OFFICIAL = {
    "nav2_bringup": ("launch/tb3_simulation_launch.py", "params/nav2_params.yaml"),
    "nav2_minimal_tb3_sim": ("worlds/tb3_sandbox.sdf.xacro",),
}


def safe_command(argv, timeout=5):
    try:
        p = subprocess.run(argv, capture_output=True, text=True,
                           timeout=timeout, check=False)
        if p.returncode:
            return ""
        return " ".join((p.stdout or p.stderr).strip().split())[:160]
    except (OSError, subprocess.TimeoutExpired):
        return ""


def os_release():
    fields = {}
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key in ("ID", "VERSION_ID", "VERSION_CODENAME"):
                fields[key.lower()] = value.strip().strip('"')
    except OSError:
        pass
    return fields


def installed_apt():
    dollar = chr(36)
    fmt = (dollar + "{Package}\t" + dollar + "{Version}\t" +
           dollar + "{db:Status-Abbrev}\n")
    try:
        p = subprocess.run(["dpkg-query", "-W", "-f=" + fmt],
                           capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        return {}
    out = {}
    for line in p.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        name, version, status = parts
        if status.startswith("ii") and PACKAGE_RE.match(name):
            if re.fullmatch(r"[a-z0-9+.-]+", name) and len(version) < 120:
                out[name] = version
    return dict(sorted(out.items()))


def apt_holds():
    text = safe_command(["apt-mark", "showhold"], timeout=5)
    return sorted(x for x in text.split() if PACKAGE_RE.match(x))[:80]


def official_file_hashes():
    out = {}
    try:
        from ament_index_python.packages import get_package_share_directory
    except ImportError:
        return out
    for package, relatives in OFFICIAL.items():
        try:
            root = Path(get_package_share_directory(package))
        except (LookupError, OSError):
            continue
        for rel in relatives:
            path = root / rel
            key = package + "/" + rel
            try:
                if path.is_file() and path.stat().st_size <= 8_000_000:
                    out[key] = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError:
                continue
    return dict(sorted(out.items()))


def safe_env():
    rmw = os.getenv("RMW_IMPLEMENTATION", "")
    discover = os.getenv("ROS_AUTOMATIC_DISCOVERY_RANGE", "")
    domain = os.getenv("ROS_DOMAIN_ID", "")
    return {
        "rmw_implementation": rmw if rmw in RMW_ALLOWED else "CUSTOM_REDACTED",
        "discovery_range": discover if discover in DISCOVERY_ALLOWED else "CUSTOM_REDACTED",
        "domain_id": int(domain) if domain.isdecimal() and 0 <= int(domain) <= 232 else None,
        "gz_sim_resource_path_set": bool(os.getenv("GZ_SIM_RESOURCE_PATH")),
        "gz_partition_set": bool(os.getenv("GZ_PARTITION")),
    }


def collect():
    kernel = platform.release()
    wsl = "microsoft" in kernel.lower() or "wsl" in kernel.lower()
    apt = installed_apt()
    return {
        "schema": SCHEMA,
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "profile_kind": "wsl2_owner" if wsl else "ci_linux",
        "os": os_release(),
        "architecture": platform.machine(),
        "kernel_release": kernel[:120],
        "wsl2_detected": wsl,
        "wslg": {
            "dev_dxg_exists": Path("/dev/dxg").exists(),
            "wayland_display_set": bool(os.getenv("WAYLAND_DISPLAY")),
            "display_set": bool(os.getenv("DISPLAY")),
        },
        "python": {
            "major_minor": f"{sys.version_info.major}.{sys.version_info.minor}",
            "full_version": platform.python_version(),
        },
        "ros": {
            "distro": os.getenv("ROS_DISTRO", ""),
            "version": os.getenv("ROS_VERSION", ""),
            "official_file_sha256": official_file_hashes(),
        },
        "commands": {
            "gz": safe_command(["gz", "--version"]),
            "gz_sim": safe_command(["gz", "sim", "--version"]),
            "colcon": safe_command(["colcon", "version-check"]),
        },
        "apt_packages": apt,
        "apt_held_packages": apt_holds(),
        "env_allowlist": safe_env(),
        "package_count": len(apt),
        "privacy": {
            "only_allowlisted_fields": True,
            "hostname_username_paths_addresses_tokens_excluded": True,
        },
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--require-wsl2", action="store_true")
    args = p.parse_args(argv)
    out = collect()
    if args.require_wsl2 and not out["wsl2_detected"]:
        print("AXIA_ENV_BLOCKED_NOT_WSL2", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(args.output.parent, 0o700)
    args.output.write_text(json.dumps(out, indent=2, ensure_ascii=False,
                                     sort_keys=True) + "\n", encoding="utf-8")
    args.output.chmod(0o600)
    required = ("ros-jazzy-nav2-bringup",
                "ros-jazzy-nav2-minimal-tb3-sim",
                "ros-jazzy-navigation2",
                "ros-jazzy-ros-gz")
    missing = [name for name in required if name not in out["apt_packages"]]
    ready = (out["os"].get("id") == "ubuntu" and
             out["os"].get("version_id") == "24.04" and
             out["ros"]["distro"] == "jazzy" and
             bool(out["commands"]["gz_sim"]) and not missing)
    print("AXIA_ENV_PROFILE_WRITTEN")
    print("AXIA_ENV_DISTRO=" + out["ros"]["distro"])
    print("AXIA_ENV_GZ_SIM=" + (out["commands"]["gz_sim"] or "UNKNOWN"))
    print("AXIA_ENV_PACKAGE_COUNT=" + str(out["package_count"]))
    print("AXIA_ENV_USERSPACE_READY=" + str(ready).lower())
    if missing:
        print("AXIA_ENV_MISSING_CRITICAL=" + ",".join(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
