"""C29-04: compare exact same C27 cold-run with CycloneDDS, but NEVER
substitute this result for an unverified instructor WSL2 RMW.
"""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
FILE=ROOT/".github/workflows/axia-d06-c29-cyclonedds-ab-two-cold-l2.yml"

class C29RmwIsolatedAB(unittest.TestCase):
    def test_no_hidden_source_or_safety_contract_change(self):
        s=FILE.read_text()
        self.assertIn("cycle: [1, 2]",s)
        self.assertIn("max-parallel: 2",s)
        self.assertIn("ref: 6c79c09d91f13c81961492eb30e66d99d307831c",s)
        self.assertIn("cc3c64f7ae769a11d9daad4acdbdb48141253f7c",s)
        self.assertIn("72a117d9a1b22748ffd16171d213916c095a623e",s)
        self.assertIn("RMW_IMPLEMENTATION: rmw_cyclonedds_cpp",s)
        self.assertIn('nav["rmw_implementation_identifier"]=="rmw_cyclonedds_cpp"',s)
        self.assertIn("assert gap<=.300",s)
        self.assertIn('"NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE"',s)
        self.assertIn('assert audit["cm_exit_code"]==0',s)
        self.assertIn('assert gz_clean and not gz_bad',s)
        self.assertIn("G07_GAZEBO_SERVER_NATIVE_EXIT0_BEFORE_GROUP_SIGINT",s)
        self.assertIn("C29_RMW_AB_NOT_WSL2_OWNER_PARITY",s)
        self.assertNotIn("AXIA_MVP_DEMO_ACCEPTED=PASS",s)
        self.assertIn("AXIA_G07_CI_SIM_GOAL_ALLOWED: '0'",s)
    def test_same_real_world_and_bounded_artifacts(self):
        s=FILE.read_text()
        for k in ("Actual same-world Gazebo and official Nav2 CM NO_GOAL teardown",
                  "native/d06_gz_scan_receipts.jsonl",
                  "native/d06_ros_scan_receipts.jsonl",
                  "native/g07_wslg_sensor_truth.json",
                  "native/g07_ordered_shutdown.json",
                  "native/g07_shutdown_audit.json",
                  "name: axia-d06-c29-cyclone-ab-cycle-"):
             self.assertIn(k,s)

if __name__=="__main__":unittest.main()
