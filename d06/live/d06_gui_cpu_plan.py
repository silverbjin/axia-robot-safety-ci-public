#!/usr/bin/env python3
"""D06 display-only CPU separation: no ROS, no Goal, no safety process changes.

Private G07 Owner / CI recorder pins the *last* allowed CPU. Use the first
allowed CPU for RViz2 + read-only Marker observer so display work cannot
compete on the evidence-recorder CPU. This does not isolate the ROS safety
processes or prove DDS/scheduling causality. Run-time requires >=2 CPUs.
"""
from __future__ import annotations

import argparse
import os
import sys


def select_cpu(cpus: set[int] | list[int] | tuple[int, ...]) -> int:
    distinct = sorted(set(cpus))
    if len(distinct) < 2 or not all(type(x) is int and x >= 0 for x in distinct):
        raise ValueError("D06_GUI_CPU_INSUFFICIENT_OR_INVALID_AFFINITY")
    return distinct[0]


def select_monitor_cpu(cpus: set[int] | list[int] | tuple[int, ...]) -> int:
    """Read-only Marker must NOT share official CM CPU.

    Original 4-CPU CI: CM {1,2}, Goal {2,3}, Marker 2 (3 roles on core 2).
    Original 8-CPU WSL2: Marker 6, which collides with the new exclusive
    CM {1,6}. This is a role-conflict hypothesis, not a proven TTL cause.
    On 4/5 CPUs put Marker with Goal/low-priority recorder role, while
    >=6 CPUs place Marker on the Goal observer pool's first middle core.
    Renderer=first, CM=second+(6+:second last), recorder=last.
    Both CI and Owner launch the SAME public sidecar with this function.
    """
    distinct = sorted(set(cpus))
    if len(distinct) < 4 or not all(type(x) is int and x >= 0 for x in distinct):
        raise ValueError("D06_MONITOR_CPU_INSUFFICIENT_OR_INVALID_AFFINITY")
    return distinct[2] if len(distinct)>=6 else distinct[3]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--cpus", help="L0 test fixture only; actual runtime uses sched_getaffinity")
    p.add_argument("--role", choices=("gui", "monitor"), default="gui")
    args = p.parse_args()
    try:
        if args.cpus is None:
            cpus = os.sched_getaffinity(0)
        else:
            if not args.cpus or not all(v.isascii() and v.isdigit()
                                            for v in args.cpus.split(",")):
                raise ValueError("D06_GUI_CPU_INVALID_TEST_FIXTURE")
            cpus = {int(v) for v in args.cpus.split(",")}
        print(select_monitor_cpu(cpus) if args.role == "monitor" else select_cpu(cpus))
        return 0
    except (ValueError, OSError) as exc:
        print("D06_GUI_CPU_INSUFFICIENT: " + str(exc), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
