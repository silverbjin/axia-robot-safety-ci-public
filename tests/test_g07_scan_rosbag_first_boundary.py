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

if __name__=="__main__":unittest.main()
