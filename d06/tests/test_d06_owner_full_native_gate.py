"""Owner WSL2 NVIDIA single-run acceptance MUST inspect native child exit proofs.
This is an offline fixture of the actual strict Gazebo L2 #44461627846:
no ROS/Gazebo launched in unit tests. Parent GRACEFUL alone can never pass.
"""
import io, json, pathlib, subprocess, sys, tarfile, tempfile, unittest

ROOT=pathlib.Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh"
ROOT_NAME="d06-wslg-sensor-mocked"
BASE={
"native/g07_wslg_sensor_truth.json":{
 "status":"NO_GOAL_SENSOR_WINDOW_CLEAR_CANDIDATE","reasons":[],
 "goal_sent":False,"fixture_moved":False,
 "dual_topic_required_observation_sec":20,
 "dual_topic_actual_wall_observation_sec":20.003,
 "startup_pre_both_scan_diagnostics":{
    "both_topics_ready":True,"pre_ready_observations_not_motion_authority":True},
 "metrics":{
    "raw":{"count":196,"max_receipt_gap_sec":.127526,
           "first_receipt_ttl_breach_at_index":None},
    "safety":{"count":196,"clear_count":196,"max_receipt_gap_sec":.125545,
        "first_receipt_ttl_breach_at_index":None,
        "front_median_m":1.414726,"side_median_m":2.520725}}
},
"native/g07_ordered_shutdown.json":{
 "status":"NAV2_LIFECYCLE_SHUTDOWN_ACK","navigation_ack":True,
 "localization_ack":True,"cm_managed_by_navigation":True},
"native/g07_shutdown_audit.json":{
 "status":"SHUTDOWN_CLEAN_CANDIDATE","cm_exit_code":0},
"native/teardown.txt":"P2_L2_GRACEFUL_TEARDOWN\n",
"native/g07_gz_world_pause.log":"data: true\n",
"native/g07_witness_probe_complete.signal":"G07_READONLY_SENSOR_PROBE_FINISHED\n",
"native/g07_witness_stopped.ack":"G07_READONLY_WITNESSES_STOPPED\n",
"native/launch.log":"[INFO] [gz-21]: process has finished cleanly [pid 111]\n"
                    "[INFO] [collision_monitor-16]: process has finished cleanly [pid 222]\n",
}

def make_tar(path,patch=None):
    src={k:(json.loads(json.dumps(v)) if isinstance(v,dict) else v) for k,v in BASE.items()}
    if patch:
        patch(src)
    with tarfile.open(path,"w:gz") as tar:
        for name,value in src.items():
            b=(json.dumps(value).encode() if isinstance(value,dict) else value.encode())
            info=tarfile.TarInfo(ROOT_NAME+"/"+name)
            info.size=len(b)
            tar.addfile(info,io.BytesIO(b))

def gate_code():
    s=SCRIPT.read_text()
    a=s.split("# D06_OWNER_NO_GOAL_NATIVE_GATE_START",1)[1]
    a=a.split("# D06_OWNER_NO_GOAL_NATIVE_GATE_END",1)[0]
    return a.split("<<'PY'\n",1)[1].split("\nPY",1)[0]

def check(patch=None,mode="--nvidia-causal",rc=0):
    with tempfile.TemporaryDirectory() as td:
        file=pathlib.Path(td)/"evidence.tar.gz"
        make_tar(file,patch)
        return subprocess.run([sys.executable,"-c",gate_code(),str(file),mode,str(rc)],
                              text=True,capture_output=True,timeout=10)

class OwnerWholeNoGoalNativeGate(unittest.TestCase):
    def test_real_l2_valid_full_native_child_and_sensor_proofs_pass_candidate(self):
        p=check()
        self.assertEqual(p.returncode,0,(p.stdout,p.stderr))
        self.assertIn("D06_OWNER_NO_GOAL_NATIVE_COMPLETE_CANDIDATE",p.stdout)
        self.assertIn("NO_MOVING_L3",p.stdout)
    def test_gazebo_server_minus11_despite_graceful_marker_must_hold(self):
        def update(s):
            s["native/launch.log"] += "[ERROR] [gz-21]: process has died [pid 111, exit code -11]\n"
        self.assertNotEqual(check(update).returncode,0)
    def test_cm_exit_minus11_must_hold_even_if_audit_is_wrong(self):
        def update(s):
            s["native/launch.log"] += "[ERROR] [collision_monitor-16]: process has died [pid 222, exit code -11]\n"
        self.assertNotEqual(check(update).returncode,0)
    def test_no_navigation_ack_must_hold(self):
        def update(s):s["native/g07_ordered_shutdown.json"]["navigation_ack"]=False
        self.assertNotEqual(check(update).returncode,0)
    def test_sensor_raw_over300_must_hold(self):
        def update(s):s["native/g07_wslg_sensor_truth.json"]["metrics"]["raw"]["max_receipt_gap_sec"]=.434354
        self.assertNotEqual(check(update).returncode,0)
    def test_safety_bad_distance_must_hold(self):
        def update(s):s["native/g07_wslg_sensor_truth.json"]["metrics"]["safety"]["front_median_m"]=.74
        self.assertNotEqual(check(update).returncode,0)
    def test_missing_twenty_second_both_ready_dwell_must_hold(self):
        def update(s):s["native/g07_wslg_sensor_truth.json"]["dual_topic_actual_wall_observation_sec"]=19.3
        self.assertNotEqual(check(update).returncode,0)
    def test_causal_mode_missing_readonly_witness_handoff_must_hold(self):
        def update(s):s.pop("native/g07_witness_stopped.ack")
        self.assertNotEqual(check(update).returncode,0)
    def test_suspect_parent_graceful_without_positive_gz_child_must_hold(self):
        def update(s):s["native/launch.log"]="P2_L2_GRACEFUL_TEARDOWN\n[INFO] [collision_monitor-16]: process has finished cleanly [pid 222]\n"
        self.assertNotEqual(check(update).returncode,0)
    def test_only_one_owner_session_and_no_goal_in_release(self):
        s=SCRIPT.read_text()
        self.assertIn("# D06_OWNER_NO_GOAL_NATIVE_GATE_START",s)
        self.assertIn("D06_GAZEBO_LIVE_RELEASE=HOLD",s)
        self.assertIn("CERTIFIED_ESTOP=false",s)
        self.assertNotIn("YES-P2-G07-GOAL",s)

if __name__=="__main__":unittest.main()
