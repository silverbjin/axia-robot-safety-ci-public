"""S05 bounded CI-only SIM Stop/Reset/Rearm; never Owner TTY replacement."""
import unittest
from tools.p3_s01_public_contract import admit_s05

SHA="2"*40
ENV={"GITHUB_ACTIONS":"true","AXIA_P0_SIM_ONLY":"1","ROS_DISTRO":"jazzy",
     "AXIA_P3_S05_CI_GOAL_ALLOWED":"1","GZ_PARTITION":"axia_p2_s05_93"}


class ScopedS05PublicAdmission(unittest.TestCase):
    def test_real_ci_one_sim_goal_and_stop_only(self):
        self.assertTrue(admit_s05(ENV,source_sha=SHA,checkout_sha=SHA,
                                  goals=1,goal=(-1.7,.7),case="S05",
                                  operations=("sw_stop","rearm_denied","reset","rearm")))

    def test_disallow_owner_without_tty(self):
        bad=dict(ENV,GITHUB_ACTIONS="false")
        with self.assertRaises(ValueError):
            admit_s05(bad,source_sha=SHA,checkout_sha=SHA,goals=1,
                      goal=(-1.7,.7),case="S05",operations=("sw_stop","rearm_denied","reset","rearm"))

    def test_disallow_another_goal(self):
        with self.assertRaises(ValueError):
            admit_s05(ENV,source_sha=SHA,checkout_sha=SHA,goals=2,
                      goal=(-1.7,.7),case="S05",operations=("sw_stop","rearm_denied","reset","rearm"))

    def test_disallow_any_crash_fault(self):
        with self.assertRaises(ValueError):
            admit_s05(ENV,source_sha=SHA,checkout_sha=SHA,goals=1,
                      goal=(-1.7,.7),case="S05",operations=("sw_stop","cm_crash","reset","rearm"))

    def test_disallow_wrong_source(self):
        with self.assertRaises(ValueError):
            admit_s05(ENV,source_sha=SHA,checkout_sha="f"*40,goals=1,
                      goal=(-1.7,.7),case="S05",operations=("sw_stop","rearm_denied","reset","rearm"))

    def test_disallow_wrong_target(self):
        with self.assertRaises(ValueError):
            admit_s05(ENV,source_sha=SHA,checkout_sha=SHA,goals=1,
                      goal=(-1.6,-.5),case="S05",operations=("sw_stop","rearm_denied","reset","rearm"))

    def test_disallow_no_sim_marker(self):
        bad=dict(ENV);bad.pop("AXIA_P0_SIM_ONLY")
        with self.assertRaises(ValueError):
            admit_s05(bad,source_sha=SHA,checkout_sha=SHA,goals=1,
                      goal=(-1.7,.7),case="S05",operations=("sw_stop","rearm_denied","reset","rearm"))


if __name__=="__main__":
    unittest.main()
