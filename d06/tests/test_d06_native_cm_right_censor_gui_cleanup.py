"""Public fail-first regression from second Owner: native Guard join,
read-only marker observer clean shutdown, known official Nav2 RViz mesh path.
Only D06 educational visualization changes; no Nav2/CM/Guard/TTL mutation.
"""
from pathlib import Path
from d06.live.d06_guard_cm_first_latch_join import analyze_first_latch,from_original_events
ROOT=Path(__file__).resolve().parents[2]
MONITOR=(ROOT/"d06/live/d06_readonly_monitor.py").read_text()
RVIZ=(ROOT/"d06/rviz/d06_safety_bubble.rviz").read_text()

def test_late_first_consecutive_rmw_source_packet_is_joined_to_native_guard_latch():
    a={"kind":"pre_guard","t":10.3,"rmw_source_ns":100000000000,
       "rmw_received_ns":100001000000,"rmw_publication_seq":126}
    b={"kind":"pre_guard","t":10.523656034,"rmw_source_ns":100184414666,
       "rmw_received_ns":100185358695,"rmw_publication_seq":127}
    sup=[{"kind":"supervised","t":t,"rmw_source_ns":ns}
         for t,ns in ((10.36,100050000000),(10.40,100090000000),
                      (10.44,100130000000),(10.48,100170000000))]
    result={"first_guard_latch":{"reason":"UPSTREAM_STALE_AFTER_MOTION",
            "cm_age_sec":0.169168036,"tick_monotonic":10.469168036,
            "supervisor_fsm":"NORMAL"}}
    proof=from_original_events([a,b,*sup],result)
    assert proof["post_latch_joined_pair"]["upstream_supervisor_publications_during_window"]==4
    got=analyze_first_latch(proof)
    assert got["status"]=="HOLD_CM_SOURCE_GAP_WITH_FIRST_GUARD_LATCH"
    assert got["cm_source_gap_ms"]==184.414666
    assert got["earliest_native_threshold_crossing_ms_before_latch"]==19.168036
    assert got["cm_publisher_interval_gap_confirmed_post_latch"] is True
    assert got["safety_pass"] is False

def test_native_rviz_marker_monitor_handles_ros_context_shutdown_without_traceback():
    assert "ExternalShutdownException" in MONITOR
    assert "except (KeyboardInterrupt, ExternalShutdownException)" in MONITOR
    assert "D06_READONLY_MONITOR_STOPPED" in MONITOR
    assert "create_publisher(Twist" not in MONITOR

def test_rviz_low_load_profile_does_not_request_broken_official_mesh_URIs():
    # Ubuntu24.04 Jazzy official nav2_minimal_tb3_sim has mesh path mismatch
    # (ros-navigation/nav2_minimal_turtlebot_simulation#19). Gazebo keeps Waffle.
    # RViz keeps LaserScan/TF/Odom and safety annotation rings, not true CM state.
    assert "Name: RobotModel" in RVIZ
    assert "Name: RobotModel\n      Enabled: false" in RVIZ
    assert "Frame Rate: 3" in RVIZ
    for token in ("/scan","/odom","/axia/d06/rviz/bubble",
                  "rviz_default_plugins/TF","NOT_OFFICIAL_CM"):
        assert token in RVIZ
