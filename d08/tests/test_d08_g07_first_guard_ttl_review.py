"""G07 first safety transition regression from actual public Gazebo run ids.

#44483897411 and #44485688526: explicit fail-closed timing, no safety
threshold or fake DDS/rcl publication proof. L0 analysis != L2 PASS.
"""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from d08_g07_first_guard_ttl_review import assess_first_guard_event,first_pair_from_log,analyze_file

@pytest.mark.parametrize("guard,obs,tick,rx",[
  (.169428615,.167194531,305.784145710,305.614717095),
  (.186991342,.181808582,336.877635575,336.690644233),
])
def test_actual_first_guard_breaches_are_fail_closed_and_common_boundary(guard,obs,tick,rx):
    evidence=assess_first_guard_event({
        "latched":True,"reason":"UPSTREAM_STALE_AFTER_MOTION",
        "cm_age_sec":guard,"tick_monotonic":tick,
        "cm_rx_monotonic":rx}, {
        "observer_cm_age_at_latch_sec":obs,
        "guard_cm_age_at_latch_sec":guard})
    assert evidence["ttl_limit_ms"]==150.0
    assert evidence["guard_cm_age_ms"]>150
    assert evidence["candidate"]=="COMMON_CM_SOURCE_OR_SHARED_DISPATCH_GAP_CANDIDATE"
    assert evidence["cause"]=="UNDETERMINED"
    assert evidence["publisher_timestamp_or_lttng_proven"] is False
    assert evidence["cm_guard_150ms_safety_contract_pass"] is False
    assert evidence["moving_l2_accepted"] is False

def test_only_guard_stale_is_distinct_candidate_but_still_hold():
    evidence=assess_first_guard_event({
        "latched":True,"reason":"UPSTREAM_STALE_AFTER_MOTION",
        "cm_age_sec":.173,"tick_monotonic":10.200,
        "cm_rx_monotonic":10.027}, {
        "observer_cm_age_at_latch_sec":.08,
        "guard_cm_age_at_latch_sec":.173})
    assert evidence["candidate"]=="GUARD_RMW_RECEIVE_OR_EXECUTOR_LAG_CANDIDATE"
    assert evidence["moving_l2_accepted"] is False

def test_do_not_make_a_zero_or_non_latch_a_safe_pass():
    with pytest.raises(ValueError,match="TRANSITION"):
        assess_first_guard_event({"latched":False,"reason":"FORWARDING_MONITORED_CM"}, {})
    with pytest.raises(ValueError,match="VIOLATION"):
        assess_first_guard_event({
            "latched":True,"reason":"UPSTREAM_STALE_AFTER_MOTION",
            "cm_age_sec":.13,"tick_monotonic":9.13,
            "cm_rx_monotonic":9}, {
            "observer_cm_age_at_latch_sec":.12,
            "guard_cm_age_at_latch_sec":.13})

def test_real_structured_lines_first_only_with_incomplete_failclosed(tmp_path):
    log=tmp_path/"latch.log"
    log.write_text("random log\n"+
      "AXIA_G07_PUBLIC_CI_FIRST_CM_GUARD_RECEIPT_SKEW "+
        json.dumps({"observer_cm_age_at_latch_sec":.167194531,
                    "guard_cm_age_at_latch_sec":.169428615})+"\n"+
      "AXIA_G07_PUBLIC_CI_FIRST_GUARD_LATCH_INTERNAL "+
        json.dumps({"latched":True,"reason":"UPSTREAM_STALE_AFTER_MOTION",
                    "cm_age_sec":.169428615,"tick_monotonic":305.784145710,
                    "cm_rx_monotonic":305.614717095})+"\n")
    assert first_pair_from_log(log.read_text())[0]["latched"] is True
    out=tmp_path/"first.json"
    assert analyze_file(log,out)==0
    v=json.loads(out.read_text())
    assert v["status"]=="FIRST_SAFETY_TRANSITION_PROVEN_MOVING_L2_HOLD"
    assert v["ttl_excess_ms"]==pytest.approx(19.429,abs=.001)
    assert v["cm_guard_150ms_safety_contract_pass"] is False
    log2=tmp_path/"no_latch.log"
    log2.write_text("last shutdown warning only\n")
    out2=tmp_path/"incomplete.json"
    assert analyze_file(log2,out2)==2
    assert json.loads(out2.read_text())["cause"]=="UNDETERMINED"
