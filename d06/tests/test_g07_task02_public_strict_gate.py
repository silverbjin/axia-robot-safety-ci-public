"""Task02 real publisher/Observer and Guard safety accept: strict ROS-free fixture."""
import unittest
from d06.diagnostic.g07_task02_strict_gate import assess


def fixture():
    result={"schema":"axia_g07_public_ci_moving_goal_v1",
            "status":"CI_GAZEBO_MOVING_GOAL_CANDIDATE",
            "guard_latched":False,"real_gazebo_world":True,
            "actual_physical_scan":True,"native_obstacle_set_pose_ack":True,
            "stop_native_set_pose_ack":True,
            "odom_stopped_dwell_sec":1.04,
            "observed_odom_moved_m":0.23,
            "max_source_interval_sec":.055,
            "max_cm_interval_sec":.058,
            "max_guard_interval_sec":.07,
            "max_scan_interval_sec":.202,
            "max_odom_interval_sec":.15,
            "max_clock_interval_sec":.102,
            "goal_status_at_clear":2,"goal_status_at_slow":2,
            "goal_status_at_stop":2}
    rows=[{"kind":"owner_goal_published","t":20.0}]
    rows.extend({"kind":"pre_guard","t":20.1+i*.05,
                 "rmw_source_ns":1_000_000_000+i*50_000_000,
                 "rmw_publication_seq":100+i} for i in range(40))
    return result,rows


class StrictTask02NoRelaxation(unittest.TestCase):
    def test_same_goal_real_cm_publisher_120ms_and_guard_sensor_ttls(self):
        d,r=fixture()
        v=assess(d,r)
        self.assertEqual(v["status"],"TASK02_PUBLIC_L2_NUMERICAL_CANDIDATE")
        self.assertLess(v["source_gap_max_ms"],120)
        self.assertLess(v["observer_gap_max_ms"],120)
        self.assertEqual(v["actual_publisher_pairs"],39)
        self.assertFalse(v["tracer_off_release_pass"])
        self.assertFalse(v["owner_wsl2_accepted"])

    def test_first_121ms_source_gap_blocks_despite_other_green(self):
        d,r=fixture()
        r[14]["rmw_source_ns"]+=71_000_000
        v=assess(d,r)
        self.assertNotEqual(v["status"],"TASK02_PUBLIC_L2_NUMERICAL_CANDIDATE")
        self.assertFalse(v["tracer_off_release_pass"])

    def test_first_151ms_cm_to_guard_stale_blocks(self):
        d,r=fixture()
        d["max_guard_interval_sec"]=.151
        v=assess(d,r)
        self.assertNotEqual(v["status"],"TASK02_PUBLIC_L2_NUMERICAL_CANDIDATE")
        d,r=fixture()
        d["guard_latched"]=True
        v=assess(d,r)
        self.assertNotEqual(v["status"],"TASK02_PUBLIC_L2_NUMERICAL_CANDIDATE")

    def test_missing_or_out_of_order_source_sequence_blocks(self):
        d,r=fixture()
        r[14]["rmw_publication_seq"]+=1
        self.assertNotEqual(assess(d,r)["status"],"TASK02_PUBLIC_L2_NUMERICAL_CANDIDATE")
        d,r=fixture()
        r[0]["kind"]="other"
        self.assertNotEqual(assess(d,r)["status"],"TASK02_PUBLIC_L2_NUMERICAL_CANDIDATE")

    def test_gazebo_and_odom_stop_required_even_if_timing_green(self):
        d,r=fixture()
        d["odom_stopped_dwell_sec"]=.99
        self.assertNotEqual(assess(d,r)["status"],"TASK02_PUBLIC_L2_NUMERICAL_CANDIDATE")
        d,r=fixture()
        d["actual_physical_scan"]=False
        self.assertNotEqual(assess(d,r)["status"],"TASK02_PUBLIC_L2_NUMERICAL_CANDIDATE")


if __name__=="__main__":
    unittest.main()
