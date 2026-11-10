"""Native Jazzy CM SIGSEGV crash cannot be disguised as clean pass."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'d08/harness'))
from p2_teardown_audit import assess_teardown_log

REAL='''[INFO] [collision_monitor-18]: Destroying Scan
[ERROR] [collision_monitor-18]: process has died [pid 11908, exit code -11, cmd '/opt/ros/jazzy/lib/nav2_collision_monitor/collision_monitor'].
'''
def test_actual_owner_native_cm_shutdown_segfault_is_detected():
    v=assess_teardown_log(REAL)
    assert v['collision_monitor_exit_minus11'] is True
    assert v['teardown_status']=='CM_SIGSEGV_OBSERVED'
    assert v['clean_shutdown_certified'] is False
    assert v['certified_estop'] is False

def test_unrelated_ros_failure_not_mislabeled_cm_crash():
    v=assess_teardown_log('[ERROR] [controller_server-4]: process has died [pid 88, exit code -11, cmd x]')
    assert v['collision_monitor_exit_minus11'] is False
    assert v['clean_shutdown_certified'] is False
    assert 'NOT_SEEN' in v['teardown_status']

def test_no_native_log_does_not_certify_clean_teardown():
    assert assess_teardown_log('')['clean_shutdown_certified'] is False
