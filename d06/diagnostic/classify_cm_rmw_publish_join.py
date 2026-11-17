"""Public numeric-only diagnostic: exact FastDDS source timestamp to native publish.

Jazzy rmw_fastrtps_shared_cpp calls Time_t::now(), emits the rmw_publish
tracepoint with stamp.to_ns(), and write_w_timestamp() uses the SAME stamp.
Never infer this link from host clock anchors alone. Every actual event must
be linked by identical publisher handle + timestamp + CM callback PID/TID.
No raw pointers, ROS message contents or native epoch leaves this module.
"""
from __future__ import annotations
from d06.live.g07_cycle05_cm_callback_window import _first_pair, _anchor
from d06.live.g07_cycle31_cm_topic_callback_identity import resolve_cm_cmdvel_handles

CM_PROC=("collision_monitor","collision_monit")
OUT_TOPIC="/cmd_vel_pre_guard"
IN_TOPIC="/cmd_vel_supervised"
MAX_CLOCK_ERROR_NS=5_000_000


def _hold(reason, **public):
    return dict(
        schema="axia.g07.task01.exact_native_rmw_publisher_tf_v1",
        status=reason,
        rmw_publisher_source_timestamp_pair_exact=False,
        same_cm_input_callback_tf_publisher=False,
        publisher_source_causality_proven=False,
        source_clock_epoch_calibrated=False,
        scheduler_runqueue_wait_proven=False,
        cm120_release_pass=False,
        owner_wsl2_accepted=False,
        certified_estop=False, **public)


