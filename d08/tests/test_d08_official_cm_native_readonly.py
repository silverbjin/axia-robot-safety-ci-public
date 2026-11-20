"""D08 Task02 real official CM lifecycle+scan configuration probe contract.

Original Run #44245796892: native official collision_monitor configured [scan]
and activated, but DDS scan graph returned _NODE_NAME_UNKNOWN_. Never
reinterpret that as internal RMW receive or actual STOP/velocity action.
"""
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"harness"))
from d08_same_world_replan import assess_official_cm_native_scan

def test_active_collision_monitor_with_real_scan_param_only_scoped_pass():
    r=assess_official_cm_native_scan(3,"active",["scan"],"/scan")
    assert r["official_cm_active_scan_configured"] is True
    assert r["cm_internal_receive_gap_verified"] is False
    assert r["cm_action_state_verified"] is False
    assert r["moving_goal_sent"] is False

@pytest.mark.parametrize("args,first",[
    ((2,"inactive",["scan"],"/scan"),"NOT_ACTIVE"),
    ((3,"active",[],"/scan"),"SCAN_SOURCE_MISSING"),
    ((3,"active",["scan"],"/synthetic_scan"),"SCAN_TOPIC_NOT_REAL"),
    ((3,"active",["scan"],""),"SCAN_TOPIC_NOT_REAL"),
])
def test_unknown_graph_never_substitutes_real_native_configuration(args,first):
    with pytest.raises(ValueError,match=first):
        assess_official_cm_native_scan(*args)

def test_readonly_observer_calls_real_native_services_without_unsafe_twist():
    s=(ROOT/"harness"/"d08_same_world_replan.py").read_text()
    assert '"/collision_monitor/get_state"' in s
    assert '"/collision_monitor/get_parameters"' in s
    assert '"observation_sources","scan.topic"' in s
    assert 'D08_OFFICIAL_CM_NATIVE_STATE_SCAN_NOT_VERIFIED' in s
    assert "official_cm_active_scan_configured" in s
    assert "Twist()" not in s
