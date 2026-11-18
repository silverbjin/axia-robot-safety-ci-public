"""D08 Task04 RED: CI PR synthetic merge checkout must not differ from Owner SHA.

Only L0 release contract; true no-Goal Gazebo/RViz stays L2/Owner L3.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
W=ROOT/".github/workflows/d08-main-no-goal-real-gazebo-l2.yml"
RUNNER=ROOT/"d08/scripts/d08_public_gazebo_l2.py"
OWNER=ROOT/"d08/scripts/d08_owner_no_goal_bootstrap.sh"

def test_same_exact_source_sha_in_public_pr_ci_and_owner_checkout():
    workflow=W.read_text()
    exact="${{ github.event.pull_request.head.sha || github.sha }}"
    assert workflow.count("ref: "+exact)==4
    assert "AXIA_D08_EXACT_SOURCE_SHA: "+exact in workflow
    runner=RUNNER.read_text()
    assert "env.get('AXIA_D08_EXACT_SOURCE_SHA')" in runner
    assert "D08_GITHUB_EVENT_SHA_CHECKOUT_MISMATCH" in runner
    assert 'export AXIA_D08_EXACT_SOURCE_SHA="$SHA"' in OWNER.read_text()

def test_owner_gui_cycle_failure_after_before_pass_cannot_return_success():
    s=RUNNER.read_text()
    assert "result['status']='D08_REAL_GAZEBO_WAFFLE_RGBD_NO_GOAL_PASS'" in s
    assert "except Exception as exc:\n        result['status']='BLOCKED'" in s
    assert "return 0 if result['status']=='D08_REAL_GAZEBO_WAFFLE_RGBD_NO_GOAL_PASS' else 2" in s
