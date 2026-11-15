"""Public-source-only contract: instructor deletion never runs on GitHub Actions."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/"scripts/axia_d04_d08_instructor_superseded_prune.py"
s=SCRIPT.read_text()
spec=importlib.util.spec_from_file_location("owner_cleanup",SCRIPT)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class InstructorCleanupSourceTests(unittest.TestCase):
    def test_known_scope_and_no_automatic_deletion(self):
        self.assertEqual(len(m.PROVENANCE),8)
        self.assertEqual(m.REPO,"silverbjin/axia-robot-safety-instructor")
        self.assertIn("parser.add_argument(\"--apply\",action=\"store_true\")",s)
        self.assertNotIn("GH_TOKEN",s)
        self.assertNotIn("send_goal_async",s)
        self.assertNotIn("ros2 topic pub",s)
    def test_no_pr_planning_branch_has_fixed_file_proof(self):
        self.assertEqual(m.PROVENANCE[m.NO_PR_BRANCH][0],None)
        self.assertEqual(len(m.RETAINED_BLOBS),2)
        self.assertEqual(len(m.NO_PR_HEAD),40)

if __name__=="__main__":
    unittest.main()
