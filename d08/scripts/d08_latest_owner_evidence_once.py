#!/usr/bin/env python3
"""Extract only the most recent AXIA D08 WSL2 Owner failure as one small ZIP.

No ROS, Gazebo or third-party Python dependencies. Never modifies original logs.
Only allowlisted text/JSON is included; no CTF, binaries, models, full bags or builds.
"""
from __future__ import annotations

import argparse
from collections import deque
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
import zipfile

DEFAULT_ROOT = Path.home() / "axia_d08_owner_runs"
STAMP = re.compile(r"(20\d{6}T\d{6})")
BAD = re.compile(
    r"ERROR|FATAL|Exception|Traceback|BLOCKED|TIMEOUT|"
    r"first[_ -]?(?:boundary|scan|gap)|\bFAIL(?:ED|URE)?\b|"
    r"RMW_|D08_OWNER_|D08_REAL_|GAP|not found|missing|"
    r"Permission denied|Killed|SIGABRT|Segmentation|"
    r"Keyboard initialization|exit code|lifecycle|stale", re.I
)
MAX_LOG_SCAN = 160 * 1024 * 1024
MAX_LOG_OUTPUT = 256 * 1024
MAX_JSON = 512 * 1024


def session_time(path: Path) -> float:
    match = STAMP.search(path.name)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y%m%dT%H%M%S").replace(
                tzinfo=timezone.utc).timestamp()
        except ValueError:
            pass
    return path.stat().st_mtime


def latest(root: Path) -> tuple[Path, Path | None]:
    if not root.is_dir():
        raise FileNotFoundError("D08_ROOT_MISSING: " + str(root))
    sessions = [p for p in root.iterdir() if p.is_dir() and not p.is_symlink()
                and (p.name.startswith("once_") or p.name.startswith("run_"))]
    if not sessions:
        raise FileNotFoundError("D08_NO_OWNER_RUNS: " + str(root))
    session = max(sessions, key=lambda p: (session_time(p), p.name))
    if session.name.startswith("run_"):
        return session, session
    children = [p for p in session.iterdir() if p.is_dir() and not p.is_symlink()
                and p.name.startswith("run_")]
    return session, (max(children, key=lambda p: (session_time(p), p.name))
                     if children else None)


def excerpt(path: Path) -> bytes:
    first = []
    recent = deque(maxlen=55)
    tail = deque(maxlen=55)
    start = []
    previous = deque(maxlen=2)
    scanned = 0
    limited = False
    with path.open("rb") as stream:
        for n, raw in enumerate(stream, 1):
            scanned += len(raw)
            if scanned > MAX_LOG_SCAN:
                limited = True
                break
            line = f"L{n} " + raw[:8192].decode("utf-8", "replace").rstrip() + "\n"
            if len(start) < 35:
                start.append(line)
            if BAD.search(line):
                context = "".join(previous) + line
                if len(first) < 20:
                    first.append(context)
                recent.append(context)
            previous.append(line)
            tail.append(line)
        if limited:
            stream.seek(max(0, path.stat().st_size - 1024 * 1024))
            lines = stream.read(1024 * 1024).decode("utf-8", "replace").splitlines()
            for n, line in enumerate(lines[-1000:]):
                if BAD.search(line):
                    recent.append(f"END+{n} {line[:8192]}\n")
            for line in lines[-50:]:
                tail.append("END " + line[:8192] + "\n")
    return (
        "=== START ===\n" + "".join(start)
        + "\n=== FIRST ERRORS AND FIRST STATE BOUNDARIES ===\n" + "".join(first)
        + "\n=== LAST ERRORS AND STATE BOUNDARIES ===\n" + "".join(recent)
        + "\n=== LAST LINES ===\n" + "".join(tail)
        + f"\nSCAN_CAPPED={limited}\n"
    ).encode("utf-8", "replace")[:MAX_LOG_OUTPUT]


