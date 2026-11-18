"""Task02: native Nav2 first-Path failure cannot skip pinned YOLO diagnostic.

Static L0 only. Different CI jobs cannot be fused into a single E2E run.
"""
from pathlib import Path
W=(Path(__file__).resolve().parents[2]/
   ".github/workflows/d08-main-no-goal-real-gazebo-l2.yml")

def test_independent_job_contract():
    txt=W.read_text()
    assert "  gazebo-official-nav2-oneworld:\n    needs: l0-human-proxy-red-green" in txt
    assert "  real-gazebo-rgb-pinned-upstream-yolo-ros:\n    needs: gazebo-contact-positive-once" in txt
    original=txt.split("  gazebo-contact-positive-once:",1)[1].split("  gazebo-official-nav2-oneworld:",1)[0]
    assert "--official-nav2" not in original
    branch=txt.split("  gazebo-official-nav2-oneworld:",1)[1].split("  real-gazebo-rgb-pinned-upstream-yolo-ros:",1)[0]
    assert "--official-nav2" in branch
    assert "D08_OFFICIAL_NAV2_SAME_WORLD_FIRST_PATH_L2_PASS_NO_GOAL" in branch
    assert "amcl_service_ack" in branch and "localization_verified" in branch
    assert "d08-official-nav2-oneworld-l2-evidence" in branch
    assert "D08_OFFICIAL_NAV2_SAME_WORLD_FIRST_PATH_L2_PASS_NO_GOAL" not in original
