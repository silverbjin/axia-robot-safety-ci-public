"""C11: only one isolated WSLg NVIDIA NO_GOAL core stack capture.
Do not confuse a CI Xvfb pass with WSLg D3D12 crash resolution.
Mocked core-list parser tests run on public Linux L0; no Gazebo is started.
"""
import importlib.util,json,os,pathlib,subprocess,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
FINDER=ROOT/"d06/tools/d06_wslg_latest_gz_sigsegv_core.py"
SCRIPT=ROOT/"d06/scripts/axia_d06_g07_wslg_sigsegv_capture_once.sh"
def load():
    spec=importlib.util.spec_from_file_location("d06_core_find",FINDER)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module
class C11CoreOnce(unittest.TestCase):
    def test_find_latest_only_gazebo_sigsegv(self):
        f=load()
        entries=[
          {"COREDUMP_PID":"100","COREDUMP_EXE":"/usr/bin/gz","COREDUMP_SIGNAL":"11","COREDUMP_TIMESTAMP":"1100"},
          {"COREDUMP_PID":"200","COREDUMP_EXE":"/usr/bin/gz","COREDUMP_SIGNAL":"6","COREDUMP_TIMESTAMP":"1200"},
          {"COREDUMP_PID":"300","COREDUMP_EXE":"/usr/bin/other","COREDUMP_SIGNAL":"11","COREDUMP_TIMESTAMP":"1300"},
          {"COREDUMP_PID":"400","COREDUMP_EXE":"/usr/bin/gz","COREDUMP_SIGNAL":"11","COREDUMP_TIMESTAMP":"1400"},
        ]
        self.assertEqual(f.latest_gazebo_sigsegv_pid(json.dumps(entries)),400)
        self.assertEqual(f.latest_gazebo_sigsegv_pid("\n".join(map(json.dumps,entries))),400)
        self.assertIsNone(f.latest_gazebo_sigsegv_pid("corrupted"))
        self.assertIsNone(f.latest_gazebo_sigsegv_pid(json.dumps([entries[1],entries[2]])))
    def test_wslg_preflight_one_nvidia_no_goal_only_and_core_private(self):
        src=SCRIPT.read_text()
        self.assertIn("D06_WSLG_CORE_ONCE_L0_PASS_NO_ROS_NO_GAZEBO",src)
        self.assertIn("--nvidia-causal",src)
        self.assertIn("systemd-coredump",src)
        self.assertIn("ulimit -c 524288",src)
        self.assertIn("D06_WSLG_CORE_STACK_CAPTURED_NOT_RESOLVED",src)
        self.assertIn("CERTIFIED_ESTOP=false",src)
        self.assertIn("AXIA_MVP_DEMO_ACCEPTED=HOLD",src)
        self.assertIn("GITHUB_ACTIONS",src)
        self.assertIn("sha256sum",src)
        self.assertIn("git hash-object",src)
        self.assertIn("core_not_archived",src)
        self.assertNotIn("sudo ",src)
        self.assertNotIn("pkill ",src)
        self.assertNotIn("LD_PRELOAD=",src)
        self.assertNotIn("RMW_IMPLEMENTATION=",src)
        self.assertNotIn("--compare",src)
        self.assertNotIn("set_pose",src)
        self.assertNotIn("send_goal",src)
        self.assertEqual(subprocess.run(["bash","-n",str(SCRIPT)],capture_output=True).returncode,0)
    def test_selfcheck_has_no_side_effects(self):
        env=os.environ.copy()
        with tempfile.TemporaryDirectory() as td:
            env["HOME"]=td
            r=subprocess.run(["bash",str(SCRIPT),"--self-check"],env=env,capture_output=True,text=True,timeout=7)
            self.assertEqual(r.returncode,0,(r.stdout,r.stderr))
            self.assertIn("D06_WSLG_CORE_ONCE_L0_PASS_NO_ROS_NO_GAZEBO",r.stdout)
            self.assertEqual(list(pathlib.Path(td).iterdir()),[])
if __name__=="__main__":unittest.main()
