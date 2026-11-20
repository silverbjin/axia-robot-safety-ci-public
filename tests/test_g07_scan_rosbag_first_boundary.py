"""Independent existing rosbag exact LaserScan header pair vs pregoal Observer.

No ROS runtime required here. All sample RX nanoseconds are from ONE rosbag
recording's receive clock, never subtracted from host monotonic timestamps.
"""
import unittest
from d06.diagnostic.g07_scan_rosbag_first_boundary import classify

FIRST={"previous_header_sim":57.102,"current_header_sim":57.201,
       "gap_ms":348.760134,"previous_rx_host_monotonic":943.313032543,
       "current_rx_host_monotonic":943.661792677}

def rows(scan_b=150, safety_b=120):
    a=10_000_000_000
    return {
       "/scan":[{"rx_ns":a,"header_sim_ns":57_102_000_000},
                {"rx_ns":a+int(scan_b*1e6),"header_sim_ns":57_201_000_000}],
       "/safety/scan":[{"rx_ns":a+10_000_000,"header_sim_ns":57_102_000_000},
                       {"rx_ns":a+10_000_000+int(safety_b*1e6),"header_sim_ns":57_201_000_000}],
       "/clock":[{"rx_ns":a+i*10_000_000} for i in range(19)],
       "/odom":[{"rx_ns":a+i*50_000_000} for i in range(4)]}

class SameExactBagPair(unittest.TestCase):
    def test_bag_healthy_when_oracle_slow_never_passes_scan300(self):
        r=classify(FIRST,rows())
        self.assertEqual(r["status"],"OBSERVER_RX_GAP_NOT_REPRODUCED_IN_BAG_CANDIDATE_HOLD")
        self.assertEqual(r["independent_bag_scan_gap_ms"],150.)
        self.assertFalse(r["root_cause_proven"])
        self.assertEqual(r["release"],"HOLD")

    def test_bag_exact_scan_gap_sim99ms_still_holds(self):
        r=classify(FIRST,rows(scan_b=322.262,safety_b=320.522))
        self.assertEqual(r["status"],"SHARED_SCAN_DELIVERY_GAP_CANDIDATE_HOLD")
        self.assertAlmostEqual(r["independent_bag_scan_gap_ms"],322.262,places=3)
        self.assertFalse(r["gazebo_native_publish_root_proven"])

    def test_missing_same_header_pair_does_not_invent_attribution(self):
        d=rows();d["/scan"]=[d["/scan"][0]]
        r=classify(FIRST,d)
        self.assertEqual(r["status"],"EXACT_LASERSCAN_BAG_PAIR_UNVERIFIED_HOLD")
        self.assertIsNone(r["independent_bag_scan_gap_ms"])
        self.assertFalse(r["certified_estop"])

    def test_no_cross_clock_epoch_subtraction(self):
        r=classify(FIRST,rows())
        self.assertTrue(r["all_clock_intervals_same_rosbag_receive_timebase"])
        self.assertFalse(r["host_monotonic_minus_rosbag_epoch_subtracted"])

    def test_clock_odom_first_violation_without_scan_pair_still_compares_independent_bag(self):
        # Real #44773940465: first /clock334.226ms, /odom335.862ms.
        # No first Scan violation must NOT imply the raw bag was unexamined.
        d=rows()
        a=10_000_000_000
        d["/clock"]=[{"rx_ns":a},{"rx_ns":a+9_000_000},
                     {"rx_ns":a+350_000_000},{"rx_ns":a+360_000_000}]
        d["/odom"]=[{"rx_ns":a},{"rx_ns":a+340_000_000},
                    {"rx_ns":a+390_000_000}]
        pre={"first_delivery_violation":{"channel":"clock","gap_ms":334.226257},
             "clock_max_wall_gap_ms":334.226257,
             "odom_max_wall_gap_ms":335.861632}
        r=classify(None,d,pregoal_report=pre)
        self.assertEqual(r["status"],"CLOCK_ODOM_ROSBAG_INTERVALS_NO_EXACT_SCAN_PAIR_HOLD")
        self.assertEqual(r["independent_bag_clock_max_gap_ms"],341.0)
        self.assertEqual(r["independent_bag_odom_max_gap_ms"],340.0)
        self.assertEqual(r["observer_first_delivery_channel"],"clock")
        self.assertFalse(r["root_cause_proven"])
        self.assertFalse(r["host_monotonic_minus_rosbag_epoch_subtracted"])

    def test_clock_odom_no_scan_pair_bag_healthy_still_holds(self):
        pre={"first_delivery_violation":{"channel":"odom","gap_ms":335.861632},
             "clock_max_wall_gap_ms":110.0,"odom_max_wall_gap_ms":335.861632}
        r=classify(None,rows(),pregoal_report=pre)
        self.assertEqual(r["status"],"CLOCK_ODOM_ROSBAG_INTERVALS_NO_EXACT_SCAN_PAIR_HOLD")
        self.assertLess(r["independent_bag_odom_max_gap_ms"],300)
        self.assertEqual(r["release"],"HOLD")
        self.assertFalse(r["observer_callback_root_proven"])

if __name__=="__main__":unittest.main()
