"""Public L0 no-ROS policy tests for standalone L1 isolated diagnostic."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
spec=importlib.util.spec_from_file_location("pr52_l1_fake_ros",ROOT/"scripts/pr52_l1_fake_ros.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
workflow=(ROOT/".github/workflows/pr52-l1-fake-ros.yml").read_text()


class L1PolicyTests(unittest.TestCase):
    def test_categorization(self):
        self.assertEqual(mod.classify("ROS_DIAGNOSTIC_UNAVAILABLE"),"ROS_DIAGNOSTIC_UNAVAILABLE")
        self.assertEqual(mod.classify("ModuleNotFoundError: no module"),"PYTHON_MODULE_MISSING")
        self.assertEqual(mod.classify("health_diagnostics={}"),"HEALTH_ASSERTION_FAILED")
        self.assertEqual(mod.classify("PRIVATE_RANDOM_STRING"),"OTHER_OR_MISSING_DIAGNOSTIC")

    def test_health_fields_are_allowlisted_and_tristate_only(self):
        raw="PRIVATE_PATH=/home/internal clock_ok=True scan_ok=False graph_ok=None cm_ok=False action_ready=True SECRET=password"
        out=mod.extract_health_flags(raw)
        self.assertEqual(out,{"clock_ok":"True","scan_ok":"False","graph_ok":"None",
                              "cm_ok":"False","action_ready":"True"})
        self.assertNotIn("PRIVATE_PATH",repr(out))
        self.assertNotIn("SECRET",repr(out))

    def test_failclosed_missing_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            rec, ok=mod._evidence(Path(d))
        self.assertFalse(ok)
        self.assertEqual(rec["reason"],"SUMMARY_MISSING_OR_AMBIGUOUS")

    def test_l1_is_separate_from_gazebo_and_protects_private_source(self):
        self.assertIn("workflow_dispatch:",workflow)
        self.assertIn("pr52-l1-fake-ros.request",workflow)
        self.assertIn("axia-instructor-sealed",workflow)
        self.assertIn("AXIA_P1_L0_PRIVATE_SAFE_DOMAIN_PASS",workflow)
        self.assertIn("secrets.AXIA_CLOUD_CI",workflow)
        self.assertNotIn("ros-jazzy-ros-gz",workflow)
        self.assertNotIn("upload-artifact",workflow)
        self.assertIn("rm -rf _instructor_private",workflow)
        self.assertIn("5a458a0ca8533b77e548dbb500b00fbe70d61942",workflow)
        self.assertIn("5a458a0ca8533b77e548dbb500b00fbe70d61942",(ROOT/"scripts/pr52_l1_fake_ros.py").read_text())

    def test_workflow_scripts_use_bash_not_posix_sh(self):
        # Container defaults to /bin/sh and rejects 'set -o pipefail'.
        self.assertIn('defaults:\\n  run:\\n    shell: bash'.replace('\\n','\n'),workflow)

    def test_exact_fakeros_evidence_runner_without_goal(self):
        s=(ROOT/"scripts/pr52_l1_fake_ros.py").read_text()
        self.assertIn('"--repeat","3"',s)
        self.assertIn('"--profile","ros-fake"',s)
        self.assertIn("len(stages)==12",s)
        self.assertIn("bridge.ros_workspace_build",s)
        self.assertNotIn("ros2 action send_goal",s)
        self.assertNotIn("ros2 topic pub",s)
        self.assertNotIn("upload-artifact",s)

if __name__=="__main__":
    unittest.main()
