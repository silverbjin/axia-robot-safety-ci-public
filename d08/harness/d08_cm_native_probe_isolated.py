#!/usr/bin/env python3
"""D08 diagnostic-only official CM GetState/GetParameters in a SEPARATE OS process.

No CM configuration, TTL, Planner, robot cmd_vel, Goal or sensor publishing.
Do not use this probe to certify CM internal 120ms / Guard 150ms.
ROS imports are deliberately inside run() so unit contracts are ROS-free.
"""
from __future__ import annotations
import argparse
import json
import math
import statistics
import time


PREFIX="D08_CM_NATIVE_ISOLATED_RESULT="
MODES=("in_process","isolated_process")
PASS="D08_REAL_THREE_OFFICIAL_NAV2_PATH_PHASES_L2_PASS_NO_GOAL"


def mode_for_cycle(index:int,enabled:bool=False)->str:
    if not isinstance(index,int) or index<0:
        raise ValueError("D08_CM_AB_INVALID_CYCLE_INDEX")
    return MODES[index%2] if enabled else "in_process"


def parse_isolated_probe_output(output:str)->dict:
    lines=[line.split(PREFIX,1)[1] for line in output.splitlines()
           if line.startswith(PREFIX)]
    if len(lines)!=1:
        raise ValueError("D08_CM_ISOLATED_RESULT_MISSING_OR_DUPLICATED")
    try:
        data=json.loads(lines[0])
    except (json.JSONDecodeError,TypeError) as exc:
        raise ValueError("D08_CM_ISOLATED_RESULT_INVALID_JSON") from exc
    if not isinstance(data,dict):
        raise ValueError("D08_CM_ISOLATED_RESULT_NOT_OBJECT")
    if (data.get("status")!="D08_CM_NATIVE_ACTIVE_SCAN_PASS"
        or data.get("official_cm_active_scan_configured") is not True
        or data.get("cm_native_lifecycle_state")!="active"
        or data.get("cm_actual_configured_scan_topic") not in ("scan","/scan")
        or "scan" not in (data.get("cm_native_observation_sources") or [])
        or data.get("cm_internal_receive_gap_verified") is not False
        or data.get("cm_action_state_verified") is not False):
        raise ValueError("D08_CM_ISOLATED_NATIVE_REAL_ACTIVE_SCAN_NOT_PROVEN")
    return data


def summarize_cm_ab(cycles:list[dict])->dict:
    if len(cycles)!=8:
        raise ValueError("D08_CM_AB_EIGHT_REAL_CYCLES_REQUIRED")
    rows=[]
    for index,cycle in enumerate(cycles):
        expected=mode_for_cycle(index,enabled=True)
        if (cycle.get("status")!=PASS
            or cycle.get("cm_service_probe_mode")!=expected
            or cycle.get("official_cm_active_scan_configured") is not True
            or cycle.get("cm_native_lifecycle_state")!="active"
            or cycle.get("cm_actual_configured_scan_topic") not in ("scan","/scan")
            or cycle.get("first_scan_timing_boundary") is not None):
            raise ValueError("D08_CM_AB_ACTIVE_SCAN_OR_PHASE_NOT_PROVEN")
        pair=cycle.get("worst_scan_pair_source_stamps") or {}
        try:
            gap=float(pair["receive_gap_sec"])
        except (KeyError,TypeError,ValueError) as exc:
            raise ValueError("D08_CM_AB_EXACT_SCAN_GAP_MISSING") from exc
        if not math.isfinite(gap) or gap<0 or gap>.5:
            raise ValueError("D08_CM_AB_FIRST_REAL_SCAN_GAP_OVER_500MS")
        spans=cycle.get("read_only_operation_spans",[])
        query=[float(s["end_sec"])-float(s["start_sec"])
               for s in spans if s.get("name")=="cm_native_service_probe"]
        rows.append({"cycle":index,"mode":expected,
                     "source_matched_scan_gap_sec":gap,
                     "real_cm_query_elapsed_sec":round(query[0],6)
                     if query else None,
                     "cm_internal_120ms_verified":False,
                     "guard_150ms_verified":False})
    results={}
    for mode in MODES:
        subset=[r for r in rows if r["mode"]==mode]
        values=[r["source_matched_scan_gap_sec"] for r in subset]
        results[mode]={"cycles":len(subset),
                       "observed_max_same_scan_gap_sec":round(max(values),6),
                       "observed_median_same_scan_gap_sec":
                           round(statistics.median(values),6),
                       "proof_not_of_long_term_reliability":True}
    return {"status":"D08_CM_SERVICE_AB_OBSERVED_L2_PASS_NOT_ROOT_CAUSE",
            "cycles_per_mode":{key:4 for key in MODES},
            "modes":results,"cycles":rows,
            "root_cause":"UNDETERMINED",
            "no_goal_only":True,
            "cm_internal_120ms_verified":False,
            "guard_150ms_verified":False,
            "owner_wsl2_accepted":False,
            "certified_estop":False}


