"""D07-H01 field handoff L0 only. Does NOT run Gazebo, ROS or WSLg."""
from pathlib import Path
import json
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/axia_d07_h01_instructor_l3_wsl2_once.sh"
PIN="c25d63d928da0cfb6513b191e582742fd2f0a6bb"
STAGES=("free","intrusion","lateral","restored")


def synthetic_session(where,cycles=2,goal=False,teardown="P2_L2_GRACEFUL_TEARDOWN"):
    root=Path(where)
    geo=root/"native/evidence/d07_h01_geometry"
    geo.mkdir(parents=True)
    (root/"native/source.txt").write_text("student_source_sha="+PIN+"\n")
    (geo/"d07_h01_geometry.json").write_text(json.dumps({
        "real_nav2":True,
        "real_laser_scan":True,
        "actual_costmap_obstacle_observed":True,
        "obstacle_restored_away":True,
        "goal_sent":goal,
        "robot_moved":False,
        "certified_estop":False,
    }))
    with (geo/"teaching_cycle_evidence.jsonl").open("w") as file:
        for cycle in range(1,cycles+1):
            for stage in STAGES:
                file.write(json.dumps({
                    "stage":stage,"cycle":cycle,
                    "real_native_gazebo_pose_ack":True,
                    "real_scan_stamp":100.0,
                    "real_costmap_stamp":100.1,
                    "official_action":"ComputePathToPose",
                    "path_frame":"map",
                    "path_pose_count":52,
                    "rviz_path_subscribers":1,
                    "goal_sent":goal,
                    "cmd_vel_sent":False,
                    "robot_moved":False,
                    "certified_estop":False,
                })+"\n")
    (root/"native/evidence/teardown.txt").write_text(teardown+"\n")
    (root/"native/evidence/d07_h01_teaching_loop.log").write_text(
        "D07_H01_TEACHING_CTRL_C_STOP OPERATOR\n")
    (root/"windows-triple.txt").write_text(
        'Gazebo\nRViz\nrqt_graph\n')


def verify(path):
    return subprocess.run(
        ["bash",str(SCRIPT),"--verify",str(path)],
        text=True,capture_output=True,timeout=12,
    )


