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


if __name__ == "__main__":
    print("AXIA_P3_S01_CI_SIM_ONLY_PUBLIC_CONTRACT_STATIC_NO_GOAL")
