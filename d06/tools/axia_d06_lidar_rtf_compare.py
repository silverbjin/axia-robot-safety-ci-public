#!/usr/bin/env python3
"""Read-only A/B comparison: LiDAR geometry and RTF are independent axes.

The result is ALWAYS no-goal/HOLD. Renderer labels must be actual glxinfo
strings, not requested MESA_D3D12_DEFAULT_ADAPTER_NAME values.
"""
import argparse
import json
import math
from pathlib import Path


def _safe_range(report):
    try:
        m=report["metrics"]["safety"]
        f,s,near=float(m["front_median_m"]),float(m["side_median_m"]),m.get("near_ring_fraction_median")
        return (math.isfinite(f) and math.isfinite(s) and f>.75 and s>1.2
                and (near is None or (math.isfinite(float(near)) and float(near)<.95))
                and int(m["count"]) >=20)
    except (KeyError,ValueError,TypeError):
        return False


def _rtf(report):
    try:
        val=report["rtf_diagnostics"]["ros_clock_rtf"]
        return float(val) if val is not None and math.isfinite(float(val)) and float(val)>0 else None
    except (KeyError,TypeError,ValueError):
        return None


def compare_adapter_results(intel, nvidia, intel_renderer, nvidia_renderer):
    """Correlation matrix; no proof that an individual GPU caused the fault."""
    good_adapter=("d3d12" in intel_renderer.lower()
                  and "intel" in intel_renderer.lower()
                  and "d3d12" in nvidia_renderer.lower()
                  and "nvidia" in nvidia_renderer.lower()
                  and "llvmpipe" not in nvidia_renderer.lower())
    int_rtf,nv_rtf=_rtf(intel),_rtf(nvidia)
    int_clear,nv_clear=_safe_range(intel),_safe_range(nvidia)
    if not good_adapter:
        result="ADAPTER_COMPARISON_INVALID"
    elif int_rtf is None or nv_rtf is None:
        result="RTF_AXIS_UNVERIFIED"
    elif not int_clear and nv_clear and int_rtf<.8 and nv_rtf>=.8:
        result="DISTANCE_AND_RTF_BOTH_IMPROVE_CANDIDATE"
    elif not nv_clear and int_rtf<.8 and nv_rtf>=.8:
        result="RTF_RECOVERED_DISTANCE_STILL_UNSAFE"
    elif not int_clear and nv_clear and nv_rtf<.8:
        result="DISTANCE_RECOVERED_RTF_STILL_LOW"
    else:
        result="NO_INDEPENDENT_RECOVERY_PROVEN"
    return {
        "schema":"axia_d06_wslg_lidar_rtf_ab_v1",
        "result":result,
        "intel":{"actual_renderer":intel_renderer,"range_clear":int_clear,
                 "ros_clock_rtf":int_rtf,
                 "max_safety_receipt_gap_sec":intel.get("metrics",{}).get("safety",{}).get("max_receipt_gap_sec")},
        "nvidia":{"actual_renderer":nvidia_renderer,"range_clear":nv_clear,
                  "ros_clock_rtf":nv_rtf,
                  "max_safety_receipt_gap_sec":nvidia.get("metrics",{}).get("safety",{}).get("max_receipt_gap_sec")},
        "adapter_verified":good_adapter,
        "gpu_causality_proven":False,
        "moving_goal_approved":False,
        "certified_estop":False,
        "owner_wslg_a_b_inherited_environment_uncontrolled":False,
        "release":"HOLD",
        "notes":"Actual WSLg renderer and ROS/clock RTF must be measured in BOTH sessions; statistical correlation alone does not establish exact GPU driver root cause."
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--intel-json",type=Path,required=True)
    p.add_argument("--nvidia-json",type=Path,required=True)
    p.add_argument("--intel-renderer",type=Path,required=True)
    p.add_argument("--nvidia-renderer",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    def renderer(path):
        return next((x.split(":",1)[1].strip() for x in path.read_text().splitlines()
                     if x.startswith("OpenGL renderer string:")), "NOT_MEASURED")
    result=compare_adapter_results(
        json.loads(args.intel_json.read_text()),
        json.loads(args.nvidia_json.read_text()),
        renderer(args.intel_renderer),renderer(args.nvidia_renderer))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("AXIA_D06_LIDAR_RTF_INDEPENDENT_AB "+json.dumps(result,sort_keys=True))
    print("D06_GAZEBO_LIVE_RELEASE=HOLD CERTIFIED_ESTOP=false")
    return 0 if result["adapter_verified"] and result["result"]!="RTF_AXIS_UNVERIFIED" else 3


if __name__=="__main__":
    raise SystemExit(main())
