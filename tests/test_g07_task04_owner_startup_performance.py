"""G07 Owner startup: preserve baseline, cache only pinned native witness; no ROS/Goal."""
import unittest
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/axia_g07_task04_owner_moving_l3_once.sh"

class OwnerNativeCacheContract(unittest.TestCase):
    def setUp(self):
        self.text=SCRIPT.read_text(encoding="utf-8")

    def test_red_per_session_configure_is_replaced_by_persistent_cache(self):
        self.assertIn('NATIVE_BUILD_CACHE_ROOT=',self.text)
        self.assertNotIn('cmake -S "$RUNTIME/tools/native_s02_public" -B "$OUT/native_build"',self.text)
        self.assertIn('AXIA_G07_NATIVE_WITNESS_CACHE_STATUS=',self.text)

    def test_cache_fingerprint_tracks_source_and_binary_abi(self):
        for marker in ("native_s02_public/CMakeLists.txt","native_s02_public/s02_witness.cc",
                       'STUDENT_SHA','dpkg-query','c++ -dumpfullversion','cmake --version',
                       'sha256sum','NATIVE_BUILD_CACHE_KEY'):
            with self.subTest(marker=marker):
                self.assertIn(marker,self.text)

    def test_per_run_custody_and_startup_timing_are_preserved(self):
        for marker in ('native_witness_build_profile.json','native_build_config.log',
                       'native_build.log','native_witness.sha256',
                       'GZ_SIM_SYSTEM_PLUGIN_PATH',
                       'AXIA_G07_NATIVE_WITNESS_CACHE_WALL_SEC='):
            with self.subTest(marker=marker):
                self.assertIn(marker,self.text)
        self.assertIn("'native_witness_build_profile.json'",self.text)
        self.assertIn('AXIA_G07_TASK04_OWNER_MOVING_BEGIN',self.text)

    def test_same_original_owner_permissions_and_fixed_ros_safety_settings(self):
        for marker in ('AXIA_G07_CI_SIM_GOAL_ALLOWED=0',
                       'AXIA_G07_TASK04_OWNER_MOVING_L3=1',
                       'AXIA_NAV2_USE_COMPOSITION=False',
                       'timeout --foreground --signal=TERM',
                       'YES-P2-G07-GOAL'):
            self.assertIn(marker,self.text)
        self.assertNotIn("AXIA_SCAN_TTL_SEC=0.5",self.text)
        self.assertNotIn("GITHUB_ACTIONS=true",self.text)

    def test_existing_self_check_still_fast_and_has_no_build(self):
        p=subprocess.run(["bash",str(SCRIPT),"--self-check"],
                         text=True,capture_output=True,timeout=8)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn("NO_ROS_NO_GAZEBO_NO_GOAL",p.stdout)
        self.assertIn("AXIA_G07_TASK04_NATIVE_WITNESS_CACHE_V1=",p.stdout)

if __name__=="__main__":
    unittest.main()
