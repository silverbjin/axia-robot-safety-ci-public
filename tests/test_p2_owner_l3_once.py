"""Public CI only: no ROS, private source, Goal, Crash, or fixtures are run."""
from pathlib import Path
import subprocess
import unittest
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/axia_p2_owner_l3_once.sh'

class PublicOwnerL3Contract(unittest.TestCase):
    def test_jazzy_setup_sourced_before_nounset(self):
        w=(ROOT/'.github/workflows/p2-owner-l3-contract.yml').read_text()
        assert 'set +u\n          source /opt/ros/jazzy/setup.bash\n          set -u' in w

    def test_protected_jazzy_real_process_l1_is_required(self):
        wf=(ROOT/'.github/workflows/p2-owner-l3-contract.yml').read_text()
        assert 'instructor-l1-real-pid:' in wf
        assert 'needs: instructor-l1-qos' in wf
        assert 'python3 tools/p2_pid_real_l1.py --expected-sha' in wf
        assert 'ros-jazzy-nav2-collision-monitor' in wf
        assert 'AXIA_P2_T07_JAZZY_REAL_PROC_PID_L1_PASS_NO_GOAL_NO_FAULT' in wf

    def test_protected_real_jazzy_tty_boundary_required(self):
        wf=(ROOT/'.github/workflows/p2-owner-l3-contract.yml').read_text()
        assert 'test_p2_owner_tty_deadline_contract.py' in wf
        assert 'test_p2_tty_stdio_contract.py' in wf
        assert 'AXIA_P2_T07_JAZZY_REAL_PTY_CONSENT_L1_PASS_NO_GOAL_NO_FAULT' in wf
        assert 'python3-pytest' in wf

    def test_exact_integrated_branch_and_sha(self):
        s=SCRIPT.read_text()
        wf=(ROOT/'.github/workflows/p2-owner-l3-contract.yml').read_text()
        self.assertIn("readonly BRANCH='integration/p1-p2-mvp-shell-consent-20261110'",s)
        self.assertIn("readonly SHA='d5be4b55a935c0c4d9ca3ff895ce44090ef07fd5'",s)
        self.assertIn('ref: d5be4b55a935c0c4d9ca3ff895ce44090ef07fd5',wf)

    def test_bash_syntax(self):
        self.assertEqual(subprocess.run(['bash','-n',str(SCRIPT)]).returncode,0)
    def test_bootstrap_tracks_integrated_private_ref(self):
        # Catch a mismatched branch+SHA before Owner WSL2 spends time on Gazebo.
        source=SCRIPT.read_text()
        self.assertIn("readonly BRANCH='integration/p1-p2-mvp-shell-consent-20261110'",source)
        self.assertIn("readonly SHA='d5be4b55a935c0c4d9ca3ff895ce44090ef07fd5'",source)

    def test_offline_selfcheck(self):
        p=subprocess.run(['bash',str(SCRIPT),'--self-check'],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn('L3_NOT_RUN',p.stdout)
        self.assertIn('d5be4b55a935c0c4d9ca3ff895ce44090ef07fd5',p.stdout)
    def test_noninteractive_always_refused(self):
        p=subprocess.run(['bash',str(SCRIPT)],stdin=subprocess.DEVNULL,capture_output=True,text=True)
        self.assertEqual(p.returncode,2,p.stdout+p.stderr)
        self.assertIn('controlling TTY',p.stderr)
    def test_unsupported_flags_refused(self):
        p=subprocess.run(['bash',str(SCRIPT),'--execute','G05'],capture_output=True,text=True)
        self.assertEqual(p.returncode,2)
    def test_no_private_material_or_auto_consent_in_public_wrapper(self):
        s=SCRIPT.read_text()
        for term in ('gh repo clone','--single-branch','--depth 1','expected private SHA mismatch',
                     'AXIA_P2_OWNER_PINNED_SHA','/dev/tty','cd "$HOME"','scripts/p2_owner_l3_wsl2.sh'):
            self.assertIn(term,s)
        for unsafe in ('SIGKILL','kill -9','ros2 topic pub','/cmd_vel',
                       'git reset --hard','YES-P2-G05-GOAL','YES-P2-G06-CRASH',
                       'gh secret','--token','pip install'):
            self.assertNotIn(unsafe,s)
if __name__=='__main__':unittest.main()
