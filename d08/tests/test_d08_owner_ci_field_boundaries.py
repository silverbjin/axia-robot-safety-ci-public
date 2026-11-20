"""Owner WSLg Intel GPU + first receive gap + CM ACTIVE readiness.
L0 regression only; actual Jazzy/Gazebo L2 mandatory for release.
"""
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"d08/harness"))
sys.path.insert(0,str(ROOT/"d08/tests"))
from d08_amcl_initial_pose import summarize_actual_receive_history
from d08_same_world_replan import cm_state_is_active

def test_owner_sparse_real_scan_reproducer_is_custodied_not_forged():
    sparse={"scan":[(100.0,1_000_000_000),(100.82,1_100_000_000)],
            "odom":[(100.0,1_000_000_000),(100.75,1_100_000_000)],
            "clock":[(100.0,1_000_000_000),(100.8,1_060_000_000)]}
    report=summarize_actual_receive_history(sparse,now=119.0,started_at=99.0)
    assert report["status"]=="D08_REAL_RX_DIAGNOSTIC_NOT_SAFETY_PASS"
    assert report["scan"]["callback_count"]==2
    assert report["scan"]["max_host_receive_gap_sec"]==.82
    assert report["scan"]["latest_receive_age_sec"]>.5
    assert report["clock"]["observed_sim_time_progress_sec"]==.06
    assert report["clock"]["observed_rtf"]<.1
    assert report["publisher_rmw_cadence_measured"] is False
    assert report["control_published"] is False
    with pytest.raises(ValueError,match="INSUFFICIENT_REAL_CALLBACKS"):
        from d08_amcl_initial_pose import assess_pre_goal_receive_recovery
        assess_pre_goal_receive_recovery(sparse,started_at=99.0,now=119.0)

def test_native_cm_transitional_state_requires_real_active_not_fake():
    for state_id,label in [(0,'unknown'),(1,'unconfigured'),(2,'inactive'),
                           (3,'activating'),(4,'finalized')]:
        assert cm_state_is_active(state_id,label) is False
    assert cm_state_is_active(3,'active') is True
    assert cm_state_is_active(3,'inactive') is False

def test_owner_gpu_precheck_and_timing_capture_in_real_runner():
    s=(ROOT/'d08/scripts/d08_owner_no_goal_bootstrap.sh').read_text()
    assert 'MESA_D3D12_DEFAULT_ADAPTER_NAME' in s
    assert 'D08_OWNER_WSLG_NVIDIA_D3D12_VERIFIED' in s
    assert 'D08_OWNER_WSLG_NVIDIA_D3D12_NOT_AVAILABLE' in s
    src=(ROOT/'d08/harness/d08_amcl_initial_pose.py').read_text()
    assert 'amcl_receive_timing.json' in (ROOT/'d08/harness/d08_nav2_path_preflight.py').read_text()
    assert 'D08_AMCL_REAL_RX_CADENCE_FIRST_FAILURE' in src
    assert 'AXIA_D08_CI_REAL_SUBSCRIBER_PAUSE_SEC' in src
    assert 'callback_receive_limit_sec":.5' in src
    assert 'create_publisher(' not in src

def test_same_source_real_nav2_ci_must_exercise_recovered_gap():
    workflow=(ROOT/'.github/workflows/d08-main-no-goal-real-gazebo-l2.yml').read_text()
    assert 'AXIA_D08_CI_REAL_SUBSCRIBER_PAUSE_SEC: "0.65"' in workflow
    assert "D08_ACTUAL_NO_GOAL_INITIAL_RECEIVE_GAP_RECOVERED_WITH_REAL_STREAM" in workflow
    assert "assert a['startup_gap_recovered_no_goal'] is True" in workflow
    assert "D08_REAL_RX_DIAGNOSTIC_NOT_SAFETY_PASS" in workflow
    src=(ROOT/'d08/harness/d08_same_world_replan.py').read_text()
    assert 'D08_OFFICIAL_CM_ACTIVATION_NOT_READY' in src
    assert 'cm_state_is_active(' in src


def test_real_runtime_deque_not_rejected_as_insufficient_scan_callbacks():
    from collections import deque
    from test_d08_owner_first_scan_odom_gap_regression import recovered
    from d08_amcl_initial_pose import assess_pre_goal_receive_recovery
    actual_buffers={k:deque(v,maxlen=200) for k,v in recovered().items()}
    assert len(actual_buffers['scan'])>=6
    report=assess_pre_goal_receive_recovery(
        actual_buffers,started_at=28430.,now=28433.49)
    assert report['status']=='D08_NO_GOAL_REAL_RX_RECOVERED'
    assert report['historical_first_gaps']['scan']['gap_sec']==.819491


def test_clock_callback_sampling_preserves_one_second_recovery_window_and_gap():
    from collections import deque
    from d08_amcl_initial_pose import append_clock_sample
    samples=deque(maxlen=200)
    # Actual public ROS L2 clock: 200 records span only ~0.6s at 3ms cadence.
    for i in range(600):
        append_clock_sample(samples,now=i*.003,stamp_ns=1_000_000_000+i*3_000_000)
    assert len(samples)<=100
    assert len(samples)>=50
    assert samples[-1][0]-samples[0][0]>=1.5
    # Do not hide a fresh 650ms callback pause by decimating /clock.
    before=samples[-1][0]
    assert append_clock_sample(samples,now=before+.65,
        stamp_ns=samples[-1][1]+650_000_000) is True
    assert samples[-1][0]-samples[-2][0]>=.5
