"""First ROS receive gap from real LaserScan callbacks; no synthetic scan."""
from __future__ import annotations

def first_scan_receive_gap(samples, limit_s=0.5):
    """samples: [(host_monotonic_receive_sec, ROS_sim_header_stamp_ns)].

    Header delta records SIM time, not actual Gazebo RMW send or ROS receiver
    transport; requires separate publisher observation for source attribution.
    """
    for i,(before,after) in enumerate(zip(samples,samples[1:]),start=1):
        wall=float(after[0])-float(before[0])
        sim=(int(after[1])-int(before[1]))/1e9
        if wall>=limit_s:
            return {
                "kind":"ROS_LASERSCAN_FIRST_RECEIVE_GAP",
                "sample_index":i,
                "receive_gap_sec":round(wall,6),
                "header_sim_gap_sec":round(sim,6),
                "previous_ros_stamp_ns":int(before[1]),
                "current_ros_stamp_ns":int(after[1]),
                "previous_host_monotonic_sec":round(float(before[0]),6),
                "current_host_monotonic_sec":round(float(after[0]),6),
                "limit_sec":limit_s,
                "publisher_rmw_gap_measured":False,
                "clock_receive_gap_measured":False,
                "not_proven_source_vs_transport":True,
            }
    return None


def _bracketed_host_gaps(host_times, start, end):
    """Measure one host-monotonic window, never compare to ROS sim stamps.

    Evidence is insufficient if readings do not span BOTH ends of the
    original Observer violation. This returns NO guessed source cadence.
    """
    import math
    try:
        readings = sorted(float(t) for t in host_times)
    except (TypeError, ValueError):
        return {"window_bracketed": False, "max_gap_sec": None, "count": 0}
    if any(not math.isfinite(t) for t in readings):
        return {"window_bracketed": False, "max_gap_sec": None,
                "count": len(readings)}
    before = [t for t in readings if t <= start]
    after = [t for t in readings if t >= end]
    if not before or not after:
        return {"window_bracketed": False, "max_gap_sec": None,
                "count": len(readings)}
    left, right = before[-1], after[0]
    window = [t for t in readings if left <= t <= right]
    if len(window) < 2:
        return {"window_bracketed": False, "max_gap_sec": None,
                "count": len(readings)}
    return {"window_bracketed": True,
            "max_gap_sec": round(max(b-a for a,b in zip(window, window[1:])),6),
            "count": len(readings)}


def diagnose_first_receive_boundary(first_boundary, independent,
                                    observer_first_callback=None):
    """Conservative candidate at first >500ms Scan callback gap.

    The independent ROS subscriber can distinguish *relative* observer
    starvation, but cannot prove native Gazebo publisher or RMW/bridge timing.
    No later recovery may replace the already-recorded first violation.
    """
    import math
    independent = independent or {}
    boundary = first_boundary if isinstance(first_boundary,dict) else {}
    start = boundary.get("previous_host_monotonic_sec")
    end = boundary.get("current_host_monotonic_sec")
    gap = boundary.get("receive_gap_sec")
    if not all(isinstance(v,(int,float)) and math.isfinite(v)
               for v in (start,end,gap)) or end <= start:
        return {"cause":"UNDETERMINED","candidate":"MISSING_FIRST_BOUNDARY",
                "first_scan_violation_retained":False,
                "publisher_rmw_gap_measured":False,
                "sim_native_gap_measured":False,
                "native_source_gap_not_measured":True,
                "independent_scan_window_bracketed":False}
    traces = {}
    for topic in ("scan","clock","odom","tf"):
        traces[topic] = _bracketed_host_gaps(independent.get(topic, []),
                                            float(start),float(end))
    scan = traces["scan"]
    candidate = "INSUFFICIENT_INDEPENDENT_SAMPLES"
    if scan["window_bracketed"]:
        if scan["max_gap_sec"] > .5:
            candidate = "SHARED_ROS_RECEIVE_DELAY"
        else:
            candidate = "OBSERVER_DISPATCH_OR_QOS"
            callback = observer_first_callback or {}
            try:
                entry_gap = (float(callback["current_entry_sec"])
                             - float(callback["previous_entry_sec"]))
                if 0 <= entry_gap <= .5 and float(gap) > .5:
                    candidate = "OBSERVER_PROCESSING_OR_LOCK"
            except (ValueError, TypeError, KeyError):
                pass
    # Direct native Gazebo / bridge send / DDS RMW cadence is NOT measured
    # by a ROS topic observer, even with real topic header stamps.
    return {
        "cause":"UNDETERMINED",
        "candidate":candidate,
        "first_scan_violation_retained":float(gap) > .5,
        "first_boundary":dict(boundary),
        "independent_scan_window_bracketed":scan["window_bracketed"],
        "independent_scan_max_gap_sec":scan["max_gap_sec"],
        "independent_ros_topic_gaps":traces,
        "clock_receive_gap_measured":traces["clock"]["window_bracketed"],
        "publisher_rmw_gap_measured":False,
        "sim_native_gap_measured":False,
        "native_source_gap_not_measured":True,
        "observer_entry_gap_measured":bool(observer_first_callback),
    }


