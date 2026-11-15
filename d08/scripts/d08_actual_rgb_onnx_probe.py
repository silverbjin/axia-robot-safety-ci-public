#!/usr/bin/env python3
"""No-Goal, actual Gazebo RGB frame -> exact D04 YOLO26n ONNX model L2 canary.

This exercises the trained MODEL on real Gazebo pixels. It is NOT a substitute
for the Owner yolo_ros DetectionArray, private D05, WSLg/YOLO timing or Goal.
Never use colour-only framing to assert a person classification.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

EXPECTED_SHA="4f44c33cea12d4b5785e5e7c0a20c13d0c62a77de607ce96a40d6036c7d7bbcf"
PERSON_CLASS_ID=0
UMBRELLA_CLASS_ID=25
CONFIDENCE=0.25

def inspect_frame(session, frame:Path)->dict:
    import numpy as np
    from PIL import Image
    with Image.open(frame) as image:
        if image.size!=(640,480):
            raise ValueError("D08_L2_RGB_NOT_REAL_640x480")
        pix=np.asarray(image.convert("RGB"),dtype=np.float32)
    assert pix.shape==(480,640,3)
    # Exact model input shape from the real Owner yolo_ros Model log:
    # [1,3,480,640], RGB, float32, normalized. No resize/letterbox required.
    tensor=np.transpose(pix/255.0,(2,0,1))[None].copy()
    input_name=session.get_inputs()[0].name
    pred=session.run(None,{input_name:tensor})[0]
    if pred.shape!=(1,84,6300):
        raise ValueError(f"D08_YOLO_ONNX_OUTPUT_SHAPE_CHANGED:{pred.shape}")
    values=pred[0]
    coords=values[:4,:]           # cx,cy,width,height on native frame
    scores=values[4:,:]           # 80 COCO-class confidences
    if not np.isfinite(values).all():
        raise ValueError("D08_YOLO_ONNX_NONFINITE_OUTPUT")
    classes=np.argmax(scores,axis=0)
    confidence=scores[classes,np.arange(scores.shape[1])]
    valid=(confidence>=CONFIDENCE)&(coords[2,:]>=4)&(coords[3,:]>=4)&(
        coords[0,:]>=0)&(coords[0,:]<=640)&(coords[1,:]>=0)&(coords[1,:]<=480)
    person=(classes==PERSON_CLASS_ID)&valid
    umbrella=(classes==UMBRELLA_CLASS_ID)&valid
    # Raw high-confidence candidate boxes are NOT NMS'ed yolo_ros detections.
    # Never equate this count to the Owner's original 52 DetectionArray records.
    return {
        "rgb_source":str(frame),
        "real_rgb_expected":True,
        "pixels_shape":[480,640,3],
        "onnx_output_shape":[1,84,6300],
        "confidence_threshold":CONFIDENCE,
        "person_class_id":PERSON_CLASS_ID,
        "umbrella_class_id":UMBRELLA_CLASS_ID,
        "person_candidate_count":int(person.sum()),
        "umbrella_candidate_count":int(umbrella.sum()),
        "highest_person_class_score":round(float(scores[PERSON_CLASS_ID].max()),6),
        "highest_umbrella_class_score":round(float(scores[UMBRELLA_CLASS_ID].max()),6),
        "pass_real_person_model_canary":bool(person.any()),
    }

def run(args)->int:
    import onnxruntime as ort
    model=Path(args.model)
    if not model.is_file() or hashlib.sha256(model.read_bytes()).hexdigest()!=EXPECTED_SHA:
        raise ValueError("D08_YOLO26N_ONNX_SHA256_MISMATCH")
    report=Path(args.report)
    if report.exists() or report.is_symlink():
        raise ValueError("D08_ONNX_REPORT_MUST_BE_NEW")
    session=ort.InferenceSession(str(model),providers=["CPUExecutionProvider"])
    if (len(session.get_inputs())!=1 or
            session.get_inputs()[0].shape!=[1,3,480,640]):
        raise ValueError("D08_YOLO_ONNX_INPUT_NOT_OWNER_480x640")
    before=inspect_frame(session,Path(args.frame))
    after=inspect_frame(session,Path(args.stop_frame)) if args.stop_frame else None
    # Owner UI9iQEzj originally observed only umbrella at the 1.35m
    # world fixture. A nearby real Gazebo stop-frame class-0 response must
    # be POSITIVE too. Earlier CI calculated the StopZone diagnostic but
    # silently allowed it to be person-zero.
    stop_frame_person_verified=(
        after is not None and after["pass_real_person_model_canary"])
    pass_both_frames=(before["pass_real_person_model_canary"]
                      and stop_frame_person_verified)
    verdict={
        "source":"ACTUAL_PUBLIC_GAZEBO_RGB_FRAME_OFFLINE_ONNX_MODEL",
        "model_sha256":EXPECTED_SHA,
        "status":"PASS_MODEL_ONLY" if pass_both_frames
                 else "STOPZONE_PERSON_CLASS_ZERO",
        "pre_goal":before,
        "stop_frame_diagnostic_only":after,
        "stop_frame_person_verified":stop_frame_person_verified,
        "stop_frame_actual_rgb_required":True,
        "owner_yolo_ros_detection_array_verified":False,
        "private_d05_verified":False,
        "owner_wslg_full_runtime_verified":False,
        "goal_sent":False,"certified_estop":False,
    }
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(json.dumps(verdict,sort_keys=True,indent=2)+"\n")
    if verdict["status"]!="PASS_MODEL_ONLY":
        print("D08_ACTUAL_ONNX_PERSON_FRAME_L2_BLOCKED "+json.dumps({
            "person_candidates":before["person_candidate_count"],
            "umbrella_candidates":before["umbrella_candidate_count"],
            "person_max":before["highest_person_class_score"],
            "umbrella_max":before["highest_umbrella_class_score"],
            "stop_person_candidates":after["person_candidate_count"] if after else None,
            "stop_person_max":after["highest_person_class_score"] if after else None}),
            flush=True)
        return 2
    print("D08_ACTUAL_ONNX_PERSON_FRAME_L2_PASS "+
          json.dumps({"person_candidates":before["person_candidate_count"],
                      "person_max":before["highest_person_class_score"],
                      "stop_person_candidates":after["person_candidate_count"],
                      "stop_person_max":after["highest_person_class_score"]}),flush=True)
    return 0

def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--frame",type=Path,required=True)
    parser.add_argument("--stop-frame",type=Path)
    parser.add_argument("--model",type=Path,required=True)
    parser.add_argument("--report",type=Path,required=True)
    raise SystemExit(run(parser.parse_args()))

if __name__=="__main__":
    main()
