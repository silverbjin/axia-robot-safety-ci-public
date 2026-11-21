"""L2 #44455727595: official Nav2 manager was active, but a fresh client
missed /lifecycle_manager_navigation/get_parameters during 3sec discovery.
Require bounded retry without changing Scan300/CM120/Guard150 or issuing Goal.
"""
import sys, pathlib, unittest, importlib.util
ROOT=pathlib.Path(__file__).resolve().parents[2]
SRC_ROOT=ROOT/"student" if (ROOT/"student").is_dir() else ROOT.parent/"student"
TOOLS=SRC_ROOT/"block_B/day07/h01_runtime/tools"
sys.path.insert(0,str(TOOLS))
import p2_g07_ordered_shutdown as ordered

class BoundedManagerServiceDiscovery(unittest.TestCase):
    def test_witness_related_3s_service_discovery_delay_allows_bounded_retry(self):
        class Delayed:
            calls=[]
            def wait_for_service(self, timeout_sec):
                self.calls.append(timeout_sec)
                return len(self.calls)==5
        obj=Delayed()
        self.assertTrue(ordered.wait_for_service_bounded(obj,12.0))
        self.assertEqual(len(obj.calls),5)
        self.assertTrue(all(0<v<=1 for v in obj.calls))

    def test_missing_service_still_holds_and_never_exceeds_12s_budget(self):
        class Never:
            calls=[]
            def wait_for_service(self, timeout_sec):
                self.calls.append(timeout_sec)
                return False
        obj=Never()
        self.assertFalse(ordered.wait_for_service_bounded(obj,50.0))
        self.assertLessEqual(sum(obj.calls),12.001)
        self.assertEqual(len(obj.calls),12)

    def test_remaining_global_deadline_is_respected(self):
        class Never:
            calls=[]
            def wait_for_service(self, timeout_sec):
                self.calls.append(timeout_sec)
                return False
        obj=Never()
        self.assertFalse(ordered.wait_for_service_bounded(obj,2.2))
        self.assertLessEqual(sum(obj.calls),2.20001)

    def test_ros_parameters_discovery_reuses_bounded_helper_and_no_ttl_change(self):
        source=(TOOLS/"p2_g07_ordered_shutdown.py").read_text()
        self.assertIn("wait_for_service_bounded(client, remaining)",source)
        self.assertIn("deadline = monotonic() + limit",source)
        self.assertIn("SERVICE_MISSING:",source)
        for forbidden in ("SCAN_TTL_SEC = 0.5","CM_TTL_SEC = 1.0",
                          "AXIA_G07_CI_SIM_GOAL_ALLOWED=1"):
            self.assertNotIn(forbidden,source)
if __name__=="__main__":unittest.main()
