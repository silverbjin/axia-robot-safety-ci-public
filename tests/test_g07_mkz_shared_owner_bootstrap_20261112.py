"""Public-only exact G07 WSL2 Owner bootstrap after real CI moving + shutdown.

Source SHA must correspond to the SAME actual moving/CM clean-exit L2, not
a historical successful different source. No private checkout in this L0,
no TTY consent automation, no ROS or Goal.
"""
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
WRAPPER=ROOT/"scripts/axia_p2_g07_ci_pass_owner_wsl2_once.sh"
WORKFLOW=ROOT/".github/workflows/axia-p2-g07-ci-pass-owner-bootstrap-static-l0.yml"
REAL_L2=ROOT/".github/workflows/axia-p2-g07-ci-real-gazebo-moving-goal-l2.yml"
PRIVATE_SHA="6099ed78c4b7079c60c447cb03ccb3817a99c7a4"
REAL_RUN="43250221111"
SCOPE="SHARED_STARTUP_GOAL_SHUTDOWN_CM_EXIT0"
OLD_SHA="cc92327d1ae4a17d331d06e845437760ca2bdafe"


class G07MKZBootstrap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=WRAPPER.read_text(encoding="utf-8")

    def test_exact_source_was_actual_public_l2_with_post_goal_cm_exit0(self):
        self.assertIn("readonly PRIVATE_SHA='"+PRIVATE_SHA+"'",self.s)
        self.assertIn("readonly CI_L2_RUN='"+REAL_RUN+"'",self.s)
        self.assertIn("readonly CI_L2_SCOPE='"+SCOPE+"'",self.s)
        self.assertIn("ref: "+PRIVATE_SHA,REAL_L2.read_text())
        self.assertIn("G07_MOVING_GOAL_CM_CLEAN_EXIT_AFTER_NAV2_ACK_PASS",
                      REAL_L2.read_text()+self.s)
        self.assertNotIn("PRIVATE_SHA='"+OLD_SHA+"'",self.s)

    def test_legacy_static_contract_updated_to_same_evidence(self):
        text=WORKFLOW.read_text()
        self.assertIn("private_sha="+PRIVATE_SHA+" ci_l2="+REAL_RUN+" scope="+SCOPE+" OWNER_L3_NOT_RUN",text)

    def test_script_syntax_and_precise_self_check(self):
        a=subprocess.run(["bash","-n",str(WRAPPER)],capture_output=True,text=True,timeout=10)
        self.assertEqual(a.returncode,0,a.stderr)
        b=subprocess.run(["bash",str(WRAPPER),"--self-check"],
                         capture_output=True,text=True,timeout=10)
        self.assertEqual(b.returncode,0,b.stderr)
        self.assertEqual(b.stdout.strip(),
            "AXIA_G07_CI_PASS_OWNER_BOOTSTRAP_STATIC_PASS private_sha="+PRIVATE_SHA+
            " ci_l2="+REAL_RUN+" scope="+SCOPE+" OWNER_L3_NOT_RUN")

    def test_fail_closed_when_no_controlling_tty_no_goal(self):
        p=subprocess.run(["bash",str(WRAPPER)],input="",text=True,
                         capture_output=True,timeout=10)
        self.assertEqual(p.returncode,2)
        self.assertIn("real controlling TTY required; NO_GOAL",p.stderr)

    def test_manual_exact_sha_and_post_goal_cleanup_checks_not_bypassed(self):
        for value in (
            "gh auth status",
            'checkout --detach "$PRIVATE_SHA"',
            '[[ "$ACTUAL" == "$PRIVATE_SHA" ]]',
            '[[ -t 0 && -t 1 && -r /dev/tty ]]',
            'export AXIA_P2_OWNER_PINNED_SHA="$PRIVATE_SHA"',
            "tools/p2_g07_lifecycle_service.py",
            "scripts/p2_g07_shared_staged_startup.sh",
            "tools/p2_g07_ordered_shutdown.py",
            "tools/p2_g07_owner_shutdown_audit.py",
            'bash "$WORK/instructor/scripts/p2_owner_l3_wsl2.sh"',
            '--case G07 --mvp-relocated-obstacle',
            "YES-P2-G07-GOAL",
            "SW Stop != certified E-Stop.",
        ):
            self.assertIn(value,self.s)
        self.assertNotIn("echo YES-P2-G07-GOAL",self.s)
        self.assertNotIn("--case G05",self.s)
        self.assertNotIn("--case G06",self.s)

    def test_old_source_or_l2_pin_mutation_is_not_accepted(self):
        self.assertNotIn(OLD_SHA,self.s)
        self.assertFalse("PRIVATE_SHA='"+PRIVATE_SHA+"'" in self.s.replace(PRIVATE_SHA,OLD_SHA))
        self.assertFalse("CI_L2_RUN='"+REAL_RUN+"'" in self.s.replace(REAL_RUN,"43186070186"))


if __name__=="__main__":
    unittest.main()
