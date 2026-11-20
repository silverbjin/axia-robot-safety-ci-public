"""Task02 read-only post-Goal strict CM RMW source/Observer + Guard/sensor gate.

Uses only original owner simulation callback evidence and report, not fake
ROS. A GREEN result is a *diagnostic-only* numerical candidate: not
tracer-OFF release, not L3, not contact proof or a certified E-Stop.
"""
from __future__ import annotations
import math


def _hold(status, **observed):
    return dict(schema="axia.g07.task02.strict_actual_cm_period_v1",
                status=status,tracer_off_release_pass=False,
                owner_wsl2_accepted=False,certified_estop=False,
                **observed)


def _isfloat(x):
    return type(x) in (int,float) and math.isfinite(x)


def assess(report, events):
    if not isinstance(report,dict) or not isinstance(events,list) or len(events)>100000:
        return _hold("TASK02_REPORT_OR_EVENTS_UNVERIFIED_HOLD")
    # Same physical ROS/Gazebo/CM evidence contract in CI and true Owner.
    # Do NOT fake GITHUB_ACTIONS or rewrite Owner's actual source status.
    # Owner provenance is stronger than a mere NUMERICAL_CANDIDATE label.
    ci=(report.get("status")=="CI_GAZEBO_MOVING_GOAL_CANDIDATE"
        and report.get("shared_execution_mode")!="owner")
    owner=(report.get("status")=="NUMERICAL_CANDIDATE"
           and report.get("shared_execution_mode")=="owner"
           and report.get("common_g07_ci_oracle_status")=="CI_GAZEBO_MOVING_GOAL_CANDIDATE"
           and report.get("owner_authority_verified") is True
           and report.get("ci_specific") is False)
    if (report.get("schema")!="axia_g07_public_ci_moving_goal_v1"
            or report.get("guard_latched") is not False
            or not (ci or owner)):
        return _hold("TASK02_ACTUAL_GOAL_OR_GUARD_UNVERIFIED_HOLD")
    for key in ("real_gazebo_world","actual_physical_scan",
                "native_obstacle_set_pose_ack","stop_native_set_pose_ack"):
        if report.get(key) is not True:
            return _hold("TASK02_ACTUAL_OBSTACLE_OR_SCAN_UNVERIFIED_HOLD")
    if (not _isfloat(report.get("odom_stopped_dwell_sec"))
            or report["odom_stopped_dwell_sec"]<1
            or not _isfloat(report.get("observed_odom_moved_m"))
            or report["observed_odom_moved_m"]<.05):
        return _hold("TASK02_ACTUAL_ODOM_ZERO_DWELL_UNVERIFIED_HOLD")
    if any(report.get("goal_status_at_"+stage)!=2 for stage in ("clear","slow","stop")):
        return _hold("TASK02_NAV2_GOAL_EXECUTING_STAGES_UNVERIFIED_HOLD")
    period_limits={"max_source_interval_sec":.15,
                   "max_cm_interval_sec":.12,
                   "max_guard_interval_sec":.15,
                   "max_scan_interval_sec":.30,
                   "max_odom_interval_sec":.30,
                   "max_clock_interval_sec":.30}
    for key,limit in period_limits.items():
        value=report.get(key)
        if not _isfloat(value) or value<=0 or value>limit:
            return _hold("TASK02_INTER_NODE_TTL_LIMIT_HOLD",first_failed_period=key)
    goal=[x["t"] for x in events if isinstance(x,dict)
          and x.get("kind")=="owner_goal_published" and _isfloat(x.get("t"))]
    if len(goal)!=1:
        return _hold("TASK02_SINGLE_ACTUAL_GOAL_BOUNDARY_UNVERIFIED_HOLD")
    received=[x for x in events if isinstance(x,dict)
              and x.get("kind")=="pre_guard"
              and _isfloat(x.get("t")) and x["t"]>goal[0]]
    received.sort(key=lambda x:x["t"])
    if len(received)<10 or len(received)>30000:
        return _hold("TASK02_CM_RMW_SOURCE_SAMPLE_COVERAGE_INSUFFICIENT_HOLD")
    source=[]
    observer=[]
    for prev,nxt in zip(received,received[1:]):
        a,b=prev.get("rmw_source_ns"),nxt.get("rmw_source_ns")
        seq1,seq2=prev.get("rmw_publication_seq"),nxt.get("rmw_publication_seq")
        if (type(a) is int and type(b) is int and a>0 and b>0
                and b<=a and type(seq1) is int and type(seq2) is int
                and seq2==seq1+1):
            # FV17z53O: RMW source/received stamps moved ~6.7s backwards
            # on TWO independent Twist topics, while real monotonic
            # Observer callbacks and sequential packet IDs advanced.
            # Never misreport a timestamp anomaly as CM delivery TTL
            # violation; strict RMW evidence is still HOLD, not PASS.
            return _hold(
                "TASK02_RMW_TIMEBASE_DISCONTINUITY_HOLD",
                timebase=_first_rmw_timestamp_regression(
                    events,prev,nxt))
        if not (type(a) is int and type(b) is int and a>0 and b>a
                and type(seq1) is int and type(seq2) is int and seq2==seq1+1):
            return _hold("TASK02_CM_RMW_SEQUENCE_OR_SOURCE_UNVERIFIED_HOLD")
        gap=b-a
        dt=round((nxt["t"]-prev["t"])*1e9)
        if dt<=0:
            return _hold("TASK02_CM_OBSERVER_CLOCK_INVALID_HOLD")
        source.append(gap)
        observer.append(dt)
    max_s,max_o=max(source),max(observer)
    details=dict(actual_publisher_pairs=len(source),source_gap_max_ms=round(max_s/1e6,6),
                 observer_gap_max_ms=round(max_o/1e6,6),
                 max_guard_period_ms=round(report["max_guard_interval_sec"]*1000,6),
                 max_scan_period_ms=round(report["max_scan_interval_sec"]*1000,6),
                 max_odom_period_ms=round(report["max_odom_interval_sec"]*1000,6),
                 max_clock_period_ms=round(report["max_clock_interval_sec"]*1000,6),
                 odom_zero_dwell_ms=round(report["odom_stopped_dwell_sec"]*1000,6))
    if max_s>120_000_000 or max_o>120_000_000:
        return _hold("TASK02_CM120_SOURCE_OR_OBSERVER_FIRST_VIOLATION_HOLD",**details)
    return _hold("TASK02_PUBLIC_L2_NUMERICAL_CANDIDATE",**details)


