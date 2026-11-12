#!/usr/bin/env python3
"""Read-only D04 Owner evidence. Does not run ROS, Gazebo or publish topics.

After managed shutdown there are no live ROS topics to query. Assess the
previously recorded message counts and original gate verdict instead.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

def latest(base:Path)->Path|None:
    items=[p for p in base.glob("d04-package-*") if p.is_dir()]
    return max(items,key=lambda p:p.stat().st_mtime) if items else None

def read_json(p:Path)->dict:
    result=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(result,dict):
        raise ValueError(f"JSON object required: {p.name}")
    return result

def check(root:Path)->int:
    print(f"D04_EVIDENCE_DIR={root}")
    vfile=root/"round-1/live/verdict.json"
    ofile=root/"owner_summary.json"
    rfile=root/"repeat_summary.json"
    needed=[vfile,ofile,rfile,root/"round-1/live/person_samples.json",
            root/"round-1/live/debug_frame.png"]
    if not root.is_dir() or any(not p.is_file() for p in needed):
        missing=[str(p.relative_to(root)) for p in needed if not p.is_file()]
        print("D04_EVIDENCE_MISSING="+",".join(missing or [str(root)]))
        print("D04_RECORDED_RGB_BRIDGE_YOLO=UNVERIFIED")
        print("D04_REALTIME_ROS_RECHECK=NOT_RUN")
        return 2
    try:
        v=read_json(vfile)
        o=read_json(ofile)
        r=read_json(rfile)
        samples=read_json(root/"round-1/live/person_samples.json")
        vis=v.get("vision") or {}
        if not isinstance(vis,dict):
            raise ValueError("vision is not object")
        camera=int(vis.get("camera_frames",0))
        detect=int(vis.get("detection_frames",0))
        debug=int(vis.get("debug_frames",0))
        num_samples=len(samples.get("samples",[]))
        print(f"D04_RECORDED_CAMERA_FRAMES={camera}")
        print(f"D04_RECORDED_DETECTION_FRAMES={detect}")
        print(f"D04_RECORDED_DEBUG_FRAMES={debug}")
        print(f"D04_RECORDED_PERSON_SAMPLES={num_samples}")
        print(f"D04_RECORDED_RUNTIME_STATUS={v.get('status','MISSING')}")
        print(f"D04_RECORDED_SHUTDOWN_QUALITY={v.get('shutdown_quality','MISSING')}")
        ok=all((
            o.get("status")=="PASS_PACKAGED_P1_YOLO_CLEAN_1X",
            o.get("gate_exit")==0,
            o.get("wrapper_exit")==0,
            r.get("passed") is True,
            r.get("completed_rounds")==1,
            v.get("status")=="PASS_P1_AND_YOLO_PACKAGE_CLEAN_EXIT",
            v.get("graph_stable") is True,
            v.get("person_valid") is True,
            v.get("rgb_valid") is True,
            v.get("debug_image_saved") is True,
            v.get("motion_verified") is True,
            v.get("shutdown_quality")=="PASS_NAV2_MANAGED_NO_SIGABRT",
            (v.get("shutdown_service") or {}).get("passed") is True,
            v.get("goal_sent") is False,
            v.get("fault_injected") is False,
            camera>0,detect>0,debug>0,num_samples>0
        ))
    except (ValueError,TypeError,KeyError,AttributeError,OSError) as exc:
        print(f"D04_EVIDENCE_INVALID={type(exc).__name__}:{exc}")
        print("D04_RECORDED_RGB_BRIDGE_YOLO=UNVERIFIED")
        print("D04_REALTIME_ROS_RECHECK=NOT_RUN")
        return 2
    print("D04_RECORDED_RGB_BRIDGE_YOLO="+
          ("PASS_FROM_SAVED_VERDICT" if ok else "UNVERIFIED"))
    print("D04_AFTER_MANAGED_SHUTDOWN_TOPICS=NOT_EXPECTED")
    print("D04_LIVE_DOMAIN_ID=40 D04_DISCOVERY_RANGE=LOCALHOST")
    print("D04_REALTIME_ROS_RECHECK=NOT_RUN")
    print("D04_EVIDENCE_MEANING=prior_owner_record_only_not_new_inference")
    return 0 if ok else 2

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--evidence",type=Path,
                   help="Exact Owner EVIDENCE path; otherwise latest ~/axia_d04_evidence/d04-package-*")
    args=p.parse_args()
    root=args.evidence if args.evidence else latest(Path.home()/"axia_d04_evidence")
    if root is None:
        print("D04_EVIDENCE_MISSING=no_d04_package_directories")
        print("D04_RECORDED_RGB_BRIDGE_YOLO=UNVERIFIED")
        print("D04_REALTIME_ROS_RECHECK=NOT_RUN")
        return 2
    return check(root)

if __name__=="__main__":
    raise SystemExit(main())
