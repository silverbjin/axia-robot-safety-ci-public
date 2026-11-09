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

    def test_bash_syntax(self):
        self.assertEqual(subprocess.run(['bash','-n',str(SCRIPT)]).returncode,0)
    def test_offline_selfcheck(self):
        p=subprocess.run(['bash',str(SCRIPT),'--self-check'],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn('L3_NOT_RUN',p.stdout)
        self.assertIn('f40182a1f3b22ece906e4b02eb5fd2c5630001ff',p.stdout)
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
