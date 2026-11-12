#!/usr/bin/env python3
"""Instructor D04 visual evidence of real single-image YOLO boxes.

Consumes the *public student demo's actual* detections.csv + SHA256 manifest.
Does NOT rerun YOLO. Class, confidence and xyxy coordinates are taken from
the same CSV rows as the boxes rendered in the annotated PNG and HTML.
No ROS/Gazebo/Nav2/Goal/stop, no automatic image viewer spawning.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
from html import escape
import json
import math
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _font(size: int):
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                 "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"):
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            pass
    return ImageFont.load_default()


def parse_original_evidence(image: Path, model: Path, out: Path):
    if not image.is_file() or image.is_symlink():
        raise ValueError("INPUT_IMAGE_MISSING_OR_SYMLINK")
    if not model.is_file() or model.is_symlink() or model.suffix != ".pt":
        raise ValueError("LOCAL_PT_MODEL_MISSING_OR_SYMLINK")
    manifest_path=out/"run_manifest.json"
    csv_path=out/"detections.csv"
    if not manifest_path.is_file() or not csv_path.is_file():
        raise ValueError("ORIGINAL_YOLO_RESULTS_MISSING")
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("image_sha256") != sha256(image) or
            manifest.get("model_sha256") != sha256(model)):
        raise ValueError("ORIGINAL_ASSET_SHA256_MISMATCH")
    if (manifest.get("level") != "LOCAL_YOLO_CPU_ONLY" or
            manifest.get("ros_verified") is not False or
            manifest.get("gazebo_verified") is not False):
        raise ValueError("INFERENCE_SCOPE_NOT_SINGLE_IMAGE")
    with Image.open(image) as src:
        src.verify()
    with Image.open(image) as src:
        width,height=src.size
    if width<4 or height<4:
        raise ValueError("INVALID_IMAGE_SIZE")
    with csv_path.open(newline="",encoding="utf-8") as handle:
        reader=csv.DictReader(handle)
        required={"frame_id","category","confidence","x1","y1","x2","y2",
                  "image_width","image_height"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError("CSV_FIELDS_INCOMPLETE")
        raw=list(reader)
    if len(raw)!=manifest.get("detections") or not raw or len(raw)>100:
        raise ValueError("CSV_DETECTION_COUNT_INVALID")
    detections=[]
    for i,row in enumerate(raw,1):
        label=str(row["category"])
        score=float(row["confidence"])
        box=[int(row[k]) for k in ("x1","y1","x2","y2")]
        x1,y1,x2,y2=box
        if (label!="person" or not math.isfinite(score) or
                not (0<=score<=1) or
                (int(row["image_width"]),int(row["image_height"]))!=(width,height) or
                not (0<=x1<x2<=width and 0<=y1<y2<=height)):
            raise ValueError(f"INVALID_CLASS_CONFIDENCE_BBOX_{i}")
        detections.append({
            "index":i,"class":label,"confidence":score,
            "bbox_xyxy":box,"bbox_width":x2-x1,"bbox_height":y2-y1,
        })
    return (width,height),detections,manifest


def make_report(image: Path, model: Path, out: Path):
    size, detections, manifest=parse_original_evidence(image,model,out)
    outputs=[out/"bbox_class_confidence.png",
             out/"bbox_class_confidence.json",
             out/"bbox_class_confidence.html"]
    if any(p.exists() for p in outputs):
        raise ValueError("REPORT_ALREADY_EXISTS_EVIDENCE_PRESERVED")

    with Image.open(image) as source:
        rendered=source.convert("RGB")
    font=_font(max(12,min(22,size[0]//50)))
    draw=ImageDraw.Draw(rendered)
    for row in detections:
        x1,y1,x2,y2=row["bbox_xyxy"]
        ink=(235,32,62)
        # Larger border + filled label: text and bbox are visually linked.
        draw.rectangle((x1,y1,x2,y2),outline=ink,width=max(2,size[0]//300))
        label=f"#{row['index']} class={row['class']} conf={row['confidence']:.4f}"
        bounds=draw.textbbox((0,0),label,font=font,stroke_width=0)
        text_height=bounds[3]-bounds[1]+6
        text_width=bounds[2]-bounds[0]+8
        ty=y1-text_height if y1>=text_height else min(y2,max(0,size[1]-text_height))
        tx=min(x1,max(0,size[0]-text_width))
        draw.rectangle((tx,ty,min(size[0]-1,tx+text_width),
                        min(size[1]-1,ty+text_height)),fill=ink)
        draw.text((tx+4,ty+2),label,font=font,fill="white")
    rendered.save(outputs[0],format="PNG")

    report={
        "source":"LOCAL_YOLO_CPU_ONLY", "source_csv":"detections.csv",
        "image_sha256":manifest["image_sha256"],
        "model_sha256":manifest["model_sha256"],
        "image_size":list(size),
        "person_count":len(detections),
        "detections":detections,
        "ros_gazebo_nav2_safety":"NOT_RUN",
        "annotation_tool":"Pillow; no new inference and no auto GUI viewer",
    }
    outputs[1].write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",
                          encoding="utf-8")
    table="\n".join(
        "<tr><td>{index}</td><td>{cls}</td><td>{conf:.4f}</td>"
        "<td>{bbox}</td><td>{width} x {height}</td></tr>".format(
            index=r["index"],cls=escape(r["class"]),conf=r["confidence"],
            bbox=escape(str(tuple(r["bbox_xyxy"]))),
            width=r["bbox_width"],height=r["bbox_height"])
        for r in detections)
    html=f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><title>AXIA D04 — bbox, class, confidence</title>
<style>body{{font:16px system-ui, sans-serif;max-width:1180px;margin:24px auto;padding:0 16px}}
img{{display:block;max-width:100%;height:auto;border:1px solid #ccc}}
table{{border-collapse:collapse;width:100%;margin-top:16px}}
th,td{{border:1px solid #aaa;padding:8px;text-align:left}}
th{{background:#eee}}code{{background:#eee;padding:2px 5px}}</style></head>
<body><h1>AXIA D04 — 단일 이미지 YOLO 검출</h1>
<p>검증 범위: <b>실제 이미지 CPU YOLO 추론</b> / ROS·Gazebo·Nav2·안전 정지 <b>NOT_RUN</b></p>
<p><b>class</b> = 객체 범주, <b>confidence</b> = 모델 신뢰도(0–1),
<b>bbox_xyxy</b> = 이미지 픽셀 좌상단(x1,y1)·우하단(x2,y2).
YOLO bbox는 로봇과의 물리 거리나 안전 인증을 나타내지 않는다.</p>
<img src="bbox_class_confidence.png" alt="사람 검출 Bounding Boxes / class / confidence">
<table><thead><tr><th>#</th><th>class</th><th>confidence</th>
<th>bbox_xyxy (pixels)</th><th>bbox width × height</th></tr></thead>
<tbody>{table}</tbody></table></body></html>
"""
    outputs[2].write_text(html,encoding="utf-8")
    for row in detections:
        box=",".join(map(str,row["bbox_xyxy"]))
        print(f"D04_SINGLE_IMAGE_BBOX index={row['index']} "
              f"class={row['class']} confidence={row['confidence']:.4f} "
              f"bbox_xyxy=({box}) bbox_wh=({row['bbox_width']},"
              f"{row['bbox_height']})",flush=True)
    print(f"D04_SINGLE_IMAGE_IMAGE_PATH={outputs[0]}",flush=True)
    print(f"D04_SINGLE_IMAGE_HTML_REPORT={outputs[2]}",flush=True)
    print(f"D04_SINGLE_IMAGE_REPORT_PASS persons={len(detections)} "
          "NO_GAZEBO NO_ROS NO_GOAL NO_SAFETY",flush=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--image",required=True,type=Path)
    p.add_argument("--model",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    try:
        make_report(args.image,args.model,args.out)
    except (OSError,ValueError,TypeError,KeyError,csv.Error,
            json.JSONDecodeError) as err:
        print("D04_SINGLE_IMAGE_REPORT_BLOCKED="+type(err).__name__+":"+str(err),
              file=sys.stderr)
        return 2
    return 0


if __name__=="__main__":
    raise SystemExit(main())
