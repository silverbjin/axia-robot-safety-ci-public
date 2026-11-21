"""First actual CM callback timing vs independent DDS receipt intervals.

Only pairwise INTERARRIVAL DELTAS are compared; host CLOCK_MONOTONIC and
RMW received SYSTEM_CLOCK absolute epochs are never subtracted. A widening
interval is evidence of post-DDS receipt callback spacing, not proof of
scheduler, callback-group, OS CPU, ROS writer or hardware root cause.
"""
import math


def _number(x):
    return type(x) in (float,int) and math.isfinite(x)


def _base(status, **kwargs):
    row=dict(schema="axia.g07.first_cm_observer_post_receive_delta.v1",
             status=status,release="HOLD",root_cause_proven=False,
             executor_scheduler_cause_proven=False,publisher_halt_proven=False,
             certified_estop=False,owner_wsl2_l3_accepted=False,
             cancel_client_is_sole_cause_proven=False,
             host_monotonic_minus_rmw_absolute_epoch_subtracted=False)
    row.update(kwargs)
    return row


def classify(fixture):
    if not isinstance(fixture,dict):
        return _base("FIRST_CM_OBSERVER_NUMERIC_EVIDENCE_MISSING_HOLD")
    w=fixture.get("first_cm_observer_breach",{})
    if not isinstance(w,dict):
        return _base("FIRST_CM_OBSERVER_NUMERIC_EVIDENCE_MISSING_HOLD")
    cm=w.get("pre_guard");sup=w.get("supervised")
    if not isinstance(cm,dict) or not isinstance(sup,dict):
        return _base("FIRST_CM_OBSERVER_NUMERIC_EVIDENCE_MISSING_HOLD")
    for item in (cm,sup):
        if (not all(_number(item.get(k)) for k in
                    ("observer_gap_ms","received_gap_ms","source_gap_ms",
                     "previous_rx_host_monotonic","current_rx_host_monotonic"))
                or item.get("pub_seq_delta")!=1
                or item["observer_gap_ms"]<=0 or item["received_gap_ms"]<=0):
            return _base("FIRST_CM_OBSERVER_PAIR_UNVERIFIED_HOLD")
    delta_cm=cm["observer_gap_ms"]-cm["received_gap_ms"]
    delta_sup=sup["observer_gap_ms"]-sup["received_gap_ms"]
    marker=fixture.get("motion_window_end_monotonic")
    spans=(_number(marker)
           and cm["previous_rx_host_monotonic"]<=marker<cm["current_rx_host_monotonic"])
    previous=fixture.get("first_pre_cancel_observer_backlog",{})
    p=previous.get("pre_guard",{}) if isinstance(previous,dict) else {}
    predelta=None
    pre_cause_candidate=False
    if (_number(p.get("observer_gap_ms"))
            and _number(p.get("rmw_received_gap_ms"))
            and _number(p.get("current_rx_host_monotonic"))
            and _number(marker)
            and p.get("pub_seq_delta")==1
            and p["current_rx_host_monotonic"]<marker):
        predelta=p["observer_gap_ms"]-p["rmw_received_gap_ms"]
        pre_cause_candidate=predelta>40 and p["observer_gap_ms"]<120
    peers=w.get("other_observed_topics",{})
    peers_count=(sum(1 for k,v in peers.items()
                     if k.endswith("_observer_gap_ms") and _number(v) and v>120)
                 if isinstance(peers,dict) else 0)
    backlog=(cm["observer_gap_ms"]>120 and delta_cm>40
             and sup["observer_gap_ms"]>120 and delta_sup>40
             and abs(cm["current_rx_host_monotonic"]-
                     sup["current_rx_host_monotonic"])<.15
             and cm["received_gap_ms"]<=120 and sup["received_gap_ms"]<=120)
    if backlog:
        status="POST_RMW_OBSERVER_DELIVERY_SPACING_HOLD"
    elif cm["observer_gap_ms"]>120:
        status="REAL_OBSERVER_120MS_BREACH_WITH_NO_BACKLOG_PROOF_HOLD"
    else:
        status="NO_CM120_OBSERVER_BREACH_IN_NUMERIC_PAIR_NOT_ACCEPTANCE_HOLD"
    return _base(status,
                 first_observer_violation_channel="pre_guard",
                 cm_observer_minus_rmw_receive_delta_ms=round(delta_cm,6),
                 supervised_observer_minus_rmw_receive_delta_ms=round(delta_sup,6),
                 pre_cancel_cm_observer_minus_rmw_receive_delta_ms=(
                     round(predelta,6) if predelta is not None else None),
                 pre_cancel_backlog_candidate=pre_cause_candidate,
                 first_gap_spans_goal_cancel_boundary=bool(spans),
                 observed_peer_count_over_120ms=peers_count,
                 exact_rmw_publication_sequence_increment=1,
                 cm_120ms_limit_changed=False,
                 relative_callback_queue_widening_observed=bool(backlog),
                 actual_guard_internal_age_ms=fixture.get("guard_internal_cm_age_max_ms"),
                 underlying_scheduler_root_cause="UNDETERMINED")
