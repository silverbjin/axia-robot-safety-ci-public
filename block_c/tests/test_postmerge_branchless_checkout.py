"""Regression: post-release branch pruning must not break accepted Owner source retrieval.

Real Public CI C01 Owner runner performs the actual Git clone/fetch.
Full Instructor clone remains private to Owner WSL2.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / "scripts" / "axia_block_c_owner_final_once.sh"
C01 = ROOT / "scripts" / "axia_c01_owner_wsl2_once.sh"


def test_c01_clone_uses_permanent_main_not_deleted_feature_branch():
    source = C01.read_text(encoding="utf-8")
    assert "STUDENT_BRANCH=main" in source
    assert "feat/block-c-c01-synthetic-20261115" not in source
    assert 'git -C "$SOURCE" fetch --quiet --depth 1 origin "$PINNED_STUDENT_SHA"' in source
    assert 'git -C "$SOURCE" checkout --quiet --detach "$PINNED_STUDENT_SHA"' in source


def test_full_owner_clone_uses_permanent_main_for_both_repos():
    source = OWNER.read_text(encoding="utf-8")
    assert "INSTRUCTOR_BRANCH=main" in source
    assert "STUDENT_BRANCH=main" in source
    assert "plan/block-c-d09-d12-freeze-20261115" not in source
    assert "feat/block-c-c01-synthetic-20261115" not in source
    for name, pinned in [("INSTRUCTOR", "INSTRUCTOR_SHA"), ("STUDENT", "STUDENT_SHA")]:
        assert f'git -C "${name}" fetch --quiet --depth 1 origin "${pinned}"' in source
        assert f'git -C "${name}" checkout --quiet --detach "${pinned}"' in source


def test_public_wsl2_contract_is_still_fail_closed_and_no_motion():
    source = OWNER.read_text(encoding="utf-8")
    assert "run_step MANIFEST_SHA_AND_PARITY check_manifests_and_source_parity" in source
    assert "BLOCK_C_OWNER_ACCEPTED=READY_FOR_OWNER_APPROVAL" in source
    assert "BLOCK_C_RELEASE_APPROVED=false" in source
    assert "git reset --hard" not in source
    assert "ros2 action send_goal" not in source
