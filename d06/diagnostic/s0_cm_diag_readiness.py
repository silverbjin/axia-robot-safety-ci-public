"""Only CM C++ cmd callback trace rows, not all CM callbacks.

S0 diagnostic pregoal: no ROS, no Goal authorization, no release acceptance.
Meta linkage is the existing Cycle31 RCL topic -> C++ subscription -> callback.
"""
from __future__ import annotations
import os
from d06.live.g07_cycle31_cm_topic_callback_identity import resolve_cm_cmdvel_handles

TOPIC="/cmd_vel_supervised"
CM_PROCS={"collision_monit","collision_monitor"}
META={"ros2:rcl_subscription_init","ros2:rclcpp_subscription_init",
      "ros2:rclcpp_subscription_callback_added"}
CB={"ros2:callback_start","ros2:callback_end"}

def _result(status,rows,seen,target,meta_count):
    return dict(status=status,rows=rows,
                stats=dict(raw_examined=seen,accepted_cm_callback_count=target,
                           cm_metadata_count=meta_count),
                goal_authorized=False,release_pass=False,tf_wait_proven=False)

def select_exact_cm_callbacks(events,*,max_raw_events=3_000_000,
                              max_target_events=12_000,max_metadata=800):
    """Bound memory by exact callback handle, never raise the old 100k cap.

    Source iteration can be huge; only relevant metadata and exact callback
    start/end go into memory. Two CM processes / ambiguous links fail closed.
    """
    meta=[]
    selected=[]
    owner=None
    handles=set()
    seen=0
    hit=0
    for event in events:
        seen+=1
        if seen>max_raw_events:
            return _result("TRACE_RAW_VOLUME_UNBOUNDED_HOLD",meta+selected,
                           seen,hit,len(meta))
        if not isinstance(event,dict):
            return _result("TRACE_EVENT_INVALID_HOLD",meta+selected,
                           seen,hit,len(meta))
        name=event.get("name")
        pid=event.get("vpid")
        proc=event.get("procname")
        if name in META and proc in CM_PROCS and type(pid) is int:
            if name=="ros2:rcl_subscription_init" and event.get("topic_name")==TOPIC:
                if owner is not None and owner!=pid:
                    return _result("MULTIPLE_CM_INPUT_OWNERS_HOLD",meta+selected,
                                   seen,hit,len(meta))
                owner=pid
            # At this point metadata for other C++ CM subscriptions is needed
            # to build a complete unambiguous link for the owned CM process.
            meta.append(event)
            if len(meta)>max_metadata:
                return _result("CM_METADATA_UNBOUNDED_HOLD",meta+selected,
                               seen,hit,len(meta))
            if owner is not None:
                try:
                    h,info=resolve_cm_cmdvel_handles(meta,cm_pid=owner)
                except ValueError:
                    return _result("CM_CALLBACK_IDENTITY_INVALID_HOLD",
                                   meta+selected,seen,hit,len(meta))
                if len(h)==1 and info.get("topic_matched_subscriptions")==1:
                    handles=h
        elif (name in CB and type(pid) is int and pid==owner and
              proc in CM_PROCS and str(event.get("callback")) in handles):
            selected.append(event)
            hit+=1
            if hit>max_target_events:
                return _result("TARGET_CM_CALLBACK_TRACE_UNBOUNDED_HOLD",
                               meta+selected,seen,hit,len(meta))
    if owner is None or len(handles)!=1:
        return _result("CM_INPUT_CALLBACK_IDENTITY_UNVERIFIED_HOLD",
                       meta+selected,seen,hit,len(meta))
    if hit<2:
        return _result("CM_INPUT_CALLBACK_START_END_UNVERIFIED_HOLD",
                       meta+selected,seen,hit,len(meta))
    return _result("EXACT_CM_CALLBACK_FILTER_READY",
                   meta+selected,seen,hit,len(meta))

def check_cm_loaded(comm,maps,expected_so):
    """Only verifies the actual CM's ELF mapping. NOT a real TF call.

    Caller reads /proc/PID/comm and /proc/PID/maps from *the running*
    original official CM process. No environment value alone can prove load.
    """
    reason="CM_SHIM_MAPPING_UNVERIFIED_NO_GOAL"
    if (isinstance(comm,str) and isinstance(maps,str) and
        isinstance(expected_so,str) and expected_so.startswith("/") and
        comm.strip() in CM_PROCS and
        any(row.split()[-1]==expected_so for row in maps.splitlines()
            if len(row.split())>=6)):
        reason="CM_SHIM_MAPPED_NO_GOAL"
    return dict(status=reason,tf_call_observed=False,goal_authorized=False,
                original_nav2_modified=False,release_pass=False,
                certified_estop=False)
