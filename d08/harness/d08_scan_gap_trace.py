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
