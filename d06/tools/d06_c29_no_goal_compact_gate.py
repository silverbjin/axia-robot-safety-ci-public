#!/usr/bin/env python3
"""C29 L3 NO_GOAL evidence verifier.

Checks only a compact TAR already produced by C28; this script cannot start
ROS, Gazebo, change DDS or send a Goal. Passing a synthetic TAR in CI is NOT
proof of WSL2/WSLg GPU behavior. Never claim full moving CM120/Guard150.
"""
import hashlib
import json
from pathlib import Path
import re
import sys
import tarfile

MAX_FILE = 1_000_000
REQUIRED = (
    "summary.txt", "native_gazebo_exit_events.log", "renderer.txt",
    "sensor_truth.json", "ordered_shutdown.json", "cm_shutdown_audit.json",
    "teardown.txt", "scan_delivery.json",
)

class Hold(Exception):
    pass

def fail(reason):
    raise Hold(reason)

def verified_items(file):
    if not file.is_absolute() or not file.is_file():
        fail("COMPACT_ABSOLUTE_FILE_REQUIRED")
    sidecar=Path(str(file)+".sha256")
    if not sidecar.is_file():
        fail("COMPACT_SHA256_SIDECAR_REQUIRED")
    supplied=sidecar.read_text(errors="replace").split()
    if not supplied or not re.fullmatch(r"[0-9a-f]{64}",supplied[0]):
        fail("COMPACT_INVALID_SHA256")
    if hashlib.sha256(file.read_bytes()).hexdigest()!=supplied[0]:
        fail("COMPACT_SHA256_MISMATCH")
    selected={}
    with tarfile.open(file,"r:gz") as tf:
        for m in tf:
            if not m.isfile():
                continue
            if m.name not in REQUIRED:
                continue
            if m.size>MAX_FILE or m.size<0 or m.name in selected:
                fail("COMPACT_BOUNDED_REQUIRED_ENTRY_INVALID")
            stream=tf.extractfile(m)
            if stream is None:
                fail("COMPACT_READ_FAILED")
            selected[m.name]=stream.read(MAX_FILE+1).decode("utf-8","replace")
    missing=sorted(set(REQUIRED)-set(selected))
    if missing:
        fail("COMPACT_REQUIRED_EVIDENCE_MISSING_"+",".join(missing))
    return selected

def load(j,name):
    try: return json.loads(j[name])
    except (ValueError,TypeError): fail("INVALID_"+name.replace(".","_"))

