#!/usr/bin/env python3
"""G07 Cycle36 Owner result review; read-only original ROS evidence, no ROS/Goal.

Public CI L2 proof is separate. This tool NEVER issues a formal acceptance
verdict, E-Stop claim, or another Goal. It fails closed on missing source,
RMW publication chronology, any of seven delivery intervals, or Guard latch.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import re

LIMITS={
 "max_source_interval_sec":.12, "max_cm_interval_sec":.12,
 "max_guard_interval_sec":.12, "max_supervisor_fsm_interval_sec":.12,
 "max_scan_interval_sec":.24, "max_odom_interval_sec":.24,
 "max_clock_interval_sec":.24,
}
EXPECTED_ORACLE="CI_GAZEBO_MOVING_GOAL_CANDIDATE"

def assess_owner_original(root: Path, expected_sha: str) -> dict:
    result={"schema":"axia.g07.cycle36.owner_raw_candidate_v1",
            "status":"HOLD","owner_l3_accepted":False,
            "mvp_demo_accepted":False,"certified_estop":False,
            "raw_review_required":True,"goal_authority_inferred":False}
    try:
        if not re.fullmatch(r"[a-f0-9]{40}",expected_sha):
            raise ValueError("INVALID_PIN")
        if root.is_symlink() or not root.is_dir():
            raise ValueError("ROOT_NOT_DIRECTORY")
        src=root/"source.sha"
        live=root/"G07"/"live"
        original=live/"actual_ros_events.jsonl"
        verdict=live/"ci_moving_goal_result.json"
        if any(p.is_symlink() or not p.is_file() for p in (src,original,verdict)):
            raise ValueError("ORIGINAL_MISSING_OR_SYMLINK")
        if src.read_text(encoding="utf-8").strip()!=expected_sha:
            raise ValueError("ORIGINAL_SOURCE_SHA_MISMATCH")
        j=json.loads(verdict.read_text(encoding="utf-8"))
        if (j.get("status")!="NUMERICAL_CANDIDATE"
                or j.get("common_g07_ci_oracle_status")!=EXPECTED_ORACLE
                or j.get("shared_execution_mode")!="owner"
                or j.get("owner_authority_verified") is not True
                or j.get("goal_cancel_ack") is not True
                or j.get("guard_latched") is not False
                or j.get("first_guard_latch") is not None
                or j.get("first_timing_violation") is not None
                or not isinstance(j.get("goal_uuid"),str)
                or not re.fullmatch(r"[a-f0-9]{32}",j["goal_uuid"])):
            raise ValueError("GOAL_GUARD_OR_CANCEL_NOT_PROVEN")
        for key, limit in LIMITS.items():
            x=j.get(key)
            if type(x) not in (float,int) or not math.isfinite(x) or not 0<=x<limit:
                raise ValueError("SEVEN_CHANNEL_RELEASE_MARGIN_"+key)
        dwell=j.get("odom_stopped_dwell_sec")
        if type(dwell) not in (float,int) or not math.isfinite(dwell) or dwell<1.0:
            raise ValueError("ODOM_DWELL_MISSING_OR_TOO_SHORT")
        rows=[json.loads(line) for line in original.read_text(encoding="utf-8").splitlines()]
        goals=[e.get("t") for e in rows if e.get("kind")=="owner_goal_published"]
        if len(goals)!=1 or type(goals[0]) not in (float,int):
            raise ValueError("ONE_ORIGINAL_GOAL_START_NOT_PROVEN")
        cm=[e for e in rows if e.get("kind")=="pre_guard"
            and type(e.get("t")) in (int,float) and e["t"]>=goals[0]]
        if len(cm)<10:
            raise ValueError("CM_RMW_ORIGINAL_COVERAGE_MISSING")
        for e in cm:
            if (type(e.get("rmw_publication_seq")) is not int or
                type(e.get("rmw_source_ns")) is not int or
                type(e.get("rmw_received_ns")) is not int or
                e["rmw_source_ns"]<=0 or
                e["rmw_received_ns"]<e["rmw_source_ns"]):
                raise ValueError("CM_RMW_SOURCE_RECEIPT_INVALID")
        source_gaps=[];receive_gaps=[]
        for a,b in zip(cm,cm[1:]):
            if b["rmw_publication_seq"]!=a["rmw_publication_seq"]+1:
                raise ValueError("CM_RMW_PUBLICATION_SEQUENCE_DISCONTINUITY")
            dt_source=(b["rmw_source_ns"]-a["rmw_source_ns"])/1e9
            dt_recv=(b["rmw_received_ns"]-a["rmw_received_ns"])/1e9
            if not 0<dt_source<.12 or not 0<dt_recv<.12:
                raise ValueError("CM_RMW_120MS_SOURCE_OR_RECEIVE_BREACH")
            source_gaps.append(dt_source);receive_gaps.append(dt_recv)
        result.update(status="NUMERICAL_CANDIDATE_RAW_REVIEW_REQUIRED",
                      goal_uuid=j["goal_uuid"],
                      seven_channel_max={k:round(j[k],6) for k in LIMITS},
                      odom_dwell_sec=round(dwell,6),
                      cm_rmw_source_max_sec=round(max(source_gaps),6),
                      cm_rmw_receive_max_sec=round(max(receive_gaps),6),
                      original_cm_packets=len(cm))
    except (OSError,ValueError,TypeError,KeyError,OverflowError) as exc:
        result["reason"]=str(exc)[:160]
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-root",type=Path,required=True)
    p.add_argument("--source-sha",required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    if a.output.exists() or a.output.is_symlink() or not a.output.parent.is_dir():
        print("AXIA_G07_CYCLE36_OWNER_RAW_REPORT_TARGET_INVALID_HOLD")
        return 3
    v=assess_owner_original(a.run_root,a.source_sha)
    a.output.write_text(json.dumps(v,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print("AXIA_G07_CYCLE36_OWNER_RAW_GATE "+json.dumps(v,sort_keys=True),flush=True)
    print("AXIA_MVP_DEMO_ACCEPTED=HOLD CERTIFIED_ESTOP=false")
    return 0 if v["status"]=="NUMERICAL_CANDIDATE_RAW_REVIEW_REQUIRED" else 3

if __name__=="__main__":
    raise SystemExit(main())
