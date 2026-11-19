"""G07 99PX1WNS regression: ROS_DOMAIN_ID=86 foreign clocks before Nav2 Startup."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
HELPER=ROOT/'scripts/axia_g07_task04_select_free_domain.py'
OWNER=ROOT/'scripts/axia_g07_task04_owner_moving_l3_once.sh'

class ForeignClockDomain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('domain',HELPER)
        cls.mod=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def test_field_first_cross_clock_is_rejected(self):
        # CDR /clock from 99PX1WNS toggled 1940.5 <-> 0.04s;
        # CZObXAdP baseline monotonically advanced 0 -> 84.627s.
        self.assertGreater(self.mod.count_clock_backwards([1940.511,.075,1940.514,.081,1940.523]),0)
        self.assertEqual(self.mod.count_clock_backwards([0.006,0.009,.012,84.627]),0)

    def test_auto_rejects_busy_domain_and_chooses_clean_one(self):
        seen=[]
        def probe(domain):
            seen.append(domain)
            return {'node_count':2 if domain==86 else 0,
                    'clock_publishers':1 if domain==86 else 0,
                    'scan_publishers':0}
        result=self.mod.choose_domain([86,87],probe=probe)
        self.assertEqual(result['domain_id'],87)
        self.assertEqual(result['status'],'SELECTED')
        self.assertEqual(seen,[86,87])
        self.assertEqual(result['candidates'][0]['status'],'BUSY')

    def test_explicit_86_must_fail_closed_when_clock_already_running(self):
        outcome=self.mod.choose_domain([86],probe=lambda d: {'node_count':1,'clock_publishers':1,'scan_publishers':0})
        self.assertEqual(outcome['status'],'NO_FREE_DOMAIN')
        self.assertIsNone(outcome['domain_id'])

    def test_graph_unknown_fails_closed(self):
        outcome=self.mod.choose_domain([88],probe=lambda d: {'status':'ERROR'})
        self.assertEqual(outcome['status'],'NO_FREE_DOMAIN')

    def test_owner_domain_helper_pin_matches_exact_git_blob(self):
        import re
        import subprocess
        src=OWNER.read_text()
        pin=re.search(r"readonly DOMAIN_HELPER_GIT_BLOB='([0-9a-f]{40})'",src)
        self.assertIsNotNone(pin)
        actual=subprocess.run(["git","hash-object",str(HELPER)],
                              text=True,capture_output=True,check=True).stdout.strip()
        self.assertEqual(pin.group(1),actual)

    def test_owner_replaces_default_domain_86_before_launch(self):
        src=OWNER.read_text()
        self.assertIn('axia_g07_task04_select_free_domain.py',src)
        self.assertIn('AXIA_G07_TASK04_ROS_DOMAIN_SELECTED=',src)
        self.assertIn('domain_selection.json',src)
        self.assertNotIn('AXIA_G07_TASK04_DOMAIN_ID:-86',src)
        self.assertIn('AXIA_G07_CI_SIM_GOAL_ALLOWED=0',src)
        self.assertIn('NATIVE_BUILD_CACHE_ROOT=',src)

if __name__=='__main__':unittest.main()
