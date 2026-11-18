"""Conservative AXIA component-readiness classifier; NOT formal G06/G07 acceptance.

Sealed facts are from separately reviewed real CI and owner evidence. It does
NOT run ROS, Gazebo or a Goal, and cannot claim integrated live behavior.
"""
import copy
import json

PRIVATE_SHA = "1216d8589b2a8ac4c7e75aedaa7854eb7b2470b3"
G07_L2_RUN = 42754104452
CM_L1_RUN = 42656227824

VERIFIED_COMPONENT_EVIDENCE = {
    "profile": "AXIA_SIMULATION_ONLY_MVP",
    "p1_lkg_ref": "AXIA_P1_R08_FINAL_ACCEPTANCE_REPORT_20261108_KO.md",
    "g07_l2": {
        "private_sha": PRIVATE_SHA, "run_id": G07_L2_RUN,
        "ros": "jazzy", "gazebo": "harmonic",
        "actual_gazebo": True, "set_pose_ack": True,
        "laser_before_m": 1.4135154485702515,
        "laser_after_m": 0.3922160565853119,
        "goal_sent": False, "collision_ground_truth": False,
    },
    "cm_l1": {
        "run_id": CM_L1_RUN, "ros": "jazzy", "actual_ros": True,
        "gazebo_actual": False,
        "clear_front_m": 1.20, "clear_output_mps": 0.20,
        "slow_front_m": 0.65, "slow_output_mps": 0.06,
        "stop_front_m": 0.30, "stop_output_mps": 0.00,
    },
}


def assess(evidence):
    """Only returns component readiness or HOLD; never a formal PASS."""
    result = {
        "status": "HOLD", "scope": "SIMULATION_ONLY_MVP",
        "g06_retest_required": False, "g07_integrated_goal_e2e": False,
        "collision_ground_truth": False, "mvp_demo_observed": False,
        "formal_gate_accepted": False, "certified_estop": False,
        "explanation": "Independent ROS L1 and Gazebo L2 components only; one-session Goal not verified",
    }
    if not isinstance(evidence, dict):
        return result
    if any(evidence.get(k) is True for k in (
            "mvp_demo_observed", "formal_gate_accepted", "certified_estop")):
        return result
    if evidence.get("profile") != "AXIA_SIMULATION_ONLY_MVP":
        return result
    if evidence.get("p1_lkg_ref") != VERIFIED_COMPONENT_EVIDENCE["p1_lkg_ref"]:
        return result
    l2 = evidence.get("g07_l2")
    l1 = evidence.get("cm_l1")
    if not isinstance(l2, dict) or not isinstance(l1, dict):
        return result
    if any(l2.get(k) != v for k, v in (
        ("private_sha", PRIVATE_SHA), ("run_id", G07_L2_RUN),
        ("ros", "jazzy"), ("gazebo", "harmonic"),
        ("actual_gazebo", True), ("set_pose_ack", True),
        ("goal_sent", False), ("collision_ground_truth", False),
    )):
        return result
    if any(l1.get(k) != v for k, v in (
        ("run_id", CM_L1_RUN), ("ros", "jazzy"),
        ("actual_ros", True), ("gazebo_actual", False),
    )):
        return result
    fields = ("laser_before_m", "laser_after_m")
    if any(type(l2.get(k)) not in (float, int) for k in fields):
        return result
    before, after = (l2[k] for k in fields)
    if not (0.55 < before <= 8 and 0.14 <= after <= 0.53
            and before - after >= 0.10):
        return result
    keys = ("clear_front_m", "clear_output_mps", "slow_front_m",
            "slow_output_mps", "stop_front_m", "stop_output_mps")
    if any(type(l1.get(k)) not in (float, int) for k in keys):
        return result
    try:
        if not (l1["clear_front_m"] > .75 and
                .4 < l1["slow_front_m"] < .75 and
                0 < l1["stop_front_m"] < .4 and
                l1["clear_output_mps"] > .03 and
                0 <= l1["slow_output_mps"] <= .30 * l1["clear_output_mps"] + .01 and
                abs(l1["stop_output_mps"]) < .01):
            return result
    except (ArithmeticError, ValueError):
        return result
    result["status"] = "MVP_DEMO_COMPONENT_READY"
    return result


def main():
    print(json.dumps(assess(copy.deepcopy(VERIFIED_COMPONENT_EVIDENCE)),
                     ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
