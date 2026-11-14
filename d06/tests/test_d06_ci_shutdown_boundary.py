"""Only terminal cleanup failing after real L2 safety candidate: fail-first.

Synthetic, no actual private Owner logs, no ROS and no Goal in unit tests.
"""
import json
from pathlib import Path

def fixture(tmp_path, *, rc=3, marker="G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET"):
    root=tmp_path/"owner_l2"
    root.mkdir()
    (root/"g07_ci_moving").mkdir()
    (root/"g07_ci_moving"/"ci_moving_goal_result.json").write_text(
        json.dumps({"status":"CI_GAZEBO_MOVING_GOAL_CANDIDATE",
                    "goal_sent":True,"guard_latched":False,
                    "odom_stopped_dwell_sec":1.00166}))
    (root/"g07_ordered_shutdown.json").write_text(
        json.dumps({"status":"NAV2_LIFECYCLE_SHUTDOWN_ACK",
                    "navigation_ack":True,"localization_ack":True}))
    (root/"teardown.txt").write_text("P2_L2_FORCED_TEARDOWN\n")
    logfile=tmp_path/"run.log"
    logfile.write_text("private uuid not for output\n"+marker+"\n")
    rcfile=tmp_path/"run.rc"
    rcfile.write_text(str(rc)+"\n")
    return root,logfile,rcfile

def test_scoped_l2_motion_success_but_cleanup_rc3_must_not_be_full_pass(tmp_path):
    from d06.live.d06_ci_shutdown_triage import review_cleanup
    root,logfile,rcfile=fixture(tmp_path)
    r=review_cleanup(root,logfile,rcfile)
    assert r["status"]=="HOLD_POST_GOAL_CLEANUP"
    assert r["original_g07_motion_candidate"] is True
    assert r["first_cleanup_failure"]=="G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET"
    assert r["full_run_pass"] is False
    assert r["owner_l3_accepted"] is False

def test_first_cleanup_marker_precedes_later_generic_rc(tmp_path):
    from d06.live.d06_ci_shutdown_triage import review_cleanup
    root,logfile,rcfile=fixture(tmp_path,
        marker="G07_MOVING_GOAL_ORDERED_SHUTDOWN_BLOCKED")
    logfile.write_text(logfile.read_text()+
                       "G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET\n")
    r=review_cleanup(root,logfile,rcfile)
    assert r["first_cleanup_failure"]=="G07_MOVING_GOAL_ORDERED_SHUTDOWN_BLOCKED"

def test_missing_private_raw_fails_closed_no_debug_leaks(tmp_path):
    from d06.live.d06_ci_shutdown_triage import review_cleanup
    root,logfile,rcfile=fixture(tmp_path)
    (root/"g07_ordered_shutdown.json").unlink()
    r=review_cleanup(root,logfile,rcfile)
    assert r["status"]=="HOLD_POST_GOAL_CLEANUP"
    assert r["full_run_pass"] is False
    assert "private uuid" not in json.dumps(r)
    assert "certified_estop" in r and r["certified_estop"] is False

def test_valid_ack_and_graceful_exit_is_scope_only_not_l3(tmp_path):
    from d06.live.d06_ci_shutdown_triage import review_cleanup
    root,logfile,rcfile=fixture(tmp_path,rc=0,marker="")
    (root/"teardown.txt").write_text("P2_L2_GRACEFUL_TEARDOWN\n")
    (root/"g07_shutdown_audit.json").write_text(
        json.dumps({"status":"SHUTDOWN_CLEAN_CANDIDATE","cm_exit_code":0}))
    r=review_cleanup(root,logfile,rcfile)
    assert r["status"]=="CI_G07_L2_CLEANUP_CANDIDATE_ONLY"
    assert r["full_run_pass"] is True
    assert r["owner_l3_accepted"] is False


def test_masked_rc3_without_goal_prefers_first_startup_gate(tmp_path):
    from d06.live.d06_ci_shutdown_triage import review_cleanup
    root,logfile,rcfile=fixture(tmp_path,rc=3,
                                    marker="G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET")
    (root/"g07_ci_moving"/"ci_moving_goal_result.json").unlink()
    (root/"startup_verdict.json").write_text(json.dumps({
        "status":"BLOCKED","failed_gate":"CLOCK_READY","goal_sent":False}))
    logfile.write_text("P2_STAGED_NO_GOAL_BLOCKED\n"
                       "G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET\n")
    r=review_cleanup(root,logfile,rcfile)
    assert r["first_failure_phase"]=="PRE_GOAL_STARTUP"
    assert r["first_failure_gate"]=="CLOCK_READY"
    assert r["first_cleanup_failure"] is None
    assert r["status"]=="HOLD_PRE_GOAL_STARTUP"
    assert r["full_run_pass"] is False

def test_masked_rc3_without_goal_but_ready_startup_is_pregoal_not_shutdown(tmp_path):
    from d06.live.d06_ci_shutdown_triage import review_cleanup
    root,logfile,rcfile=fixture(tmp_path,rc=3)
    (root/"g07_ci_moving"/"ci_moving_goal_result.json").unlink()
    (root/"startup_verdict.json").write_text(json.dumps({
        "status":"SMOKE_READY","goal_sent":False,"stages":[]}))
    (root/"g07_ci_pregoal.log").write_text(
        "AXIA_G07_CI_MOVING_GOAL_REAL_GAZEBO_PREG0AL_BLOCKED")
    r=review_cleanup(root,logfile,rcfile)
    assert r["first_failure_phase"]=="PRE_GOAL_PHYSICAL"
    assert r["status"]=="HOLD_PRE_GOAL_PHYSICAL"
    assert r["first_cleanup_failure"] is None
    assert r["owner_l3_accepted"] is False


def test_goal_guard_latch_first_wins_over_cleanup_rc3(tmp_path):
    from d06.live.d06_ci_shutdown_triage import review_cleanup
    root,logfile,rcfile=fixture(tmp_path,rc=3,
        marker="G07_CI_LAUNCH_LIVE_AFTER_MANAGED_EXIT_BUDGET")
    (root/"g07_ci_moving"/"ci_moving_goal_result.json").write_text(
        json.dumps({"status":"BLOCKED","goal_sent":True,"guard_latched":True,
                    "first_guard_latch":{"reason":"UPSTREAM_STALE_AFTER_MOTION",
                                          "cm_age_sec":0.15301809}}))
    r=review_cleanup(root,logfile,rcfile)
    assert r["status"]=="HOLD_G07_SAFETY_LATCH"
    assert r["first_failure_phase"]=="GOAL_SAFETY_LATCH"
    assert r["first_failure_gate"]=="UPSTREAM_STALE_AFTER_MOTION"
    assert r["first_cleanup_failure"] is None
    assert r["full_run_pass"] is False
