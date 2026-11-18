"""Task04 real public Gazebo #44237948105 postrun KeyError:'phase' regression.

Pure original official path relay schema (stage) must match CI reader.
No fake moving Nav2 Goal. Source is public Student SHA pinned in native job.
"""
import importlib.util
from pathlib import Path
from types import SimpleNamespace as S
import unittest

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/".github/workflows/axia-g07-task04-public-native-gui-xvfb-l2-20261118.yml"
STUDENT=ROOT.parent/"student/block_B/day07/h01_runtime/tools/d07_h01_path_visual.py"

class RealOfficialPathSchema(unittest.TestCase):
    def test_pinned_public_official_path_has_stage_not_phase(self):
        self.assertTrue(STUDENT.is_file())
        spec=importlib.util.spec_from_file_location("original_student_path_visual",STUDENT)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        msg=S(header=S(frame_id="map",stamp=S(sec=1,nanosec=0)),
              poses=[S(pose=S(position=S(x=0.0,y=0.0,z=0.0)))]*3)
        v=module.validate_official_path(msg,phase="before",current_clock=2.0)
        self.assertEqual(v["stage"],"before")
        self.assertNotIn("phase",v)
        self.assertEqual(module.PHASES,("before","intrusion","restored"))

    def test_native_ci_review_reads_the_actual_stage_property(self):
        txt=WORKFLOW.read_text()
        self.assertIn('p["stage"] for p in phases',txt)
        self.assertNotIn('p["phase"] for p in phases',txt)
        self.assertIn('p.get("rviz_subscription_count",0)>=1',txt)
        self.assertIn("AXIA_G07_TASK04_PUBLIC_REAL_GAZEBO_RVIZ_XVFB_PATH_SUBSCRIBER_L2_PASS",txt)

if __name__=="__main__":
    unittest.main()
