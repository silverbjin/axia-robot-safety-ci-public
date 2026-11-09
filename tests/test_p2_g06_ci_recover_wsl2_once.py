"""Public no-network contract: CI repair must fail closed without Owner TTY."""
from pathlib import Path
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/axia_p2_g06_ci_recover_wsl2_once.sh'

class G06CiRecover(unittest.TestCase):
    def test_syntax_and_offline_selfcheck(self):
        self.assertEqual(subprocess.run(['bash','-n',str(SCRIPT)]).returncode,0)
        p=subprocess.run(['bash',str(SCRIPT),'--self-check'],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn('L3_NOT_RUN',p.stdout)

    def test_missing_controlling_tty_refuses_before_github(self):
        p=subprocess.run(['bash',str(SCRIPT)],stdin=subprocess.DEVNULL,capture_output=True,text=True)
        self.assertEqual(p.returncode,2,p.stdout+p.stderr)
        self.assertIn('interactive Owner TTY',p.stderr)

    def test_scoped_environment_change_and_one_g06(self):
        s=SCRIPT.read_text()
        self.assertIn("BRANCH='release/p2-g06-cm-ttl-20261110'",s)
        self.assertIn("CI_SHA='c14819c7109fc143de14cc7935880b922c2d0074'",s)
        self.assertIn("PRIVATE_SHA='276c13d4d046df0f0ee73e7953d7639f312e0029'",s)
        self.assertIn("WRAPPER_BLOB='441e40a5c1d8dfb65dfb2d1c358f77d652debe73'",s)
        self.assertIn("gh run rerun",s)
        self.assertIn('bash "$FILE" --case G06',s)
        self.assertIn("-f 'type=branch'",s)
        for forbidden in ('bash "$FILE" --case G05','bash "$FILE" --case G07',
                          'kill -9','pkill','git reset --hard','printf YES-P2',
                          "gh api -X DELETE"):
            self.assertNotIn(forbidden,s)

if __name__=='__main__':
    unittest.main()
