"""D06 G07 live cold-start wait: first pending gate without a new Goal.

A synthetic inspection regression. Never loads actual Owner evidence into CI.
"""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def make_run(tmp_path, status="BLOCKED", gates=None, failed=None):
    path = tmp_path/"axia_p2_private_evidence"/"p2-l3-owner-fixture"/"G07"
    path.mkdir(parents=True)
    (path/"staged_startup.log").write_text("AXIA_G07_SHARED_STAGED_RUNNER_BEGIN NO_GOAL\n", encoding="utf-8")
    (path/"startup_verdict.json").write_text(
        json.dumps({"status":status, "stages":gates or [], "failed_gate":failed, "goal_sent":False}),
        encoding="utf-8")
    return path


def test_after_clock_waiting_localization_is_not_misreported_as_goal_progress(tmp_path):
    from d06.live.d06_owner_startup_inspect import inspect_run
    run = make_run(tmp_path,gates=[
        {"gate":"CLOCK_READY","status":"PASS","detail":"clock"},
        {"gate":"NAVIGATION_NOT_ACTIVE","status":"PASS","detail":"stage"},
    ])
    result=inspect_run(run,now=run.stat().st_mtime+30)
    assert result["status"]=="STARTUP_IN_PROGRESS_NO_GOAL"
    assert result["last_completed"]=="NAVIGATION_NOT_ACTIVE"
    assert result["next_pending"]=="LOCALIZATION_START"
    assert result["goal_sent"] is False
    assert result["acceptance_pass"] is False


def test_empty_stage_ledger_reports_wait_without_guessing_specific_gate(tmp_path):
    from d06.live.d06_owner_startup_inspect import inspect_run
    run=make_run(tmp_path)
    r=inspect_run(run)
    assert r["status"]=="STARTUP_IN_PROGRESS_NO_GOAL"
    assert r["next_pending"]=="CLOCK_READY"
    assert r["acceptance_pass"] is False


def test_first_blocked_gate_is_not_relabelled_success(tmp_path):
    from d06.live.d06_owner_startup_inspect import inspect_run
    run=make_run(tmp_path,status="BLOCKED", failed="LOCALIZATION_START",
                 gates=[{"gate":"CLOCK_READY","status":"PASS"},
                        {"gate":"LOCALIZATION_START","status":"BLOCKED","detail":"SERVICE_TIMEOUT"}])
    r=inspect_run(run)
    assert r["status"]=="STARTUP_BLOCKED"
    assert r["first_failed_gate"]=="LOCALIZATION_START"
    assert "SERVICE_TIMEOUT" in r["last_stage_detail"]
    assert r["acceptance_pass"] is False


def test_ready_state_is_only_no_goal_preflight(tmp_path):
    from d06.live.d06_owner_startup_inspect import inspect_run
    run=make_run(tmp_path,status="SMOKE_READY",
                 gates=[{"gate":"NAV2_ACTION_READY","status":"PASS"}])
    r=inspect_run(run)
    assert r["status"]=="STARTUP_READY_NO_GOAL"
    assert r["acceptance_pass"] is False
    assert r["goal_sent"] is False


def test_missing_source_does_not_invent_live_wsl2_success(tmp_path):
    from d06.live.d06_owner_startup_inspect import inspect_run
    r=inspect_run(tmp_path/"missing")
    assert r["status"]=="NO_OWNER_STAGED_LOG"
    assert r["acceptance_pass"] is False


def test_inspection_module_never_imports_ros_or_issues_goal_commands():
    src=(Path(__file__).resolve().parents[1]/"live"/"d06_owner_startup_inspect.py").read_text()
    assert "rclpy" not in src
    assert "subprocess" not in src
    assert "os.system" not in src
    assert "send_goal" not in src
    assert "create_publisher" not in src
    assert "unlink(" not in src
    assert "write_text(" not in src



def test_587s_is_log_write_age_not_480s_startup_timeout(tmp_path):
    """Field regression: READY + log mtime age 587s must not be TIMEOUT."""
    import os
    from d06.live.d06_owner_startup_inspect import inspect_run
    run=make_run(tmp_path,status="SMOKE_READY",gates=[
        {"gate":"CLOCK_READY","status":"PASS"},
        {"gate":"NAV2_ACTION_READY","status":"PASS",
         "detail":"SIMULATION_READINESS_CONFIRMED_NO_GOAL"},
    ])
    moment=1800000000.0
    for filename in ("staged_startup.log","startup_verdict.json"):
        os.utime(run/filename,(moment-587.3,moment-587.3))
    got=inspect_run(run,now=moment)
    assert got["status"]=="STARTUP_READY_NO_GOAL"
    assert got["startup_log_last_write_age_sec"]==587.3
    assert "elapsed_since_start_log_sec" not in got
    assert got["post_startup_phase"]=="NAV2_READY_NEXT_STAGE_NOT_YET_OBSERVED"
    assert got["startup_timeout_proven"] is False
    assert got["acceptance_pass"] is False


