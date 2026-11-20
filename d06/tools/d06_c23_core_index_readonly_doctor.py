#!/usr/bin/env python3
"""C23 read-only current-boot diagnosis for failed C22 WSL2 systemd core index.

Queries socket state, the exact synthetic PID's journal metadata, and
coredumpctl info; never generates a new crash or runs ROS/Gazebo.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

PID = 1424
MAX_OUTPUT = 100000


def summarize_wsl2_layers(kernel_release, pid1, dxg_present, wslg_visible,
                          glx_output, persistent_journal, volatile_journal):
    """Read-only layer inventory; no result here proves core capture or Gazebo.

    Ubuntu distro and WSLg system distro do not share the same GUI service
    process boundary. A present D3D12 renderer is not an exit0 or safety proof.
    """
    renderer = "UNAVAILABLE"
    if "OpenGL renderer string:" in glx_output:
        raw = next((line for line in glx_output.splitlines()
                    if "OpenGL renderer string:" in line), "")
        value = raw.split(":", 1)[1].strip().lower()
        if "d3d12" in value and "nvidia" in value:
            renderer = "D3D12_NVIDIA"
        elif "d3d12" in value:
            renderer = "D3D12_OTHER"
        elif "llvmpipe" in value:
            renderer = "SOFTWARE_LLVMPIPE"
        else:
            renderer = "OTHER_GL"
    storage = ("PERSISTENT_DIR_PRESENT" if persistent_journal
               else "VOLATILE_DIR_ONLY" if volatile_journal
               else "JOURNAL_DIRECTORY_UNKNOWN")
    return {
        "environment": ("WSL2_UBUNTU2404" if "microsoft" in kernel_release.lower()
                        or "wsl" in kernel_release.lower()
                        else "WSL2_NOT_VERIFIED"),
        "kernel_release": kernel_release[:120],
        "pid1_systemd": pid1.strip() == "systemd",
        "dxg_present": bool(dxg_present),
        "wslg_visible": bool(wslg_visible),
        "renderer_class": renderer,
        "journal_storage_class": storage,
        "core_capture_proven": False,
        "gazebo_exit0_proven": False,
    }


def subprocess_text(argv, timeout=12):
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                           check=False, errors="replace")
        return r.returncode, r.stdout[:MAX_OUTPUT], r.stderr[:4000]
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, "", str(type(exc).__name__)


def has_exact_info(text):
    return (
        re.search(r"(?im)^\s*PID:\s*1424(?:\s|$)", text) is not None
        and re.search(r"(?im)^\s*Signal:\s*(?:11\b|SIGSEGV\b)", text) is not None
        and re.search(r"(?im)^\s*Executable:\s*/(?:usr/)?bin/bash\s*$", text) is not None
    )


def matching_rows(snapshot):
    matches = []
    for item in snapshot.get("journal_records", []):
        if not isinstance(item, dict):
            continue
        if str(item.get("COREDUMP_PID", "")) != str(PID):
            continue
        signal = str(item.get("COREDUMP_SIGNAL", ""))
        exe = str(item.get("COREDUMP_EXE", ""))
        if signal in ("11", "SIGSEGV") and Path(exe).name == "bash":
            matches.append(item)
    return matches


def classify(snapshot):
    if not snapshot.get("journal_access", False):
        return "D06_C23_JOURNAL_PERMISSION_UNVERIFIED_HOLD"
    if has_exact_info(snapshot.get("info_text", "")):
        return "D06_C23_INFO_PRESENT_C22_MATCHER_OR_TIMING_CANDIDATE_HOLD"
    if matching_rows(snapshot):
        return "D06_C23_JOURNAL_RECORD_PRESENT_INFO_MISSING_HOLD"
    # The C22 source did not record boot_id. On WSL2 a VM termination or
    # distro restart can invalidate current --boot/PID evidence. A missing
    # current-boot row cannot be promoted to a backend storage failure.
    if snapshot.get("event_boot_known") is False:
        return "D06_C24_WSL2_PREVIOUS_EVENT_BOOT_UNVERIFIED_HOLD"
    if snapshot.get("socket_active") is False:
        return "D06_C23_SOCKET_NOT_LISTENING_HOLD"
    return "D06_C23_NO_PID_RECORD_CURRENT_BOOT_HOLD_ROOT_CAUSE_UNKNOWN"


def write_forensic(snapshot, verdict):
    root = Path.home() / "axia_d06_c23_core_index_doctor"
    root.mkdir(parents=True, exist_ok=True)
    os.chmod(root, 0o700)
    run = Path(tempfile.mkdtemp(prefix="readonly-", dir=root))
    os.chmod(run, 0o700)
    status = {
        "scope": "current_boot_read_only_pid_1424_not_verified_same_event",
        "pid": PID,
        "socket_active": snapshot.get("socket_active"),
        "journal_access": snapshot.get("journal_access"),
        "journal_exact_pid_rows": sum(
            1 for z in snapshot.get("journal_records", [])
            if isinstance(z, dict) and str(z.get("COREDUMP_PID", "")) == "1424"),
        "journal_exact_segv_bash_rows": len(matching_rows(snapshot)),
        "coredumpctl_exact_info": has_exact_info(snapshot.get("info_text", "")),
        "verdict": verdict,
        "wsl2_layers": snapshot.get("wsl2_layers", {}),
        "event_boot_known": snapshot.get("event_boot_known"),
        "core_not_archived": True,
        "gazebo_not_run": True,
        "root_cause": "UNCONFIRMED",
    }
    (run / "observation.json").write_text(json.dumps(status, indent=2) + "\n")
    (run / "preflight.txt").write_text(
        "kernel_core_pattern=" + snapshot.get("kernel_core_pattern", "UNAVAILABLE") + "\n"
        + "boot_id=" + snapshot.get("boot_id", "UNAVAILABLE") + "\n"
        + "systemd_socket_load=" + snapshot.get("socket_load", "UNVERIFIED") + "\n"
        + "systemd_socket_active=" + str(snapshot.get("socket_active")) + "\n"
        + "storage_config=" + snapshot.get("storage_config", "UNVERIFIED") + "\n"
        + "PID=1424 current boot query only; no evidence this is the same crash event\n"
        + "wsl2_ubuntu_user_distro_not_equal_wslg_system_distro=true\n"
    )
    (run / "summary.txt").write_text(
        verdict + "\nD06_C23_NO_NEW_SIGSEGV_NO_GAZEBO\n"
        "core_not_archived=true\nAXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false\n")
    archive = root / (run.name + ".tar.gz")
    with tarfile.open(archive, "w:gz") as tf:
        for name in ("summary.txt", "preflight.txt", "observation.json"):
            tf.add(run / name, arcname=name)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    sidecar = Path(str(archive) + ".sha256")
    sidecar.write_text(digest + "  " + str(archive) + "\n")
    os.chmod(archive, 0o600)
    os.chmod(sidecar, 0o600)
    print("D06_C23_FORENSIC_ARCHIVE=" + str(archive))
    print("D06_C23_FORENSIC_SHA256=" + str(sidecar))


def doctor():
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print("D06_C23_CI_DENIED_READONLY_NO_CRASH")
        return 3
    osrelease = Path("/proc/sys/kernel/osrelease").read_text(errors="replace").lower()
    if not ("microsoft" in osrelease or "wsl" in osrelease):
        print("D06_C23_NOT_OWNER_WSL2_NO_CRASH")
        return 3
    osinfo = Path("/etc/os-release").read_text(errors="replace")
    if 'ID=ubuntu' not in osinfo or 'VERSION_ID="24.04"' not in osinfo:
        print("D06_C23_NOT_UBUNTU2404_NO_CRASH")
        return 3
    if not all(subprocess_text(["which", x])[0] == 0
               for x in ("systemctl", "journalctl", "coredumpctl", "sudo")):
        print("D06_C23_READONLY_TOOLS_MISSING_HOLD")
        return 3
    # Prompt once for read-only system journal queries. No sudo install or config.
    root_commands = [] if os.geteuid() == 0 else ["sudo", "-n"]
    access = os.geteuid() == 0
    if not access:
        rc, _, _ = subprocess_text(["sudo", "-v"], timeout=20)
        access = rc == 0
    if not access:
        print("D06_C23_SUDO_JOURNAL_PERMISSION_HOLD_NO_CHANGE")
    rc, raw, _ = subprocess_text([
        "systemctl", "show", "systemd-coredump.socket",
        "--property=LoadState", "--property=ActiveState", "--property=SubState"])
    props = dict(line.split("=", 1) for line in raw.splitlines() if "=" in line)
    socket_active = props.get("ActiveState") == "active" if rc == 0 else None
    journal_rows = []
    journal_access = False
    info_text = ""
    if access:
        rc, raw, _ = subprocess_text(root_commands + [
            "journalctl", "--boot", "--no-pager", "--quiet", "--output=json",
            "--lines=20", "COREDUMP_PID=1424"])
        journal_access = rc == 0
        if journal_access:
            for line in raw.splitlines()[:20]:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(event, dict):
                    journal_rows.append({
                        "COREDUMP_PID": str(event.get("COREDUMP_PID", "")),
                        "COREDUMP_SIGNAL": str(event.get("COREDUMP_SIGNAL", "")),
                        "COREDUMP_EXE": str(event.get("COREDUMP_EXE", "")),
                    })
        _, info_text, _ = subprocess_text(root_commands + [
            "coredumpctl", "--no-pager", "info", str(PID)])
    config_rc, config_raw, _ = subprocess_text([
        "systemd-analyze", "cat-config", "systemd/coredump.conf"])
    config_terms = []
    if config_rc == 0:
        for line in config_raw.splitlines():
            if re.match(r"^\s*(Storage|ProcessSizeMax|ExternalSizeMax)=", line):
                config_terms.append(line.strip()[:100])
    # WSL2 user distro's Linux core handler is separate from the WSLg
    # system distro's Wayland/X11 backend and Windows host GPU driver.
    # This display check is optional and is not a prerequisite for a
    # read-only coredump index investigation.
    glx_text = ""
    if os.environ.get("DISPLAY") and shutil.which("glxinfo"):
        _, glx_text, _ = subprocess_text(["glxinfo", "-B"], timeout=8)
    try:
        pid1_name = Path("/proc/1/comm").read_text().strip()
    except OSError:
        pid1_name = "UNAVAILABLE"
    layers = summarize_wsl2_layers(
        osrelease, pid1_name, Path("/dev/dxg").exists(),
        Path("/mnt/wslg").exists(), glx_text,
        Path("/var/log/journal").is_dir(),
        Path("/run/log/journal").is_dir())
    snapshot = {
        "pid": PID,
        "event_boot_known": False,  # C22 did not record a boot UUID.
        "wsl2_kernel": layers["environment"] == "WSL2_UBUNTU2404",
        "wsl2_layers": layers,
        "socket_active": socket_active,
        "socket_load": props.get("LoadState", "UNKNOWN"),
        "journal_access": journal_access,
        "journal_records": journal_rows,
        "info_text": info_text,
        "kernel_core_pattern": Path("/proc/sys/kernel/core_pattern").read_text().strip(),
        "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
        "storage_config": ";".join(config_terms) if config_terms else "DEFAULT_OR_UNAVAILABLE",
    }
    verdict = classify(snapshot)
    print("D06_C23_QUERY_SCOPE=CURRENT_BOOT_ONLY_PID_1424")
    print("D06_C24_WSL2_KERNEL=" + str(layers["environment"]))
    print("D06_C24_WSL2_PID1_SYSTEMD=" + str(layers["pid1_systemd"]).lower())
    print("D06_C24_WSLG_RENDERER_CLASS=" + layers["renderer_class"])
    print("D06_C24_WSL2_JOURNAL_STORAGE_DIR=" + layers["journal_storage_class"])
    print("D06_C24_WSL2_LAYER_DIAGNOSTIC_ONLY_NOT_GAZEBO_ACCEPTANCE")
    print("D06_C23_SYSTEMD_SOCKET_ACTIVE=" + str(socket_active).lower())
    print("D06_C23_CURRENT_BOOT_JOURNAL_RECORDS=" + str(len(journal_rows)))
    print("D06_C23_EXACT_SIGSEGV_BASH_JOURNAL_RECORDS=" + str(len(matching_rows(snapshot))))
    print("D06_C23_COREDUMPCTL_INFO_MATCH=" + str(has_exact_info(info_text)).lower())
    print(verdict)
    write_forensic(snapshot, verdict)
    return 3  # Diagnostic never releases or authorizes Gazebo.


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-check", action="store_true")
    group.add_argument("--doctor", action="store_true")
    group.add_argument("--classify-fixture", type=Path)
    args = parser.parse_args()
    if args.self_check:
        print("D06_C23_STATIC_L0_PASS_NO_CORE_NO_GAZEBO")
        print("AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false")
        return 0
    if args.classify_fixture:
        try:
            snapshot = json.loads(args.classify_fixture.read_text())
        except (ValueError, OSError):
            print("D06_C23_INVALID_OFFLINE_FIXTURE")
            return 3
        print(classify(snapshot))
        print("D06_C23_OFFLINE_FIXTURE_NOT_HARDWARE_PROOF")
        return 0
    return doctor()


if __name__ == "__main__":
    sys.exit(main())
