"""Public CI-only authorization contract for one nominal AXIA P3 S01 SIM goal.

L0 scope check. Owner manual TTY authority is a separate system and cannot
be simulated by setting this environment. No ROS/Nav2/Gazebo here.
"""
import re

HEX40 = re.compile(r"[0-9a-f]{40}\Z")
EXPECTED_ENV = {
    "GITHUB_ACTIONS": "true",
    "AXIA_P0_SIM_ONLY": "1",
    "AXIA_P3_S01_CI_GOAL_ALLOWED": "1",
    "ROS_DISTRO": "jazzy",
}


def admit_s01(env, *, source_sha, checkout_sha, case, goals, goal):
    if not isinstance(env, dict):
        raise ValueError("INVALID_ENV")
    for name, value in EXPECTED_ENV.items():
        if env.get(name) != value:
            raise ValueError("S01_SIM_SCOPE_DENIED_" + name)
    if not isinstance(env.get("GZ_PARTITION"), str) or not env["GZ_PARTITION"].startswith("axia_p2_"):
        raise ValueError("NO_ISOLATED_GAZEBO_PARTITION")
    if (not isinstance(source_sha, str) or not HEX40.fullmatch(source_sha)
            or checkout_sha != source_sha):
        raise ValueError("EXACT_IMMUTABLE_PRIVATE_SOURCE_REQUIRED")
    if case != "S01" or type(goals) is not int or goals != 1:
        raise ValueError("ONLY_ONE_NOMINAL_S01_GOAL_ALLOWED")
    if (not isinstance(goal, (tuple, list)) or len(goal) != 2
            or tuple(goal) != (-1.6, -0.5)):
        raise ValueError("UNAUTHORIZED_GOAL_COORDINATES")
    return True




def admit_s05(env, *, source_sha, checkout_sha, case, goals, goal, operations):
    """One CI SIM-only S05 SW Stop/Reset/Rearm, NOT human Owner authority."""
    if not isinstance(env, dict):
        raise ValueError("INVALID_ENV")
    required={
        "GITHUB_ACTIONS":"true","AXIA_P0_SIM_ONLY":"1",
        "ROS_DISTRO":"jazzy","AXIA_P3_S05_CI_GOAL_ALLOWED":"1",
    }
    for k,v in required.items():
        if env.get(k)!=v:
            raise ValueError("S05_SIM_SCOPE_DENIED_"+k)
    if not isinstance(env.get("GZ_PARTITION"),str) or not env["GZ_PARTITION"].startswith("axia_p2_"):
        raise ValueError("S05_PARTITION_NOT_ISOLATED")
    if not isinstance(source_sha,str) or not HEX40.fullmatch(source_sha) or checkout_sha!=source_sha:
        raise ValueError("EXACT_S05_PRIVATE_SOURCE_REQUIRED")
    if case!="S05" or type(goals) is not int or goals!=1:
        raise ValueError("S05_ONLY_ONE_GOAL")
    if not isinstance(goal,(list,tuple)) or tuple(goal)!=(-1.7,.7):
        raise ValueError("S05_NON_APPROVED_G07_LONG_CORRIDOR")
    if tuple(operations)!=("sw_stop","rearm_denied","reset","rearm"):
        raise ValueError("S05_NO_FAULT_CRASH_OR_SECOND_GOAL_ALLOWED")
    return True