def _wait_for_reply(node,future,timeout_s:float,code:str):
    import rclpy
    end=time.monotonic()+timeout_s
    while time.monotonic()<end and rclpy.ok():
        if future.done():
            return future.result()
        rclpy.spin_once(node,timeout_sec=.05)
    raise RuntimeError("D08_CM_ISOLATED_"+code+"_TIMEOUT")


def run()->dict:
    import rclpy
    from rclpy.node import Node
    from lifecycle_msgs.srv import GetState
    from rcl_interfaces.srv import GetParameters
    from d08_same_world_replan import (
        cm_state_is_active,assess_official_cm_native_scan)

    rclpy.init()
    node=Node("axia_d08_cm_isolated_service_query_no_goal")
    try:
        state_cli=node.create_client(GetState,"/collision_monitor/get_state")
        param_cli=node.create_client(
            GetParameters,"/collision_monitor/get_parameters")
        started=time.monotonic()
        if not state_cli.wait_for_service(timeout_sec=8):
            raise RuntimeError("D08_CM_ISOLATED_GET_STATE_ABSENT")
        state_wait=time.monotonic()-started
        started=time.monotonic()
        if not param_cli.wait_for_service(timeout_sec=8):
            raise RuntimeError("D08_CM_ISOLATED_GET_PARAMETERS_ABSENT")
        params_wait=time.monotonic()-started
        deadline=time.monotonic()+12.
        states=[]
        observed=None
        while time.monotonic()<deadline:
            r=state_cli.call_async(GetState.Request())
            observed=_wait_for_reply(node,r,4,"GET_STATE_REPLY")
            if observed is None:
                raise RuntimeError("D08_CM_ISOLATED_EMPTY_STATE")
            entry=(int(observed.current_state.id),
                   str(observed.current_state.label))
            states.append(list(entry))
            if cm_state_is_active(*entry):
                break
            time.sleep(.2)
        if observed is None or not cm_state_is_active(
                int(observed.current_state.id),
                str(observed.current_state.label)):
            raise RuntimeError("D08_CM_ISOLATED_NOT_ACTIVE:"+str(states[-5:]))
        request=GetParameters.Request()
        request.names=["observation_sources","scan.topic"]
        result=_wait_for_reply(
            node,param_cli.call_async(request),8,"GET_PARAMETERS_REPLY")
        if result is None or len(result.values)!=2:
            raise RuntimeError("D08_CM_ISOLATED_EMPTY_PARAMS")
        sources=list(result.values[0].string_array_value)
        topic=str(result.values[1].string_value)
        witness=assess_official_cm_native_scan(
            int(observed.current_state.id),
            str(observed.current_state.label),sources,topic)
        witness.update({
            "status":"D08_CM_NATIVE_ACTIVE_SCAN_PASS",
            "cm_native_state_observed_transitions":states,
            "cm_native_state_service":"/collision_monitor/get_state",
            "cm_native_param_service":"/collision_monitor/get_parameters",
            "cm_native_observation_sources":sources,
            "cm_native_verified_at_monotonic_s":round(time.monotonic(),6),
            "cm_state_service_discovery_sec":round(state_wait,6),
            "cm_parameter_service_discovery_sec":round(params_wait,6),
            "cm_internal_receive_gap_verified":False,
            "cm_action_state_verified":False,
            "cm_service_probe_mode":"isolated_process",
            "no_cm_command_or_parameter_change":True,
            "root_cause":"UNDETERMINED",
        })
        return witness
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--once",action="store_true",required=True)
    parser.parse_args()
    try:
        report=run()
        print(PREFIX+json.dumps(report,sort_keys=True),flush=True)
    except Exception as exc:
        import sys
        print("D08_CM_ISOLATED_NATIVE_FIRST_FAILURE "+
              type(exc).__name__+":"+str(exc)[:200],file=sys.stderr,flush=True)
        raise SystemExit(2)