def compare_native_scan_first_gap(first_boundary, native_events):
    """First ROS /scan gap, native Gazebo Transport *receive* comparison.

    The stamps must match EXACTLY. Transport receive is not Gazebo sensor
    publication, nor ros_gz_bridge/RMW send. Candidate only, never cause PASS.
    All host monotonic clocks are from the same Linux OS instance.
    """
    verdict = {
        "cause": "UNDETERMINED",
        "candidate": "NO_ROS_FIRST_GAP",
        "native_pair_matched": False,
        "native_receive_gap_sec": None,
        "publisher_send_timing_proven": False,
        "bridge_dds_send_measured": False,
        "first_scan_violation_retained": False,
        "native_transport_receive_measured": False,
    }
    b = first_boundary if isinstance(first_boundary, dict) else {}
    try:
        ros_gap = float(b["receive_gap_sec"])
        before_ns = int(b["previous_ros_stamp_ns"])
        after_ns = int(b["current_ros_stamp_ns"])
        old_ros = float(b["previous_host_monotonic_sec"])
        new_ros = float(b["current_host_monotonic_sec"])
    except (KeyError, TypeError, ValueError, OverflowError):
        return verdict
    if ros_gap <= .5 or after_ns <= before_ns or new_ros <= old_ros:
        return verdict
    verdict["first_scan_violation_retained"] = True
    verdict["candidate"] = "NATIVE_SOURCE_STAMP_PAIR_UNAVAILABLE"

    def match(stamp_ns):
        # The actual bridge should preserve LaserScan header source timestamps.
        # If it does not, neither the cadence nor the causal layer is proven.
        if not isinstance(native_events, (list, tuple)):
            return None
        for event in native_events:
            if not isinstance(event, dict):
                continue
            try:
                source = int(event["source_stamp_ns"])
                host = float(event["host_monotonic_sec"])
            except (KeyError, TypeError, ValueError, OverflowError):
                continue
            if source == stamp_ns and host == host and abs(host) < 1e12:
                return host
        return None

    old_native, new_native = match(before_ns), match(after_ns)
    if old_native is None or new_native is None or new_native <= old_native:
        return verdict
    # Independent native transport callbacks can lag the bridge (different
    # subscriber queue/thread). Never infer causation from inverted ordering.
    if old_native > old_ros + .05 or new_native > new_ros + .05:
        verdict["candidate"] = "NATIVE_CLOCK_ORDER_NOT_VERIFIED"
        return verdict
    gap = round(new_native - old_native, 6)
    verdict.update({
        "native_pair_matched": True,
        "native_transport_receive_measured": True,
        "native_receive_gap_sec": gap,
        "native_to_ros_old_sec": round(old_ros - old_native, 6),
        "native_to_ros_new_sec": round(new_ros - new_native, 6),
        "candidate": ("AT_OR_BEFORE_NATIVE_TRANSPORT_RX"
                      if gap > .5 else "AFTER_NATIVE_TRANSPORT_RX"),
    })
    return verdict


