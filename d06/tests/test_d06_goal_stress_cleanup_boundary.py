"""RED first: G07 CI adversarial CPU load is confined to moving-Goal evidence.
Native Navigation/Localization shutdown must never be stressed unknowingly.
Actual L2 #43671373817 passed Guard/Scan/CM/dwell but Navigation SERVICE_TIMEOUT.
"""
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
PHASE=ROOT/"d06/live/d06_ci_goal_phase_stress_gate.py"

def decision(payload):
    assert PHASE.is_file(), "D06_CI_GOAL_PHASE_STRESS_CLASSIFIER_MISSING"
    from d06.live.d06_ci_goal_phase_stress_gate import classify_goal_phase
    return classify_goal_phase(payload)

def test_stress_must_cover_moving_goal_and_stop_only_after_real_oracle():
    assert decision(None)=="CONTINUE_GOAL_STRESS"
    assert decision({})=="CONTINUE_GOAL_STRESS"
    assert decision({"status":"BLOCKED", "goal_sent":True})=="CONTINUE_GOAL_STRESS"
    assert decision({"status":"CI_GAZEBO_MOVING_GOAL_CANDIDATE","goal_sent":True,
                     "real_gazebo_world":True,"odom_stopped_dwell_sec":0.75})=="CONTINUE_GOAL_STRESS"
    assert decision({"status":"CI_GAZEBO_MOVING_GOAL_CANDIDATE","goal_sent":True,
                     "real_gazebo_world":True,"odom_stopped_dwell_sec":1.013,
                     "guard_latched":False})=="STOP_AFTER_VERIFIED_GOAL_ORACLE"
    assert decision({"status":"NUMERICAL_CANDIDATE","goal_sent":True,
                     "odom_stopped_dwell_sec":1.15})=="CONTINUE_GOAL_STRESS"

def test_bad_partial_json_cannot_terminate_load_or_turn_ci_green(tmp_path):
    p=tmp_path/"report.json"
    p.write_text('{"status":"CI_GAZEBO_MOVING_GOAL_CANDIDATE" ')
    r=subprocess.run([sys.executable,str(PHASE),"--goal-report",str(p)],
                     text=True,capture_output=True,check=False)
    assert r.returncode==1
    assert "CONTINUE_GOAL_STRESS" in r.stdout

def test_bounded_stress_shutdown_failure_is_not_a_whole_l2_pass():
    failure={"first_failure_phase":"POST_GOAL_CLEANUP",
             "first_failure_gate":"NAVIGATION_SERVICE_TIMEOUT",
             "native_nav2_lifecycle_ack":False,
             "native_cm_clean_exit":False,
             "runner_rc":3}
    assert failure["first_failure_gate"]=="NAVIGATION_SERVICE_TIMEOUT"
    assert not failure["native_nav2_lifecycle_ack"]
    assert not failure["native_cm_clean_exit"]
    assert failure["runner_rc"]!=0
