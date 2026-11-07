"""Public CI privacy/no-motion assertions for exact SHA official Gazebo prelocal."""
import pathlib
import unittest
from unittest.mock import patch
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
S=(ROOT/"scripts/private_pr52_gazebo3_ci.py").read_text()
W=(ROOT/".github/workflows/pr52-gazebo3-current-sha.yml").read_text()

class Contract(unittest.TestCase):
    def test_exact_private_pin_and_protected_workflow(self):
        pin="b7eed78b9855ab1bd8eb96285abbe30c4379af72"
        self.assertIn(pin,S)
        self.assertIn(pin,W)
        self.assertIn("axia-instructor-sealed",W)
        self.assertIn("secrets.AXIA_CLOUD_CI",W)
    def test_existing_official_gazebo_runner_reused(self):
        self.assertIn('bridge.run_gate(Path(root),"gazebo3-prepause")',S)
        self.assertIn("ros-jazzy-nav2-minimal-tb3-sim",W)
        self.assertIn("ros-jazzy-ros-gz",W)
    def test_no_goal_or_fault_admission_in_this_workflow(self):
        self.assertIn('"goal_sent":False',S)
        self.assertIn('"fault_injected":False',S)
        self.assertIn('"start_called":False',S)
        self.assertIn('"gate_accepted":False',S)
        self.assertNotIn("run_p1_t08_wsl2_field_capture.sh",W)
        self.assertNotIn("AXIA_P1_CLOUD_G00_START_APPROVED=YES",W)
    def test_private_evidence_not_uploaded_to_public_actions(self):
        self.assertNotIn("upload-artifact",W)
        self.assertNotIn("cat _instructor_private",W)
        self.assertIn("rm -rf _instructor_private",W)

if __name__=="__main__":unittest.main()
