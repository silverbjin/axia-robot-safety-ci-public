"""Public source-only release gate: G07 one-shot WSL2 bootstrap.

This never launches Nav2/Gazebo or sends a Goal. Real physical LiDAR
no-Goal evidence is https://github.com/silverbjin/axia-robot-safety-ci-public/actions/runs/42754104452
"""
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/axia_p2_g07_mvp_demo_once.sh'
SOURCE_SHA='1216d8589b2a8ac4c7e75aedaa7854eb7b2470b3'

class TestMvpOwnerLauncher(unittest.TestCase):
    def test_shell_syntax_and_offline_pinned_self_check(self):
        p=subprocess.run(['bash','-n',str(SCRIPT)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        p=subprocess.run(['bash',str(SCRIPT),'--self-check'],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn('P2_G07_MVP_OWNER_WRAPPER_STATIC_OK',p.stdout)
        self.assertIn(SOURCE_SHA,p.stdout)
        self.assertIn('L3_NOT_RUN',p.stdout)

    def test_noninteractive_rejected_without_goal(self):
        p=subprocess.run(['bash',str(SCRIPT)],input='',capture_output=True,text=True)
        self.assertEqual(p.returncode,2,p.stdout+p.stderr)
        self.assertIn('real Owner controlling TTY required',p.stderr)

    def test_exact_private_source_and_no_auto_consent_or_other_cases(self):
        s=SCRIPT.read_text()
        self.assertIn("readonly BRANCH='fix/p2-g07-official-spawn-sensor-proof-20261110'",s)
        self.assertIn("readonly SHA='"+SOURCE_SHA+"'",s)
        self.assertIn('git -C "$SRC/instructor" rev-parse HEAD',s)
        self.assertIn('gh repo clone',s)
        self.assertIn('bash "$SRC/instructor/scripts/p2_owner_l3_wsl2.sh" --case G07',s)
        self.assertNotIn('YES-P2-G07-GOAL\n',s)
        self.assertNotIn('kill -9',s)
        self.assertNotIn('--case G05',s)
        self.assertNotIn('--case G06',s)

    def test_release_scope_disclaimer_and_private_source_cleanup(self):
        s=SCRIPT.read_text()
        for required in ('SIMULATION_ONLY','CONTACT_GROUND_TRUTH_UNVERIFIED',
                         'CONTACT', 'cleanup()', 'AXIA_P2_OWNER_PINNED_SHA',
                         'P2_G07_MVP_DEMO_ONLY'):
            self.assertIn(required,s)
        self.assertIn('rm -rf -- "$SRC"',s)
        self.assertIn('[[ -t 0 && -t 1 && -r /dev/tty ]]',s)

if __name__=='__main__':
    unittest.main()