def classify_publish_join(observer, trace, anchors, tf_calls):
    pair=_first_pair(observer)
    if pair is None:
        return _hold("FIRST_SOURCE_120MS_GAP_NOT_REPRODUCED_HOLD")
    if not isinstance(trace,list) or len(trace)>150000:
        return _hold("NATIVE_PUBLISH_TRACE_UNBOUNDED_HOLD")
    if not isinstance(tf_calls,dict) or not isinstance(tf_calls.get("spans"),list):
        return _hold("NATIVE_TF_CALL_SPANS_MISSING_HOLD")
    a,b,_=pair
    pids={x.get("vpid") for x in trace if isinstance(x,dict)
          and x.get("name")=="ros2:rcl_subscription_init"
          and x.get("topic_name")==IN_TOPIC
          and x.get("procname") in CM_PROC
          and type(x.get("vpid")) is int}
    if len(pids)!=1:
        return _hold("NATIVE_CM_INPUT_OWNER_MISSING_HOLD")
    pid=next(iter(pids))
    try:
        handles,meta=resolve_cm_cmdvel_handles(trace,cm_pid=pid)
    except (KeyError,TypeError,ValueError):
        return _hold("NATIVE_CM_INPUT_CALLBACK_LINK_INVALID_HOLD")
    if len(handles)!=1 or meta.get("topic_matched_subscriptions")!=1:
        return _hold("NATIVE_CM_INPUT_CALLBACK_LINK_MISSING_HOLD")
    callback_handle=next(iter(handles))
    publishers={str(e.get("rmw_publisher_handle")) for e in trace
                if isinstance(e,dict)
                and e.get("name")=="ros2:rcl_publisher_init"
                and e.get("vpid")==pid
                and e.get("procname") in CM_PROC
                and e.get("topic_name")==OUT_TOPIC
                and e.get("rmw_publisher_handle") is not None}
    if len(publishers)!=1:
        return _hold("NATIVE_CM_PRE_GUARD_PUBLISHER_NOT_UNIQUE_HOLD")
    publisher_handle=next(iter(publishers))
    expected=(a["rmw_source_ns"],b["rmw_source_ns"])
    if not all(type(x) is int and x>0 for x in expected):
        return _hold("NATIVE_RMW_SOURCE_STAMP_INVALID_HOLD")
    relevant=[e for e in trace if isinstance(e,dict)
              and e.get("name")=="ros2:rmw_publish"
              and e.get("vpid")==pid and e.get("procname") in CM_PROC
              and str(e.get("rmw_publisher_handle"))==publisher_handle
              and e.get("timestamp") in expected]
    if len(relevant)!=2 or {e.get("timestamp") for e in relevant}!=set(expected):
        return _hold("NATIVE_RMW_SOURCE_STAMP_NOT_EXACT_HOLD")
    relevant.sort(key=lambda e:e["timestamp"])
    for e in relevant:
        if (type(e.get("timestamp_ns")) is not int or
                type(e.get("vtid")) is not int):
            return _hold("NATIVE_RMW_PUBLISH_CLOCK_FIELDS_MISSING_HOLD")
    cbs=[e for e in trace if isinstance(e,dict)
         and e.get("name") in ("ros2:callback_start","ros2:callback_end")
         and e.get("vpid")==pid and e.get("procname") in CM_PROC
         and str(e.get("callback"))==callback_handle]
    # Sanitized native TF spans have no TID. If more than one official
    # cmd_vel callback worker exists, temporal overlap alone cannot prove
    # the TF invocation belongs to the source-publishing worker.
    tids={e.get("vtid") for e in cbs if type(e.get("vtid")) is int}
    if len(tids)!=1:
        return _hold("NATIVE_CM_TF_THREAD_OWNERSHIP_AMBIGUOUS_HOLD")
    offset=_anchor(cbs,anchors)
    if offset is None:
        return _hold("NATIVE_PUBLISH_CTF_CLOCK_DOMAIN_UNVERIFIED_HOLD")
    if not isinstance(anchors,dict):
        return _hold("NATIVE_PUBLISH_HOST_CLOCK_ANCHOR_INVALID_HOLD")
    start=anchors.get("start",{})
    if not isinstance(start,dict):
        return _hold("NATIVE_PUBLISH_HOST_CLOCK_ANCHOR_INVALID_HOLD")
    wall=start.get("wall_ns")
    mono=start.get("mono_ns")
    if type(wall) is not int or type(mono) is not int:
        return _hold("NATIVE_PUBLISH_HOST_CLOCK_ANCHOR_INVALID_HOLD")
    native_ns=[e["timestamp_ns"]-offset for e in relevant]
    if native_ns[0]>=native_ns[1]:
        return _hold("NATIVE_RMW_PUBLISH_MONO_ORDER_INVALID_HOLD")
    err=[abs((e["timestamp"]-wall)-(t-mono))
         for e,t in zip(relevant,native_ns)]
    if any(x>MAX_CLOCK_ERROR_NS for x in err):
        return _hold("NATIVE_RMW_SOURCE_TO_HOST_CLOCK_CALIBRATION_HOLD")
    source_ns=expected[1]-expected[0]
    native_gap_ns=native_ns[1]-native_ns[0]
    if abs(native_gap_ns-source_ns)>MAX_CLOCK_ERROR_NS:
        return _hold("NATIVE_RMW_SOURCE_TO_MONO_INTERVAL_MISMATCH_HOLD")
    # Only exact CM input callbacks, not other nested subscriptions. Pair
    # each RMW publish with a unique complete callback in its native thread.
    complete=[]
    active={}
    for e in sorted(cbs,key=lambda row:row.get("timestamp_ns",0)):
        tid=e.get("vtid")
        t=e.get("timestamp_ns")
        if type(tid) is not int or type(t) is not int:
            return _hold("NATIVE_CM_CALLBACK_FIELDS_INVALID_HOLD")
        if e["name"]=="ros2:callback_start":
            if tid in active:
                return _hold("NATIVE_CM_CALLBACK_NESTED_UNVERIFIED_HOLD")
            active[tid]=t-offset
        elif tid in active:
            first=active.pop(tid)
            if t-offset>=first:
                complete.append((tid,first,t-offset))
    owners=[]
    for e,t in zip(relevant,native_ns):
        candidates=[c for c in complete
                    if c[0]==e["vtid"] and c[1]<=t<=c[2]]
        if len(candidates)!=1:
            return _hold("NATIVE_RMW_PUBLISH_OUTSIDE_CM_CMD_CALLBACK_HOLD")
        owners.append(candidates[0])
    tf_start_reference=round(a["t"]*1e9)
    tf_candidates=[]
    for item in tf_calls["spans"]:
        if not isinstance(item,dict) or item.get("coverage_complete") is not True:
            continue
        begin=item.get("start_rel_observer_ns")
        end=item.get("end_rel_observer_ns")
        request=item.get("sleep_request_ns")
        if not all(type(x) is int for x in (begin,end,request)):
            continue
        if (begin<end and request>=90_000_000 and
                native_ns[0]<tf_start_reference+begin and
                tf_start_reference+end<=native_ns[1] and
                owners[1][1]<=tf_start_reference+begin
                and tf_start_reference+end<=owners[1][2]):
            tf_candidates.append((begin,end,request))
    if len(tf_candidates)!=1:
        return _hold("NATIVE_TF_POLLING_OUTSIDE_SECOND_CM_PUBLISH_CALLBACK_HOLD")
    begin,end,request=tf_candidates[0]
    # This establishes a scoped causal budget of the FIRST consecutive
    # publisher gap, not the global kernel runnable wait or safety release.
    return dict(_hold("CM_SOURCE_TF_POLLING_NATIVE_PUBLISH_JOIN_PROVEN_SCOPED"),
        rmw_publisher_source_timestamp_pair_exact=True,
        same_cm_input_callback_tf_publisher=True,
        publisher_source_causality_proven=True,
        source_clock_epoch_calibrated=True,
        first_rmw_source_gap_ns=source_ns,
        first_native_rmw_publish_gap_ns=native_gap_ns,
        max_native_source_clock_error_ns=max(err),
        first_publisher_native_to_second_same_tf_sleep_ns=request,
        sleep_requests_within_native_publisher_gap_ns=request,
        tf_original_call_wall_ns=end-begin,
        tf_native_seconds_after_first_publish_ns=(
            tf_start_reference+begin-native_ns[0]),
        second_native_publish_after_tf_end_ns=(
            native_ns[1]-(tf_start_reference+end)),
        scoped_publisher_gap_sleep_request_fraction=round(request/source_ns,6),
        original_nav2_modified=False)