class D07H01InstructorL3Contract(unittest.TestCase):
    def test_l0_self_check_does_not_run_ros_or_gazebo(self):
        r=subprocess.run(["bash",str(SCRIPT),"--self-check"],
                         capture_output=True,text=True,timeout=12)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn("WSL2_NOT_RUN GAZEBO_NOT_RUN",r.stdout)

    def test_bash_parses_and_reuses_pinned_public_main_without_goal(self):
        s=SCRIPT.read_text()
        self.assertEqual(
            subprocess.run(["bash","-n",str(SCRIPT)]).returncode,0)
        for name in (
            PIN, "axia-robot-safety-student.git",
            "run_d07_h01_gazebo_rviz_student_once.sh",
            "AXIA_G07_CI_SIM_GOAL_ALLOWED=0",
            "D07_H01_TEACHING_CTRL_C_STOP OPERATOR",
            "P2_L2_GRACEFUL_TEARDOWN",
            "AXIA_MVP_DEMO_ACCEPTED=HOLD",
            "AXIA_D07_H01_L3_DATA_VERDICT=READY_FOR_OWNER_PIXEL_REVIEW",
            "git -C \"$SRC\" rev-parse HEAD",
            "GITHUB_ACTIONS",
            "ROS_DOMAIN_ID=95",
            "GZ_PARTITION",
            "xwd",
            "sha256sum -c SHA256SUMS",
        ):
            self.assertIn(name,s,name)
        for forbidden in ("ros2 action send_goal","ros2 topic pub",
                          "pkill -f","wsl --shutdown",
                          "AXIA_MVP_DEMO_ACCEPTED=PASS"):
            self.assertNotIn(forbidden,s)
        self.assertIn("kill -INT -- \"-$RQT_PID\"",s)
        self.assertIn('tar --exclude=',s)

    def test_ros_environment_is_sourced_before_command_discovery(self):
        # A fresh WSL2 shell need not pre-source /opt/ros/jazzy;
        # the one-shot must not falsely reject ros2 before sourcing it.
        s=SCRIPT.read_text()
        self.assertLess(s.index("source /opt/ros/jazzy/setup.bash"),
                        s.index("for bin in git ros2 gz rviz2"))

    def test_rqt_graph_is_manual_separate_terminal_and_not_l3_child(self):
        # Owner requested rqt_graph in another terminal, never auto-start.
        s=SCRIPT.read_text()
        self.assertIn("--rqt)",s)
        self.assertIn('exec ros2 run rqt_graph rqt_graph',s)
        self.assertIn("AXIA_D07_H01_L3_RQT_INDEPENDENT_TERMINAL",s)
        self.assertNotIn('RQT_PID=',s)
        self.assertNotIn('setsid bash -c',s)
        self.assertNotIn("windows-triple.txt",s)
        self.assertIn("windows-gazebo-rviz.txt",s)

    def test_actual_owner_geometry_without_robot_moved_field_is_valid(self):
        # Actual WSL2 uX8uxx0z geometry.json lacks robot_moved; it has
        # motion_admitted=false. Each real teaching-cycle row has robot_moved=false.
        with tempfile.TemporaryDirectory() as folder:
            synthetic_session(folder)
            p=Path(folder)/"native/evidence/d07_h01_geometry/d07_h01_geometry.json"
            geo=json.loads(p.read_text())
            del geo["robot_moved"]
            geo["motion_admitted"]=False
            p.write_text(json.dumps(geo))
            r=verify(folder)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)

    def test_teaching_first_shutdown_error_blocks_acceptance(self):
        with tempfile.TemporaryDirectory() as folder:
            synthetic_session(folder)
            p=Path(folder)/"native/evidence/d07_h01_teaching_loop.log"
            p.write_text(p.read_text()+
                "D07_H01_TEACHING_BLOCKED_FIRST_BOUNDARY RCLError:failed to shutdown: rcl_shutdown already called\n")
            r=verify(folder)
            self.assertEqual(r.returncode,3)
            self.assertIn("FIRST_TEACHING_RUNTIME_FAILURE",r.stdout)

    def test_two_real_cycle_schema_fixture_ready_for_pixel_review(self):
        with tempfile.TemporaryDirectory() as folder:
            synthetic_session(folder)
            r=verify(folder)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            self.assertIn("COMPLETE_PHYSICAL_CYCLES=2",r.stdout)
            self.assertIn("DATA_VERDICT=READY_FOR_OWNER_PIXEL_REVIEW",r.stdout)
            self.assertIn("AXIA_MVP_DEMO_ACCEPTED=HOLD",r.stdout)

    def test_one_cycle_or_moving_goal_must_not_be_accepted(self):
        with tempfile.TemporaryDirectory() as folder:
            synthetic_session(folder,cycles=1)
            r=verify(folder)
            self.assertEqual(r.returncode,3)
            self.assertIn("TWO_COMPLETE_REAL_PHYSICAL_REPEAT_CYCLES_NOT_PROVEN",r.stdout)
        with tempfile.TemporaryDirectory() as folder:
            synthetic_session(folder,goal=True)
            r=verify(folder)
            self.assertEqual(r.returncode,3)
            self.assertIn("UNSAFE_OR_UNVERIFIED_goal_sent",r.stdout)

    def test_forced_teardown_or_no_operator_ctrl_c_is_hold(self):
        with tempfile.TemporaryDirectory() as folder:
            synthetic_session(folder,teardown="P2_L2_FORCED_TEARDOWN")
            r=verify(folder)
            self.assertEqual(r.returncode,3)
            self.assertIn("CLEAN_NATIVE_TEARDOWN_NOT_PROVEN",r.stdout)
        with tempfile.TemporaryDirectory() as folder:
            synthetic_session(folder)
            (Path(folder)/"native/evidence/d07_h01_teaching_loop.log").unlink()
            r=verify(folder)
            self.assertEqual(r.returncode,3)
            self.assertIn("OPERATOR_CTRL_C_STOP_NOT_PROVEN",r.stdout)


if __name__=="__main__":
    unittest.main()
