"""Public CI simulation-only S04 controlled G09 PNU goal admission RED."""
import unittest
from tools.p3_s01_public_contract import admit_s04

SHA="d"*40
BASE={"GITHUB_ACTIONS":"true","AXIA_P0_SIM_ONLY":"1",
      "ROS_DISTRO":"jazzy","AXIA_P3_S04_CI_PNU_ALLOWED":"1",
      "GZ_PARTITION":"axia_p2_s04_97"}
OPS=("N","P","U","sw_stop")

def gate(env=None,**kw):
    return admit_s04(BASE if env is None else env,
                     source_sha=SHA,
                     checkout_sha=kw.pop("checkout_sha",SHA),
                     goals=kw.pop("goals",1),
                     goal=kw.pop("goal",(-1.7,.7)),
                     kinds=kw.pop("kinds",("N","P","U")),
                     operations=kw.pop("operations",OPS),
                     case=kw.pop("case","S04"),
                     source=kw.pop("source","FROZEN_SYNTHETIC_G09"))

class S04PublicAuthority(unittest.TestCase):
    def test_one_sim_goal_and_original_g09_pnu_only(self):
        self.assertTrue(gate())

    def test_owner_no_implicit_consent(self):
        with self.assertRaises(ValueError):gate(dict(BASE,GITHUB_ACTIONS="false"))

    def test_second_goal_forbidden(self):
        with self.assertRaises(ValueError):gate(goals=2)

    def test_foreign_private_sha_forbidden(self):
        with self.assertRaises(ValueError):gate(checkout_sha="a"*40)

    def test_pnu_wrong_order_forbidden(self):
        with self.assertRaises(ValueError):gate(kinds=("P","N","U"))

    def test_no_live_person_claim_or_new_ai_model(self):
        with self.assertRaises(ValueError):gate(source="REAL_YOLO_PERSON")

    def test_no_stop_bypass_or_second_action(self):
        with self.assertRaises(ValueError):gate(operations=("N","P","U","rearm"))

    def test_wrong_map_target_forbidden(self):
        with self.assertRaises(ValueError):gate(goal=(9.9,9.9))

    def test_s04_never_admits_s03_faults(self):
        with self.assertRaises(ValueError):gate(case="S03")

    def test_no_gazebo_namespace_isolation_denied(self):
        with self.assertRaises(ValueError):gate(dict(BASE,GZ_PARTITION="host"))

    def test_other_case_optin_concurrently_forbidden(self):
        with self.assertRaises(ValueError):
            gate(dict(BASE,AXIA_P3_S03_CI_COMPOUND_ALLOWED="1"))

if __name__=="__main__":
    unittest.main()
