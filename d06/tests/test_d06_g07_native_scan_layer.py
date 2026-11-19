"""One failed NVIDIA Owner run remains unsafe; D08 native receiver reuse
must distinguish same-stamp native vs ROS reception without a second Goal.
"""
import importlib.util, json, pathlib, subprocess, sys, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
SCRIPT=ROOT/"d06/tools/d06_g07_scan_rx_witness.py"
FIX=ROOT/"d06/fixtures/g07_owner_nvidia_first_ttl_20261119.json"
def load():
    spec=importlib.util.spec_from_file_location("d06_witness",SCRIPT)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
def event(t,s,topic):
    return {"host_monotonic_sec":t,"source_stamp_ns":s,"topic":topic}
class SafetyGapNativeWitness(unittest.TestCase):
    def test_real_uploaded_nvidia_gap_and_shutdown_must_hold(self):
        m=load()
        d=json.loads(FIX.read_text())
        result=m.historical_verdict(d)
        self.assertEqual(result["first_failure"],"SAFETY_RECEIPT_TTL_300MS_BLOCKED")
        self.assertEqual(result["process_crashes"],["collision_monitor","gazebo_server"])
        self.assertFalse(result["scan_300ms_pass"])
        self.assertFalse(result["native_first_boundary_proven"])
        self.assertEqual(result["release"],"HOLD")
        self.assertFalse(result["goal_allowed"])
    def test_same_stamps_native_good_ros_both_late_is_after_native_candidate(self):
        m=load()
        native=[event(100.0,1000000000,"gz"),event(100.100,1100000000,"gz")]
        raw=[event(100.030,1000000000,"raw"),event(100.421,1100000000,"raw")]
        safe=[event(100.040,1000000000,"safety"),event(100.427,1100000000,"safety")]
        result=m.classify(native,raw,safe,limit=.3)
        self.assertEqual(result["candidate"],"AFTER_NATIVE_TRANSPORT_RX")
        self.assertAlmostEqual(result["native_gap_sec"],.1)
        self.assertGreater(result["raw_gap_sec"],.3)
        self.assertGreater(result["safety_gap_sec"],.3)
        self.assertEqual(result["release"],"HOLD")
    def test_native_slow_not_mislabeled_ros_bridge_or_executor(self):
        m=load()
        native=[event(100,1000000000,"gz"),event(100.399,1100000000,"gz")]
        raw=[event(100.02,1000000000,"raw"),event(100.423,1100000000,"raw")]
        safe=[event(100.03,1000000000,"safety"),event(100.43,1100000000,"safety")]
        result=m.classify(native,raw,safe)
        self.assertEqual(result["candidate"],"AT_OR_BEFORE_NATIVE_TRANSPORT_RX")
        self.assertFalse(result["publisher_send_timing_proven"])
    def test_missing_native_exact_pair_stays_undetermined(self):
        m=load()
        raw=[event(100,1000000000,"raw"),event(100.4,1100000000,"raw")]
        safe=[event(100.001,1000000000,"safety"),event(100.401,1100000000,"safety")]
        v=m.classify([],raw,safe)
        self.assertEqual(v["candidate"],"NATIVE_SOURCE_STAMP_PAIR_UNAVAILABLE")
        self.assertEqual(v["release"],"HOLD")
    def test_render_clear_cannot_override_shutdown_sigsegv(self):
        m=load()
        d=json.loads(FIX.read_text())
        d["safety"]["max_host_gap_sec"]=.101
        d["raw"]["max_host_gap_sec"]=.102
        v=m.historical_verdict(d)
        self.assertEqual(v["release"],"HOLD")
        self.assertEqual(v["first_failure"],"NATIVE_CHILD_EXIT_MINUS_11")
    def test_no_goal_readonly_script_no_twist_publish(self):
        txt=SCRIPT.read_text()
        self.assertIn('create_subscription(',txt)
        self.assertNotIn('create_publisher(',txt)
        self.assertNotIn('send_goal_async(',txt)
        self.assertIn('--analyze',txt)
        self.assertIn('D06_G07_FIRST_SCAN_TTL_HOLD',txt)
        cmd=subprocess.run(["python3",str(SCRIPT),"--self-check"],
                           capture_output=True,text=True,timeout=5)
        self.assertEqual(cmd.returncode,0,(cmd.stdout,cmd.stderr))
    def test_native_d08_probe_is_real_reused_no_private_clone(self):
        owner=(ROOT/"d06/scripts/axia_d06_g07_wslg_sensor_no_goal_once.sh").read_text()
        self.assertIn("AXIA_D06_G07_RX_WITNESS",owner)
        self.assertIn("d08_gz_native_scan_probe.py",owner)
        self.assertIn("d06_g07_scan_rx_witness.py",owner)
        self.assertIn("d06_g07_scan_delivery_layer.json",owner)
        self.assertIn("D06_G07_NATIVE_PROBE_IMPORT_MISSING_NO_GOAL",owner)
        compare=(ROOT/"d06/scripts/axia_d06_g07_wslg_gpu_rtf_compare_once.sh").read_text()
        self.assertIn("--nvidia-causal",compare)
        self.assertIn("D06_G07_FIRST_SCAN_TTL_HOLD",compare)
if __name__=="__main__":unittest.main()