def diagnose_native_clock_during_first_gap(first_boundary, native_scan, native_clock):
    """Classify a *live observed* first ROS gap using SAME-host native clock.

    A Gazebo Transport /clock callback is not Gazebo's internal sensor send
    timestamp; resource root cause is always undetermined. Timestamp pairs
    must be found in original native scan; never synthesize missing samples.
    """
    base=compare_native_scan_first_gap(first_boundary, native_scan)
    result={
        "timing_layer":"NO_REAL_FIRST_ROS_GAP",
        "root_resource_cause":"UNDETERMINED",
        "first_scan_violation_retained":base["first_scan_violation_retained"],
        "native_pair_matched":base["native_pair_matched"],
        "native_receive_gap_sec":base["native_receive_gap_sec"],
        "clock_window_bracketed":False,
        "clock_callback_gap_max_sec":None,
        "clock_sim_progress_sec":None,
        "clock_host_span_sec":None,
        "effective_rtf":None,
        "gz_internal_publisher_send_measured":False,
        "bridge_dds_send_measured":False,
    }
    if not base["first_scan_violation_retained"]:
        return result
    if not base["native_pair_matched"]:
        result["timing_layer"]="INSUFFICIENT_NATIVE_SCAN_PAIR"
        return result
    if base["native_receive_gap_sec"] <= .5:
        result["timing_layer"]="AFTER_NATIVE_TRANSPORT_RX"
        return result

    try:
        first_stamp=int(first_boundary["previous_ros_stamp_ns"])
        last_stamp=int(first_boundary["current_ros_stamp_ns"])
    except (KeyError,ValueError,TypeError,OverflowError):
        result["timing_layer"]="INSUFFICIENT_NATIVE_CLOCK"
        return result
    events=[x for x in native_scan if (
        isinstance(x,dict) and
        x.get("source_stamp_ns") in (first_stamp,last_stamp) and
        isinstance(x.get("host_monotonic_sec"),(int,float)))]
    try:
        native_start=next(float(x["host_monotonic_sec"])
                         for x in events if x["source_stamp_ns"]==first_stamp)
        native_end=next(float(x["host_monotonic_sec"])
                       for x in events if x["source_stamp_ns"]==last_stamp)
    except (ValueError,StopIteration,TypeError):
        result["timing_layer"]="INSUFFICIENT_NATIVE_CLOCK"
        return result

    result["timing_layer"]="INSUFFICIENT_NATIVE_CLOCK"
    if not isinstance(native_clock,(list,tuple)) or len(native_clock)<3:
        return result
    import math
    samples=[]
    for item in native_clock:
        if not isinstance(item,dict):
            continue
        try:
            host=float(item["host_monotonic_sec"])
            sim_ns=int(item["sim_stamp_ns"])
        except (ValueError,KeyError,TypeError,OverflowError):
            continue
        if math.isfinite(host) and sim_ns>=0 and native_start-.1 <= host <= native_end+.1:
            samples.append((host,sim_ns))
    samples.sort()
    if len(samples)<3:
        return result
    before=min(samples,key=lambda p:abs(p[0]-native_start))
    after=min(samples,key=lambda p:abs(p[0]-native_end))
    if (abs(before[0]-native_start)>.08 or
        abs(after[0]-native_end)>.08 or
        after[0]-before[0]<.25):
        return result
    window=[p for p in samples if before[0] <= p[0] <= after[0]]
    if len(window)<3:
        return result
    gaps=[b[0]-a[0] for a,b in zip(window,window[1:])]
    if any(g<0 for g in gaps):
        return result
    max_gap=max(gaps)
    result["clock_callback_gap_max_sec"]=round(max_gap,6)
    if max_gap>.25:
        result["timing_layer"]="NATIVE_CLOCK_RECEIVE_STALL_OR_MISSING_SAMPLES"
        return result
    sim_progress=(after[1]-before[1])/1e9
    if sim_progress<0:
        result["timing_layer"]="NATIVE_CLOCK_SIM_TIME_DISCONTINUITY"
        return result
    span=after[0]-before[0]
    if span<=0:
        return result
    rtf=sim_progress/span
    result.update({
        "clock_window_bracketed":True,
        "clock_sim_progress_sec":round(sim_progress,6),
        "clock_host_span_sec":round(span,6),
        "effective_rtf":round(rtf,6),
        "timing_layer":(
            "SIMULATION_PROGRESS_SLOW"
            if rtf < .25 else "NATIVE_SENSOR_OR_TRANSPORT_DELAY"
        ),
    })
    return result


