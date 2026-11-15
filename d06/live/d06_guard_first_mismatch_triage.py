"""Read-only, sanitized Owner G07 first-safety-boundary classification.

This does NOT infer CM publisher origin from Twist, correlate RMW system epoch
with host monotonic, run ROS/Goal, or override a Guard latch.
"""
from __future__ import annotations
import math

def _finite(value):
    return type(value) in (int,float) and math.isfinite(value)

def inspect(record):
    fail={"schema":"axia.g07.owner_first_mismatch_triage.v1",
          "status":"HOLD_INCOMPLETE_FIRST_SAFETY_EVIDENCE",
          "first_safety_transition":None,
          "reconciliation_elapsed_ms":None,
          "cm_age_ms":None,"supervisor_age_ms":None,
          "cm_linear_x":None,"supervisor_linear_x":None,
          "last_emitted":None,
          "ttl_violation_proven":False,
          "clock_domain_status":"UNVERIFIED",
          "rmw_cm_source_jump_ms":None,
          "cm_observer_monotonic_gap_ms":None,
          "cm_publisher_stopped_proven":False,
          "clock_step_root_cause_proven":False,
          "safety_pass":False,"owner_l3_accepted":False,"certified_estop":False}
    if not isinstance(record,dict):
        return fail
    latch=record.get("guard_first_latch")
    clock=record.get("clock_domain")
    if not isinstance(latch,dict) or not isinstance(clock,dict):
        return fail
    fields=("cm_age_sec","supervisor_age_sec","reconciliation_since_mono",
            "first_latch_tick_mono","ttl_cm_sec","reconciliation_grace_sec")
    if not all(_finite(latch.get(x)) for x in fields):
        return fail
    if (not isinstance(latch.get("cm"),dict) or
        not isinstance(latch.get("supervisor"),dict) or
        not isinstance(latch.get("last_emitted"),dict)):
        return fail
    cm,supervisor,out=latch["cm"],latch["supervisor"],latch["last_emitted"]
    if not all(_finite(v.get(k)) for v in (cm,supervisor,out) for k in ("linear_x","angular_z")):
        return fail
    elapsed=latch["first_latch_tick_mono"]-latch["reconciliation_since_mono"]
    if elapsed<0 or any(latch[k]<=0 for k in ("ttl_cm_sec","reconciliation_grace_sec")):
        return fail
    result={**fail,
        "first_safety_transition":latch.get("reason"),
        "reconciliation_elapsed_ms":round(elapsed*1000,6),
        "cm_age_ms":round(latch["cm_age_sec"]*1000,6),
        "supervisor_age_ms":round(latch["supervisor_age_sec"]*1000,6),
        "cm_linear_x":cm["linear_x"],
        "supervisor_linear_x":supervisor["linear_x"],
        "last_emitted":"ZERO" if out["linear_x"]==0 and out["angular_z"]==0 else "NONZERO",
        "ttl_violation_proven":latch["cm_age_sec"]>=latch["ttl_cm_sec"]}
    if (latch.get("reason")=="CM_EXCEEDS_SUPERVISOR" and
            latch.get("latched") is True and elapsed>latch["reconciliation_grace_sec"] and
            latch["cm_age_sec"]<latch["ttl_cm_sec"] and
            latch.get("supervisor_fsm")=="NORMAL" and
            latch.get("goal_authorized") is True and
            (abs(cm["linear_x"])>abs(supervisor["linear_x"])+0.01 or
             abs(cm["angular_z"])>abs(supervisor["angular_z"])+0.02) and
            result["last_emitted"]=="ZERO"):
        result["status"]="HOLD_CM_SUPERVISOR_RECONCILIATION_EXPIRED"
    keys=("cm_rmw_source_gap_sec","supervisor_rmw_source_gap_sec",
          "cm_observer_monotonic_gap_sec","estimated_system_step_sec")
    if all(_finite(clock.get(x)) and clock[x]>=0 for x in keys):
        result["rmw_cm_source_jump_ms"]=round(clock["cm_rmw_source_gap_sec"]*1000,6)
        result["cm_observer_monotonic_gap_ms"]=round(clock["cm_observer_monotonic_gap_sec"]*1000,6)
        if (clock.get("source_timestamp_domain")=="RMW_SYSTEM_CLOCK" and
                clock.get("observer_timestamp_domain")=="HOST_MONOTONIC" and
                clock["cm_observer_monotonic_gap_sec"]<.15 and
                abs(clock["cm_rmw_source_gap_sec"]-
                    clock["supervisor_rmw_source_gap_sec"])<.05 and
                clock["cm_rmw_source_gap_sec"]>1.0):
            result["clock_domain_status"]="HOST_SYSTEM_CLOCK_STEP_CANDIDATE"
    # Cross-clock comparisons do not establish a publisher outage. The
    # caller-supplied claim itself is not authority to override this.
    return result
