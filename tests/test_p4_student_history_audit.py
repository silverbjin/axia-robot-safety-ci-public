"""P4 G12 public student history scanner tests (synthetic git repos only)."""
import importlib.util
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "tools/p4_student_history_audit.py"
spec = importlib.util.spec_from_file_location("p4_student_history_audit", SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                          text=True, check=True).stdout.strip()


class GitFixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "student"
        self.repo.mkdir()
        git(self.repo, "init", "-b", "main")
        git(self.repo, "config", "user.email", "ci@example.invalid")
        git(self.repo, "config", "user.name", "Public CI Synthetic")
        self.write("README.md", "Public TODO only")
        self.commit("safe base")
        git(self.repo, "checkout", "-b", "D03")
        self.write("block_A/day03/todo.py", "# TODO_NOT_IMPLEMENTED")
        self.commit("independent student TODO")
        git(self.repo, "checkout", "main")

    def write(self, path, content):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def commit(self, message):
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-m", message)

    def test_safe_two_branch_history_passes_scoped_only(self):
        out = m.scan_repo(self.repo, required_refs={"refs/heads/main", "refs/heads/D03"})
        self.assertEqual(out["status"], "HISTORY_METADATA_PASS_SCOPED")
        self.assertFalse(out["formal_g12_accepted"])
        self.assertGreaterEqual(out["commit_count"], 2)
        self.assertEqual(out["finding_count"], 0)

    def test_deleted_solution_file_still_blocks_through_history(self):
        self.write("training/d03/instructor/solutions/answer.py", "def solve(): return True")
        self.commit("historical leak")
        (self.repo / "training/d03/instructor/solutions/answer.py").unlink()
        self.commit("remove visible file")
        out = m.scan_repo(self.repo)
        self.assertEqual(out["status"], "BLOCKED")
        self.assertIn("FORBIDDEN_HISTORY_PATH", out["finding_types"])

    def test_deleted_hidden_tests_still_block(self):
        self.write("docs/hidden_tests/test_answer.py", "assert True")
        self.commit("historical hidden")
        (self.repo / "docs/hidden_tests/test_answer.py").unlink()
        self.commit("remove it")
        self.assertIn("FORBIDDEN_HISTORY_PATH", m.scan_repo(self.repo)["finding_types"])

    def test_secret_pattern_in_old_text_history_blocks_without_emitting_content(self):
        secret = "ghp_" + "X" * 35
        self.write("src/example.py", "value = '" + secret + "'\n")
        self.commit("accidental secret")
        (self.repo / "src/example.py").unlink()
        self.commit("remove visible example")
        result = m.scan_repo(self.repo)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("SECRET_CONTENT_PATTERN", result["finding_types"])
        self.assertNotIn(secret, repr(result))

    def test_symlink_and_private_key_path_are_blocked(self):
        (self.repo / "shortcut").symlink_to("README.md")
        self.commit("unsafe symlink")
        self.assertIn("GIT_SYMLINK", m.scan_repo(self.repo)["finding_types"])
        (self.repo / "shortcut").unlink()
        self.write("tls/temporary.pem", "dummy")
        self.commit("unsafe key file")
        self.assertIn("FORBIDDEN_HISTORY_PATH", m.scan_repo(self.repo)["finding_types"])

    def test_missing_expected_branch_and_wrong_sha_fail_closed(self):
        out = m.scan_repo(self.repo, required_refs={"refs/heads/main", "refs/heads/UNKNOWN"})
        self.assertEqual(out["status"], "BLOCKED")
        self.assertIn("REQUIRED_REF_MISSING", out["finding_types"])
        out = m.scan_repo(self.repo, expected_heads={"refs/heads/main": "0"*40})
        self.assertEqual(out["status"], "BLOCKED")
        self.assertIn("EXPECTED_SHA_MISMATCH", out["finding_types"])

    def test_full_history_checks_other_branch_not_only_main(self):
        git(self.repo, "checkout", "D03")
        self.write("private_keys/key.txt", "not a real key")
        self.commit("bad other branch")
        git(self.repo, "checkout", "main")
        self.assertIn("FORBIDDEN_HISTORY_PATH", m.scan_repo(self.repo)["finding_types"])


if __name__ == "__main__":
    unittest.main()
