"""Actual #44534113749 never reached Gazebo: noble-security InRelease
HTTP source failed to fetch (APT rc100) while provisioning Xvfb/RViz.
Enforce HTTPS source normalization in disposable public CI container only.
Do not disable signature checking or change WSL2 Owner apt configuration.
"""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
WF=ROOT/".github/workflows/axia-d06-g07-native-nogoal-cm-clean-l2-20261119.yml"

class CiAptHttpsBootstrap(unittest.TestCase):
    def test_real_l2_ci_normalizes_ubuntu_sources_to_https(self):
        s=WF.read_text()
        self.assertIn('CI_ONLY_UBUNTU_APT_HTTPS_BEFORE_GAZEBO',s)
        self.assertIn('https://security.ubuntu.com/ubuntu',s)
        self.assertIn('https://archive.ubuntu.com/ubuntu',s)
        self.assertIn('Acquire::Retries=2',s)
        self.assertIn('Acquire::http::Timeout=20',s)
        self.assertIn('apt-get update',s)
        self.assertNotIn('Acquire::AllowInsecureRepositories',s)
        self.assertNotIn('APT::Get::AllowUnauthenticated',s)
        self.assertNotIn('trusted=yes',s)

    def test_does_not_change_owner_sim_or_safety(self):
        s=WF.read_text()
        self.assertIn("AXIA_G07_CI_SIM_GOAL_ALLOWED: '0'",s)
        self.assertIn("AXIA_G07_NO_GOAL_ORDERED_SHUTDOWN: '1'",s)
        self.assertIn("assert gap<=.300",s)
        self.assertIn("AXIA_G07_NO_GOAL_WITNESS_HANDOFF: '1'",s)
        self.assertIn('native/g07_ordered_shutdown.json',s)

if __name__=="__main__":unittest.main()
