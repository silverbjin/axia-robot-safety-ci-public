"""D06 G07 real-L2 #43676192483 BLOCKED first phase must be public and redacted.

Sanitized source-only reproduction; never publish private G07 reason, path,
Goal UUID, rosbag message or evidence. A diagnostic cannot admit Owner L3.
"""
import json
from d06.live.d06_ci_first_goal_block import classify_first_goal_block


def test_timed_out_goal_stage_classified_without_leaking_raw_reason():
    data = {"status": "BLOCKED", "goal_sent": True,
            "reason": "RuntimeError:CI_MOVING_GOAL_TIMEOUT_SLOW /home/private/Goal-UUID"}
    result = classify_first_goal_block(data)
    assert result["status"] == "HOLD_G07_FIRST_GOAL_PHASE_BLOCK"
    assert result["first_failed_phase"] == "SLOW"
    assert result["failure_class"] == "PHASE_TIMEOUT"
    assert result["native_guard_latch_observed"] is False
    assert result["owner_l3_accepted"] is False
    assert result["safety_pass"] is False
    assert "/home/" not in json.dumps(result)
    assert "Goal-UUID" not in json.dumps(result)


def test_first_guard_latch_takes_precedence_over_terminal_timeout():
    data = {"status": "BLOCKED", "goal_sent": True,
            "reason": "RuntimeError:CI_MOVING_GOAL_TIMEOUT_STOP",
            "first_guard_latch": {"reason": "UPSTREAM_STALE_AFTER_MOTION",
                                  "cm_age_sec": 0.169168036}}
    result = classify_first_goal_block(data)
    assert result["status"] == "HOLD_G07_FIRST_NATIVE_GUARD_LATCH"
    assert result["native_guard_latch_observed"] is True
    assert result["first_native_transition"] == "UPSTREAM_STALE_AFTER_MOTION"
    assert result["failure_class"] == "NATIVE_GUARD_FIRST"
    assert result["owner_l3_accepted"] is False


def test_missing_or_unknown_reason_is_unverified_not_safety_pass():
    for data in (None, {}, {"status": "BLOCKED", "goal_sent": True,
                             "reason": "ValueError:/home/private/raw-bag.db3"},
                 {"status": "BLOCKED", "goal_sent": False,
                  "reason": "RuntimeError:CI_MOVING_GOAL_TIMEOUT_CLEAR"}):
        result = classify_first_goal_block(data)
        assert result["safety_pass"] is False
        assert result["owner_l3_accepted"] is False
        assert result["certified_estop"] is False
        assert result["first_failed_phase"] is None
        assert "/home/" not in json.dumps(result)


def test_original_oracle_blocked_not_promoted_by_healthy_rmw_publication():
    data = {"status": "BLOCKED", "goal_sent": True,
            "reason": "RuntimeError:ACTUAL_MOVING_GOAL_CI_ORACLE_SOURCE_TTL",
            "guard_latched": False,
            "max_cm_interval_sec": 0.091306}
    result = classify_first_goal_block(data)
    assert result["status"] == "HOLD_G07_FIRST_GOAL_PHASE_BLOCK"
    assert result["failure_class"] == "ORIGINAL_ORACLE_REJECTION"
    assert result["first_failed_phase"] == "ORACLE"
    assert result["safety_pass"] is False


def test_goal_terminated_phase_is_not_silently_accepted():
    data = {"status": "BLOCKED", "goal_sent": True,
            "reason": "RuntimeError:GOAL_TERMINATED_DURING_CLEAR:4"}
    result = classify_first_goal_block(data)
    assert result["first_failed_phase"] == "CLEAR"
    assert result["failure_class"] == "GOAL_TERMINATED"
    assert result["owner_l3_accepted"] is False
