#!/usr/bin/env python3
"""Three real Gazebo/YOLO cold starts using same pinned, prebuilt engine.

No synthetic detection, fake ROS, goal or fault; each round uses own GZ partition,
actual Waffle Pi RGB, actor mesh and CPU ONNX inference. Output is evidence only.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

def evaluate_round(folder: Path, rc: int):
    verdict_path=folder/"verdict.json"
    if not verdict_path.is_file():
        return {"passed":False,"reason":"NO_VERDICT","exit_code":rc}
    v=json.loads(verdict_path.read_text())
    e=v.get("ros_evidence") or {}
    person=e.get("person") or {}
    passed=(
        rc==0 and v.get("status")=="PASS_REAL_GAZEBO_PERSON_BBOX_CONFIDENCE"
        and person.get("class_name")=="person"
        and isinstance(person.get("score"),float) and 0.0<person["score"]<=1.0
        and e.get("camera_frames",0)>=1
        and e.get("detection_frames",0)>=1
        and e.get("debug_frames",0)>=1
        and (folder/"debug_frame.png").is_file()
        and (folder/"camera_frame.png").is_file()
    )
    return {
        "passed":passed,
        "exit_code":rc,
        "status":v.get("status"),
        "reason":v.get("blocker"),
        "person_score":person.get("score"),
        "person_bbox":{k:person.get(k) for k in
            ("center_x","center_y","size_x","size_y")},
        "camera_frames":e.get("camera_frames",0),
        "detection_frames":e.get("detection_frames",0),
        "debug_frames":e.get("debug_frames",0),
    }

def run(rounds, output: Path):
    if rounds!=3:
        raise ValueError("Only 3x short MVP stability gate is authorized")
    output.mkdir(parents=True,exist_ok=True)
    per=[]
    for n in range(1,rounds+1):
        env=os.environ.copy()
        env["GITHUB_RUN_ID"]=str(env.get("GITHUB_RUN_ID","local"))+"-round"+str(n)
        source=Path("results/d04-yolo-person")
        if source.is_dir():
            shutil.rmtree(source)
        start=time.monotonic()
        try:
            r=subprocess.run([sys.executable,"scripts/d04_yolo_person_runtime.py"],
                             env=env,capture_output=True,text=True,
                             timeout=170,check=False)
            rc=r.returncode
            stdout=r.stdout
            stderr=r.stderr
        except subprocess.TimeoutExpired as exc:
            rc=124
            stdout=(exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout,bytes) else (exc.stdout or "")
            stderr=(exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr,bytes) else (exc.stderr or "")
        target=output/("round-"+str(n))
        if source.is_dir():
            shutil.move(str(source),str(target))
        else:
            target.mkdir(parents=True,exist_ok=True)
        (target/"runner_stdout.log").write_text(stdout)
        (target/"runner_stderr.log").write_text(stderr)
        result=evaluate_round(target,rc)
        result["round"]=n
        result["elapsed_s"]=round(time.monotonic()-start,2)
        per.append(result)
        print(json.dumps(result,ensure_ascii=False),flush=True)
        if not result["passed"]:
            break
    passed=len(per)==rounds and all(x["passed"] for x in per)
    summary={
        "gate":"G-D04-4_STABILITY_GAZEBO_YOLO_3X",
        "passed":passed,"completed_rounds":len(per),"required_rounds":rounds,
        "source_sha":os.environ.get("AXIA_TESTED_HEAD_SHA","NOT_PINNED"),
        "p1_included":False,"goal_sent":False,"fault_injected":False,
        "results":per,
    }
    (output/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
    files=sorted(p for p in output.rglob("*") if p.is_file() and p.name!="SHA256SUMS")
    (output/"SHA256SUMS").write_text("".join(
        hashlib.sha256(p.read_bytes()).hexdigest()+"  "+p.relative_to(output).as_posix()+"\n"
        for p in files))
    print(json.dumps({k:summary[k] for k in ("gate","passed","completed_rounds","required_rounds")},
                     ensure_ascii=False))
    return 0 if passed else 2

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--rounds",type=int,default=3)
    p.add_argument("--out",type=Path,default=Path("results/d04-yolo-stability"))
    args=p.parse_args()
    raise SystemExit(run(args.rounds,args.out))
