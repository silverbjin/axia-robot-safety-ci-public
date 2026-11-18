"""Owner first PREGOAL field observation regression (ROS-free L0).

Values are exact rounded medians supplied with the Owner evidence bundle.
This test never sends a Goal, publishes a synthetic LaserScan, or proves L2.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = Path(os.environ.get(
    "AXIA_G07_STUDENT_RUNTIME",
    ROOT / "student" / "block_B" / "day07" / "h01_runtime"))
sys.path.insert(0, str(RUNTIME / "tools"))

if (RUNTIME / "tools" / "p2_g07_owner_pregoal_l2.py").is_file():
    from p2_g07_owner_pregoal_l2 import build_pregoal_baseline, save_pregoal_baseline, parse_gz_model_pose
else:
    # Public generic pytest does NOT checkout the Student repository.
    # The dedicated Owner contract workflow checks the exact Student SHA.
    build_pregoal_baseline = None
    save_pregoal_baseline = None
    parse_gz_model_pose = None


@unittest.skipUnless(build_pregoal_baseline is not None,
                     "exact Student source requires dedicated pinned CI checkout")
class FirstOwnerPregoalFailureL0(unittest.TestCase):
    def _record(self, front, side):
        return build_pregoal_baseline(
            front_m=front, side_m=side,
            scan_topic="/safety/scan", publisher_identity=None,
            scan_frame_id="base_scan",
            scan_header_stamp=31.2, scan_host_receive_time=1784500000.2,
            gazebo_robot_world_pose=None, initial_obstacle_world_pose=None)

    def test_owner_recorded_nearfield_blocks_before_fixture(self):
        record=self._record(.527, .630)
        self.assertEqual(record["status"], "BLOCKED")
        self.assertEqual(record["first_failure"], "OWNER_PREGOAL_NOT_CLEAR_BEFORE_FIXTURE")
        self.assertFalse(record["goal_sent"])
        self.assertEqual(record["front_m"], .527)
        self.assertEqual(record["side_m"], .630)
        self.assertEqual(record["required_front_m"], .75)
        self.assertEqual(record["required_side_m"], 1.20)
        self.assertIsNone(record["gazebo_robot_world_pose"])
        self.assertIsNone(record["initial_obstacle_world_pose"])
        with tempfile.TemporaryDirectory() as folder:
            save_pregoal_baseline(Path(folder), record)
            persisted=json.loads((Path(folder)/"pregoal_baseline.json").read_text())
            self.assertEqual(persisted, record)

    def test_real_clear_thresholds_remain_strict(self):
        for front,side,expected in (
            (.75,1.30,"BLOCKED"), (1.10,1.20,"BLOCKED"),
            (1.10,1.21,"CLEAR")):
            with self.subTest(front=front,side=side):
                self.assertEqual(self._record(front,side)["status"],expected)

    def test_native_gz_model_pose_parse_or_unknown(self):
        model_output = """Requesting state for world [default]...
Model: [18]
- Name: turtlebot3_waffle
- Pose [ XYZ (m) ] [ RPY (rad) ]:
[-2.000000 | -0.500000 | 0.100000]
[0.000000 | 0.000000 | 1.570796]
"""
        self.assertEqual(parse_gz_model_pose(model_output),
                         {"x": -2.0, "y": -.5, "z": .1, "roll": 0.0,
                          "pitch": 0.0, "yaw": 1.570796})
        self.assertIsNone(parse_gz_model_pose("no model"))
        self.assertIsNone(parse_gz_model_pose(
            model_output.replace("-2.000000", "nan")))

    def test_unknown_poses_are_not_invented(self):
        record=self._record(.527,.630)
        self.assertIsNone(record["gazebo_robot_world_pose"])
        self.assertIsNone(record["initial_obstacle_world_pose"])


if __name__=="__main__":
    unittest.main()
