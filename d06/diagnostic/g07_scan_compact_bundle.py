#!/usr/bin/env python3
"""Six bounded allowlisted numeric Owner records; never copy bag/Goal UUID/path."""
import argparse
import json
import math
from pathlib import Path

NAMES=("first_scan_timing_boundary.json","scan_wall_sim_rtf_summary.json",
       "scan_pipeline_first_failure.json","guard_supervisor_first_state_transition.json",
       "native_shutdown_verdict.json","release_scope.json")

def _read(path):
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size>262144:return {}
        x=json.loads(path.read_text(encoding="utf-8"))
        return x if isinstance(x,dict) else {}
    except (OSError,ValueError,UnicodeError):return {}

def _num(v):
    return round(v,9) if type(v) in (int,float) and math.isfinite(v) else None

def _enum(v,options):
    return v if isinstance(v,str) and v in options else "NOT_VERIFIED"

def build_compact_records(root,student_sha,l2_run):
    root=Path(root)
    motion=_read(root/"native/g07_ci_moving/ci_moving_goal_result.json")
    pre=_read(root/"native/g07_ci_scan_pregoal.json")
    shutdown=_read(root/"native/g07_ordered_shutdown.json")
    first=motion.get("first_timing_violation")
    first=first if isinstance(first,dict) else {}
    diag=motion.get("delivery_interval_diagnostics")
    scan=diag.get("scan",{}) if isinstance(diag,dict) else {}
    if not isinstance(scan,dict):scan={}
    gap=_num(scan.get("first_violation_sec"))
    gap_ms=round(gap*1000,6) if gap is not None else None
    maximum=_num(motion.get("max_scan_interval_sec"))
    max_ms=round(maximum*1000,6) if maximum is not None else None
    breached=gap_ms is not None and gap_ms>=300
    boundary={"status":"SCAN300_BREACH" if breached else "NOT_MEASURED",
              "first_gap_ms":gap_ms,"maximum_gap_ms":max_ms,"limit_ms":300,
              "first_at_host_monotonic":_num(scan.get("first_violation_at")),
              "first_from_host_monotonic":_num(scan.get("first_violation_from")),
              "first_stage":_enum(scan.get("first_violation_stage"),
                     {"PRE_STOP","POST_STOP","CROSSES_STOP","UNKNOWN_STOP_TIME"}),
              "first_global_channel":_enum(first.get("channel"),
                     {"scan","odom","clock","guard","supervisor","source","cm"}),
              "native_gazebo_publication_pair":"NOT_MEASURED",
              "owner_l3_pass":False}
    topics=pre.get("topic_results",{})
    topics=topics if isinstance(topics,dict) else {}
    def tinfo(topic):
        x=topics.get(topic,{})
        if not isinstance(x,dict):return {}
        return {"max_wall_gap_ms":_num(x.get("max_wall_gap_ms")),
                "max_sim_header_gap_ms":_num(x.get("max_header_sim_gap_ms")),
                "samples":x.get("pairs") if type(x.get("pairs")) is int else None}
    prestatus=_enum(pre.get("status"),{"HOLD","PASS_SCOPED_RECEIVED_SCAN_ONLY"})
    rtf={"pre_goal_status":prestatus,
         "pre_goal_rtf_estimate":_num(pre.get("local_window_rtf_estimate")),
         "pre_goal_raw_scan":tinfo("scan"),"pre_goal_safety_scan":tinfo("safety_scan"),
         "motion_scan_wall_max_ms":max_ms,
         "motion_sim_header_delta":"NOT_MEASURED",
         "native_sim_vs_host_causal_attribution":"UNPROVEN"}
    pipeline={"status":"SCAN300_BREACH_HOLD" if breached else "NOT_MEASURED_HOLD",
              "first_known_layer":"ROS_OBSERVER_CALLBACK",
              "root_cause":"UNDETERMINED","gazebo_native_publish_monotonic":"NOT_MEASURED",
              "bridge_emit_monotonic":"NOT_MEASURED",
              "rosbag_independent_receiver":"NOT_PARSED_IN_COMPACT_TOOL",
              "observer_only_root_proven":False,"sensor_generation_root_proven":False,
              "safety_ttl_changed":False}
    state={"first_guard_transition":"NOT_MEASURED",
           "guard_latched_at_oracle":motion.get("guard_latched") if type(motion.get("guard_latched")) is bool else None,
           "goal_cancel_ack":motion.get("goal_cancel_ack") if type(motion.get("goal_cancel_ack")) is bool else None,
           "odom_zero_dwell_sec":_num(motion.get("odom_stopped_dwell_sec")),
           "first_timing_channel":boundary["first_global_channel"],
           "supervisor_fsm_first_change":"NOT_MEASURED","formal_safety_accepted":False}
    keys=("navigation_ack","localization_ack","cm_exit_code","gazebo_exit_code",
          "collision_monitor_exit_code","gazebo_server_exit_code")
    codes={key:shutdown[key] for key in keys
           if key in shutdown and type(shutdown[key]) in (int,bool)}
    native={"status":"RAW_NUMERIC_SCOPED" if codes else "NOT_VERIFIED",
            "actual_exit_codes_or_ack_if_present":codes,
            "native_full_lifecycle_ack_proven":False,
            "native_actual_gazebo_exit0_proven":False}
    scope={"status":"HOLD_RAW_WSL2_REVIEW_PENDING",
           "source_sha":student_sha if isinstance(student_sha,str) and
               len(student_sha)==40 and all(c in "0123456789abcdef" for c in student_sha) else None,
           "historical_public_strict_l2_run":l2_run if type(l2_run) is int else None,
           "wsl2_performance_preflight":prestatus,
           "owner_wsl2_l3":"NOT_ACCEPTED",
           "first_scan_root_cause":"UNDETERMINED",
           "certified_estop":False,"main_merged":False}
    return dict(zip(NAMES,(boundary,rtf,pipeline,state,native,scope)))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--student-sha",required=True)
    p.add_argument("--l2-run",type=int,required=True)
    a=p.parse_args()
    records=build_compact_records(a.root,a.student_sha,a.l2_run)
    for name,record in records.items():
        data=json.dumps(record,sort_keys=True,indent=2,allow_nan=False)+"\n"
        if len(data.encode())>8192:raise ValueError("DIAGNOSTIC_RECORD_TOO_LARGE")
        (a.root/name).write_text(data,encoding="utf-8")
    print("AXIA_G07_SCAN_COMPACT_SIX_RECORDS_WRITTEN_HOLD_NOT_CERTIFIED",flush=True)
    return 0

if __name__=="__main__":raise SystemExit(main())
