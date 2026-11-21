"""Owner 1ibYCGPg original RMW forward clock step and real CM observer gap.

Only numeric fixture; no raw bag, Goal UUID or instructor source in CI.
This is a diagnostic classification regression, NEVER safety acceptance.
"""
import json
from pathlib import Path
import unittest
from d06.diagnostic.g07_task02_strict_gate import assess

FIXTURE=json.loads((Path(__file__).parent/"fixtures"/
  "g07_owner_1ibycgpg_cm_first_timing_numeric_20261121.json").read_text())

def fake_report():
    return {
      "schema":"axia_g07_public_ci_moving_goal_v1",
      "status":"NUMERICAL_CANDIDATE","shared_execution_mode":"owner",
      "common_g07_ci_oracle_status":"CI_GAZEBO_MOVING_GOAL_CANDIDATE",
      "owner_authority_verified":True,"ci_specific":False,
      "guard_latched":False,"real_gazebo_world":True,
      "actual_physical_scan":True,"native_obstacle_set_pose_ack":True,
      "stop_native_set_pose_ack":True,
      "odom_stopped_dwell_sec":1.092702188,"observed_odom_moved_m":.135770715,
      "goal_status_at_clear":2,"goal_status_at_slow":2,"goal_status_at_stop":2,
      "max_source_interval_sec":.111863284,"max_cm_interval_sec":.11191275,
      "max_guard_interval_sec":.08539246,
      "max_scan_interval_sec":.271170908,
      "max_odom_interval_sec":.153280517,
      "max_clock_interval_sec":.108642822}

def measured_like_events(*,forward=True,late=True,correlate=True):
    rows=[{"kind":"owner_goal_published","t":253.0}]
    # Same exact first-pair numeric gaps; other entries are artificial
    # scaffolding for the unchanged Task02 min-10-sample contract.
    values={
      "pre_guard":(FIXTURE["first_clock_step"]["pre_guard"],
                   FIXTURE["first_cm_observer_breach"]["pre_guard"],200),
      "supervised":(FIXTURE["first_clock_step"]["supervised"],
                    FIXTURE["first_cm_observer_breach"]["supervised"],2750)}
    for kind,(step,latepair,seq0) in values.items():
        t=254.0 if kind=="pre_guard" else 254.00013
        src=1_795_223_730_000_000_000
        recv=src+500000
        for i in range(17):
            if i:
                if i==6 and forward and (kind=="pre_guard" or correlate):
                    dt=step["observer_gap_ms"]
                    srcdiff=step["source_gap_ms"]
                    recvdiff=step["received_gap_ms"]
                elif i==16 and late:
                    dt=latepair["observer_gap_ms"]
                    srcdiff=latepair["source_gap_ms"]
                    recvdiff=latepair["received_gap_ms"]
                else:
                    dt=48.9
                    srcdiff=48.7
                    recvdiff=48.8
                t+=dt/1000
                src+=round(srcdiff*1e6)
                recv+=round(recvdiff*1e6)
            rows.append({"kind":kind,"t":t,"vx":0.02,"wz":0.0,
                         "rmw_publication_seq":seq0+i,
                         "rmw_source_ns":src,"rmw_received_ns":recv})
    rows.append({"kind":"task03_motion_window_end",
                 "t":FIXTURE["motion_window_end_monotonic"]})
    return rows

class OwnerCmFirstGapRegression(unittest.TestCase):
    def test_forward_step_on_two_publishers_plus_genuine_observer_breach_holds(self):
        r=assess(fake_report(),measured_like_events())
        self.assertEqual(r["status"],
            "TASK02_RMW_FORWARD_TIMEBASE_AND_OBSERVER_GAP_HOLD")
        self.assertFalse(r["owner_wsl2_accepted"])
        self.assertFalse(r["certified_estop"])
        d=r["timebase"]
        self.assertEqual(d["classification"],
            "CORRELATED_FORWARD_RMW_TIMESTAMP_STEP_CANDIDATE")
        self.assertAlmostEqual(d["pre_guard_source_gap_ms"],
                               FIXTURE["first_clock_step"]["pre_guard"]["source_gap_ms"],places=3)
        self.assertAlmostEqual(d["pre_guard_observer_gap_ms"],34.407404,places=3)
        self.assertAlmostEqual(d["supervised_source_gap_ms"],2815.603594,places=3)
        self.assertAlmostEqual(d["first_real_observer_gap_ms"],124.069382,places=3)
        self.assertLess(d["first_real_observer_source_gap_ms"],120)
        self.assertEqual(d["first_real_observer_seq_delta"],1)
        self.assertFalse(d["system_clock_or_rmw_cause_proven"])
        self.assertFalse(d["guard_internal_ttl_proven"])

    def test_forward_step_without_observer_120_still_not_a_pass(self):
        r=assess(fake_report(),measured_like_events(late=False))
        self.assertEqual(r["status"],"TASK02_RMW_FORWARD_TIMEBASE_DISCONTINUITY_HOLD")
        self.assertFalse(r["owner_wsl2_accepted"])

    def test_real_source_and_callback_200ms_is_not_mislabeled_as_clock_step(self):
        rows=measured_like_events(forward=False,late=False)
        pre=[r for r in rows if r.get("kind")=="pre_guard"]
        # One true co-increasing pair, without a disproportionate clock step;
        # keep the original strict >=120ms fail-closed verdict.
        i=6
        for row in pre[i:]:
            row["t"]+=0.21
            row["rmw_source_ns"]+=210_000_000
            row["rmw_received_ns"]+=210_000_000
        r=assess(fake_report(),rows)
        self.assertEqual(r["status"],"TASK02_CM120_SOURCE_OR_OBSERVER_FIRST_VIOLATION_HOLD")

    def test_no_verified_cross_topic_discontinuity_cannot_grant_success(self):
        r=assess(fake_report(),measured_like_events(correlate=False))
        self.assertFalse(r["owner_wsl2_accepted"])
        self.assertNotEqual(r["status"],"TASK02_PUBLIC_L2_NUMERICAL_CANDIDATE")

if __name__=="__main__":
    unittest.main()
