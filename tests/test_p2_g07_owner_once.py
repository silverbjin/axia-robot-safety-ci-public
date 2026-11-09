"""Public G07 bootstrap contract: no Goal, fault or Gazebo executed here."""
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/axia_p2_g07_owner_once.sh'
SHA='0af856dbf5dfcbbce62a6e6bd3242a25c91a343d'

class P2G07OwnerContract(unittest.TestCase):
    def test_wrapper_syntax_and_offline_selfcheck(self):
        self.assertEqual(subprocess.run(['bash','-n',str(SCRIPT)]).returncode,0)
        r=subprocess.run(['bash',str(SCRIPT),'--self-check'],text=True,capture_output=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn(SHA,r.stdout)
        self.assertIn('L3_NOT_RUN',r.stdout)

    def test_noninteractive_fails_before_goal(self):
        r=subprocess.run(['bash',str(SCRIPT)],stdin=subprocess.DEVNULL,text=True,capture_output=True)
        self.assertEqual(r.returncode,2,r.stdout+r.stderr)
        self.assertIn('real Owner controlling TTY required',r.stderr)

    def test_only_g07_at_pinned_sha(self):
        s=SCRIPT.read_text()
        self.assertIn("readonly BRANCH='fix/p2-g07-fresh-zone-observation-20261110'",s)
        self.assertIn("readonly SHA='"+SHA+"'",s)
        self.assertIn('bash "$SRC/instructor/scripts/p2_owner_l3_wsl2.sh" --case G07',s)
        self.assertIn('gh repo clone',s)
        self.assertIn('AXIA_P2_OWNER_PINNED_SHA',s)
        self.assertNotIn('YES-P2-G07-GOAL',s)
        self.assertNotIn('kill -9',s)
        self.assertNotIn('--case G05',s)
        self.assertNotIn('--case G06',s)

if __name__=='__main__': unittest.main()
