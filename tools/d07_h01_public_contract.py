"""D07-H01 scoped PUBLIC simulation admission. No ROS imports, Goal, or cmd_vel."""
from __future__ import annotations
import math


REQUIRED_ENV = {
    "GITHUB_ACTIONS": "true",
    "AXIA_P0_SIM_ONLY": "1",
    "AXIA_G07_CI_SIM_GOAL_ALLOWED": "1",
    "AXIA_D07_H01_CI_ALLOWED": "1",
    "AXIA_G07_CI_OWNER_BAG_PARITY": "1",
    "AXIA_G07_OWNER_STARTUP_PARITY": "1",
    "ROS_DISTRO": "jazzy",
}
GOAL = (-1.7, 0.7)
REQUIRED_REAL_GEOMETRY = (
    "real_nav2", "real_laser_scan", "path_viable",
    "obstacle_pose_native_ack", "post_ack_scan_stamp_progressed",
    "actual_costmap_obstacle_observed", "path_changed",
    "contact_topic_proven",
)


def admit_h01(env, *, source_sha, checkout_sha, case, goals, goal, geometry_report):
    """Pure independent pre-Goal authorization predicate, not a Goal sender.

    A falsified report cannot replace the live ROS/Gazebo verifier: the latter
    must generate the report from real stamped sensor/Action results.
    """
    if not isinstance(env, dict) or any(env.get(k) != v for k, v in REQUIRED_ENV.items()):
        raise ValueError("D07_H01_NOT_PUBLIC_SIMULATION_CI_SCOPE")
    if not isinstance(env.get("GZ_PARTITION"), str) or not env["GZ_PARTITION"].startswith("axia_p2_"):
        raise ValueError("D07_H01_GAZEBO_PARTITION_NOT_ISOLATED")
    if (
        type(source_sha) is not str or len(source_sha) != 40
        or any(c not in "0123456789abcdef" for c in source_sha)
        or checkout_sha != source_sha
    ):
        raise ValueError("D07_H01_IMMUTABLE_PRIVATE_SOURCE_MISMATCH")
    if case != "D07-H01" or type(goals) is not int or goals != 1:
        raise ValueError("D07_H01_EXACTLY_ONE_CASE_AND_GOAL_REQUIRED")
    if (
        not isinstance(goal, (list, tuple)) or len(goal) != 2
        or any(type(v) not in (int,float) or not math.isfinite(v) for v in goal)
        or tuple(goal) != GOAL
    ):
        raise ValueError("D07_H01_FROZEN_CORRIDOR_GOAL_CHANGED")
    if (
        not isinstance(geometry_report, dict)
        or geometry_report.get("status") != "D07_H01_REAL_NAV2_GEOMETRY_READY_NO_GOAL"
        or geometry_report.get("source_sha") != source_sha
        or geometry_report.get("goal_sent") is not False
        or geometry_report.get("map_frame") != "map"
        or any(geometry_report.get(k) is not True for k in REQUIRED_REAL_GEOMETRY)
    ):
        raise ValueError("D07_H01_REAL_NAV2_DETOUR_NOT_ADMITTED_NO_GOAL")
    return True
