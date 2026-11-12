"""D04 instructor single-image classroom regression; PUBLIC CI, no private P1.

Reuses public Student exact image/YOLO CPU demo and adds a visual bbox/class/conf
report. Synthetic RGB/CSV tests MUST precede expensive real CPU inference CI.
"""
from __future__ import annotations
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
ENTRY=ROOT/"scripts/axia_d04_classroom_wsl2_once.sh"
WRAPPER=ROOT/"scripts/axia_d04_instructor_single_image_once.sh"
REPORT=ROOT/"scripts/d04_instructor_single_image_report.py"
STUDENT_SHA="6012336bef42be7f9d74cc9632baea41db555ae9"


def test_entry_and_public_student_pinning_contract():
    assert WRAPPER.is_file(), "RED: single-image instructor sidecar missing"
    assert REPORT.is_file(), "RED: class, confidence, bbox visual report missing"
    assert subprocess.run(["bash","-n",str(WRAPPER)]).returncode==0
    result=subprocess.run(["bash",str(WRAPPER),"--self-check"],
                          capture_output=True,text=True,timeout=5)
    assert result.returncode==0,result.stderr+result.stdout
    assert "D04_SINGLE_IMAGE_STATIC_PASS NO_ROS NO_GAZEBO" in result.stdout
    body=WRAPPER.read_text()
    for required in (
        STUDENT_SHA, "block_B/day04/yolo_single_image_demo.py",
        "block_B/day04/run_teacher_yolo_demo_once.sh",
        "AXIA_D04_STUDENT_PYTHON", "AXIA_D04_STUDENT_CACHE",
        "AXIA_D04_STUDENT_RESULTS", "D04_SINGLE_IMAGE_REPORT_PASS",
    ):
        assert required in body,required
    for forbidden in (
        "axia-robot-safety-instructor", "gh auth", "send_goal",
        "pkill ", "killall ", "xdg-open", "ros2 topic pub",
    ):
        assert forbidden not in body,forbidden


def test_existing_gazebo_demo_is_unchanged_unless_opted_in():
    script=ENTRY.read_text()
    assert "--single-image" in script
    assert "axia_d04_instructor_single_image_once.sh" in script
    assert "AXIA_D04_SINGLE_IMAGE_AFTER_GAZEBO" in script
    assert "SINGLE_IMAGE_AFTER_GAZEBO:-0" in script
    assert "D04_CLASSROOM_PINNED_OWNER_RUNNER_READY" in script
    assert "D04_RVIZ_GUI_ACCEPTANCE=NOT_INFERRED_FROM_OWNER_EXIT" in script
    r=subprocess.run(["bash",str(ENTRY),"--self-check"],
                     capture_output=True,text=True,timeout=5)
    assert r.returncode==0
    assert "SINGLE_IMAGE" in r.stdout
    assert "GAZEBO_NOT_RUN" in r.stdout


def fixture(tmp:Path):
    image=tmp/"bus.jpg"
    Image.new("RGB",(120,90),(240,240,240)).save(image)
    model=tmp/"yolo26n.pt"
    model.write_bytes(b"test-only-public-fake-model")
    out=tmp/"out"
    out.mkdir()
    with (out/"detections.csv").open("w",newline="") as fp:
        writer=csv.DictWriter(fp,fieldnames=[
            "frame_id","stamp_s","category","confidence","x1","y1",
            "x2","y2","image_width","image_height"])
        writer.writeheader()
        writer.writerows([
            dict(frame_id="f1",stamp_s="NA",category="person",confidence="0.9304",
                 x1="10",y1="10",x2="48",y2="65",image_width="120",image_height="90"),
            dict(frame_id="f1",stamp_s="NA",category="person",confidence="0.745",
                 x1="60",y1="20",x2="105",y2="70",image_width="120",image_height="90"),
        ])
    (out/"run_manifest.json").write_text(json.dumps({
        "image_sha256":hashlib.sha256(image.read_bytes()).hexdigest(),
        "model_sha256":hashlib.sha256(model.read_bytes()).hexdigest(),
        "detections":2, "level":"LOCAL_YOLO_CPU_ONLY",
        "ros_verified":False,"gazebo_verified":False,
    }))
    return image,model,out


def test_report_real_saved_png_and_lecture_labels_without_inference(tmp_path):
    image,model,out=fixture(tmp_path)
    r=subprocess.run([sys.executable,str(REPORT),"--image",str(image),
                      "--model",str(model),"--out",str(out)],
                     capture_output=True,text=True,timeout=10)
    assert r.returncode==0,r.stderr+r.stdout
    for term in ("D04_SINGLE_IMAGE_BBOX index=1", "class=person",
                 "confidence=0.9304","bbox_xyxy=(10,10,48,65)",
                 "D04_SINGLE_IMAGE_BBOX index=2","confidence=0.7450",
                 "D04_SINGLE_IMAGE_REPORT_PASS", "NO_GAZEBO NO_ROS"):
        assert term in r.stdout,term
    annotated=out/"bbox_class_confidence.png"
    assert annotated.is_file()
    with Image.open(annotated) as pic:
        assert pic.size==(120,90)
        assert pic.getpixel((10,10)) != Image.open(image).getpixel((10,10))
    rows=json.loads((out/"bbox_class_confidence.json").read_text())
    assert rows["source"]=="LOCAL_YOLO_CPU_ONLY"
    assert len(rows["detections"])==2
    assert rows["detections"][0]["bbox_xyxy"]==[10,10,48,65]
    assert rows["detections"][0]["class"]=="person"
    assert rows["detections"][0]["confidence"]==0.9304
    html=(out/"bbox_class_confidence.html").read_text()
    for required in ("class","confidence","bbox_xyxy",
                     "bbox_class_confidence.png","person","0.9304"):
        assert required in html


def test_report_rejects_tampering_without_new_artifact(tmp_path):
    image,model,out=fixture(tmp_path)
    (out/"run_manifest.json").write_text('{"detections":999}')
    r=subprocess.run([sys.executable,str(REPORT),"--image",str(image),
                      "--model",str(model),"--out",str(out)],
                     capture_output=True,text=True,timeout=10)
    assert r.returncode!=0
    assert "D04_SINGLE_IMAGE_REPORT_BLOCKED" in r.stderr
    assert not (out/"bbox_class_confidence.png").exists()


def test_report_rejects_invalid_bbox_or_confidence(tmp_path):
    image,model,out=fixture(tmp_path)
    csv_path=out/"detections.csv"
    text=csv_path.read_text().replace("0.9304","1.2")
    csv_path.write_text(text)
    r=subprocess.run([sys.executable,str(REPORT),"--image",str(image),
                      "--model",str(model),"--out",str(out)],
                     capture_output=True,text=True,timeout=10)
    assert r.returncode!=0
    assert "D04_SINGLE_IMAGE_REPORT_BLOCKED" in r.stderr