def admit_s03(env, *, source_sha, checkout_sha, case, goals, goal,
              operations, cm_killed):
    """Only a bounded SIGSTOP/SIGCONT in isolated public Gazebo S03.

    Does NOT authorize a real CM SIGKILL or Owner /dev/tty workflow.
    """
    if not isinstance(env,dict):
        raise ValueError("INVALID_S03_ENV")
    required={
        "GITHUB_ACTIONS":"true","AXIA_P0_SIM_ONLY":"1",
        "ROS_DISTRO":"jazzy",
        "AXIA_P3_S03_CI_COMPOUND_ALLOWED":"1",
        "AXIA_P3_S03_CI_CM_PAUSE_ALLOWED":"1",
    }
    for key,value in required.items():
        if env.get(key)!=value:
            raise ValueError("S03_SCOPED_SIM_ONLY_"+key)
    if not isinstance(env.get("GZ_PARTITION"),str) or not env["GZ_PARTITION"].startswith("axia_p2_"):
        raise ValueError("S03_GAZEBO_PARTITION_NOT_ISOLATED")
    if not isinstance(source_sha,str) or not HEX40.fullmatch(source_sha) or checkout_sha!=source_sha:
        raise ValueError("S03_IMMUTABLE_PRIVATE_SHA_REQUIRED")
    if case!="S03" or type(goals) is not int or goals!=1:
        raise ValueError("S03_ONE_NOMINAL_GOAL_ONLY")
    if not isinstance(goal,(list,tuple)) or tuple(goal)!=(-1.7,.7):
        raise ValueError("S03_UNAUTHORIZED_G07_CORRIDOR")
    if cm_killed is not False or tuple(operations)!=(
        "scan_drop","cm_sigstop","cm_sigcont","scan_normal"
    ):
        raise ValueError("S03_NO_CRASH_RESET_OR_SAFETY_BYPASS")
    if env.get("AXIA_P3_S01_CI_GOAL_ALLOWED")=="1" or env.get("AXIA_P3_S05_CI_GOAL_ALLOWED")=="1":
        raise ValueError("S03_MUTUALLY_EXCLUSIVE_CASE")
    return True



def admit_s04(env, *, source_sha, checkout_sha, case, goals, goal,
              kinds, operations, source):
    """PUBLIC isolated SIM only: original G09 fixture -> existing Supervisor LIMITED.

    Exactly one mapped Nav2 Goal, no real person/YOLO assertion, second Goal,
    process crash, direct Twist publisher, reset/rearm or synthetic gate bypass.
    """
    if not isinstance(env,dict):
        raise ValueError("INVALID_S04_ENV")
    required={"GITHUB_ACTIONS":"true","AXIA_P0_SIM_ONLY":"1",
              "ROS_DISTRO":"jazzy","AXIA_P3_S04_CI_PNU_ALLOWED":"1"}
    for key,value in required.items():
        if env.get(key)!=value:
            raise ValueError("S04_PUBLIC_SIM_SCOPE_REQUIRED_"+key)
    if (not isinstance(env.get("GZ_PARTITION"),str)
            or not env["GZ_PARTITION"].startswith("axia_p2_")):
        raise ValueError("S04_PARTITION_NOT_ISOLATED")
    if (not isinstance(source_sha,str) or not HEX40.fullmatch(source_sha)
            or checkout_sha!=source_sha):
        raise ValueError("S04_EXACT_SOURCE_SHA_REQUIRED")
    if case!="S04" or type(goals) is not int or goals!=1:
        raise ValueError("S04_EXACTLY_ONE_GOAL")
    if not isinstance(goal,(tuple,list)) or tuple(goal)!=(-1.7,.7):
        raise ValueError("S04_MAP_CORRIDOR_SCOPE_DENIED")
    if source!="FROZEN_SYNTHETIC_G09" or tuple(kinds)!=("N","P","U"):
        raise ValueError("S04_NO_LIVE_DETECTOR_CLAIM_OR_REORDER")
    if tuple(operations)!=("N","P","U","sw_stop"):
        raise ValueError("S04_NO_UNAUTHORIZED_FAULT_OR_REARM")
    if any(env.get(k)=="1" for k in (
            "AXIA_P3_S01_CI_GOAL_ALLOWED",
            "AXIA_P3_S03_CI_COMPOUND_ALLOWED",
            "AXIA_P3_S05_CI_GOAL_ALLOWED")):
        raise ValueError("S04_NO_OVERLAPPING_SIM_CASE")
    return True

if __name__ == "__main__":
    print("AXIA_P3_S01_CI_SIM_ONLY_PUBLIC_CONTRACT_STATIC_NO_GOAL")
