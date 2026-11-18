"""Real public CI #43664497257: concurrent RViz/G07, fail-first source vs receive.
Sanitized public fixture only. A success in prior no-GUI L2 MUST NOT re-admit Owner.
"""
import json
from pathlib import Path
from d06.live.d06_sensor_rmw_first_delivery import analyze_delivery

ROOT=Path(__file__).resolve().parents[2]
FIX=ROOT/"d06/tests/fixtures/g07_ci_20261115_concurrent_gui_first_boundary_sanitized.json"
GATE=ROOT/"d06/acceptance/d06_g07_final_owner_ci_gate.json"
WRAPPER=(ROOT/"d06/scripts/d06_gazebo_rviz_owner_wsl2_once.sh").read_text()


def test_actual_gui_load_ci_cm_receive_gap_can_occur_with_healthy_cm_source():
    x=json.loads(FIX.read_text())
    m=x["cm_rmw_first_consecutive_receive_gap"]
    assert m["rmw_source_gap_ms"] < 150 < m["rmw_receive_gap_ms"]
    assert m["publication_sequence_gap"] == 1
    # Synthetic clock is goal-relative; values reproduce measured intervals only.
    events=[
        {"kind":"owner_goal_published","t":1.0},
        {"kind":"pre_guard","t":2.0,"rmw_source_ns":10000000000,
         "rmw_received_ns":10001000000,"rmw_publication_seq":31},
        {"kind":"pre_guard","t":2.0+m["observer_callback_gap_ms"]/1000,
         "rmw_source_ns":10000000000+round(m["rmw_source_gap_ms"]*1e6),
         "rmw_received_ns":10001000000+round(m["rmw_receive_gap_ms"]*1e6),
         "rmw_publication_seq":32},
    ]
    result=analyze_delivery(events)
    assert result["status"]=="HOLD_G07_FIRST_SOURCE_RECEIVE_OR_OBSERVER_TIMING"
    assert result["first_boundary"]["channel"]=="pre_guard"
    assert result["first_boundary"]["classification"]=="RMW_RECEIVE_GAP"
    assert abs(result["first_boundary"]["source_gap_ms"]-69.596117)<0.001
    assert abs(result["first_boundary"]["received_gap_ms"]-393.57951)<0.001
    assert result["guard_received_same_delay_proven"] is False
    assert result["sensor_source_stalled_proven"] is False
    assert result["safety_pass"] is False


def test_observer_scan_gap_does_not_falsely_implicate_supervisor_native_scan():
    x=json.loads(FIX.read_text())
    assert x["observer_scan"]["callback_gap_ms"]>300
    assert x["observer_scan"]["native_supervisor_scan_callback_gap_delta_since_goal"]==0
    assert x["observer_scan"]["sensor_source_stall_proven"] is False
    assert x["native_guard"]["guard_latch_observed"] is False


def test_failed_gui_load_l2_cannot_re_admit_without_new_real_gui_l2_success():
    x=json.loads(FIX.read_text())
    g=json.loads(GATE.read_text())
    assert g["whole_ci_l2_pass"] is True  # Historical no-GUI 3/3 must remain.
    assert g["status"]=="HOLD_OWNER_L3_FIRST_CM_SOURCE_TTL_GAP"
    assert g["allow_one_final_wsl2_owner"] is False
    assert g["previous_failed_concurrent_gui_l2_run_id"] == x["origin"]["public_actions_run_id"]
    assert g["last_actual_concurrent_gui_l2_run_id"] == 43667573251
    assert g["last_actual_concurrent_gui_l2_pass"] is True
    assert g["whole_concurrent_gui_l2_pass"] is True
    assert g["owner_l3_accepted"] is False
    assert g["certified_estop"] is False
    # Raising status alone must not re-enable Owner: actual GUI-load L2 is required.
    assert 'value.get("whole_concurrent_gui_l2_pass") is True' in WRAPPER


def test_public_fixture_carries_no_actual_ros_bag_private_original_or_goal_uuid():
    src=FIX.read_text()
    for needle in ("/home/", "p2-l3-owner-", "G85prCn1", "c3c8b122",
                   "rosbag2_0.db3", "YES-P2-G07-GOAL", "AXIA_CLOUD_CI"):
        assert needle not in src
