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
