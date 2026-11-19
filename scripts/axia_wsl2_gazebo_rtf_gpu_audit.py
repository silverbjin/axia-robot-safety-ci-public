#!/usr/bin/env python3
"""AXIA WSL2/Gazebo Harmonic read-only renderer + interval RTF audit.

Run in a SECOND terminal while a single AXIA Gazebo demo is active. Does not
start, stop, pause, publish, install packages, change GPU or alter ~/.bashrc.
Only diagnostics children (glxinfo, gz topic -e) are stopped by this script.

Evidence boundaries: GLX child != actual Gazebo Ogre2 server renderer;
nvidia-smi != proof of WSLg OpenGL offload; disk sensor SDF != live sensor
configuration; ROS safety TTL/GUI pixels/E-Stop are NOT verified.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import statistics
import subprocess
import sys
import time
import zipfile

GPU_KEYS = (
    "GALLIUM_DRIVER", "MESA_D3D12_DEFAULT_ADAPTER_NAME",
    "LIBGL_ALWAYS_SOFTWARE", "LIBGL_DRI3_DISABLE", "EGL_PLATFORM",
    "QT_QPA_PLATFORM", "GZ_SIM_RENDER_ENGINE", "GZ_RENDER_ENGINE_PATH",
)
RUN_KEYS = ("GZ_PARTITION", "ROS_DOMAIN_ID", "AXIA_D08_RGBD_RATE_HZ",
            "AXIA_D08_GUI_BACKEND", "AXIA_D08_GUI_RENDER_ENGINE",
            "AXIA_D04_STUDENT_RVIZ", "AXIA_D04_STUDENT_IMAGE_VIEW")
TIME_PATTERN = re.compile(
    r"\b%s\s*\{\s*sec:\s*(-?\d+)\s*nsec:\s*(\d+)\s*\}",
    re.MULTILINE | re.DOTALL,
)
RTF_PATTERN = re.compile(r"(?m)^\s*real_time_factor:\s*([0-9.+eE-]+)\s*$")
PAUSED_PATTERN = re.compile(r"(?m)^\s*paused:\s*(true|false)\s*$", re.I)


def parse_stats(raw: str) -> dict:
    """Use delta(sim_time)/delta(real_time), NOT a median of RTF fields."""
    def times(field):
        reg = re.compile(TIME_PATTERN.pattern % re.escape(field),
                         re.MULTILINE | re.DOTALL)
        return [int(m.group(1)) + int(m.group(2)) * 1e-9
                for m in reg.finditer(raw)]
    sim, real = times("sim_time"), times("real_time")
    pauses = [v.lower() == "true" for v in PAUSED_PATTERN.findall(raw)]
    rates = []
    for item in RTF_PATTERN.findall(raw):
        try:
            v = float(item)
            if 0 <= v <= 10:
                rates.append(v)
        except ValueError:
            pass
    result = {
        "samples_sim": len(sim), "samples_real": len(real),
        "samples_rtf_field": len(rates),
        "rtf_field_median": round(statistics.median(rates), 5) if rates else None,
        "paused_observed": any(pauses),
        "interval_rtf_percent": None,
        "delta_sim_s": None, "delta_real_s": None,
        "status": "INSUFFICIENT_STATS",
    }
    if len(sim) < 2 or len(real) < 2 or len(sim) != len(real):
        return result
    ds, dr = sim[-1] - sim[0], real[-1] - real[0]
    result["delta_sim_s"], result["delta_real_s"] = round(ds, 6), round(dr, 6)
    if any(b < a for a, b in zip(sim, sim[1:])) or \
       any(b < a for a, b in zip(real, real[1:])):
        result["status"] = "TIME_RESET_OR_REGRESSION"
    elif any(pauses):
        result["status"] = "PAUSED_DURING_WINDOW"
    elif dr <= 0 or ds < 0:
        result["status"] = "INVALID_INTERVAL"
    else:
        result["interval_rtf_percent"] = round(100 * ds / dr, 2)
        result["status"] = "INTERVAL_MEASURED"
    return result


def renderer_env(profile: str, env: dict) -> dict:
    out = dict(env)
    if profile == "inherited":
        return out
    for key in ("GALLIUM_DRIVER", "MESA_D3D12_DEFAULT_ADAPTER_NAME",
                "LIBGL_ALWAYS_SOFTWARE"):
        out.pop(key, None)
    if profile in ("d3d12_auto", "d3d12_nvidia"):
        out["GALLIUM_DRIVER"] = "d3d12"
    if profile == "d3d12_nvidia":
        out["MESA_D3D12_DEFAULT_ADAPTER_NAME"] = "NVIDIA"
    return out


def limited_command(args: list[str], *, env=None, timeout=8) -> dict:
    if not shutil.which(args[0]):
        return {"status": "COMMAND_MISSING", "output": ""}
    try:
        v = subprocess.run(args, env=env, text=True, capture_output=True,
                           timeout=timeout, check=False)
        return {"status": "OK" if v.returncode == 0 else f"RC_{v.returncode}",
                "output": (v.stdout + "\n" + v.stderr)[-5000:]}
    except (subprocess.TimeoutExpired, OSError) as exc:
        return {"status": type(exc).__name__, "output": str(exc)[:240]}


def renderer_profiles(out: Path) -> dict:
    data = {}
    for name in ("inherited", "default", "d3d12_auto", "d3d12_nvidia"):
        response = limited_command(["glxinfo", "-B"],
                                   env=renderer_env(name, os.environ),
                                   timeout=9)
        raw = response.pop("output")
        match = re.search(r"(?im)^OpenGL renderer string:\s*(.+)$", raw)
        accelerated = re.search(r"(?im)^Accelerated:\s*(.+)$", raw)
        data[name] = {
            "status": response["status"],
            "renderer": match.group(1).strip() if match else None,
            "accelerated": accelerated.group(1).strip() if accelerated else None,
        }
        (out / f"glx_{name}.txt").write_text(raw[-2600:] + "\n",
                                             encoding="utf-8")
    return data


def process_role(argv: list[str], comm: str) -> str | None:
    text = " ".join(argv).lower()
    base = comm.lower()
    if "gz-sim-server" in text or re.search(r"\bgz\s+sim\b", text) \
            or "gz-sim" in base:
        if re.search(r"(?:^|\s)-g(?:\s|$)", text) and \
                not re.search(r"(?:^|\s)-s(?:\s|$)", text):
            return "gazebo_gui"
        return "gazebo_server_candidate"
    if "rviz2" in text or base == "rviz2":
        return "rviz2"
    if "yolo" in base or ("yolo" in text and "ros2 launch" in text):
        return "yolo"
    if "image_view" in text:
        return "image_view"
    if "tb3_simulation_launch.py" in text or "axia_bringup" in text:
        return "ros_launch"
    return None


def read_proc(pid: int) -> dict | None:
    p = Path("/proc") / str(pid)
    try:
        cmd = (p / "cmdline").read_bytes().decode(errors="replace").strip("\0").split("\0")
        comm = (p / "comm").read_text().strip()
        role = process_role(cmd, comm)
        if role is None:
            return None
        env_data = {}
        error = None
        try:
            for token in (p / "environ").read_bytes().split(b"\0"):
                if b"=" not in token:
                    continue
                key, value = token.split(b"=", 1)
                name = key.decode(errors="replace")
                if name in GPU_KEYS + RUN_KEYS:
                    env_data[name] = value.decode(errors="replace")[:128]
        except OSError as exc:
            error = type(exc).__name__
        # /proc/[pid]/stat fields after the process comm in parentheses.
        raw_stat = (p / "stat").read_text()
        fields = raw_stat[raw_stat.rfind(")") + 2:].split()
        cpu_ticks = int(fields[11]) + int(fields[12])
        flags = [a for a in cmd if a in ("-g", "-s", "-r", "--render-engine",
                                          "ogre", "ogre2", "headless:=True",
                                          "headless:=False", "use_rviz:=False")]
        return {"pid": pid, "comm": comm, "role": role, "env": env_data,
                "env_read_error": error, "cpu_ticks": cpu_ticks,
                "flags": flags}
    except (OSError, ValueError, IndexError):
        return None


def scan_processes() -> list[dict]:
    result = []
    try:
        pids = [int(p.name) for p in Path("/proc").iterdir() if p.name.isdigit()]
    except OSError:
        return result
    for pid in pids:
        record = read_proc(pid)
        if record is not None:
            result.append(record)
    return sorted(result, key=lambda x: (x["role"], x["pid"]))


def choose_server(processes: list[dict], target_pid: int | None,
                  partition: str | None) -> tuple[dict | None, str | None, str]:
    servers = [p for p in processes if p["role"] == "gazebo_server_candidate"]
    if target_pid is not None:
        match = next((p for p in servers if p["pid"] == target_pid), None)
        if match is None:
            return None, partition, "SERVER_PID_NOT_FOUND"
        assigned = match["env"].get("GZ_PARTITION")
        if assigned and partition and assigned != partition:
            return None, partition, "SERVER_PID_PARTITION_MISMATCH"
        return match, partition or assigned, "EXPLICIT_SERVER_PID"
    if partition:
        matching = [p for p in servers if p["env"].get("GZ_PARTITION") == partition]
        return (matching[0] if len(matching) == 1 else None), partition, \
            ("SERVER_BY_PARTITION" if len(matching) == 1 else "SERVER_PID_AMBIGUOUS")
    partitions = {p["env"].get("GZ_PARTITION") for p in servers
                  if p["env"].get("GZ_PARTITION")}
    if len(partitions) == 1:
        value = next(iter(partitions))
        matching = [p for p in servers if p["env"].get("GZ_PARTITION") == value]
        return (matching[0] if len(matching) == 1 else None), value, \
            ("SERVER_AUTO" if len(matching) == 1 else "SERVER_PID_AMBIGUOUS")
    if not servers:
        return None, None, "NO_GAZEBO_SERVER"
    # Owner WSL2 may retain a previous Gazebo server in another partition.
    # Pair a unique active GUI partition with a unique server *in that same*
    # GZ_PARTITION. Multiple GUI wrappers in one partition are still one demo.
    # Never infer "latest" from PID, nor join GUI to a different world.
    gui_partitions = {
        p["env"].get("GZ_PARTITION") for p in processes
        if p["role"] == "gazebo_gui" and p["env"].get("GZ_PARTITION")
    }
    paired = partitions & gui_partitions
    if len(paired) == 1:
        selected = next(iter(paired))
        matched = [p for p in servers if p["env"].get("GZ_PARTITION") == selected]
        if len(matched) == 1:
            return matched[0], selected, "AUTO_PAIRED_SERVER_GUI_PARTITION"
        return None, None, "PAIRED_PARTITION_SERVER_PID_AMBIGUOUS"
    if len(paired) > 1:
        return None, None, "MULTIPLE_ACTIVE_GAZEBO_GUI_SESSIONS"
    return None, None, "MULTIPLE_OR_UNIDENTIFIED_GAZEBO_PARTITIONS"


def proc_cpu_delta(before: list[dict], after: list[dict],
                   wall_s: float) -> list[dict]:
    prior = {x["pid"]: x for x in before}
    hz = os.sysconf("SC_CLK_TCK")
    result = []
    for p in after:
        row = {key: p[key] for key in
               ("pid", "comm", "role", "env", "env_read_error", "flags")}
        a = prior.get(p["pid"])
        row["cpu_percent_one_core_scale"] = (
            round((p["cpu_ticks"] - a["cpu_ticks"]) / hz / wall_s * 100, 1)
            if a and wall_s > 0 and p["cpu_ticks"] >= a["cpu_ticks"] else None
        )
        result.append(row)
    return result


def find_disk_sensor_profile(partition: str | None = None,
                             base: Path | None = None) -> dict:
    # G07 Task04 runs a separate official Nav2 world. The previous probe
    # incorrectly attached an unrelated, latest D04 camera SDF to G07.
    result = {
        "status": "DISK_ONLY_NOT_PROVEN_ACTIVE",
        "rgbd_hz_disk_candidate": None,
        "rgb_camera_hz_disk_candidate": None,
        "camera_sensors_disk": [],
        "sdf_path": None,
    }
    if partition and partition.startswith("axia_p2_"):
        result["status"] = "NOT_APPLICABLE_TO_G07_SCENARIO"
        return result
    if partition and not partition.startswith("axia_d04_student_"):
        result["status"] = "NOT_APPLICABLE_TO_UNKNOWN_SCENARIO"
        return result
    evidence = base if base is not None else Path.home() / "axia_d04_student_evidence"
    candidates = sorted(
        evidence.glob("d04-gazebo-*/scene/student_waffle_rgb.sdf.xacro"),
        key=lambda p: p.stat().st_mtime, reverse=True,
    )[:1]
    if not candidates:
        result["status"] = "DISK_SDF_NOT_FOUND"
        return result
    p = candidates[0]
    result["sdf_path"] = str(p)
    try:
        import xml.etree.ElementTree as ET
        root = ET.parse(p).getroot()
        for s in root.iter("sensor"):
            name = s.get("name", "")
            sensor_type = s.get("type", "")
            # Exclude gpu_lidar; include official RGB, registered RGBD cameras.
            if not ("rgb" in name.lower() or "camera" in name.lower()
                    or "camera" in sensor_type.lower()):
                continue
            rate = s.findtext("update_rate")
            try:
                hz = float(rate) if rate is not None else None
            except ValueError:
                hz = None
            w = s.findtext("camera/image/width")
            h = s.findtext("camera/image/height")
            entry = {"name": name, "type": sensor_type,
                     "topic": s.findtext("topic"),
                     "update_rate_hz": hz,
                     "resolution": f"{w}x{h}" if w and h else None}
            result["camera_sensors_disk"].append(entry)
            if "rgbd" in name.lower() and hz is not None:
                result["rgbd_hz_disk_candidate"] = hz
            elif (("rgb" in name.lower() or "camera" in name.lower())
                  and hz is not None):
                result["rgb_camera_hz_disk_candidate"] = hz
    except (OSError, ValueError, ET.ParseError):
        result["status"] = "DISK_SDF_PARSE_FAILED"
    return result


def count_target_roles(processes: list[dict],
                       partition: str | None) -> dict[str, int]:
    if not partition:
        return {}
    counts: dict[str, int] = {}
    for p in processes:
        if p.get("env", {}).get("GZ_PARTITION") == partition:
            role = p["role"]
            counts[role] = counts.get(role, 0) + 1
    return counts


def find_ogre_log() -> dict:
    p = Path.home() / ".gz/rendering/ogre2.log"
    if not p.is_file():
        return {"status": "NOT_FOUND", "renderer_line": None}
    try:
        tail = p.read_bytes()[-12000:].decode(errors="replace")
        lines = [s.strip() for s in tail.splitlines()
                 if ("GL_RENDERER" in s or "OpenGL renderer" in s)]
        return {"status": "LOG_MAY_BELONG_TO_PREVIOUS_SESSION",
                "modified_epoch": round(p.stat().st_mtime, 3),
                "renderer_line": lines[-1][:240] if lines else None}
    except OSError:
        return {"status": "NOT_READABLE", "renderer_line": None}


def resource_snapshot() -> dict:
    result = {"nproc": os.cpu_count(), "dev_dxg_present": Path("/dev/dxg").exists()}
    try:
        result["memory_available_kb"] = int(next(
            line.split()[1] for line in Path("/proc/meminfo").read_text().splitlines()
            if line.startswith("MemAvailable:")))
    except (OSError, StopIteration, ValueError):
        result["memory_available_kb"] = None
    try:
        result["cpu_pressure"] = Path("/proc/pressure/cpu").read_text()[:500]
    except OSError:
        result["cpu_pressure"] = None
    return result


def stats_from_live(out: Path, partition: str, seconds: int) -> tuple[str, dict, list, list, float]:
    env = dict(os.environ, GZ_PARTITION=partition)
    listing = limited_command(["gz", "topic", "-l"], env=env, timeout=9)
    (out / "gazebo_topics.txt").write_text(listing["output"][:6000] + "\n")
    topic = next((x.strip() for x in listing["output"].splitlines()
                  if re.fullmatch(r"/world/[^/]+/stats", x.strip())), None)
    if not topic:
        return "WORLD_STATS_NOT_VISIBLE", parse_stats(""), [], [], 0
    before = scan_processes()
    output = out / "world_stats_raw.txt"
    start = time.monotonic()
    with output.open("wb") as fh:
        try:
            proc = subprocess.Popen(["gz", "topic", "-e", "-t", topic],
                                    env=env, stdout=fh, stderr=subprocess.STDOUT,
                                    start_new_session=True)
        except OSError:
            return "GZ_TOPIC_SUBSCRIBER_FAILED", parse_stats(""), before, before, 0
        try:
            time.sleep(seconds)
        finally:
            if proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGINT)
                except ProcessLookupError:
                    pass
                try:
                    proc.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait(timeout=4)
    wall = time.monotonic() - start
    after = scan_processes()
    raw = output.read_bytes()[-200000:].decode(errors="replace")
    # Retain only the final bounded world stats snapshot, not many MB of telemetry.
    output.write_text(raw, encoding="utf-8")
    parsed = parse_stats(raw)
    return ("CAPTURED" if parsed["status"] == "INTERVAL_MEASURED"
            else parsed["status"]), parsed, before, after, wall


def compare(a: dict, b: dict) -> dict:
    def get(obj, *keys):
        for key in keys:
            obj = obj.get(key, {}) if isinstance(obj, dict) else {}
        return obj
    aa, bb = get(a, "rtf", "interval_rtf_percent"), get(b, "rtf", "interval_rtf_percent")
    conditions = []
    if get(a, "server", "gpu_env") != get(b, "server", "gpu_env"):
        conditions.append("gazebo_server_gpu_env")
    if get(a, "sensor_profile", "rgbd_hz_disk_candidate") != \
            get(b, "sensor_profile", "rgbd_hz_disk_candidate"):
        conditions.append("rgbd_hz_disk_candidate")
    if get(a, "gui", "gpu_env") != get(b, "gui", "gpu_env"):
        conditions.append("gazebo_gui_gpu_env")
    if get(a, "renderer_profiles", "inherited", "renderer") != \
            get(b, "renderer_profiles", "inherited", "renderer"):
        conditions.append("shell_glx_renderer")
    if get(a, "active_process_roles") != get(b, "active_process_roles"):
        conditions.append("active_process_roles")
    return {"left_interval_rtf_percent": aa, "right_interval_rtf_percent": bb,
            "rtf_gap_percentage_points": round(bb-aa, 2)
            if isinstance(aa, (int, float)) and isinstance(bb, (int, float))
            else None,
            "changed_conditions": conditions, "root_cause_confirmed": False,
            "comparison_limit": "association only; match scene, RGBD Hz, GUI, CPU and timing"}


def load_report(path: Path) -> dict:
    if path.is_dir():
        return json.loads((path / "summary.json").read_text())
    with zipfile.ZipFile(path) as archive:
        return json.loads(archive.read("summary.json"))


def store(out: Path, result: dict) -> Path:
    (out / "summary.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "AXIA Gazebo RTF/GPU read-only audit",
        f"Capture: {result['capture_status']}",
        f"Gazebo partition: {result.get('partition')}",
        f"Server selection: {result.get('server_selection')}",
        f"Interval RTF percent: {result['rtf']['interval_rtf_percent']}",
        f"World statistics: {result['rtf']['status']}",
        f"GUI/physics separation: process GPU environment only, not actual Ogre2 proof",
        "Sensor profile is latest disk candidate, not matched to active server.",
        "RTX 2060 OpenGL renderer from glxinfo child does NOT verify server GPU.",
        "nvidia-smi is NOT reliable proof of WSLg OpenGL/GUI renderer.",
        "NO_GOAL / NO_CMD_VEL / NO_PROCESS_KILL / SAFETY_TTL_NOT_TESTED / HW_ESTOP_NOT_TESTED",
    ]
    (out / "summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    sums = []
    for f in sorted(out.iterdir()):
        if f.is_file() and f.name != "SHA256SUMS" and not f.name.endswith(".zip"):
            sums.append(f"{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.name}")
    (out / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    dest = out / "axia_wsl2_gazebo_rtf_gpu_audit.zip"
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as archive:
        for f in sorted(out.iterdir()):
            if f.is_file() and f != dest:
                archive.write(f, arcname=f.name)
    return dest


def self_check():
    assert parse_stats("sim_time { sec: 1 nsec: 0 }\n"
                       "real_time { sec: 2 nsec: 0 }\n"
                       "sim_time { sec: 2 nsec: 0 }\n"
                       "real_time { sec: 3 nsec: 0 }\n")["interval_rtf_percent"] == 100
    assert renderer_env("d3d12_nvidia", {"LIBGL_ALWAYS_SOFTWARE": "1"})[
        "MESA_D3D12_DEFAULT_ADAPTER_NAME"] == "NVIDIA"
    print("AXIA_RTF_GPU_AUDIT_SELF_CHECK_PASS ROS_NOT_RUN GAZEBO_NOT_RUN")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--seconds", type=int, default=20)
    ap.add_argument("--server-pid", type=int, default=None)
    ap.add_argument("--partition", default=None)
    ap.add_argument("--out-root", type=Path,
                    default=Path.home() / "axia_gpu_rtf_diagnostics")
    ap.add_argument("--compare", nargs=2, metavar=("BEFORE_ZIP", "AFTER_ZIP"))
    ap.add_argument("--from-stats", type=Path,
                    help="synthetic CI-only input; not live Gazebo evidence")
    args = ap.parse_args(argv)
    if args.self_check:
        self_check()
        return 0
    if args.compare:
        report = compare(*(load_report(Path(p)) for p in args.compare))
        print(json.dumps(report, indent=2))
        return 0
    if not 5 <= args.seconds <= 60:
        ap.error("--seconds must be within 5..60")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = args.out_root.expanduser() / f"audit_{stamp}_{os.getpid()}"
    out.mkdir(parents=True, mode=0o700, exist_ok=False)
    if args.from_stats:
        raw = args.from_stats.read_text(encoding="utf-8")
        (out / "world_stats_raw.txt").write_text(raw[-200000:], encoding="utf-8")
        measured = parse_stats(raw)
        status = "SYNTHETIC_TEST_ONLY"
        procs, gpu, server, gui = [], {}, None, None
        select, partition = "SYNTHETIC_TEST_ONLY", None
        extra = {}
    else:
        initial = scan_processes()
        server, partition, select = choose_server(
            initial, args.server_pid, args.partition or os.getenv("GZ_PARTITION"))
        gpu = renderer_profiles(out)
        smi = limited_command(["nvidia-smi", "--query-gpu=name,driver_version,"
                               "utilization.gpu,memory.used", "--format=csv,noheader"],
                              timeout=7)
        (out / "nvidia_smi_snapshot.txt").write_text(smi["output"][:2000] + "\n")
        extra = {"nvidia_smi_status": smi["status"],
                 "ogre2_log": find_ogre_log(),
                 "machine_resources": resource_snapshot()}
        if partition:
            status, measured, before, after, wall = stats_from_live(out, partition,
                                                                    args.seconds)
            procs = proc_cpu_delta(before, after, wall) if before else initial
        else:
            status = "NO_UNIQUE_GAZEBO_PARTITION"
            measured = parse_stats("")
            procs = initial
        # Re-select after sampling in case a child process was replaced.
        all_procs = scan_processes()
        server2 = next((p for p in all_procs if server and p["pid"] == server["pid"]), None)
        if server2:
            server = server2
        gui = next((p for p in all_procs if p["role"] == "gazebo_gui" and
                    p["env"].get("GZ_PARTITION") == partition), None)
    result = {
        "schema": "axia.wsl2.gz_rtf_gpu_audit.v1",
        "capture_status": status, "partition": partition, "server_selection": select,
        "rtf": measured,
        "server": {"pid": server["pid"] if server else None,
                   "gpu_env": {k: server["env"].get(k) for k in GPU_KEYS}
                   if server else None,
                   "env_read_error": server.get("env_read_error") if server else None},
        "gui": {"pid": gui["pid"] if gui else None,
                "gpu_env": {k: gui["env"].get(k) for k in GPU_KEYS}
                if gui else None},
        "renderer_profiles": gpu, "processes": [
            {k: v for k, v in p.items() if k != "cpu_ticks"} for p in procs
        ], "active_process_roles": count_target_roles(procs, partition),
        "sensor_profile": find_disk_sensor_profile(partition) if not args.from_stats
        else {"status": "SYNTHETIC", "rgbd_hz_disk_candidate": None},
        "platform": extra,
        "actual_gazebo_gui_verified": False,
        "gazebo_server_actual_ogre_gpu_verified": False,
        "sensor_delivery_ttl_verified": False,
        "certified_hw_estop_verified": False,
    }
    dest = store(out, result)
    print("AXIA_RTF_GPU_AUDIT_CAPTURE_STATUS=" + status)
    print("AXIA_RTF_GPU_AUDIT_GAZEBO_PARTITION=" + str(partition))
    print("AXIA_RTF_GPU_AUDIT_SERVER_GPU_ENV=" +
          str(result["server"]["gpu_env"]))
    print("AXIA_GAZEBO_INTERVAL_RTF_PERCENT=" +
          str(measured["interval_rtf_percent"]))
    print("AXIA_RTF_GPU_AUDIT_ZIP=" + str(dest))
    print("AXIA_RTF_GPU_AUDIT_REPORT=" + str(out / "summary.txt"))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f"AXIA_RTF_GPU_AUDIT_ERROR={type(exc).__name__}: {exc}",
              file=sys.stderr)
        sys.exit(2)
