#!/usr/bin/env python3
"""G07 GUI-only first visual boundary: actual X11 geometry and D3D12 GPU.

No ROS, no Goal, no GUI automation. Unlike the old receipt, Qt Selection
Owner (3x3) is never a visible Gazebo/RViz window. XWD capture is only raw
render evidence; actual Waffle/world visual contents need owner review.
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path

WINDOW=re.compile(
    r'^\s*(0x[0-9a-f]+)\s+"([^"]+)"[^\n]*?\b(\d+)x(\d+)'
    r'[+-]\d+[+-]\d+',re.I|re.M)
MIN_WIDTH=320
MIN_HEIGHT=240

def window_id(tree: str, app: str) -> str | None:
    if app not in ("gazebo","rviz"):
        raise ValueError("G07_GUI_APP_UNRECOGNIZED")
    for match in WINDOW.finditer(tree):
        wid,title,w,h=match.groups()
        lo=title.lower()
        if "selection owner" in lo or int(w)<MIN_WIDTH or int(h)<MIN_HEIGHT:
            continue
        if app=="gazebo" and ("gazebo" in lo or "gz sim" in lo):
            return wid
        if app=="rviz" and "rviz" in lo:
            return wid
    return None

def gpu_is_target_accelerated(glx: str, adapter: str) -> bool:
    if adapter not in ("NVIDIA",):
        return False
    return (bool(re.search(r'D3D12\s*\([^\n]*NVIDIA',glx,re.I))
            and bool(re.search(r'Accelerated:\s*yes',glx,re.I))
            and bool(re.search(r'(?:OpenGL(?: core profile)? version string:|Max core profile version)\s*4\.[1-9]',glx,re.I)))

def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    source=p.add_mutually_exclusive_group(required=True)
    source.add_argument("--tree",type=Path)
    source.add_argument("--gpu",type=Path)
    p.add_argument("--role",choices=["gazebo","rviz"])
    p.add_argument("--adapter",choices=["NVIDIA"],default="NVIDIA")
    a=p.parse_args()
    try:
        if a.tree is not None:
            if not a.role:
                raise ValueError("MISSING_ROLE")
            result=window_id(a.tree.read_text(errors="replace"),a.role)
            if result:
                print(result)
                return 0
            print("AXIA_G07_C38_VISIBLE_X11_WINDOW_MISSING",a.role,flush=True)
            return 3
        if gpu_is_target_accelerated(a.gpu.read_text(errors="replace"),a.adapter):
            print("AXIA_G07_C38_D07_NVIDIA_D3D12_ACCELERATED_PREFLIGHT_PASS")
            return 0
        print("AXIA_G07_C38_D07_PROVEN_GPU_NOT_SELECTED_HOLD")
        return 3
    except (OSError,ValueError) as exc:
        print("AXIA_G07_C38_GUI_SOURCE_EVIDENCE_ERROR",type(exc).__name__)
        return 3

if __name__=="__main__":
    raise SystemExit(main())
