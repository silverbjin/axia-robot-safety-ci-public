"""S03 CI-only same real Goal Scan-drop + CM-SIGSTOP bounded fault admission."""
import unittest
from tools.p3_s01_public_contract import admit_s03

SHA="d"*40
ENV={"GITHUB_ACTIONS":"true","AXIA_P0_SIM_ONLY":"1","ROS_DISTRO":"jazzy",
     "AXIA_P3_S03_CI_COMPOUND_ALLOWED":"1",
     "AXIA_P3_S03_CI_CM_PAUSE_ALLOWED":"1",
     "GZ_PARTITION":"axia_p2_s03_95"}
OPS=("scan_drop","cm_sigstop","cm_sigcont","scan_normal")


def admit(env=None,**kw):
    return admit_s03(ENV if env is None else env,source_sha=SHA,
                     checkout_sha=kw.pop("checkout_sha",SHA),
                     goals=kw.pop("goals",1),
                     goal=kw.pop("goal",(-1.7,.7)),
                     operations=kw.pop("operations",OPS),
                     case=kw.pop("case","S03"),
                     cm_killed=kw.pop("cm_killed",False))


class S03PublicScopeTest(unittest.TestCase):
    def test_admit_exact_public_sim_only(self):
        self.assertTrue(admit())

    def test_disallow_owner_non_public_tty_override(self):
        env=dict(ENV,GITHUB_ACTIONS="false")
        with self.assertRaises(ValueError):admit(env)

    def test_disallow_second_goal(self):
        with self.assertRaises(ValueError):admit(goals=2)

    def test_disallow_foreign_source_sha(self):
        with self.assertRaises(ValueError):admit(checkout_sha="a"*40)

    def test_disallow_real_cm_crash_substitution(self):
        with self.assertRaises(ValueError):admit(cm_killed=True)

    def test_disallow_fault_without_scope(self):
        env=dict(ENV);env.pop("AXIA_P3_S03_CI_CM_PAUSE_ALLOWED")
        with self.assertRaises(ValueError):admit(env)

    def test_disallow_unsafe_operation_or_rearm(self):
        with self.assertRaises(ValueError):
            admit(operations=("scan_drop","cm_sigkill","reset","rearm"))

    def test_disallow_any_goal_outside_g07_corridor(self):
        with self.assertRaises(ValueError):admit(goal=(9.9,9.9))

    def test_disallow_other_scenario(self):
        with self.assertRaises(ValueError):admit(case="S05")


if __name__=="__main__":
    unittest.main()
