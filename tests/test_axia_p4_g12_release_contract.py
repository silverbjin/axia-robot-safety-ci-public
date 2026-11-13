"""P4 G12 scoped D03 release contract tests, synthetic only."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

P = Path(__file__).resolve().parents[1] / "tools/axia_p4_g12_release_contract.py"
spec = importlib.util.spec_from_file_location("axia_p4_g12_release_contract", P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def receipt(**changes):
    v = dict(student_sha="4f74916a09f726ffd6978926adfc83ee9f528298",
             instructor_sha="b01057ed4fa82b97aee8499aacbf2c55829bad23",
             student_red_rc=1, student_failures=22,
             instructor_public_green_rc=0, instructor_hidden_green_rc=0,
             protected_checkout=True)
    v.update(changes)
    return v


class P4G12Contract(unittest.TestCase):
    def test_expected_student_red_and_instructor_green_is_scoped_only(self):
        v = m.evaluate_receipt(receipt(), forbidden_files=[])
        self.assertEqual(v["status"], "G12_D03_TODO_RED_REFERENCE_GREEN_SCOPED")
        self.assertFalse(v["formal_accepted"])
        self.assertFalse(v["student_release_approved"])
        self.assertEqual(v["G13"], "NOT_RUN")
        self.assertEqual(v["G11"], "NOT_ACCEPTED")

    def test_unexpected_student_green_blocks(self):
        self.assertEqual(m.evaluate_receipt(receipt(student_red_rc=0), forbidden_files=[])["status"], "BLOCKED")

    def test_instructor_public_or_hidden_fails_closed(self):
        for name in ("instructor_public_green_rc", "instructor_hidden_green_rc"):
            with self.subTest(name=name):
                self.assertEqual(m.evaluate_receipt(receipt(**{name:1}), forbidden_files=[])["status"], "BLOCKED")

    def test_secret_or_non_independent_source_blocks(self):
        self.assertEqual(m.evaluate_receipt(receipt(protected_checkout=False), forbidden_files=[])["status"], "BLOCKED")
        self.assertEqual(m.evaluate_receipt(receipt(student_sha="bad"), forbidden_files=[])["status"], "BLOCKED")
        self.assertEqual(m.evaluate_receipt(receipt(instructor_sha="4f74916a09f726ffd6978926adfc83ee9f528298"), forbidden_files=[])["status"], "BLOCKED")

    def test_student_tree_forbids_instructor_and_hidden_files(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            for p in ["block_A/day03/todo_safety.py", "block_A/day03/p1_adapter_todo.py"]:
                f=root/p;f.parent.mkdir(parents=True,exist_ok=True);f.write_text("# TODO_NOT_IMPLEMENTED")
            self.assertEqual(m.scan_student_tree(root), [])
            f=root/"training/instructor/solutions/todo_safety.py"
            f.parent.mkdir(parents=True)
            f.write_text("PRIVATE_ANSWER")
            self.assertIn(f.relative_to(root).as_posix(), m.scan_student_tree(root))

    def test_missing_todo_or_security_finding_blocks(self):
        self.assertEqual(m.evaluate_receipt(receipt(student_failures=0), forbidden_files=[])["status"],"BLOCKED")
        self.assertEqual(m.evaluate_receipt(receipt(), forbidden_files=["solutions/key.py"])["status"],"BLOCKED")


if __name__ == "__main__":
    unittest.main()
