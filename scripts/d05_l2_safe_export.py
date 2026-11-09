#!/usr/bin/env python3
"""Sanitize actual D05 L2 evidence for public CI (no private code/weights)."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil


def export(source: Path, target: Path) -> dict:
    raw=json.loads((source/"verdict.json").read_text())
    target.mkdir(parents=True,exist_ok=True)
    valid=raw.get("valid_status") or {}
    unknown=raw.get("unknown_after_loss") or {}
    first=raw.get("first_frame") or {}
    summary={
        "gate":raw.get("gate"),
        "status":raw.get("status"),
        "blocker":raw.get("blocker"),
        "private_sha":raw.get("private_sha"),
        "public_source_sha":raw.get("public_source_sha"),
        "world_sha256":raw.get("world_sha256"),
        "model_sha256":raw.get("model_sha256"),
        "actor_sha256":raw.get("actor_sha256"),
        "rgbd_origin":"single_registered_gazebo_rgbd_camera",
        "initial_rgb_metadata":{k:first.get("rgb",{}).get(k) for k in (
            "stamp_ns","frame_id","width","height","encoding","sha256")},
        "initial_depth_metadata":{k:first.get("depth",{}).get(k) for k in (
            "stamp_ns","frame_id","width","height","encoding","sha256")},
        "initial_yolo_debug_metadata":{k:first.get("debug",{}).get(k) for k in (
            "stamp_ns","frame_id","width","height","encoding","sha256")},
        "actual_stream_counts":raw.get("source_counts"),
        "real_person_bbox_sample":(raw.get("person_examples") or [None])[0],
        "valid":{k:valid.get(k) for k in (
            "status","reason","distance_m","unit","valid_count","valid_fraction",
            "roi_pixels","frame_stamp_ns","depth_stamp_ns",
            "detection_stamp_ns","optical_frame_id","bbox_roi_xyxy")},
        "unknown_after_depth_loss":{k:unknown.get(k) for k in (
            "status","reason","distance_m","frame_stamp_ns","depth_stamp_ns",
            "detection_stamp_ns")},
        "depth_bridge_shutdown":raw.get("depth_bridge_shutdown"),
        "rgb_continued_after_loss":raw.get("rgb_continued_after_loss"),
        "yolo_continued_after_loss":raw.get("yolo_continued_after_loss"),
        "p1_g00_g04_accepted":False,
        "goal_sent":False,
        "fault_injected":False,
        "cmd_vel_published":False,
        "certified_estop":False
    }
    safe_path=target/"safe_verdict.json"
    safe_path.write_text(json.dumps(summary,indent=2,ensure_ascii=False,
                                    allow_nan=False)+"\n")
    png=source/"person_yolo_debug.png"
    if png.is_file():
        shutil.copyfile(png,target/"person_yolo_debug.png")
    files=sorted(f for f in target.iterdir() if f.is_file() and f.name!="SHA256SUMS")
    (target/"SHA256SUMS").write_text("".join(hashlib.sha256(f.read_bytes()).hexdigest()
        +"  "+f.name+"\n" for f in files))
    return summary


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--target",type=Path,required=True)
    args=parser.parse_args()
    result=export(args.source,args.target)
    print(json.dumps({"gate":result["gate"],"status":result["status"],
                      "blocker":result["blocker"]},ensure_ascii=False))
