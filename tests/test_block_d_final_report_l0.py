"""BLOCK_D final public audit report: RED until actual CI scope is documented."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"docs/reports/AXIA_BLOCK_D_FINAL_RELEASE_REPORT_20261121_KO.md"

class BlockDFinalReportContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=REPORT.read_text(encoding="utf-8")
    def test_actual_merged_student_and_instructor_main_pins(self):
        for s in (
            "2c1e7786d21e5f9385290e4bcedb9c4367c006fb",
            "33d7647e927dc0f3b948d25dd0561377fb455a08",
            "AXIA-G07-T04-DEMO-BASELINE-20261120-jrCIgoGl",
            "ae7d594b5452d96cc8802bc53bc8ad578fe99fb7",
        ):
            self.assertIn(s,self.report)
    def test_red_green_and_replay_scopes(self):
        for s in ("D13","D14","D15",
                  "10/10","20/20","18/18",
                  "8/8","18/18","7/7",
                  "intended_red=2","intended_red=11",
                  "44880178625","44880045629",
                  "21/21","141/141"):
            self.assertIn(s,self.report)
    def test_safety_limits_and_no_overclaim(self):
        for s in ("HOLD_RAW_REVIEW_AND_VISUAL_PENDING",
                  "FORMAL_SAFETY_TIMING_ACCEPTANCE=NOT_CLAIMED",
                  "CERTIFIED_ESTOP=false",
                  "ROS_GAZEBO_WSL2_NOT_RUN",
                  "VISUAL_CONTENT_NOT_VERIFIED",
                  "Guard","188.578","150ms",
                  "G09","S04","L0","main"):
            self.assertIn(s,self.report)
    def test_public_report_contains_student_and_private_guide_paths(self):
        for s in ("block_D/BLOCK_D_STUDENT_FINAL_GUIDE_KO.md",
                  "training/block_D/BLOCK_D_INSTRUCTOR_FINAL_GUIDE_KO.md",
                  "block_D/tools/verify_student_release.py",
                  "training/block_D/tools/verify_instructor_release.py",
                  "AXIA_BLOCK_D_RELEASE_VERIFICATION=OFFLINE_L0_PASS"):
            self.assertIn(s,self.report)
if __name__=="__main__":
    unittest.main()
