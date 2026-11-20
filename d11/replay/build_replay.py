#!/usr/bin/env python3
"""AXIA D11: D10 validator reuse + D11 recorded AE/IF replay, no live inference.

Public source code only. Requires private score CSVs at OWNER runtime; public CI
uses independently generated fake UI scores (no model answers in public).
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
D10_PATH=ROOT/"d10/replay/build_replay.py"
D10_SPEC=importlib.util.spec_from_file_location("axia_d10_replay_immutable_validator",D10_PATH)
if D10_SPEC is None or D10_SPEC.loader is None:
    raise RuntimeError("D11_D10_REPLAY_VALIDATOR_NOT_AVAILABLE")
D10=importlib.util.module_from_spec(D10_SPEC)
D10_SPEC.loader.exec_module(D10)

def validate_and_build(raw_path:Path, if_scores:Path, ae_scores:Path, manifest_path:Path,
                       if_source:str="RECORDED_IF_CSV",ae_source:str="RECORDED_AE_CSV")->dict:
    """D10's strict source/quality/window/timestamp validator runs TWICE."""
    if if_source==ae_source:
        raise ValueError("D11_PROVENANCE_MODEL_SOURCES_MUST_DIFFER")
    original=D10.validate_and_build(raw_path,if_scores,manifest_path,if_source)
    reconstructed=D10.validate_and_build(raw_path,ae_scores,manifest_path,ae_source)
    if original["raw_sha256"]!=reconstructed["raw_sha256"]:
        raise ValueError("D11_RAW_SHA_MISMATCH")
    if len(original["traces"])!=len(reconstructed["traces"]):
        raise ValueError("D11_TRACE_COUNT_MISMATCH")
    ordered=[]
    for a,b in zip(original["traces"],reconstructed["traces"]):
        if (a["id"],a["kind"],a["quality_reason"])!=(b["id"],b["kind"],b["quality_reason"]):
            raise ValueError("D11_TRACE_JOIN_MISMATCH")
        if a["samples"]!=b["samples"] or len(a["windows"])!=len(b["windows"]):
            raise ValueError("D11_RAW_OR_WINDOW_JOIN_MISMATCH")
        joined=[]
        for wa,wb in zip(a["windows"],b["windows"]):
            for fld in ("w","timestamp_ns","status","reason","truth"):
                if wa[fld]!=wb[fld]:
                    raise ValueError(f"D11_WINDOW_JOIN_MISMATCH {a['id']}/{wa['w']} field={fld}")
            def model_fields(w):
                return {key:w.get(key) for key in ("score","threshold","prediction","case")}
            joined.append({key:wa[key] for key in ("w","timestamp_ns","status","reason","truth")} |
                          {"if":model_fields(wa),"ae":model_fields(wb)})
        ordered.append({key:a[key] for key in ("id","kind","quality_reason","samples")} |
                       {"windows":joined})
    for name,payload in (("IF",original),("AE",reconstructed)):
        if len(payload["warnings"])>100: raise ValueError("D11_WARNING_COUNT_INVALID")
        if sum(payload["confusion"].values())!=100:raise ValueError("D11_EVALUATION_BASE_INVALID")
    return {
        "schema_version":1,"name":"AXIA D11 Recorded AE vs IF Classroom Investigation",
        "source":"SYNTHETIC_COURSE_FIXTURE","seed":2409,
        "ros_actual":False,"gazebo_actual":False,"safety_control_authority":False,
        "inference_runtime":False,"recorded_data_only":True,
        "raw_sha256":original["raw_sha256"],
        "models":{
            "IF":{"score_source":if_source,"score_sha256":original["scores_sha256"],
                  "confusion":original["confusion"],"threshold":original["threshold"]},
            "AE":{"score_source":ae_source,"score_sha256":reconstructed["scores_sha256"],
                  "confusion":reconstructed["confusion"],"threshold":reconstructed["threshold"]},
        },
        "traces":ordered
    }

