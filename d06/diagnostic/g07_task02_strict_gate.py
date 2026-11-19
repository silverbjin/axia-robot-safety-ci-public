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
    # The shared physical scenario explicitly labels Owner as NUMERICAL_CANDIDATE;
    # it never impersonates GitHub Actions or promotes itself to L3 acceptance.
    ci_case=(report.get("status")=="CI_GAZEBO_MOVING_GOAL_CANDIDATE"
             and report.get("shared_execution_mode")!="owner")
    owner_case=(report.get("status")=="NUMERICAL_CANDIDATE"
                and report.get("shared_execution_mode")=="owner"
                and report.get("owner_authority_verified") is True
                and report.get("common_g07_ci_oracle_status")==
                    "CI_GAZEBO_MOVING_GOAL_CANDIDATE")
    if (report.get("schema")!="axia_g07_public_ci_moving_goal_v1"
            or not (ci_case or owner_case)
            or report.get("guard_latched") is not False):
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
    source_raw=[]
    observer=[]
    clock_steps=[]
    for prev,nxt in zip(received,received[1:]):
        a,b=prev.get("rmw_source_ns"),nxt.get("rmw_source_ns")
        seq1,seq2=prev.get("rmw_publication_seq"),nxt.get("rmw_publication_seq")
        if not (type(a) is int and type(b) is int and a>0 and b>a
                and type(seq1) is int and type(seq2) is int and seq2==seq1+1):
            return _hold("TASK02_CM_RMW_SEQUENCE_OR_SOURCE_UNVERIFIED_HOLD")
        gap=b-a
        dt=round((nxt["t"]-prev["t"])*1e9)
        if dt<=0:
            return _hold("TASK02_CM_OBSERVER_CLOCK_INVALID_HOLD")
        source_raw.append(gap)
        # WSL2 may step CLOCK_REALTIME while the ROS steady/monotonic
        # callback clock keeps advancing normally. RMW source AND receive
        # timestamps are both wall time. Only the *Owner* scenario may use
        # the independent monotonic callback clock to distinguish a common
        # wall-clock step from a lost publication; CI remains strict raw RMW.
        # This is evidence normalization ONLY, not a change to CM/Guard TTL.
        corrected=gap
        if gap>120_000_000 and owner_case:
            ra,rb=prev.get("rmw_received_ns"),nxt.get("rmw_received_ns")
            if (type(ra) is int and type(rb) is int and rb>ra
                    and 0<=ra-a<=10_000_000
                    and 0<=rb-b<=10_000_000
                    and 500_000_000<gap<10_000_000_000
                    and 0<dt<=120_000_000):
                receive_gap=rb-ra
                # Step must occur in BOTH independent RMW time fields with
                # the same offset. A real slow source or missing sequence
                # cannot satisfy this monotonic + dual timestamp contract.
                if (abs((receive_gap-dt)-(gap-dt))<=2_000_000
                        and receive_gap-dt>500_000_000):
                    corrected=dt+(ra-a)-(rb-b)
                    if 0<corrected<=120_000_000:
                        clock_steps.append({
                            "previous_seq":seq1,"next_seq":seq2,
                            "source_wall_gap_ms":round(gap/1e6,6),
                            "receive_wall_gap_ms":round(receive_gap/1e6,6),
                            "observer_monotonic_gap_ms":round(dt/1e6,6),
                            "corrected_source_envelope_ms":round(corrected/1e6,6)})
                    else:
                        corrected=gap
        source.append(corrected)
        observer.append(dt)
    max_s,max_o=max(source),max(observer)
    details=dict(actual_publisher_pairs=len(source),source_gap_max_ms=round(max_s/1e6,6),
                 source_raw_gap_max_ms=round(max(source_raw)/1e6,6),
                 clock_step_pairs=len(clock_steps),clock_step_evidence=clock_steps,
                 host_external_clock_verified=False,
                 observer_gap_max_ms=round(max_o/1e6,6),
                 max_guard_period_ms=round(report["max_guard_interval_sec"]*1000,6),
                 max_scan_period_ms=round(report["max_scan_interval_sec"]*1000,6),
                 max_odom_period_ms=round(report["max_odom_interval_sec"]*1000,6),
                 max_clock_period_ms=round(report["max_clock_interval_sec"]*1000,6),
                 odom_zero_dwell_ms=round(report["odom_stopped_dwell_sec"]*1000,6))
    if max_s>120_000_000 or max_o>120_000_000:
        return _hold("TASK02_CM120_SOURCE_OR_OBSERVER_FIRST_VIOLATION_HOLD",**details)
    if owner_case:
        return _hold(
            "TASK02_OWNER_MONOTONIC_CLOCK_STEP_NUMERICAL_CANDIDATE"
            if clock_steps else "TASK02_OWNER_NATIVE_NUMERICAL_CANDIDATE",
            **details)
    return _hold("TASK02_PUBLIC_L2_NUMERICAL_CANDIDATE",**details)
