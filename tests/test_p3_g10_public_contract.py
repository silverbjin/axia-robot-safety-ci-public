"""G10 PUBLIC-CI-only exact-SHA sustained Scan DROP + CM SIGSTOP recovery authority."""
import unittest
from tools.p3_s01_public_contract import admit_g10

SHA="d"*40
ENV={"GITHUB_ACTIONS":"true","AXIA_P0_SIM_ONLY":"1",
     "ROS_DISTRO":"jazzy","GZ_PARTITION":"axia_p2_g10_98",
     "AXIA_G07_CI_SIM_GOAL_ALLOWED":"1",
     "AXIA_P3_G10_CI_HELD_RECOVERY_ALLOWED":"1",
     "AXIA_P3_S03_CI_COMPOUND_ALLOWED":"1",
     "AXIA_P3_S03_CI_CM_PAUSE_ALLOWED":"1"}
OPS=("scan_drop","cm_sigstop","reset_denied","rearm_denied",
     "fault_cleared_denied","cm_sigcont","scan_normal",
     "fault_cleared","rearm","no_auto_resume")

def gate(env=None,**kw):
    return admit_g10(ENV if env is None else env,source_sha=SHA,
                     checkout_sha=kw.pop("checkout_sha",SHA),
                     case=kw.pop("case","G10"),goals=kw.pop("goals",1),
                     goal=kw.pop("goal",(-1.7,.7)),
                     operations=kw.pop("operations",OPS),
                     cm_killed=kw.pop("cm_killed",False),
                     certified_estop=kw.pop("certified_estop",False))

class G10PublicCI(unittest.TestCase):
    def test_exact_sim_one_goal_held_fault_only(self):
        self.assertTrue(gate())
    def test_owner_without_public_actions_denied(self):
        with self.assertRaises(ValueError):gate(dict(ENV,GITHUB_ACTIONS="false"))
    def test_source_sha_mismatch_denied(self):
        with self.assertRaises(ValueError):gate(checkout_sha="a"*40)
    def test_multiple_goals_denied(self):
        with self.assertRaises(ValueError):gate(goals=2)
    def test_other_case_denied(self):
        with self.assertRaises(ValueError):gate(case="G06")
    def test_unsafe_g10_sigkill_denied(self):
        with self.assertRaises(ValueError):gate(cm_killed=True)
    def test_fake_certified_estop_denied(self):
        with self.assertRaises(ValueError):gate(certified_estop=True)
    def test_unsafe_rearm_while_fault_held_denied(self):
        ops=list(OPS);ops[3]="rearm_while_fault"
        with self.assertRaises(ValueError):gate(operations=tuple(ops))
    def test_unsafe_reset_before_fault_clear_denied(self):
        ops=list(OPS);ops[2]="reset_success_during_fault"
        with self.assertRaises(ValueError):gate(operations=tuple(ops))
    def test_unrelated_s04_case_denied(self):
        with self.assertRaises(ValueError):gate(dict(ENV,AXIA_P3_S04_CI_PNU_ALLOWED="1"))
    def test_unisolated_partition_denied(self):
        with self.assertRaises(ValueError):gate(dict(ENV,GZ_PARTITION="host"))
    def test_missing_explicit_held_fault_scope_denied(self):
        e=dict(ENV);e.pop("AXIA_P3_G10_CI_HELD_RECOVERY_ALLOWED")
        with self.assertRaises(ValueError):gate(e)
    def test_recovery_requires_fault_cleared_not_reset_in_protective_stop(self):
        ops=list(OPS);ops[7]="reset"
        with self.assertRaises(ValueError):gate(operations=ops)
    def test_no_unscoped_owner_tty_authority(self):
        with self.assertRaises(ValueError):gate(dict(ENV,AXIA_P3_S05_CI_GOAL_ALLOWED="1"))
if __name__=="__main__":
    unittest.main()
