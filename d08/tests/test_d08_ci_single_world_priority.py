"""D08 L0 RED CI priority: reuse prior standalone native Nav2 L2 proven.

A push needs one exact-SHA combined Gazebo/Nav2/YOLO/D05 L2; the already
successful standalone first-Path job is opt-in diagnosis, not a duplicated
flaky release gate. NEVER waive the combined actual-world job.
"""
from pathlib import Path
WF=Path(__file__).resolve().parents[2]/".github/workflows/d08-main-no-goal-real-gazebo-l2.yml"

def test_standalone_nav2_is_manual_diagnostic_only_while_combined_e2e_is_required():
    s=WF.read_text()
    nav=s.split("  gazebo-official-nav2-oneworld:",1)[1].split(
        "  real-gazebo-rgb-pinned-upstream-yolo-ros:",1)[0]
    combined=s.split("  real-gazebo-rgb-pinned-upstream-yolo-ros:",1)[1]
    assert "if: github.event_name == 'workflow_dispatch'" in nav
    assert "--official-nav2 --official-path-phases --live-person-range" in combined
    assert "D08_REAL_LIVE_RGBD_YOLO_D05_NAV2_THREE_PATHS_L2_PASS_NO_GOAL" in combined
    assert "if: github.event_name == 'workflow_dispatch'" not in combined
