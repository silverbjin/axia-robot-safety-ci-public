"""Official Nav2 Jazzy lifecycle transition-log first-failure regression.
Synthetic sanitized samples; no Goal, ROS, private trace or timeout changes.
"""
from d06.live.d06_nav2_native_shutdown_log_boundary import inspect_native_shutdown

def test_navigation_timeout_tracks_last_requested_node_not_proven_root_cause():
    log="""[lifecycle_manager_navigation] Shutting down managed nodes...
[lifecycle_manager_navigation] Deactivating velocity_smoother
[lifecycle_manager_navigation] Deactivating collision_monitor
user private /home/solution hidden
"""
    native={"status":"BLOCKED_LIFECYCLE_NAVIGATION_SERVICE_TIMEOUT",
            "navigation_ack":False,"navigation_elapsed_sec":40.00048}
    r=inspect_native_shutdown(log,native)
    assert r["status"]=="HOLD_NAV2_NATIVE_MANAGER_TRANSITION_UNVERIFIED"
    assert r["failed_manager"]=="navigation"
    assert r["last_requested_node"]=="collision_monitor"
    assert r["last_requested_action"]=="Deactivating"
    assert r["manager_completion_message_seen"] is False
    assert r["blocked_node_proven"] is False
    assert r["owner_l3_accepted"] is False
    assert "/home/" not in str(r)

def test_manager_completed_log_but_client_timeout_is_not_success():
    log="""[lifecycle_manager_navigation] Shutting down managed nodes...
[lifecycle_manager_navigation] Shutting down controller_server
[lifecycle_manager_navigation] Managed nodes have been shut down
"""
    r=inspect_native_shutdown(log,{"status":"BLOCKED_LIFECYCLE_NAVIGATION_SERVICE_TIMEOUT"})
    assert r["status"]=="HOLD_NATIVE_ACK_UNVERIFIED_AFTER_MANAGER_COMPLETION_LOG"
    assert r["manager_completion_message_seen"] is True
    assert r["safety_pass"] is False

def test_localization_manager_own_progress_not_confused_with_navigation():
    log="""[lifecycle_manager_navigation] Shutting down bt_navigator
[lifecycle_manager_localization] Shutting down managed nodes...
[lifecycle_manager_localization] Deactivating amcl
"""
    r=inspect_native_shutdown(log,{"status":"BLOCKED_LIFECYCLE_LOCALIZATION_SERVICE_TIMEOUT"})
    assert r["failed_manager"]=="localization"
    assert r["last_requested_node"]=="amcl"
    assert r["last_requested_action"]=="Deactivating"

def test_missing_or_unsafe_node_detail_stays_unknown():
    r=inspect_native_shutdown("private RMW log /tmp/keys",{
        "status":"BLOCKED_LIFECYCLE_NAVIGATION_SERVICE_TIMEOUT"})
    assert r["last_requested_node"] is None
    assert r["manager_completion_message_seen"] is False
    assert r["safety_pass"] is False
