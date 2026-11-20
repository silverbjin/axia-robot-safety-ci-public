#!/usr/bin/env python3
"""Read-only #163 Nav2 shutdown service first server boundary from SAME L2.

Lack of logs is not proof the callback was absent. A service advertisement or
/is_active reply is not a ManageLifecycleNodes SHUTDOWN ACK. Raw launch.log,
server timestamps, ROS messages and Goal UUID are never published by this.
"""
import argparse
import json
from pathlib import Path

def classify(shutdown, launch_log):
    out={"schema":"axia.g07.nav_shutdown_first_server_boundary.v1",
         "status":"NAVIGATION_FIRST_SERVER_BOUNDARY_UNVERIFIED_HOLD",
         "navigation_ack":False,"client_request_sent":False,
         "server_entry_log_observed":False,"server_finish_log_observed":False,
         "server_entry_proven":False,
         "response_transport_root_proven":False,
         "root_cause_proven":False,"release":"HOLD","certified_estop":False}
    if not isinstance(shutdown,dict) or not isinstance(launch_log,str):
        return out
    ack=shutdown.get("navigation_ack") is True and (
        shutdown.get("navigation_service_status")=="ACK")
    out["navigation_ack"]=ack
    out["client_request_sent"]=shutdown.get("navigation_service_request_sent") is True
    t=shutdown.get("navigation_response_elapsed_sec")
    out["client_response_elapsed_sec"]=round(t,6) if type(t) in (int,float) and 0<=t<=120 else None
    probe=shutdown.get("navigation_manage_group_probe",{})
    out["same_callback_group_is_active_responsive"]=(isinstance(probe,dict)
            and probe.get("status")=="MANAGE_CALLBACK_GROUP_RESPONSIVE")
    # Official Jazzy node logger + exact manager name, not arbitrary
    # localization logs, SIGINT preshutdown or a truncated unrelated entry.
    lines=[line for line in launch_log.splitlines()
           if "lifecycle_manager_navigation" in line]
    start=any("Shutting down managed nodes..." in line for line in lines)
    finish=any("Managed nodes have been shut down" in line for line in lines)
    out["server_entry_log_observed"]=start
    out["server_finish_log_observed"]=finish
    if ack:
        out["status"]="NAVIGATION_ACK_REPORTED"
    elif (out["client_request_sent"] and
          shutdown.get("navigation_service_status")=="SERVICE_TIMEOUT"):
        if finish and start:
            out["status"]="SERVER_FINISHED_CLIENT_ACK_MISSING_CANDIDATE_HOLD"
        elif start:
            out["status"]="SERVER_ENTERED_FINISH_NOT_LOGGED_HOLD"
        else:
            out["status"]="CLIENT_TIMEOUT_SERVER_CALLBACK_NOT_OBSERVED_IN_LOG_HOLD"
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--shutdown",type=Path,required=True)
    p.add_argument("--launch-log",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    try:
        if (args.shutdown.stat().st_size>262144 or
                args.launch_log.stat().st_size>50_000_000):
            raise ValueError("RAW_INPUT_TOO_LARGE")
        shutdown=json.loads(args.shutdown.read_text())
        launch=args.launch_log.read_text(errors="replace")
    except (OSError,ValueError):
        shutdown={};launch=""
    out=classify(shutdown,launch)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print("AXIA_G07_NAV_SHUTDOWN_FIRST_SERVER_BOUNDARY "+json.dumps(out,sort_keys=True),flush=True)
    return 0  # Diagnostic never grants robot acceptance.

if __name__=="__main__":
    raise SystemExit(main())
