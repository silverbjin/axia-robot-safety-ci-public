"""Regression: do not send SIGINT to all Nav2 nodes while CM is active.

Owner EEUOfVQL launch.log: CM cleaning-up intersects TF extrapolation, followed
by -11. Test the opt-in D08 teardown *order*, not native crash disappearance.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def test_owner_source_refuses_to_relabel_sigsegv_as_success():
    # Public copy of the only permitted shutdown contract. Native ROS stack
    # is NOT run in this test and a pass does not certify crash resolution.
    path=ROOT/'d08/harness/d08_orderly_nav2_shutdown_contract.txt'
    text=path.read_text()
    assert "lifecycle_manager_navigation/manage_nodes" in text
    assert "nav2_msgs/srv/ManageLifecycleNodes" in text
    assert "{command: 4}" in text
    assert "G07_D08_ONLY" in text
    assert "PRIOR_TO_GROUP_SIGINT" in text
    assert "CM_SIGSEGV_STILL_AUDITED" in text
