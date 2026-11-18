"""Run actual Owner Bash + Python parity here-document under positive/negative inputs.

WSL2 Owner captured `hold` line as Python input, producing IndentationError while continuing.
"""
import json
import pathlib
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "d06/scripts/axia_d06_g07_classroom_once.sh"

class OwnerHereDocExecution(unittest.TestCase):
    def run_gate(self, *, valid):
        src = SCRIPT.read_text()
        marker = """  python3 - "$out/owner_parity.json" <<'PY'"""
        self.assertIn(marker, src)
        begin = src.index(marker)
        end = src.index("\nPY", begin) + len("\nPY")
        fragment = src[begin:end]
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp)
            data = {
                "status": "CORE_PARITY_PASS" if valid else "PARITY_BLOCKED",
                "mode": "owner" if valid else "ci",
                "wsl_detected": True,
                "checked_packages": 25,
                "checked_official_files": 5,
                "mismatch": {} if valid else {"ci_kernel": "CI_NOT_WSL2_REQUIRED"},
            }
            (p / "owner_parity.json").write_text(json.dumps(data))
            code = (
                "set -Eeuo pipefail\n"
                "hold() { echo \"D06_TEST_HOLD_$1\" >&2; exit 3; }\n"
                f"out={tmp!r}\n"
                + fragment + "\n"
                + "echo D06_TEST_AFTER_VALIDATED_GATE\n"
            )
            return subprocess.run(
                ["bash", "-c", code], capture_output=True, text=True, timeout=8
            )

    def test_positive_owner_core_parity_executes_python_exactly_once(self):
        result = self.run_gate(valid=True)
        self.assertEqual(result.returncode, 0, (result.stdout, result.stderr))
        self.assertIn("D06_G07_OWNER_CORE_PARITY_PASS_PACKAGES25_FILES5_WSL2", result.stdout)
        self.assertIn("D06_TEST_AFTER_VALIDATED_GATE", result.stdout)
        self.assertNotIn("IndentationError", result.stderr)

    def test_negative_parity_fails_closed_before_next_owner_stage(self):
        result = self.run_gate(valid=False)
        self.assertEqual(result.returncode, 3, (result.stdout, result.stderr))
        self.assertIn(
            "D06_TEST_HOLD_D06_G07_OWNER_CORE_PARITY_REPORT_INVALID_NO_GOAL",
            result.stderr,
        )
        self.assertNotIn("D06_TEST_AFTER_VALIDATED_GATE", result.stdout)
        self.assertNotIn("IndentationError", result.stderr)

    def test_original_parity_here_doc_is_one_bash_statement(self):
        src = SCRIPT.read_text()
        marker = """  python3 - "$out/owner_parity.json" <<'PY'"""
        frag = src[src.index(marker):src.index("\nPY", src.index(marker)) + 3]
        # The exact fragment alone must be valid Bash, including its trailing
        # 'then' or closure. This catches a dangling || before a heredoc body.
        p = subprocess.run(
            ["bash", "-n"], input="set -Eeuo pipefail\n" + frag + "\n",
            capture_output=True, text=True, timeout=5
        )
        self.assertEqual(p.returncode, 0, p.stderr)

if __name__ == "__main__":
    unittest.main()