def test_after_nav2_ready_corridor_pregoal_and_live_evidence_are_distinct(tmp_path):
    from d06.live.d06_owner_startup_inspect import inspect_run
    run=make_run(tmp_path,status="SMOKE_READY",gates=[
        {"gate":"NAV2_ACTION_READY","status":"PASS"}])
    assert inspect_run(run)["post_startup_phase"]=="NAV2_READY_NEXT_STAGE_NOT_YET_OBSERVED"
    (run/"corridor.log").write_text("CHECKING_MAP_ONLY")
    assert inspect_run(run)["post_startup_phase"]=="CORRIDOR_CHECK_STARTED_OR_FAILED"
    (run/"corridor.json").write_text("{}")
    assert inspect_run(run)["post_startup_phase"]=="CORRIDOR_RESULT_EXISTS_PREG0AL_NOT_VERIFIED"
    (run/"g07_shared_pregoal.log").write_text("LiDAR WAIT NO_GOAL")
    assert inspect_run(run)["post_startup_phase"]=="PHYSICAL_PREG0AL_STARTED_OR_FAILED"
    (run/"g07_shared_pregoal").mkdir()
    (run/"g07_shared_pregoal"/"owner_pregoal_l2.json").write_text(
        json.dumps({"status":"P2_G07_OWNER_PREGOAL_L2_READY_NO_GOAL",
                    "goal_sent":False}))
    assert inspect_run(run)["post_startup_phase"]=="PHYSICAL_PREG0AL_READY_NO_GOAL"
    (run/"live.log").write_text("P2 G07 running")
    assert inspect_run(run)["post_startup_phase"]=="LIVE_OBSERVER_STARTED_GOAL_UNVERIFIED"
    assert inspect_run(run)["goal_sent"] is False


def test_latest_goal_boundary_and_latch_cannot_promote_owner_pass(tmp_path):
    from d06.live.d06_owner_startup_inspect import inspect_run
    run=make_run(tmp_path,status="SMOKE_READY",gates=[
        {"gate":"NAV2_ACTION_READY","status":"PASS"}])
    (run/"live").mkdir()
    (run/"live"/"ci_moving_goal_result.json").write_text(json.dumps({
        "goal_sent":True,"goal_status_at_clear":2,"status":"BLOCKED",
        "first_guard_latch":{"reason":"UPSTREAM_STALE_AFTER_MOTION",
                             "cm_age_sec":0.1815524}}))
    got=inspect_run(run)
    assert got["post_startup_phase"]=="LIVE_GOAL_SENT_BLOCKED_SAFETY_REVIEW"
    assert got["live_goal_sent_reported"] is True
    assert got["first_guard_latch_reason"]=="UPSTREAM_STALE_AFTER_MOTION"
    assert got["acceptance_pass"] is False
    assert got["goal_sent"] is False # this is a NO-GOAL STARTUP probe, not a Goal authority


def test_owner_summary_closes_run_but_not_acceptance(tmp_path):
    from d06.live.d06_owner_startup_inspect import inspect_run
    run=make_run(tmp_path,status="SMOKE_READY",gates=[
        {"gate":"NAV2_ACTION_READY","status":"PASS"}])
    (run.parent/"summary.json").write_text(json.dumps({
        "status":"BLOCKED_G07_RAW_CANDIDATE", "wrapper_rc":2,
        "forced_teardown":False}))
    got=inspect_run(run)
    assert got["post_startup_phase"]=="OWNER_EXIT_RECORDED_REVIEW_REQUIRED"
    assert got["owner_original_status"]=="BLOCKED_G07_RAW_CANDIDATE"
    assert got["owner_wrapper_rc"]==2
    assert got["acceptance_pass"] is False


def test_nonready_and_no_staged_log_cannot_claim_followup(tmp_path):
    from d06.live.d06_owner_startup_inspect import inspect_run
    run=make_run(tmp_path,status="BLOCKED",failed="MAP_AMCL_ACTIVE",gates=[
        {"gate":"CLOCK_READY","status":"PASS"}])
    assert inspect_run(run)["post_startup_phase"]=="NOT_STARTED_OR_NOT_VERIFIED"
    assert inspect_run(tmp_path/"missing")["post_startup_phase"]=="NOT_STARTED_OR_NOT_VERIFIED"