def compare_isolated_ros_first_gap(first_boundary, isolated_events, native_events):
    """First actual parent ROS callback gap vs separate Python ROS subscriber.

    Same-source timestamp pair is mandatory; a separate process avoids shared
    Python GIL, but cannot by itself distinguish Bridge/DDS and host scheduling.
    Conclusions are *candidate layers*, never proven resource root causes.
    """
    answer={
        "cause":"UNDETERMINED",
        "candidate":"NO_REAL_FIRST_ROS_GAP",
        "first_scan_violation_retained":False,
        "isolation_proven":False,
        "isolated_pair_matched":False,
        "native_pair_matched":False,
        "isolated_receive_gap_sec":None,
        "native_receive_gap_sec":None,
        "publisher_send_timing_proven":False,
        "dds_internal_delay_measured":False,
    }
    b=first_boundary if isinstance(first_boundary,dict) else {}
    try:
        ros_gap=float(b["receive_gap_sec"])
        prev_stamp=int(b["previous_ros_stamp_ns"])
        next_stamp=int(b["current_ros_stamp_ns"])
        parent_before=float(b["previous_host_monotonic_sec"])
        parent_after=float(b["current_host_monotonic_sec"])
    except (KeyError,ValueError,TypeError,OverflowError):
        return answer
    if ros_gap<=.5 or next_stamp<=prev_stamp or parent_after<=parent_before:
        return answer
    answer["first_scan_violation_retained"]=True

    def pair_gap(events):
        if not isinstance(events,(list,tuple)):
            return None
        def get_source(stamp):
            found=[]
            for e in events:
                if not isinstance(e,dict) or e.get("topic","scan")!="scan":
                    continue
                try:
                    at=float(e["host_monotonic_sec"])
                    ns=int(e["source_stamp_ns"])
                except (KeyError,ValueError,TypeError,OverflowError):
                    continue
                if ns==stamp and at==at and abs(at)<1e12:
                    found.append(at)
            return found
        before=get_source(prev_stamp)
        after=get_source(next_stamp)
        if not before or not after:
            return None
        # Require receipt not later than the parent after-boundary by more
        # than 50ms. Larger disagreement is not safe causal order evidence.
        for a in sorted(before):
            for c in sorted(after):
                if c>a and c<=parent_after+.05 and a<=parent_before+.05:
                    return round(c-a,6)
        return None

    isolated=pair_gap(isolated_events)
    native=pair_gap(native_events)
    answer["isolated_pair_matched"]=isolated is not None
    answer["native_pair_matched"]=native is not None
    if isolated is None or native is None:
        answer["candidate"]="ROS_PROCESS_TIMESTAMP_PAIR_MISSING"
        return answer
    answer["isolation_proven"]=True
    answer["isolated_receive_gap_sec"]=isolated
    answer["native_receive_gap_sec"]=native
    if native>.5:
        answer["candidate"]="AT_OR_BEFORE_NATIVE_TRANSPORT_RX"
    elif isolated>.5:
        answer["candidate"]="ROS_BRIDGE_DDS_OR_HOST_SCHEDULER"
    else:
        answer["candidate"]="LOCAL_ROS_PROCESS_DISPATCH_OR_GIL"
    return answer


