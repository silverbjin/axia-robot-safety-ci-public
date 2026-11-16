"""L0 only: D07 WSL2 owner bootstrap contract, using FAKE source fixtures.

These tests NEVER start ROS/Gazebo nor prove actual WSL2 GUI or safety.
The production verifier must still require original real ROS/Gazebo/X11 data.
"""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/axia_d07_h01_gui_owner_wsl2_once.sh"
PRIVATE_TOOLS=ROOT.parent/"instructor"/"tools"
PRIVATE_SHA="0e16c3781cdee603518a653f120a3be352e5f7b2"

def embedded():
    text=SCRIPT.read_text()
    first=text.index("<<'PY'\n")+len("<<'PY'\n")
    last=text.index("\nPY\nVERDICT_RC",first)
    return text[first:last]

def phase(name,i):
    return dict(stage=name,source="official_compute_path_to_pose",
        frame="map",native_action_result_relayed=True,visualization_only=True,
        goal_sent=False,robot_moved=False,source_header_stamp=10.+10*i,
        pose_count=52,rviz_subscription_count=1,
        real_scan_stamp=10.5+10*i,real_costmap_stamp=11.+10*i)

def verify(root, windows, runner_rc=0, valid=True):
    if valid:
        target=root/"real-l2"/"d07_h01_geometry"
        target.mkdir(parents=True)
        (target/"d07_h01_geometry.json").write_text(json.dumps(dict(
            source_sha=PRIVATE_SHA,goal_sent=False,real_nav2=True,
            real_laser_scan=True,obstacle_pose_native_ack=True,
            actual_costmap_obstacle_observed=True,obstacle_restored_away=True,
            route_oracle={"geometry_ready":True},
            certified_estop=False,formal_accepted=False)))
        stages=[phase(s,i) for i,s in enumerate(("before","intrusion","restored"))]
        (target/"phase_evidence.jsonl").write_text(
            "".join(json.dumps(p)+"\n" for p in stages))
    (root/"x11_real_windows.txt").write_text(windows)
    result=subprocess.run(["python3","-",str(PRIVATE_TOOLS),str(root),
                            PRIVATE_SHA,str(runner_rc),"43793585641"],
        input=embedded(),text=True,capture_output=True,check=False)
    outcome=json.loads((root/"owner_l3_verdict.json").read_text())
    return result,outcome

class OwnerBootstrapContract(unittest.TestCase):
    def test_static_l0_compiles_embedded_verifier(self):
        p=subprocess.run(["bash",str(SCRIPT),"--self-check"],
            capture_output=True,text=True,check=False)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn("AXIA_D07_H01_OWNER_PY_VERDICT_STATIC_COMPILE_PASS",p.stdout)
        self.assertIn("NO_ROS_NO_GAZEBO_NO_GOAL",p.stdout)

    def test_real_watch_sentinel_lifecycle_exercised_in_public_ci(self):
        # WSL2 field failure: touch: cannot touch '': No such file or directory.
        # --self-check must execute the SAME helper used by --run. No GUI or
        # ROS is started; a return marker alone is not runtime L3 acceptance.
        proc=subprocess.run(["bash",str(SCRIPT),"--self-check"],
            capture_output=True,text=True,check=False)
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertIn("AXIA_D07_H01_WATCH_SENTINEL_LIFECYCLE_L0_PASS",
                      proc.stdout)
        src=SCRIPT.read_text()
        self.assertIn('axia_d07_watch_start "$CHECK_DIR"',src)
        self.assertIn('axia_d07_watch_start "$RUN"',src)
        self.assertNotIn("WATCH=''\\n",src[src.index('RUN="$(mktemp'):])
        self.assertNotIn('touch "$WATCH"',src)

    def test_failure_archive_uses_same_helper_in_runtime_and_ci(self):
        # Even first pre-ROS shell error after evidence root creation must
        # be bundled before owner checkout cleanup, without a new WSL2 retry.
        proc=subprocess.run(["bash",str(SCRIPT),"--self-check"],
            capture_output=True,text=True,check=False)
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertIn("AXIA_D07_H01_FAILURE_BUNDLE_L0_PASS",proc.stdout)
        src=SCRIPT.read_text()
        self.assertIn('axia_d07_pack_failure "$CHECK_DIR"',src)
        self.assertIn('axia_d07_pack_failure "$RUN"',src)

    def test_synthetic_complete_evidence_can_only_pass_scoped_gui(self):
        self.assertTrue(PRIVATE_TOOLS.is_dir(),"private tools L0 checkout missing")
        with tempfile.TemporaryDirectory() as folder:
            r,o=verify(Path(folder),"RVIZ\nGAZEBO\n")
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertTrue(o["owner_wsl2_gui_l3_accepted"])
            self.assertFalse(o["moving_goal_accepted"])
            self.assertFalse(o["formal_axia_mvp_accepted"])
            self.assertFalse(o["certified_estop"])

    def test_missing_x11_or_nonzero_runner_holds(self):
        self.assertTrue(PRIVATE_TOOLS.is_dir())
        for windows,rc in (("RVIZ\n",0),("RVIZ\nGAZEBO\n",2)):
            with self.subTest(windows=windows,runner_rc=rc):
                with tempfile.TemporaryDirectory() as folder:
                    r,o=verify(Path(folder),windows,runner_rc=rc)
                    self.assertEqual(r.returncode,3,r.stderr)
                    self.assertFalse(o["owner_wsl2_gui_l3_accepted"])

    def test_missing_real_raw_evidence_never_accepts(self):
        with tempfile.TemporaryDirectory() as folder:
            r,o=verify(Path(folder),"RVIZ\nGAZEBO\n",valid=False)
            self.assertEqual(r.returncode,3,r.stderr)
            self.assertFalse(o["owner_wsl2_gui_l3_accepted"])
