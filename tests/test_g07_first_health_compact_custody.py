"""Actual #44864310689 HEALTH first 46 observations are >16KiB but
only allowlisted first/last/state transition should upload. Keep HOLD.
"""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]

class FirstHealthCompactCustody(unittest.TestCase):
    def test_46_samples_are_readable_but_only_numeric_allowlist_uploaded(self):
        row={"at_host_monotonic":565.123456,"supervisor_state":None,
             "cm_lifecycle_ok":None,"clock_advancing":True,
             "scan_present":False,"guard_latched":False,
             "health_clock_ok":False,"health_scan_ok":False,
             "health_graph_ok":False,"nav2_action_ready":False,
             "blockers":["cm_lifecycle_ok_not_true","scan_missing"],
             "clock_observer_age_ms":11773.492926,
             "scan_observer_age_ms":None,
             "odom_observer_age_ms":11773.955979,
             "guard_observer_age_ms":None,
             "supervisor_observer_age_ms":None}
        data={"schema":"axia.g07.events_executor_first_health_boundary.v1",
              "status":"FIRST_HEALTH_READINESS_UNVERIFIED_HOLD",
              "release":"HOLD","goal_sent":False,
              "certified_estop":False,"root_cause_proven":False,
              "first_readiness_blockers":["cm_lifecycle_ok_not_true","scan_missing"],
              "first_sample":row,"last_sample":row,
              "first_state_transition":None,"samples":46,
              "tail_samples":[dict(row,index=i,noise="bounded_test") for i in range(46)]}
        raw=json.dumps(data,sort_keys=True,indent=2).encode()
        self.assertGreater(len(raw),16384)
        self.assertLess(len(raw),65536)
        allow=("schema","status","release","goal_sent",
               "first_readiness_blockers","first_sample","last_sample",
               "first_state_transition","samples","dropped_middle_samples",
               "root_cause_proven","certified_estop","safety_ttl_changed")
        compact=json.dumps({k:data.get(k) for k in allow},sort_keys=True).encode()
        self.assertLess(len(compact),4096)
        self.assertNotIn(b"tail_samples",compact)
        for path in (
            ".github/workflows/axia-g07-events-first-health-native-l2.yml",
            ".github/workflows/axia-g07-events-first-scan-rmw-native-l2.yml"):
            with self.subTest(path=path):
                text=(ROOT/path).read_text()
                self.assertIn('"$(stat -c %s "$src")" -lt 65536',text)
                self.assertIn('"first_readiness_blockers","first_sample","last_sample"',text)
                self.assertIn('"first_state_transition","samples","dropped_middle_samples"',text)
                self.assertIn('assert data.get("release")=="HOLD"',text)
                self.assertIn('"root_cause_proven","certified_estop","safety_ttl_changed"',text)
                self.assertNotIn("CERTIFIED_ESTOP=True",text)

if __name__=="__main__":
    unittest.main()
