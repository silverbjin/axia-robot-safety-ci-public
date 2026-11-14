"""G12 actual independent Student release inventory. No Teacher answer, no release."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from axia_p4_g12_release_inventory import audit_release_inventory

MAIN="d2f16eaf5b5fb60ad9b8009fe1532fa75363e971"
D03="4f74916a09f726ffd6978926adfc83ee9f528298"
DIGEST="sha256:861ae1df0560f991698d8967193380b1619589ba7770b5e2ca91ea4ef31f0c8e"

def student_main_files():
    return {"README.md","block_B/day04/LAB.md","block_B/day05/LAB.md",
            "block_B/day06/D06_LAB_KO.md","block_B/day06/safety_bubble_todo.py",
            "block_B/day07/D07_LAB_KO.md","block_B/day07/route_todo.py"}
def student_d03_files():
    return {"README.md","block_A/day03/README_D03_KO.md","block_A/day03/todo_safety.py",
            "block_A/day03/p1_adapter_todo.py",
            "block_A/tests/test_safety_public.py"}
def go(main=None,d03=None,approval=False):
    return audit_release_inventory(student_main_paths=main if main is not None else student_main_files(),
        student_d03_paths=d03 if d03 is not None else student_d03_files(),
        main_sha=MAIN,d03_sha=D03,baseline_runtime_digest=DIGEST,
        student_release_approved=approval)

class G12ReleaseInventoryContract(unittest.TestCase):
    def test_real_current_main_and_d03_are_not_full_release(self):
        r=go()
        self.assertEqual(r["status"],"HOLD_INCOMPLETE_STUDENT_RELEASE_INVENTORY")
        self.assertIn("D03_NOT_IN_STUDENT_MAIN",r["blockers"])
        self.assertIn("ROOT_LICENSES_MD_MISSING",r["blockers"])
        self.assertIn("ROOT_VERSION_LOCK_MD_MISSING",r["blockers"])
        self.assertIn("THIRD_PARTY_ATTRIBUTION_NOT_LOCKED",r["blockers"])
        self.assertFalse(r["formal_g12_accepted"])
        self.assertFalse(r["new_student_release"])
    def test_training_D03_TODO_must_remain_unimplemented(self):
        r=go()
        self.assertTrue(r["student_d03_skeleton_present"])
        self.assertFalse(r["instructor_answers_copied"])
    def test_d03_presence_in_main_removes_only_that_one_blocker(self):
        main=student_main_files()|student_d03_files()
        r=go(main=main)
        self.assertNotIn("D03_NOT_IN_STUDENT_MAIN",r["blockers"])
        self.assertIn("ROOT_LICENSES_MD_MISSING",r["blockers"])
    def test_license_notice_and_version_lock_only_remove_compliance_flags(self):
        full=student_main_files()|student_d03_files()|{
            "LICENSES.md","VERSION_LOCK.md","THIRD_PARTY_ATTRIBUTION.md"}
        r=go(main=full)
        self.assertNotIn("ROOT_LICENSES_MD_MISSING",r["blockers"])
        self.assertNotIn("ROOT_VERSION_LOCK_MD_MISSING",r["blockers"])
        self.assertNotIn("THIRD_PARTY_ATTRIBUTION_NOT_LOCKED",r["blockers"])
        self.assertFalse(r["formal_g12_accepted"])  # path existence != license reviewed
    def test_user_approval_flag_cannot_override_missing_attribution(self):
        r=go(approval=True)
        self.assertFalse(r["formal_g12_accepted"])
        self.assertIn("ROOT_LICENSES_MD_MISSING",r["blockers"])
    def test_instructor_hidden_solution_path_is_release_blocker(self):
        main=student_main_files()|{"instructor/solutions/answer.py"}
        r=go(main=main)
        self.assertIn("PRIVATE_ANSWER_OR_HIDDEN_PATH_DETECTED",r["blockers"])
    def test_symlink_suspected_from_tree_unsafe_path_is_blocker(self):
        main=student_main_files()|{"../../teacher-secret.py"}
        with self.assertRaisesRegex(ValueError,"STUDENT_TREE_UNSAFE_PATH"):
            go(main=main)
    def test_bad_sha_or_digest_blocks(self):
        with self.assertRaisesRegex(ValueError,"PIN_INVALID"):
            audit_release_inventory(student_main_paths=student_main_files(),
                student_d03_paths=student_d03_files(),main_sha="invalid",
                d03_sha=D03,baseline_runtime_digest=DIGEST,student_release_approved=False)
        with self.assertRaisesRegex(ValueError,"DIGEST_INVALID"):
            audit_release_inventory(student_main_paths=student_main_files(),
                student_d03_paths=student_d03_files(),main_sha=MAIN,
                d03_sha=D03,baseline_runtime_digest="latest",student_release_approved=False)
    def test_missing_d03_todo_detected(self):
        r=go(d03={"README.md"})
        self.assertFalse(r["student_d03_skeleton_present"])
        self.assertIn("D03_TODO_OR_PUBLIC_TEST_MISSING",r["blockers"])
    def test_no_estop_certification_or_g11_auto_pass(self):
        r=go()
        self.assertFalse(r["certified_estop"])
        self.assertEqual(r["g11_formal_count"],0)
        self.assertFalse(r["ros_gazebo_executed"])
if __name__=="__main__":
    unittest.main()
