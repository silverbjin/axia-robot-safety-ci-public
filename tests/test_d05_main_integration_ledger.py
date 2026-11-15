"""D05 main consolidation PUBLIC static contract, no ROS/Goal or private source."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/D05_MAIN_INTEGRATION_BRANCH_LEDGER_20261115_KO.md"
WF = ROOT / ".github/workflows/d05-main-merge-docs-ci.yml"

def test_all_public_d05_branch_dispositions_documented():
    s = DOC.read_text(encoding="utf-8")
    for key in ("feature/d05-sealed-l0-l1-20261109", "feature/d05-real-rgbd-l2-20261110", "pull/28", "ahead_by=0"):
        assert key in s
    assert "비공개" in s and "UNKNOWN" in s and "NOT_RUN" in s
    assert "0.5초" in s

def test_original_main_d05_source_preserved():
    for f in (
        "scripts/d05_rgbd_gazebo_scene.py",
        "scripts/d05_real_rgbd_l2_gate.py",
        "scripts/d05_rgbd_sensor_preflight.py",
        "scripts/d05_l2_safe_export.py",
        "scripts/axia_d05_rgbd_wsl2_once.sh",
        "tests/test_d05_real_l2_contract.py",
        "tests/test_d05_rgbd_scene.py",
        ".github/workflows/d05-real-rgbd-sensor-preflight.yml",
    ):
        assert (ROOT/f).is_file(), f

def test_public_doc_ci_has_no_private_checkout_or_sealed_environment():
    s = WF.read_text()
    assert "environment: axia-instructor-sealed" not in s
    assert "secrets.AXIA_CLOUD_CI" not in s
    assert "repository: silverbjin/axia-robot-safety-instructor" not in s
    assert "pytest" in s
    assert "NO_ROS_NO_GOAL_NO_PRIVATE_CHECKOUT" in s