def sources(session: Path, run: Path | None):
    yield "session/owner_console.excerpt.txt", session / "owner_console.log", "log"
    if run is None:
        return
    for name in ("yolo_native.log", "yolo_build.log", "rmw_trace_stop.log",
                 "rmw_trace_watchdog.log", "owner_gpu_probe.txt"):
        yield "logs/" + name + ".excerpt.txt", run / name, "log"
    for name in ("d08_official_nav2_one_world.log", "gazebo_server.log"):
        yield "logs/" + name + ".excerpt.txt", run / "live_evidence" / name, "log"
    for rel in (
        "rmw_trace/owner_first_gap_verdict.json",
        "rmw_trace/summary.json",
        "rmw_trace/tracetools-status.txt",
        "rmw_trace/trace-size-bytes.txt",
        "rmw_trace/stop.success",
        "live_evidence/verdict.json",
        "live_evidence/runtime_provenance.json",
        "live_evidence/official_nav2_before_path.json",
        "live_evidence/amcl_receive_timing.json",
        "live_evidence/gazebo_startup.json",
        "live_evidence/official_path_phases/verdict.json",
        "live_evidence/official_path_phases/path_phases.jsonl",
        "live_evidence/live_person_range/verdict.json",
    ):
        kind = ("json" if rel.endswith(".json") else
                "log" if rel.endswith(".jsonl") else "text")
        yield "run/" + rel + (".excerpt.txt" if kind == "log" else ""), run / rel, kind
    cycles = run / "live_evidence" / "owner_replan_cycles"
    if cycles.is_dir():
        available = sorted((c for c in cycles.glob("cycle_[0-9][0-9][0-9][0-9]")
                            if c.is_dir() and not c.is_symlink()), key=lambda c: c.name)
        chosen = {c.name: c for c in available[:1] + available[-2:]}
        for c in available:
            verdict = c / "verdict.json"
            if not verdict.is_file() or verdict.is_symlink():
                continue
            try:
                if verdict.stat().st_size <= MAX_JSON:
                    record = json.loads(verdict.read_text("utf-8"))
                    status = str(record.get("status", "")).upper()
                    if (record.get("first_boundary")
                            or record.get("first_scan_timing_boundary")
                            or "FAIL" in status or "BLOCK" in status):
                        chosen[c.name] = c
                        break
            except (OSError, ValueError, TypeError):
                chosen[c.name] = c
                break
        for c in sorted(chosen.values(), key=lambda p: p.name):
            yield f"cycles/{c.name}/verdict.json", c / "verdict.json", "json"
            yield f"cycles/{c.name}/path_phases.excerpt.txt", c / "path_phases.jsonl", "log"


def extract(root: Path, output: Path, max_mib: int = 8):
    session, run = latest(root)
    if output.exists():
        raise FileExistsError("D08_OUTPUT_ALREADY_EXISTS: " + str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    remaining = min(max_mib * 1024 * 1024 // 2, 6 * 1024 * 1024)
    selected, omitted, entries = [], [], []
    for name, path, kind in sources(session, run):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            if kind == "log":
                content = excerpt(path)
            elif kind == "json":
                content = (path.read_bytes() if path.stat().st_size <= MAX_JSON else
                           f"OVERSIZE_JSON_SKIPPED bytes={path.stat().st_size}\n".encode())
            else:
                content = path.read_bytes()[:32768]
        except (OSError, ValueError) as err:
            omitted.append({"name": name, "error": str(err)})
            continue
        if len(content) > remaining:
            omitted.append({"name": name, "error": "ZIP_BYTE_BUDGET"})
            continue
        entries.append((name, content))
        remaining -= len(content)
        selected.append({"name": name, "source": str(path),
                         "source_bytes": path.stat().st_size,
                         "stored_bytes": len(content),
                         "sha256": sha256(content).hexdigest()})
    if not entries:
        raise RuntimeError("D08_LATEST_SESSION_HAS_NO_DIAGNOSTIC_LOGS: " + str(session))
    manifest = {"status": "DIAGNOSTICS_ONLY_NOT_SAFETY_PASS",
                "latest_session": str(session),
                "latest_run": str(run) if run else None,
                "raw_ctf_assets_bags_included": False,
                "originals_preserved": True, "included": selected, "omitted": omitted}
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as archive:
        for name, content in entries:
            archive.writestr(name, content)
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        archive.writestr("SHA256SUMS", "".join(
            f"{sha256(content).hexdigest()}  {name}\n" for name, content in entries))
    if output.stat().st_size > max_mib * 1024 * 1024:
        output.unlink()
        raise RuntimeError("D08_OUTPUT_OVER_MAX_SIZE_REMOVED")
    print("D08_LATEST_DIAGNOSTICS_READY_NOT_L3_PASS")
    print("D08_SELECTED_SESSION=" + str(session))
    print("D08_SELECTED_RUN=" + (str(run) if run else "NONE_PRE_RUN_FAILURE"))
    print("D08_COMPACT_EVIDENCE=" + str(output))
    print("D08_COMPACT_SHA256=" + sha256(output.read_bytes()).hexdigest())
    print("D08_COMPACT_BYTES=" + str(output.stat().st_size))
    print("D08_ORIGINAL_RAW_LOGS_PRESERVED=1")


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    p.add_argument("--output", type=Path)
    p.add_argument("--max-mib", type=int, choices=range(1, 17), default=8)
    a = p.parse_args(argv)
    utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = a.output or a.root / f"D08_LATEST_FAILURE_{utc}.zip"
    try:
        extract(a.root.expanduser(), output.expanduser(), a.max_mib)
    except (OSError, RuntimeError, ValueError) as err:
        print(f"D08_LATEST_DIAGNOSTICS_HOLD={err}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
