"""CI sync-first release review gate: tests are RED until verifier exists.

No ROS/Gazebo Goal runs. All green paths are explicitly only readiness for
one human-approved Owner L3 run, never formal acceptance or E-Stop.
"""
import copy
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from axia_review_gate import evaluate, PROFILE_MAX_AGE_DAYS

OWNER_SHA = "dedd807884507222e2361f70e31ed47c8b4be7701b751a35e7f4a796ba4dd7b8"
SOURCE_SHA = "a9a33cc32586e4a30843efcf9172bdaade85d8ea"
BASE_SHA = "167027902234202f7a975333759944b7ddbd8ad7"
CI_RUN_SHA = "86c0a8ad6f32b32641f42cc3ba87fb742cd594b4"
RUN_ID=42777095584
ALLOWED_DIFFS=[
    "tests/unit/test_p2_g07_mvp_motion_gate.py",
    "tools/p2_l3_acceptance_contract.py",
    "tools/p2_l3_live_session.py",
]


def fixtures():
    now=datetime(2026,11,10,9,0,tzinfo=timezone.utc)
    profile={"schema":"axia_ros_jazzy_harmonic_env_v1",
             "profile_kind":"wsl2_owner","wsl2_detected":True,
             "captured_utc":"2026-11-10T07:33:26+00:00"}
    run={"id":RUN_ID,"repository_full_name":"silverbjin/axia-robot-safety-ci-public",
         "head_sha":CI_RUN_SHA,"status":"completed","conclusion":"success",
         "created_at":"2026-11-10T07:41:54Z"}
    jobs={"jobs":[{"name":"owner-userspace-parity","conclusion":"success",
         "steps":[
            {"name":"Install official Jazzy/Harmonic dependencies once; pin exact Owner apt core; compare versions and hashes","conclusion":"success"},
            {"name":"Checkout EXACT private P1+P2 source after parity","conclusion":"success"},
            {"name":"Actual Gazebo Harmonic physical clear slow stop with P1+P2 startup (NO Goal)","conclusion":"success"},
         ]}]}
    provenance={"owner_profile_sha256":OWNER_SHA,
                "profile_age_days":1,
                "checked_source_sha":SOURCE_SHA,
                "attested_source_sha":BASE_SHA,
                "actual_source_changes":ALLOWED_DIFFS,
                "parity_run_id":RUN_ID,
                "parity_run_head_sha":CI_RUN_SHA,
                "parity_run_owner_profile_sha256":OWNER_SHA,
                "formal_g07_accepted":False,
                "moving_goal_proven":False,
                "certified_estop":False}
    return now,profile,run,jobs,provenance


def verdict(*,patch=None,profile_patch=None,run_patch=None,jobs_patch=None,now=None):
    clock,p,r,j,pr=fixtures()
    if patch:pr.update(patch)
    if profile_patch:p.update(profile_patch)
    if run_patch:r.update(run_patch)
    if jobs_patch:j.update(jobs_patch)
    return evaluate(owner_profile=p,run=r,jobs=j,provenance=pr,
                    now=now or clock)


def test_verified_sync_first_allows_only_owner_candidate():
    r=verdict()
    assert r['status']=="OWNER_L3_CANDIDATE"
    assert r['sync_status']=="VERIFIED"
    assert r['no_goal_l2_proven'] is True
    assert r['moving_goal_proven'] is False
    assert r['formal_g07_accepted'] is False
    assert r['certified_estop'] is False


@pytest.mark.parametrize("patch",[
    {"owner_profile_sha256":"0"*64},
    {"parity_run_owner_profile_sha256":"0"*64},
    {"parity_run_id":123},
    {"parity_run_head_sha":"1"*40},
    {"checked_source_sha":"1"*40},
    {"attested_source_sha":"1"*40},
    {"actual_source_changes":["ros2_ws/src/axia_safety_bringup/launch/axia_tb3_p2.launch.py"]},
    {"actual_source_changes":["configs/p2_collision_monitor_zones.yaml"]},
    {"actual_source_changes":[]},
    {"actual_source_changes":["tools/p2_l3_live_session.py","scripts/p2_owner_l3_wsl2.sh"]},
    {"moving_goal_proven":True},
    {"certified_estop":True},
    {"formal_g07_accepted":True},
])
def test_stale_wrong_sha_or_unsafe_delta_never_ready(patch):
    assert verdict(patch=patch)['status']=="HOLD"


@pytest.mark.parametrize("run_patch",[
    {"conclusion":"failure"},{"status":"in_progress"},
    {"head_sha":"f"*40},{"id":1234},{"created_at":"2026-11-09T00:00:00Z"},
])
def test_incomplete_wrong_or_pre_capture_parity_run_blocks(run_patch):
    assert verdict(run_patch=run_patch)['status']=="HOLD"


def test_missing_or_failed_actual_l2_or_parity_step_blocks():
    for idx in range(3):
        _,p,r,j,pr=fixtures()
        j["jobs"][0]["steps"][idx]["conclusion"]="failure"
        assert evaluate(owner_profile=p,run=r,jobs=j,
                        provenance=pr,now=datetime(2026,11,10,9,tzinfo=timezone.utc))['status']=="HOLD"
    assert verdict(jobs_patch={"jobs":[]})['status']=="HOLD"


def test_recheck_is_required_after_profile_expires():
    clock=datetime(2026,11,10,9,tzinfo=timezone.utc)
    assert PROFILE_MAX_AGE_DAYS <= 14
    assert verdict(now=clock+timedelta(days=PROFILE_MAX_AGE_DAYS+2))['status']=="HOLD"


def test_invalid_environment_provenance_blocks():
    assert verdict(profile_patch={"wsl2_detected":False})['status']=="HOLD"
    assert verdict(profile_patch={"schema":"unknown"})['status']=="HOLD"


def test_no_free_revalidation_by_new_pytest_count():
    from pathlib import Path
    p=Path(__file__).resolve().parents[1]/"scripts/axia_ci_review_preflight.sh"
    s=p.read_text()
    assert 'axia_review_gate.py' in s
    assert 'tests/unit/test_p2_g07_mvp_motion_gate.py' in s
    assert 'tests/unit/test_p2_mvp_one_goal_timing.py' in s
    assert 'tests/unit/test_p2_g07_live_phase.py' in s
    assert 'tests/unit/test_p2_evidence_oracles.py' in s
    assert 'AXIA_CI_SYNC_FIRST' in s
    assert 'G07_MVP_PRE_OWNER_GATE_OK' in s
