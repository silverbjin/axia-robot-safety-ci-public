"""First ROS receive gap from real LaserScan callbacks; no synthetic scan."""
from __future__ import annotations

def first_scan_receive_gap(samples, limit_s=0.5):
    """samples: [(host_monotonic_receive_sec, ROS_sim_header_stamp_ns)].

    Header delta records SIM time, not actual Gazebo RMW send or ROS receiver
    transport; requires separate publisher observation for source attribution.
    """
    for i,(before,after) in enumerate(zip(samples,samples[1:]),start=1):
        wall=float(after[0])-float(before[0])
        sim=(int(after[1])-int(before[1]))/1e9
        if wall>=limit_s:
            return {
                "kind":"ROS_LASERSCAN_FIRST_RECEIVE_GAP",
                "sample_index":i,
                "receive_gap_sec":round(wall,6),
                "header_sim_gap_sec":round(sim,6),
                "previous_ros_stamp_ns":int(before[1]),
                "current_ros_stamp_ns":int(after[1]),
                "previous_host_monotonic_sec":round(float(before[0]),6),
                "current_host_monotonic_sec":round(float(after[0]),6),
                "limit_sec":limit_s,
                "publisher_rmw_gap_measured":False,
                "clock_receive_gap_measured":False,
                "not_proven_source_vs_transport":True,
            }
    return None
