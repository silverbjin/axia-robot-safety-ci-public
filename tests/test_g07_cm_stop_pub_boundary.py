"""RED: distinguish Nav2 Jazzy stop_pub_timeout from CM/RMW/Guard starvation.

Official CollisionMonitor::publishVelocity suppresses zero velocity after
stop_pub_timeout. Synthetic cases do not assert the real #44652034063 cause.
"""
import unittest
from d06.diagnostic.g07_cm_stop_pub_boundary import classify


def synthetic(*, end=105.18, last_zero=104.95):
    rows=[{"kind":"pre_guard","t":99.95,"vx":.05,"wz":.01}]
    t=100.0
    while t<=last_zero+1e-8:
        rows.append({"kind":"pre_guard","t":round(t,6),"vx":0.0,"wz":0.0})
        t+=.05
    for i in range(68):
        tick=99.0 + i*.1
        rows.append({"kind":"clock","t":round(tick,6),
                     "ns":int(round((tick-90)*1_000_000_000))})
    rows.sort(key=lambda r:r["t"])
    first={"tick_monotonic":end,"cm_rx_monotonic":last_zero,
           "cm_age_sec":end-last_zero,
           "reason":"UPSTREAM_STALE_AFTER_MOTION","latched":True}
    return rows,first


class CMStopPubTimeoutFirstBoundary(unittest.TestCase):
    def test_zero_timeout_compatible_remains_candidate_not_root_proof(self):
        rows,latch=synthetic()
        r=classify(rows,latch,stop_pub_timeout_sec=5.0)
        self.assertEqual(r["status"],"CM_STOP_PUB_TIMEOUT_COMPATIBLE_UNPROVEN")
        self.assertGreater(r["sim_zero_to_latch_sec"],5.0)
        self.assertLess(r["sim_zero_to_last_output_sec"],5.01)
        self.assertGreater(r["guard_cm_age_ms"],150)
        self.assertFalse(r["cm_internal_stop_stamp_proven"])
        self.assertFalse(r["root_cause_confirmed"])
        self.assertEqual(r["release"],"HOLD")

    def test_early_latch_disproves_five_second_zero_suppression(self):
        rows,latch=synthetic(end=102.4,last_zero=102.2)
        r=classify(rows,latch,stop_pub_timeout_sec=5.0)
        self.assertEqual(r["status"],"CM_STOP_PUB_TIMEOUT_TIMING_INCOMPATIBLE")
        self.assertLess(r["sim_zero_to_latch_sec"],5.0)
        self.assertEqual(r["release"],"HOLD")

    def test_absent_actual_timing_is_not_pass_or_cause(self):
        rows,latch=synthetic()
        self.assertEqual(classify([],latch,stop_pub_timeout_sec=5.0)["status"],
                         "CM_STOP_PUB_FIRST_BOUNDARY_UNVERIFIED")
        self.assertEqual(classify(rows,latch,stop_pub_timeout_sec=None)["status"],
                         "CM_STOP_PUB_FIRST_BOUNDARY_UNVERIFIED")
        self.assertEqual(classify([x for x in rows if x["kind"]!="clock"],
                                  latch,stop_pub_timeout_sec=5.0)["status"],
                         "CM_STOP_PUB_FIRST_BOUNDARY_UNVERIFIED")

    def test_non_latch_and_clock_domain_mismatch_never_prove_root(self):
        rows,latch=synthetic()
        x=dict(latch,latched=False)
        self.assertEqual(classify(rows,x,stop_pub_timeout_sec=5.0)["status"],
                         "CM_STOP_PUB_FIRST_BOUNDARY_UNVERIFIED")
        altered=[dict(x) for x in rows]
        for row in altered:
            if row["kind"]=="clock" and row["t"]>=102:
                row["ns"]-=9_000_000_000
        self.assertEqual(classify(altered,latch,stop_pub_timeout_sec=5.0)["status"],
                         "CM_STOP_PUB_FIRST_BOUNDARY_UNVERIFIED")


if __name__=="__main__":
    unittest.main()
