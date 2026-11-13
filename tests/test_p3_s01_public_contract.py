"""Public S01 opt-in contract: only one actual CI-only nominal SIM goal."""
import unittest

from tools.p3_s01_public_contract import admit_s01


SHA = "1" * 40
GOOD = {
    "GITHUB_ACTIONS": "true",
    "AXIA_P0_SIM_ONLY": "1",
    "AXIA_P3_S01_CI_GOAL_ALLOWED": "1",
    "ROS_DISTRO": "jazzy",
    "GZ_PARTITION": "axia_p2_s01_l2_83",
}


class PublicS01AdmissionTest(unittest.TestCase):
    def test_one_nominal_sim_case_admitted(self):
        self.assertTrue(admit_s01(GOOD, source_sha=SHA, checkout_sha=SHA,
                                  case="S01", goals=1, goal=(-1.6, -.5)))

    def test_wrong_git_sha_does_not_move(self):
        with self.assertRaises(ValueError):
            admit_s01(GOOD, source_sha=SHA, checkout_sha="2"*40,
                      case="S01", goals=1, goal=(-1.6, -.5))

    def test_nominal_goal_cannot_be_replaced(self):
        with self.assertRaises(ValueError):
            admit_s01(GOOD, source_sha=SHA, checkout_sha=SHA,
                      case="S01", goals=1, goal=(1.0, 1.0))

    def test_no_two_goals_under_single_opt_in(self):
        with self.assertRaises(ValueError):
            admit_s01(GOOD, source_sha=SHA, checkout_sha=SHA,
                      case="S01", goals=2, goal=(-1.6, -.5))

    def test_owner_machine_cannot_use_ci_admission(self):
        env = dict(GOOD)
        env["GITHUB_ACTIONS"] = "false"
        with self.assertRaises(ValueError):
            admit_s01(env, source_sha=SHA, checkout_sha=SHA,
                      case="S01", goals=1, goal=(-1.6, -.5))

    def test_no_real_robot_or_missing_sim_marker(self):
        env = dict(GOOD)
        env.pop("AXIA_P0_SIM_ONLY")
        with self.assertRaises(ValueError):
            admit_s01(env, source_sha=SHA, checkout_sha=SHA,
                      case="S01", goals=1, goal=(-1.6, -.5))

    def test_only_s01_allowed(self):
        with self.assertRaises(ValueError):
            admit_s01(GOOD, source_sha=SHA, checkout_sha=SHA,
                      case="S05", goals=1, goal=(-1.6, -.5))


if __name__ == "__main__":
    unittest.main()
