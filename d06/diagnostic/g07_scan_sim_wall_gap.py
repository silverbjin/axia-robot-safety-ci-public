#!/usr/bin/env python3
"""Read-only first ROS LaserScan Sim-time/host-receipt boundary classifier.

Never equate simulation header stamps with host-monotonic timestamps.
Input is bounded user-reported numeric evidence, not a raw bag re-extraction.
A diagnostic alone NEVER authorizes a Goal, field release or certificate.
"""
import math

def _number(value):
    return type(value) in (float,int) and math.isfinite(value)

def _hold(status, *, candidate="UNDETERMINED", **fields):
    result=dict(schema="axia.g07.first_scan_wall_sim_boundary.v1",
                status=status,origin_candidate=candidate,
                root_cause="CAUSE_UNDETERMINED",cause_proven=False,
                gazebo_bridge_delay_proven=False,
                oracle_only_observer_stall_supported=False,
                native_publish_boundary="NOT_MEASURED",
                release="HOLD",scan_wall_300_pass=False,
                owner_wsl2_l3="BLOCKED",certified_estop=False)
    result.update(fields)
    return result

def assess_first_scan_wall_gap(facts):
    if not isinstance(facts,dict):
        return _hold("SCAN_FIRST_PAIR_UNVERIFIED_HOLD")
    required=("oracle_prev_monotonic_s","oracle_now_monotonic_s",
              "oracle_first_gap_ms","oracle_max_gap_ms",
              "scan_header_sim_prev_s","scan_header_sim_now_s",
              "rosbag_scan_receive_gap_ms","rosbag_safety_scan_receive_gap_ms",
              "scan_wall_limit_ms")
    if (facts.get("schema")!="axia.g07.scan_wall_sim_first_boundary.v1"
            or facts.get("topic")!="/scan"
            or facts.get("same_laserscan_pair") is not True
            or not all(_number(facts.get(k)) for k in required)):
        return _hold("SCAN_FIRST_PAIR_UNVERIFIED_HOLD")
    pre,cur=facts["oracle_prev_monotonic_s"],facts["oracle_now_monotonic_s"]
    h0,h1=facts["scan_header_sim_prev_s"],facts["scan_header_sim_now_s"]
    gap=facts["oracle_first_gap_ms"]
    bound=facts["scan_wall_limit_ms"]
    bag,safe=facts["rosbag_scan_receive_gap_ms"],facts["rosbag_safety_scan_receive_gap_ms"]
    if (pre<0 or cur<=pre or h1<=h0 or bound!=300. or gap<0
            or abs((cur-pre)*1000-gap)>.001 or
            not all(0<=v<=60000 for v in (bag,safe,facts["oracle_max_gap_ms"]))
            or facts["oracle_max_gap_ms"]+1e-6<gap):
        return _hold("SCAN_FIRST_PAIR_UNVERIFIED_HOLD")
    rtf=facts.get("short_window_rtf_estimate")
    rtf_valid=_number(rtf) and 0<rtf<=2
    rtf_est=round(rtf,5) if rtf_valid else None
    sim_delta=round((h1-h0)*1000,6)
    native=facts.get("gazebo_native_publish_gap_ms")
    native_valid=(_number(native) and native>0 and
                  bool(facts.get("gazebo_native_publish_host_monotonic_pair")))
    violation=max(gap,bag,safe)>bound
    if native_valid and native>bound:
        candidate="GAZEBO_NATIVE_PUBLISH_WALL_GAP_CANDIDATE"
    elif native_valid and native<=bound and bag>bound:
        candidate="POST_GAZEBO_PUBLISH_DELIVERY_GAP_CANDIDATE"
    elif bag<=bound and safe<=bound and gap>bound:
        candidate="ORACLE_ONLY_CALLBACK_STALL_CANDIDATE"
    elif sim_delta>150:
        candidate="SENSOR_SIM_PERIOD_GAP_CANDIDATE"
    elif bag>bound and safe>bound:
        candidate="UPSTREAM_OR_SHARED_ROS_DELIVERY_GAP_CANDIDATE"
    else:
        candidate="GAP_BOUNDARY_UNRESOLVED"
    expected=round(sim_delta/rtf_est,3) if rtf_valid else None
    residual=round(bag-expected,3) if expected is not None else None
    return _hold("SCAN_WALL_300_VIOLATION_HOLD" if violation
                 else "SCAN_WALL_OBSERVED_WITHIN_BOUND_BUT_NATIVE_UNVERIFIED_HOLD",
                 candidate=candidate,first_gap_ms=round(gap,6),
                 max_gap_ms=round(facts["oracle_max_gap_ms"],6),
                 scan_header_sim_gap_ms=sim_delta,
                 rosbag_scan_gap_ms=round(bag,6),
                 rosbag_safety_gap_ms=round(safe,6),
                 rtf_window_estimate=rtf_est,
                 expected_scan_wall_ms_from_local_rtf_estimate=expected,
                 unexplained_wall_residual_ms_estimate=residual,
                 residual_causal_attribution="UNPROVEN",
                 native_publish_boundary="MEASURED_SCOPED" if native_valid else "NOT_MEASURED",
                 clock_and_odom_continued=bool(facts.get("clock_and_odom_still_received_in_window")),
                 oracle_only_observer_stall_supported=(candidate=="ORACLE_ONLY_CALLBACK_STALL_CANDIDATE"),
                 scan_300_boundary_violated=violation,
                 first_safety_transition_proven=facts.get("guard_latched") is True,
                 raw_evidence_rechecked_here=facts.get("raw_evidence_rechecked_here") is True)
