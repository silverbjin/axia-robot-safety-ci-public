"""CI-only display sidecar contract: no Goal/control authority, no Owner bypass."""
from pathlib import Path
import os
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"d06/scripts/g07_unified_ci_readonly_display.sh"

class UnifiedGuiSidecarContract(unittest.TestCase):
    def test_single_sidecar_script_exists_and_shell_syntax_valid(self):
        self.assertTrue(SCRIPT.is_file(), "G07_UNIFIED_CI_READONLY_DISPLAY_MISSING")
        result=subprocess.run(["bash","-n",str(SCRIPT)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
    def test_ci_only_no_ros_no_goal_denies_external_execution(self):
        result=subprocess.run(["bash",str(SCRIPT),"/tmp","/tmp"],
            capture_output=True,text=True,env={"PATH":os.environ.get("PATH","")},timeout=5)
        self.assertEqual(result.returncode,3)
        self.assertIn("G07_UNIFIED_GUI_CI_ONLY_NO_ROS_NO_GOAL",result.stdout+result.stderr)
    def test_readonly_guard_and_real_display_attestation(self):
        s=SCRIPT.read_text()
        for x in ("GITHUB_ACTIONS","AXIA_P0_SIM_ONLY","AXIA_G07_CI_SIM_GOAL_ALLOWED",
                  "startup_verdict.json","SMOKE_READY","rviz2","d06_readonly_monitor.py",
                  "xwininfo","DISPLAY_WINDOW"):
            self.assertIn(x,s)
        for x in ("ros2 action send_goal","ros2 topic pub /cmd_vel",
                  "YES-P2-G07-GOAL","p2_owner_l3_wsl2.sh"):
            self.assertNotIn(x,s)

    def test_ros_environment_is_sourced_before_rviz_command_discovery(self):
        s=SCRIPT.read_text()
        self.assertIn("source /opt/ros/jazzy/setup.bash",s)
        self.assertLess(s.index("source /opt/ros/jazzy/setup.bash"),
                        s.index("for cmd in rviz2 gz xwininfo"),
                        "CI_GUI_SIDECAR_ROS_PATH_MUST_BE_ACTIVE_BEFORE_RVIZ_CHECK")

    def test_gui_l2_overlay_sources_ros_before_rviz_lookup(self):
        workflow=(ROOT/".github/workflows/axia-g07-unified-gui-one-goal-l2.yml").read_text()
        overlay=workflow.split("      - name: Install test-only official RViz and Xvfb overlay",1)[1].split("      - name: Isolated S02",1)[0]
        lookup=overlay.index("for cmd in Xvfb rviz2 xwininfo gz")
        source=overlay.find("source /opt/ros/jazzy/setup.bash")
        self.assertGreaterEqual(source,0,"CI_GUI_OVERLAY_ROS_ENV_NOT_SOURCED")
        self.assertLess(source,lookup,"CI_GUI_RVIZ_BIN_DISCOVERY_BEFORE_ROS_SETUP")

    def test_renderer_and_readonly_observer_use_distinct_advisory_cpus(self):
        # Actual #43683837146: a native 150ms CM/Guard deadline was exceeded
        # while Xvfb+Gazebo GUI+RViz were on unrestricted host cores.
        # Read-only Marker no longer shares CM; Guard/Nav2/CM policy unchanged.
        from d06.live.d06_gui_cpu_plan import select_cpu, select_monitor_cpu
        self.assertEqual(select_cpu({2,3,4,5}),2)
        self.assertEqual(select_monitor_cpu({2,3,4,5}),5)
        self.assertNotEqual(select_cpu({2,3,4,5}),select_monitor_cpu({2,3,4,5}))
        with self.assertRaises(ValueError):
            select_monitor_cpu({2,3,4})
        # The same physical GUI process launcher is invoked in Xvfb and WSLg.
        shared=ROOT/"d06/scripts/g07_shared_gui_clients.sh"
        self.assertTrue(shared.is_file(),"GUI_CI_OWNER_COMMON_RUNTIME_MISSING")
        s=shared.read_text()
        self.assertIn('d06_gui_cpu_plan.py',s)
        self.assertIn('--role monitor',s)
        self.assertIn('taskset -c "$GUI_CPU" nice -n 19 rviz2',s)
        self.assertIn('taskset -c "$GUI_CPU" nice -n 19 gz sim -g',s)
        self.assertIn('taskset -c "$MONITOR_CPU" nice -n 15 python3',s)
        self.assertIn('G07_UNIFIED_GUI_CPU_PARTITION',s)
        self.assertNotIn('taskset -cp',s)  # Never re-affinity safety nodes.
        self.assertIn('g07_shared_gui_clients.sh',SCRIPT.read_text())
        owner=(ROOT/"d06/scripts/d06_rviz_sidecar.sh").read_text()
        self.assertIn('g07_shared_gui_clients.sh',owner)
        self.assertIn('AXIA_G07_UNIFIED_GUI_SIDECAR', (ROOT/"d06/scripts/g07_unified_final_owner_wsl2_once.sh").read_text())

    def test_gui_l2_cpu_admission_is_checked_before_p4_one_goal(self):
        workflow=(ROOT/".github/workflows/axia-g07-unified-gui-one-goal-l2.yml").read_text()
        cpu_check="python3 unified-public/d06/live/d06_gui_cpu_plan.py"
        self.assertIn(cpu_check,workflow)
        self.assertIn("python3 unified-public/d06/live/d06_gui_cpu_plan.py --role monitor",workflow)
        self.assertLess(workflow.index(cpu_check),
                        workflow.index("      - name: Real Harmonic official TB3 Waffle and Nav2 ONE bounded simulation Goal"))
        self.assertIn("G07_UNIFIED_GUI_CPU_PREFLIGHT_NO_GOAL_PASS",workflow)

if __name__=="__main__":
    unittest.main()
