import importlib.util
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/'.github/workflows/p2-protected-minimal.yml'
M=ROOT/'scripts/p2_manifest.py'
sp=importlib.util.spec_from_file_location('p2_manifest',M)
mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)


class CIContract(unittest.TestCase):
    def test_sha_pinned_and_not_accepted(self):
        self.assertRegex(mod.SOURCE_SHA,r'^[0-9a-f]{40}$')
        self.assertEqual(mod.SCOPE,'P2_PRELOCAL_L0_L1_NO_GOAL_L2_ONLY')
        self.assertIs(mod.G05_G06_G07_ACCEPTED,False)

    def test_workflow_hardcodes_private_sha_in_every_job(self):
        text=WORKFLOW.read_text()
        self.assertGreaterEqual(text.count('ref: '+mod.SOURCE_SHA),3)
        self.assertGreaterEqual(text.count('test "$(git -c safe.directory="$PWD" rev-parse HEAD)" = '+mod.SOURCE_SHA),2)
        self.assertNotIn('pull_request_target:',text)

    def test_private_jobs_only_on_main_push(self):
        text=WORKFLOW.read_text()
        self.assertEqual(text.count("if: github.event_name == 'push' && github.ref == 'refs/heads/main'"),3)
        self.assertIn('environment: axia-instructor-sealed',text)
        self.assertIn('persist-credentials: false',text)
        self.assertNotIn('actions/upload-artifact',text)
        self.assertNotIn('issue_comment:',text)

    def test_only_no_goal_ros_script_is_run(self):
        text=WORKFLOW.read_text()
        self.assertIn('scripts/p2_no_goal_smoke_ci.sh',text)
        self.assertIn('scripts/p2_guard_ros_smoke_ci.sh',text)
        self.assertNotIn('p2_owned_process_fault.py --execute',text)
        self.assertNotIn('YES-P2-',text)


if __name__=='__main__':
    unittest.main()