def _first_rmw_timestamp_regression(events, prev, nxt):
    """Explain *observed* RMW clock regression, not guess OS/NTP cause.

    An independent supervised publisher with a correlated source+received
    timestamp step makes a common clock-layer cause more plausible. Neither
    stream proves a safe Guard internal TTL: this returns diagnostics only.
    """
    last=None
    second=None
    for row in events:
        if not isinstance(row,dict) or row.get("kind")!="supervised":
            continue
        if last is not None:
            t0,t1=last.get("t"),row.get("t")
            s0,s1=last.get("rmw_source_ns"),row.get("rmw_source_ns")
            r0,r1=last.get("rmw_received_ns"),row.get("rmw_received_ns")
            seq0,seq1=last.get("rmw_publication_seq"),row.get("rmw_publication_seq")
            if (all(_isfloat(x) for x in (t0,t1))
                    and all(type(x) is int for x in (s0,s1,r0,r1,seq0,seq1))
                    and 0<t1-t0<=.15 and s1<s0 and r1<r0
                    and seq1==seq0+1):
                second={"callback_t":t1,"source_regression_ms":round((s1-s0)/1e6,6)}
                break
        last=row
    p_t=prev.get("t"); n_t=nxt.get("t")
    ms=(nxt["rmw_source_ns"]-prev["rmw_source_ns"])/1e6
    gap=(n_t-p_t)*1000 if _isfloat(p_t) and _isfloat(n_t) else None
    correlated=(second is not None and _isfloat(n_t)
                and abs(second["callback_t"]-n_t)<=.15)
    return {"classification":("CROSS_STREAM_RMW_CLOCK_DISCONTINUITY_CANDIDATE"
                              if correlated else "CM_RMW_CLOCK_DISCONTINUITY_CANDIDATE"),
            "first_source_regression_ms":round(ms,6),
            "cm_callback_gap_ms":round(gap,6) if gap is not None else None,
            "other_topic":"supervised" if correlated else None,
            "other_source_regression_ms":(
                second["source_regression_ms"] if correlated else None),
            "system_clock_or_rmw_cause_proven":False,
            "guard_internal_ttl_proven":False}
