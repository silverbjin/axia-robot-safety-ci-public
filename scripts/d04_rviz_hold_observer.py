#!/usr/bin/env python3
"""Pass-through Owner stdout and open read-only RViz only at GUI_DEMO_HOLD.

This observer never publishes ROS topics, sends an action goal, inspects a
private instructor source, or changes Owner verdict/status/exit code.
RViz errors are logged separately; no "Gazebo PASS" is inferred from a GUI.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

TRIGGER = "[D04][GUI_DEMO_HOLD] START"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--launcher", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()

    viewer: subprocess.Popen | None = None
    log_stream = None
    try:
        for line in sys.stdin:
            sys.stdout.write(line)
            sys.stdout.flush()
            if TRIGGER not in line or viewer is not None:
                continue
            if not args.launcher.is_file():
                print("D04_RVIZ_OBSERVER_NOT_READY=LAUNCHER_MISSING", flush=True)
                continue
            try:
                args.log.parent.mkdir(parents=True, exist_ok=True)
                log_stream = args.log.open("w", encoding="utf-8")
                viewer = subprocess.Popen(
                    ["bash", str(args.launcher), "--open"],
                    stdin=subprocess.DEVNULL,
                    stdout=log_stream,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                print(f"D04_RVIZ_OBSERVER_LAUNCHED pid={viewer.pid} log={args.log}",
                      flush=True)
            except OSError as exc:
                print(f"D04_RVIZ_OBSERVER_NOT_READY={type(exc).__name__}", flush=True)
        return 0
    finally:
        if viewer is not None:
            # Give a newly launched mock/real viewer a scheduler turn.
            if viewer.poll() is None:
                time.sleep(0.2)
            if viewer.poll() is None:
                try:
                    os.killpg(viewer.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    viewer.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(viewer.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    viewer.wait(timeout=2)
            print("D04_RVIZ_OBSERVER_STOPPED: owned RViz process only", flush=True)
        if log_stream is not None:
            log_stream.close()


if __name__ == "__main__":
    raise SystemExit(main())