def assert_reference_baseline(payload:dict, metrics_path:Path|None=None):
    """PRIVATE OWNER ONLY; never call this with public mock score data."""
    # D10 invariant: exact reference SHA, TP/FP/FN/TN and warning windows.
    # This check is on D10-derived payload with private IF data.
    if payload["models"]["IF"]["confusion"]!={"TP":1,"FP":2,"FN":17,"TN":80}:
        raise ValueError("D11_PRIVATE_IF_CONFUSION_MISMATCH")
    if not math.isclose(payload["models"]["IF"]["threshold"],0.10199750,abs_tol=1e-8):
        raise ValueError("D11_PRIVATE_IF_THRESHOLD_MISMATCH")
    if payload["raw_sha256"]!="4078e35cb789cf2f468819ad1af8218e95c7489d90a8c24031ec06bc9fff8410":
        raise ValueError("D11_PRIVATE_RAW_SHA_MISMATCH")
    if payload["models"]["IF"]["score_sha256"]!="380eebbab3c83c7ba0fe60f28b25bf9c9f9dc71cd407eafd83114bb55a01ad42":
        raise ValueError("D11_PRIVATE_IF_SHA_MISMATCH")
    if payload["models"]["AE"]["confusion"]!={"TP":18,"FP":4,"FN":0,"TN":78}:
        raise ValueError("D11_PRIVATE_AE_CONFUSION_MISMATCH")
    if not math.isclose(payload["models"]["AE"]["threshold"],0.90363125,abs_tol=1e-8):
        raise ValueError("D11_PRIVATE_AE_THRESHOLD_MISMATCH")
    # Ground example windows in actual immutable private score records.
    by={x["id"]:x for x in payload["traces"]}
    def is_case(trace,w,which,pred,truth):
        item=by[trace]["windows"][w]
        return item[which]["prediction"]==pred and item["truth"]==truth
    for name,w,kind,pred,truth in [
        ("TST_A_00",4,"if","NORMAL",1),("TST_A_00",4,"ae","WARNING",1),
        ("TST_A_00",5,"if","WARNING",1),
        ("TST_N_02",4,"if","NORMAL",0),("TST_N_02",4,"ae","WARNING",0),
        ("TST_A_04",8,"if","WARNING",0),("TST_A_04",8,"ae","WARNING",0),
        ("TST_Q_01",0,"ae","INSUFFICIENT_DATA",-1)
    ]:
        if not is_case(name,w,kind,pred,truth):
            raise ValueError(f"D11_PRIVATE_STORY_WINDOW_MISMATCH {name}/{w}/{kind}")
    if metrics_path is None:
        raise ValueError("D11_AE_METRICS_REQUIRED_FOR_PRIVATE_ACCEPTANCE")
    m=json.loads(metrics_path.read_text(encoding="utf-8"))
    required={
        "source":"SYNTHETIC_COURSE_FIXTURE","model":"CPU_TORCH_AE",
        "threshold_source":"normal_valid_only","scaler_fit":"normal_train_only",
        "fit_on_test":False,"test_threshold_tuned":False,
        "test_valid_count":100,"test_invalid_count":4,"train_count":240,"valid_count":80,
        "ros_actual":False,"gazebo_actual":False,"control_authority":False,
        "weights_sha256":"5fdb2f7882f23b94d3559886dd622e363ceab87a5da4cb3f78a8e850ccf358fe"
    }
    for k,v in required.items():
        if m.get(k)!=v:raise ValueError(f"D11_PRIVATE_AE_METRICS_MISMATCH {k}")
    if m["confusion"]!=payload["models"]["AE"]["confusion"]:
        raise ValueError("D11_PRIVATE_AE_METRICS_CONFUSION_MISMATCH")
    if not math.isclose(m["threshold"],payload["models"]["AE"]["threshold"],abs_tol=1e-8):
        raise ValueError("D11_PRIVATE_AE_METRICS_CUTOFF_MISMATCH")

def render_html(payload:dict,out:Path)->Path:
    template=Path(__file__).with_name("replay_template.html").read_text(encoding="utf-8")
    token="/*__DATA_JSON__*/"
    if template.count(token)!=1:raise ValueError("D11_TEMPLATE_PLACEHOLDER_INVALID")
    safe=json.dumps(payload,ensure_ascii=False,separators=(",",":"),allow_nan=False)
    safe=safe.replace("<",r"\u003c").replace(">",r"\u003e").replace("&",r"\u0026").replace("\u2028",r"\u2028")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(template.replace(token,safe),encoding="utf-8")
    return out

def main(argv=None)->int:
    p=argparse.ArgumentParser(description="Recorded dual IF/AE classroom HTML, NO model or ROS")
    p.add_argument("--raw",type=Path,required=True)
    p.add_argument("--if-scores",type=Path,required=True)
    p.add_argument("--ae-scores",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--ae-metrics",type=Path)
    p.add_argument("--expect-baseline",action="store_true")
    p.add_argument("--if-source",default="RECORDED_IF_CSV")
    p.add_argument("--ae-source",default="RECORDED_AE_CSV")
    args=p.parse_args(argv)
    try:
        payload=validate_and_build(args.raw,args.if_scores,args.ae_scores,args.manifest,
                                  args.if_source,args.ae_source)
        if args.expect_baseline:assert_reference_baseline(payload,args.ae_metrics)
        render_html(payload,args.out)
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print("D11_REPLAY_CONTRACT_FAIL",str(exc),file=sys.stderr)
        return 2
    c=payload["models"]
    print("D11_REPLAY_L0_PASS source=SYNTHETIC_COURSE_FIXTURE"
          " traces=14 windows=104 valid=100 quality=4"
          f" if_tp={c['IF']['confusion']['TP']} if_fp={c['IF']['confusion']['FP']}"
          f" if_fn={c['IF']['confusion']['FN']} if_tn={c['IF']['confusion']['TN']}"
          f" ae_tp={c['AE']['confusion']['TP']} ae_fp={c['AE']['confusion']['FP']}"
          f" ae_fn={c['AE']['confusion']['FN']} ae_tn={c['AE']['confusion']['TN']}"
          " ros_actual=false gazebo_actual=false model_inference=false")
    print("D11_REPLAY_OUTPUT="+str(args.out.resolve()))
    return 0

if __name__=="__main__":raise SystemExit(main())
