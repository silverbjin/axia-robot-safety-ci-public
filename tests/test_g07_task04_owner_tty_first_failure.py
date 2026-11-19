"""HFbmAW8N: preserve the *first* Owner Goal consent failure, never generic RC.

Executable bash function extraction tests only; never loads ROS/Gazebo or Goal.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/axia_g07_task04_owner_moving_l3_once.sh"

def classify(log):
    s=SCRIPT.read_text()
    prefix="owner_consent_first_failure() {"
    assert prefix in s, "OWNER_CONSENT_FIRST_FAILURE_HELPER_MISSING"
    fn=s[s.index(prefix):]
    fn=fn[:fn.index("\n}\n")+2]
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/"native_runner.log"
        p.write_text(log)
        r=subprocess.run(["bash","-c",fn+'\nowner_consent_first_failure "$1"',"_",str(p)],
                         capture_output=True,text=True,timeout=3,check=True)
        return r.stdout.strip()

class OwnerTTYFirstFailure(unittest.TestCase):
    def test_approved_is_not_reported_as_failure(self):
        self.assertEqual(classify("OWNER_GOAL_CONSENT_PENDING timeout_sec=180\nOWNER_GOAL_CONSENT_ACCEPTED\n"),"")

    def test_timeout_survives_outer_shell_hold(self):
        self.assertEqual(classify("OWNER_GOAL_CONSENT_PENDING\nOWNER_GOAL_CONSENT_TIMEOUT elapsed_sec=180\nP2_L2_SMOKE_RC=2\n"),
                         "OWNER_GOAL_CONSENT_TIMEOUT")

    def test_distinguishes_tty_eof_and_denial(self):
        self.assertEqual(classify("OWNER_GOAL_CONSENT_EOF_OR_TTY_ERROR\n"),
                         "OWNER_GOAL_CONSENT_EOF_OR_TTY_ERROR")
        self.assertEqual(classify("OWNER_GOAL_CONSENT_DENIED\n"),
                         "OWNER_GOAL_CONSENT_DENIED")
        self.assertEqual(classify("OWNER_GOAL_CONSENT_TTY_UNAVAILABLE\n"),
                         "OWNER_GOAL_CONSENT_TTY_UNAVAILABLE")

    def test_first_line_wins_and_unrelated_failures_not_classified(self):
        self.assertEqual(classify("OWNER_GOAL_CONSENT_DENIED\nOWNER_GOAL_CONSENT_TIMEOUT\n"),
                         "OWNER_GOAL_CONSENT_DENIED")
        self.assertEqual(classify("NATIVE_RUNNER_FAILED_REVIEW_RAW\nCLOCK_MISSING\n"),"")

    def test_owner_failure_branch_uses_classifier_instead_of_generic(self):
        s=SCRIPT.read_text()
        self.assertIn('CONSENT_FIRST_FAILURE="$(owner_consent_first_failure "$OUT/native_runner.log")"',s)
        self.assertIn('FIRST_FAILURE="$CONSENT_FIRST_FAILURE"',s)
        self.assertIn('hold "$FIRST_FAILURE"',s)
        self.assertIn("OWNER_CONTROLLING_TTY_REQUIRED",s)
        self.assertIn("timeout --foreground --signal=TERM",s)
        self.assertNotIn("YES-P2-G07-GOAL' |",s)

if __name__=="__main__":
    unittest.main()