def compare_worst_scan_pair_receivers(pair, native, isolated_ros,
                                     same_python_ros):
    """Compare EXACT source-stamp pair across all Scan receive layers.

    This diagnostic also accepts a <500ms near-boundary sample, but never
    treats it as an actual safety violation. Same Linux host monotonic clock.
    No internal publisher or DDS send timestamps are measured.
    """
    verdict={
        "cause":"UNDETERMINED",
        "candidate":"SOURCE_PAIR_INCOMPLETE",
        "source_pair_matched":False,
        "first_500ms_violation":False,
        "observer_gap_sec":None,
        "native_gap_sec":None,
        "isolated_ros_gap_sec":None,
        "same_python_gap_sec":None,
        "publisher_rmw_gap_measured":False,
    }
    if not isinstance(pair,dict):
        return verdict
    try:
        old_ns=int(pair["previous_ros_stamp_ns"])
        new_ns=int(pair["current_ros_stamp_ns"])
        old_parent=float(pair["previous_host_monotonic_sec"])
        new_parent=float(pair["current_host_monotonic_sec"])
        parent_gap=float(pair["receive_gap_sec"])
    except (KeyError,ValueError,TypeError,OverflowError):
        return verdict
    if new_ns<=old_ns or new_parent<=old_parent or parent_gap<=0:
        return verdict
    verdict["observer_gap_sec"]=round(parent_gap,6)
    verdict["first_500ms_violation"]=parent_gap>.5

    def matched_gap(rows):
        if not isinstance(rows,(list,tuple)):
            return None
        by_stamp={}
        for row in rows:
            if not isinstance(row,dict) or row.get("topic","scan")!="scan":
                continue
            try:
                ns=int(row["source_stamp_ns"])
                at=float(row["host_monotonic_sec"])
            except (KeyError,ValueError,TypeError,OverflowError):
                continue
            if ns in (old_ns,new_ns) and at==at and abs(at)<1e12:
                by_stamp.setdefault(ns,[]).append(at)
        if old_ns not in by_stamp or new_ns not in by_stamp:
            return None
        for a in sorted(by_stamp[old_ns]):
            for b in sorted(by_stamp[new_ns]):
                # Do NOT apply a 500ms matching tolerance here: the
                # very first incident can delay the Observer >500ms.
                # Same unique source stamps and causal ordering are enough
                # to match a delayed receiver to earlier real observations.
                if (b>a and a<=old_parent+.05 and
                    b<=new_parent+.05):
                    return round(b-a,6)
        return None

    values=[matched_gap(x) for x in (native,isolated_ros,same_python_ros)]
    if any(x is None for x in values):
        return verdict
    n,iso,same=values
    verdict.update({
        "source_pair_matched":True,
        "native_gap_sec":n,
        "isolated_ros_gap_sec":iso,
        "same_python_gap_sec":same,
    })
    if parent_gap-n<.12:
        verdict["candidate"]="NO_LARGE_RELATIVE_RX_DELAY"
    elif same>=parent_gap-.08 and iso<=n+.08:
        verdict["candidate"]="SAME_PYTHON_PROCESS_DELAY_CANDIDATE"
    elif iso>=parent_gap-.08 and same>=parent_gap-.08:
        verdict["candidate"]="ROS_BRIDGE_DDS_OR_SHARED_HOST_DELAY_CANDIDATE"
    elif iso<=n+.08 and same<=n+.08:
        verdict["candidate"]="PARENT_OBSERVER_ONLY_DELAY_CANDIDATE"
    else:
        verdict["candidate"]="MIXED_RECEIVER_TIMING_UNDETERMINED"
    return verdict


def scan_gap_operation_overlaps(parent_pair, spans):
    """Read-only correlation: actual host callback gap vs synchronous spans.

    Overlap alone never proves the enclosed operation held the GIL/RMW lock.
    Any future code fix needs separate A/B evidence at same ROS/Gazebo L2.
    """
    verdict={"status":"INSUFFICIENT_TIMING_EVIDENCE",
             "root_cause_confirmed":False,
             "overlaps":[]}
    if not isinstance(parent_pair,dict) or not isinstance(spans,(list,tuple)):
        return verdict
    import math
    try:
        start=float(parent_pair["previous_host_monotonic_sec"])
        end=float(parent_pair["current_host_monotonic_sec"])
    except (KeyError,ValueError,TypeError,OverflowError):
        return verdict
    if not all(math.isfinite(t) for t in (start,end)) or end<=start:
        return verdict
    result=[]
    for span in spans[:64]:
        if not isinstance(span,dict):
            continue
        name=span.get("name")
        try:
            a=float(span["start_sec"]);b=float(span["end_sec"])
        except (KeyError,ValueError,TypeError,OverflowError):
            continue
        if not isinstance(name,str) or not math.isfinite(a) or not math.isfinite(b) or b<=a:
            continue
        overlap=min(end,b)-max(start,a)
        if overlap>0:
            result.append({"name":name,
                           "overlap_sec":round(overlap,6),
                           "span_duration_sec":round(b-a,6),
                           "started_in_gap":start<=a<=end})
    result.sort(key=lambda item:-item["overlap_sec"])
    verdict["status"]="OBSERVED_OVERLAP_NOT_CAUSE"
    verdict["overlaps"]=result[:16]
    return verdict


