"""Only source policy, no ROS or network during L0."""
import importlib.util, pathlib,sys,unittest
R=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/"scripts"))
sp=importlib.util.spec_from_file_location("focus",R/"scripts/pr52_l1_health_focus.py")
M=importlib.util.module_from_spec(sp);sp.loader.exec_module(M)
W=(R/".github/workflows/pr52-l1-health-focus.yml").read_text()


class FocusTests(unittest.TestCase):
    def test_exact_sha_and_per_case_diagnostic(self):
        self.assertEqual(len(M.CASE_IDS),3)
        self.assertEqual(M.PIN,"5a458a0ca8533b77e548dbb500b00fbe70d61942")
        self.assertIn("ref: "+M.PIN,W)
        self.assertEqual(M.diagnosis("initial health never ready clock_ok=False scan_ok=True")["reason"],
                         "SUPERVISOR_BOOT_HEALTH_TIMEOUT")
        self.assertEqual(M.diagnosis("initial health never ready clock_ok=False scan_ok=True")["flags"],
                         {"clock_ok":"False","scan_ok":"True"})
    def test_assertion_location_is_only_numeric_and_allowlisted(self):
        item=M.diagnosis("failed at tests/ros_integration/test_p1_t04_action.py:262: AssertionError")
        self.assertEqual(item["assert_line"],262)

    def test_no_gazebo_in_minimal_3x_probe(self):
        self.assertIn("workflow_dispatch",W)
        self.assertIn("axia-instructor-sealed",W)
        self.assertIn(M.PIN,W)
        self.assertNotIn("ros-jazzy-ros-gz",W)
        self.assertNotIn("upload-artifact",W)
        self.assertNotIn("ros2 action send_goal",W)
        self.assertNotIn("upload-artifact",(R/"scripts/pr52_l1_health_focus.py").read_text())

if __name__=="__main__":unittest.main()