def validate(file):
    j=verified_items(file)
    summary_line=j["summary.txt"].splitlines()
    if not summary_line: fail("SUMMARY_EMPTY")
    try: summary=json.loads(summary_line[0])
    except ValueError: fail("SUMMARY_INVALID_JSON")

    renderer=j["renderer.txt"]
    if not re.search(r"(?im)^OpenGL renderer string:.*D3D12.*NVIDIA",renderer):
        fail("WSLG_NVIDIA_D3D12_RENDERER_NOT_PROVEN")
    native=j["native_gazebo_exit_events.log"]
    if not re.search(r"(?m)^\[INFO\]\s+\[gz-\d+\]: process has finished cleanly",native):
        fail("GAZEBO_NATIVE_CHILD_EXIT0_NOT_PROVEN")
    if re.search(r"(?m)^\[ERROR\]\s+\[gz-\d+\]: process has died",native):
        fail("GAZEBO_NATIVE_CHILD_DIED")
    if summary.get("native_gz_exit0_marker") is not True or (
        summary.get("native_gz_died_marker") is not False):
        fail("GAZEBO_EXIT_SUMMARY_MISMATCH")

    sensor=load(j,"sensor_truth.json")
    if sensor.get("status")!="NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE" or sensor.get("reasons")!=[]:
        fail("SENSOR_UNSAFE")
    if sensor.get("goal_sent") is not False or sensor.get("fixture_moved") is not False or sensor.get("fault_injected") is not False:
        fail("MOTION_OR_FAULT_AUTHORITY_VIOLATION")
    if sensor.get("dual_topic_actual_wall_observation_sec",0)<20:
        fail("SENSOR_OBSERVATION_LT_20SEC")
    metrics=sensor.get("metrics",{})
    for name in ("raw","safety"):
        d=metrics.get(name,{})
        if d.get("count",0)<20 or d.get("first_receipt_ttl_breach_at_index") is not None:
            fail(name.upper()+"_SCAN_FIRST_BREACH_OR_MISSING")
        gap=d.get("max_receipt_gap_sec")
        if not isinstance(gap,(int,float)) or gap<=0 or gap>.300:
            fail(name.upper()+"_SCAN300_TTL")
    safety=metrics["safety"]
    if (safety.get("clear_count")!=safety.get("count") or
        safety.get("front_median_m",0)<=.75 or safety.get("side_median_m",0)<=1.2):
        fail("SAFETY_DISTANCE_CLEAR_NOT_PROVEN")

    nav=load(j,"ordered_shutdown.json")
    if (nav.get("status")!="NAV2_LIFECYCLE_SHUTDOWN_ACK" or
        nav.get("navigation_ack") is not True or
        nav.get("localization_ack") is not True):
        fail("NAV2_ACK_MISSING")
    if nav.get("rmw_implementation_identifier")!="rmw_cyclonedds_cpp":
        fail("RMW_DIFFERS_FROM_C29_CI_SELECTED")
    audit=load(j,"cm_shutdown_audit.json")
    if audit.get("status")!="SHUTDOWN_CLEAN_CANDIDATE" or audit.get("cm_exit_code")!=0:
        fail("CM_EXIT0_UNVERIFIED")
    if ("GRACEFUL" not in j["teardown.txt"] or "FORCED" in j["teardown.txt"]
         or summary.get("forced_teardown") is True):
        fail("FORCED_OR_MISSING_TEARDOWN")

    paired=load(j,"scan_delivery.json")
    if any(paired.get(k,0)<20 for k in ("native_count","observer_raw_count","observer_safety_count")):
        fail("NATIVE_OR_ROS_SCAN_WITNESS_MISSING")
    proxy=paired.get("post_ready_proxy",{})
    if (proxy.get("candidate")!="NO_ROS_TTL_VIOLATION_WITNESSED" or
        proxy.get("goal_allowed") is not False):
        fail("POST_NAV2_READY_EXACT_SCAN300_HOLD")
    first=paired.get("student_first_ttl",{})
    if first.get("student_first_candidate")!="STUDENT_FIRST_PAIR_UNAVAILABLE":
        fail("STUDENT_FIRST_SCAN300_VIOLATION")
    if paired.get("goal_allowed") is not False:
        fail("ROS_WITNESS_GOAL_NOT_DENIED")
    if summary.get("first_failure") not in ("NOT_OBSERVED_IN_COMPACT",):
        fail("FIRST_SAFETY_FAILURE_WITNESSED")

    return {"scope":"WSL2_NO_GOAL_COMPACT_ONLY","rmw":"rmw_cyclonedds_cpp",
            "raw_max_ms":round(metrics["raw"]["max_receipt_gap_sec"]*1000,3),
            "safety_max_ms":round(metrics["safety"]["max_receipt_gap_sec"]*1000,3),
            "cm_exit0":True,"nav_loc_ack":True,"gazebo_native_exit0":True,
            "cm120_guard150_moving_e2e":"NOT_VERIFIED"}

def main():
    if len(sys.argv)!=3 or sys.argv[1]!="--verify-compact":
        print("C29_EVIDENCE_HOLD=USAGE",file=sys.stderr)
        return 3
    try:
        output=validate(Path(sys.argv[2]))
    except (Hold,OSError,tarfile.TarError,TypeError,KeyError,AttributeError) as exc:
        print("C29_EVIDENCE_HOLD="+str(exc).replace("\n"," ")[:200])
        print("AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false")
        return 3
    print("C29_NO_GOAL_EVIDENCE_CONTRACT_PASS_NEEDS_ACTUAL_WSL2_PROVENANCE")
    print("C29_COMPACT_VERDICT="+json.dumps(output,sort_keys=True))
    print("AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false")
    return 0

if __name__=="__main__":
    sys.exit(main())