def analyze_process_heartbeat_gap(scan_pair, heartbeats):
    """Compare read-only Python process heartbeat with real Scan callback gap.

    Caller timestamps must use Linux time.monotonic(). Periodic heartbeat
    reveals process-level scheduling/GIL stalls vs rclpy callback dispatch.
    It CANNOT independently distinguish a GIL holder from an OS deschedule.
    """
    result={
        "candidate":"HEARTBEAT_WINDOW_UNBRACKETED",
        "root_cause":"UNDETERMINED",
        "bracketed":False,
        "max_heartbeat_gap_sec":None,
        "process_cpu_progress_sec":None,
        "process_cpu_per_host_sec":None,
    }
    if not isinstance(scan_pair,dict) or not isinstance(heartbeats,(list,tuple)):
        return result
    import math
    try:
        start=float(scan_pair["previous_host_monotonic_sec"])
        end=float(scan_pair["current_host_monotonic_sec"])
    except (KeyError,TypeError,ValueError,OverflowError):
        return result
    if not math.isfinite(start) or not math.isfinite(end) or end<=start:
        return result
    rows=[]
    for item in heartbeats:
        if not isinstance(item,dict):
            continue
        try:
            t=float(item["host_monotonic_sec"])
            cpu=float(item["process_cpu_sec"])
        except (KeyError,TypeError,ValueError,OverflowError):
            continue
        if math.isfinite(t) and math.isfinite(cpu) and cpu>=0:
            rows.append((t,cpu))
    rows.sort(key=lambda x:x[0])
    before=[(i,v) for i,v in enumerate(rows) if v[0]<=start]
    after=[(i,v) for i,v in enumerate(rows) if v[0]>=end]
    if not before or not after:
        return result
    i=before[-1][0]
    j=after[0][0]
    window=rows[i:j+1]
    if len(window)<3 or window[-1][0]<=window[0][0]:
        return result
    gaps=[b[0]-a[0] for a,b in zip(window,window[1:])]
    if not gaps or min(gaps)<0:
        return result
    max_gap=max(gaps)
    elapsed=window[-1][0]-window[0][0]
    cpu_progress=window[-1][1]-window[0][1]
    result.update({
        "bracketed":True,
        "max_heartbeat_gap_sec":round(max_gap,6),
        "process_cpu_progress_sec":round(cpu_progress,6)
            if cpu_progress>=0 else None,
        "process_cpu_per_host_sec":round(cpu_progress/elapsed,4)
            if cpu_progress>=0 else None,
        "candidate":(
            "PROCESS_THREAD_OR_GIL_SCHEDULING_STALL"
            if max_gap>=.12 else "ROS_EXECUTOR_DISPATCH_OR_RMW_DELAY"),
    })
    return result


def classify_executor_stack_frames(frames):
    """Read-only triage of limited Python executor stack fingerprints.

    This is not a native rcl/rmw backtrace and cannot prove DDS internals.
    Sampling a stack during a pause is correlation, not root-cause proof.
    """
    verdict={"candidate":"INSUFFICIENT_STACK_EVIDENCE",
             "root_cause":"UNDETERMINED"}
    if not isinstance(frames,(list,tuple)) or not frames:
        return verdict
    names={f.get("function","") for f in frames if isinstance(f,dict)}
    if any(name in names for name in (
            "on_grid","_lethal_near","on_scan","on_odom","on_clock")):
        verdict["candidate"]="OBSERVER_CALLBACK_WORK"
    elif any(name in names for name in (
            "wait","_wait_for_ready_callbacks",
            "wait_for_ready_callbacks","_wait_for_ready_callbacks_impl")):
        verdict["candidate"]="RCLPY_WAITSET_OR_EVENT_WAKE"
    elif any("spin" in name for name in names):
        verdict["candidate"]="RCLPY_SPIN_LOOP_UNKNOWN"
    else:
        verdict["candidate"]="UNKNOWN_EXECUTOR_PYTHON_STACK"
    return verdict
