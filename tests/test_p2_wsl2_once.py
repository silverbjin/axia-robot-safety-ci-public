import subprocess
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1]/'scripts/axia_p2_wsl2_once.sh'

class OwnerWrapperContract(unittest.TestCase):
    def test_syntax(self):
        self.assertEqual(subprocess.run(['bash','-n',str(SCRIPT)]).returncode,0)
    def test_offline_selfcheck(self):
        x=subprocess.run(['bash',str(SCRIPT),'--self-check'],capture_output=True,text=True)
        self.assertEqual(x.returncode,0,x.stderr)
        self.assertIn('L3_NOT_RUN',x.stdout)
        self.assertIn('1728b8708c6672ca8bb059fd25aab86ec9fa2c46',x.stdout)
    def test_noninteractive_refused(self):
        x=subprocess.run(['bash',str(SCRIPT)],stdin=subprocess.DEVNULL,capture_output=True,text=True)
        self.assertEqual(x.returncode,2)
        self.assertIn('controlling TTY required',x.stderr)
    def test_rejects_unknown_flag(self):
        x=subprocess.run(['bash',str(SCRIPT),'--execute'],capture_output=True,text=True)
        self.assertEqual(x.returncode,2)
    def test_ros_is_sourced_before_dependency_probe(self):
        s=SCRIPT.read_text()
        self.assertLess(s.index("source /opt/ros/jazzy/setup.bash"),s.index("for cmd in gh git python3 colcon ros2"))
    def test_fail_closed_contract(self):
        s=SCRIPT.read_text()
        for item in ('gh repo clone', 'private SHA mismatch','umask 077',
                     'P2_OWNER_L2_NO_GOAL_PASS','G05=NOT_RUN G06=NOT_RUN G07=NOT_RUN',
                     'scripts/p2_no_goal_smoke_ci.sh','gate_accepted',
                     'sha256sum "$OUT.tar.gz"','PRELOCAL_PASS_L3_HOLD'):
            self.assertIn(item,s)
        for unsafe in ('p2_owned_process_fault.py','SIGKILL', 'ros2 topic pub',
                       'ros2 action send_goal','git reset --hard','git push',
                       'YES-P2-G05-CRASH','YES-P2-G06-CRASH'):
            self.assertNotIn(unsafe,s)
if __name__ == '__main__':unittest.main()
