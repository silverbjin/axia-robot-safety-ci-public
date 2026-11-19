"""S75/n7 real Owner evidence regression. Synthetic CLOCK_REALTIME step, unchanged TTL."""
import unittest
from d06.diagnostic.g07_task02_strict_gate import assess


def owner_fixture(*, wall_step_ns=0, real_gap_ns=50_000_000):
    report = {
        "schema": "axia_g07_public_ci_moving_goal_v1",
        "status": "NUMERICAL_CANDIDATE",
        "shared_execution_mode": "owner",
        "owner_authority_verified": True,
        "common_g07_ci_oracle_status": "CI_GAZEBO_MOVING_GOAL_CANDIDATE",
        "guard_latched": False, "real_gazebo_world": True,
        "actual_physical_scan": True, "native_obstacle_set_pose_ack": True,
        "stop_native_set_pose_ack": True,
        "odom_stopped_dwell_sec": 1.0341, "observed_odom_moved_m": .2237,
        "max_source_interval_sec": .099, "max_cm_interval_sec": .092,
        "max_guard_interval_sec": .092, "max_scan_interval_sec": .197,
        "max_odom_interval_sec": .133, "max_clock_interval_sec": .070,
        "goal_status_at_clear": 2, "goal_status_at_slow": 2,
        "goal_status_at_stop": 2,
    }
    events = [{"kind": "owner_goal_published", "t": 100.0}]
    base = 1_795_047_000_000_000_000
    for i in range(40):
        jump = wall_step_ns if i >= 31 else 0
        t = 100.10 + i * .05
        # An actual 150ms delivery delay must NOT be relabeled as clock step.
        if real_gap_ns > 50_000_000 and i >= 31:
            t += (real_gap_ns - 50_000_000) / 1e9
        src = base + i * 50_000_000 + (real_gap_ns - 50_000_000 if i >= 31 else 0) + jump
        events.append({"kind": "pre_guard", "t": t,
                       "rmw_source_ns": src, "rmw_received_ns": src + 230_000,
                       "rmw_publication_seq": 100 + i})
    return report, events


class OwnerN7RMWClockRegression(unittest.TestCase):
    def test_owner_real_native_no_wall_step_accepted_only_as_scoped_candidate(self):
        report, events = owner_fixture()
        result = assess(report, events)
        self.assertEqual(result["status"], "TASK02_OWNER_NATIVE_NUMERICAL_CANDIDATE")
        self.assertEqual(result["actual_publisher_pairs"], 39)
        self.assertFalse(result["owner_wsl2_accepted"])
        self.assertFalse(result["certified_estop"])

    def test_n7_common_realtime_jump_requires_both_rmw_timestamps_and_monotonic(self):
        report, events = owner_fixture(wall_step_ns=2_920_000_000)
        result = assess(report, events)
        self.assertEqual(result["status"],
                         "TASK02_OWNER_MONOTONIC_CLOCK_STEP_NUMERICAL_CANDIDATE")
        self.assertEqual(result["clock_step_pairs"], 1)
        self.assertGreater(result["source_raw_gap_max_ms"], 2900)
        self.assertLess(result["source_gap_max_ms"], 120)
        self.assertLess(result["observer_gap_max_ms"], 120)
        self.assertFalse(result["owner_wsl2_accepted"])

    def test_n7_clock_step_not_ignored_without_received_timestamp(self):
        report, events = owner_fixture(wall_step_ns=2_920_000_000)
        del events[32]["rmw_received_ns"]
        self.assertNotIn("NUMERICAL_CANDIDATE",
                         assess(report, events)["status"].split("_")[-2:])

    def test_true_151ms_first_source_or_observer_interval_stays_hold(self):
        report, events = owner_fixture(real_gap_ns=151_000_000)
        result = assess(report, events)
        self.assertNotIn("NUMERICAL_CANDIDATE", result["status"].split("_")[-2:])

    def test_realtime_jump_mismatch_and_sequence_gap_never_pass(self):
        report, events = owner_fixture(wall_step_ns=2_920_000_000)
        events[32]["rmw_received_ns"] -= 1_000_000_000
        self.assertNotIn("NUMERICAL_CANDIDATE",
                         assess(report, events)["status"].split("_")[-2:])
        report, events = owner_fixture(wall_step_ns=2_920_000_000)
        events[32]["rmw_publication_seq"] += 1
        self.assertNotIn("NUMERICAL_CANDIDATE",
                         assess(report, events)["status"].split("_")[-2:])

    def test_unauthorized_owner_has_no_ci_bypass(self):
        report, events = owner_fixture()
        del report["owner_authority_verified"]
        self.assertEqual(assess(report, events)["status"],
                         "TASK02_ACTUAL_GOAL_OR_GUARD_UNVERIFIED_HOLD")
        report, events = owner_fixture()
        report["common_g07_ci_oracle_status"] = "HOLD"
        self.assertEqual(assess(report, events)["status"],
                         "TASK02_ACTUAL_GOAL_OR_GUARD_UNVERIFIED_HOLD")


if __name__ == "__main__":
    unittest.main()
