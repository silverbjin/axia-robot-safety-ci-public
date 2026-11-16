"""Nonprivileged contract for Owner-admin Instructor Actions closeout.

Public CI must never disable private Actions or delete Instructor branches itself.
"""
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "axia_instructor_admin_closeout_once.sh"


def test_admin_one_shot_exists_and_has_safe_no_network_self_check():
    assert RUNNER.is_file()
    assert subprocess.run(["bash", "-n", str(RUNNER)], capture_output=True).returncode == 0
    proc = subprocess.run(["bash", str(RUNNER), "--self-check"], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "AXIA_INSTRUCTOR_ADMIN_SELF_CHECK_PASS_NO_MUTATION" in proc.stdout


def test_admin_closeout_targets_only_authorized_private_repo_and_one_merge():
    src = RUNNER.read_text()
    assert 'REPO="silverbjin/axia-robot-safety-instructor"' in src
    assert 'BRANCH="plan/block-c-d09-d12-freeze-20261115"' in src
    assert 'MERGE="d1f10b220143b4138c260768a59c35b6166abfe1"' in src
    assert 'pulls/184' in src
    assert 'git/commits/$MERGE' in src
    assert 'git/refs/heads/$BRANCH' in src
    assert "gh api --method PUT" in src
    assert "gh api --method DELETE" in src
    for forbidden in ("PRIVATE_TOKEN=", "GITHUB_TOKEN=", "ros2 action send_goal", "pkill", "git reset --hard"):
        assert forbidden not in src


def test_admin_requires_verified_actions_disabled_before_success():
    src = RUNNER.read_text()
    assert "AXIA_INSTRUCTOR_ACTIONS_DISABLED_VERIFIED" in src
    assert "AXIA_INSTRUCTOR_MERGED_BRANCH_DELETED" in src
    assert "AXIA_INSTRUCTOR_ADMIN_COMPLETE" in src
    assert "enabled=false" in src


def test_admin_fails_closed_on_moved_branch_without_mutating(tmp_path):
    fake = tmp_path / "gh"
    fake.write_text("""#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$FAKE_GH_LOG"
case "$*" in
  "auth status --hostname github.com") exit 0 ;;
  "api repos/silverbjin/axia-robot-safety-instructor --jq .private") echo true; exit 0 ;;
  "api repos/silverbjin/axia-robot-safety-instructor/pulls/184 --jq .merged") echo true; exit 0 ;;
  "api repos/silverbjin/axia-robot-safety-instructor/git/commits/d1f10b220143b4138c260768a59c35b6166abfe1 --jq .parents[1].sha") echo e2b97089239f6a444056d142e752de5591c93757; exit 0 ;;
  "api repos/silverbjin/axia-robot-safety-instructor/branches/plan/block-c-d09-d12-freeze-20261115 --jq .commit.sha") echo 0000000000000000000000000000000000000001; exit 0 ;;
  "api repos/silverbjin/axia-robot-safety-instructor/actions/permissions --jq .enabled") echo true; exit 0 ;;
  *) exit 3 ;;
esac
""")
    fake.chmod(0o755)
    log = tmp_path / "calls.log"
    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env['PATH']}"
    env["FAKE_GH_LOG"] = str(log)
    result = subprocess.run(["bash", str(RUNNER), "--run"], env=env, text=True, capture_output=True)
    assert result.returncode != 0
    assert "AXIA_INSTRUCTOR_ADMIN_HOLD_BRANCH_SHA_CHANGED" in result.stdout + result.stderr
    called = log.read_text()
    assert "--method PUT" not in called
    assert "--method DELETE" not in called
