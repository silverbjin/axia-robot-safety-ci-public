"""FV17z53O CI regression: owner RMW evidence profile and WSL2 timebase step.

This reproduces *only* source-backed numeric edges. It is not a simulated
Nav2 Goal, formal safety release, or an Owner WSL2 acceptance.
"""
import copy
from pathlib import Path
import unittest
from d06.diagnostic.g07_task02_strict_gate import assess
from scripts.axia_g07_task04_owner_demo_scope import assess_owner_demo_scope

FIELD_PREV=1795134992890347373   # actual pre_guard seq132
FIELD_NEXT=1795134986208843701   # actual pre_guard seq133
FIELD_SUP_PREV=1795134992890087700
FIELD_SUP_NEXT=1795134986208495000

def report(mode):
    r={"schema":"axia_g07_public_ci_moving_goal_v1",
       "status":"CI_GAZEBO_MOVING_GOAL_CANDIDATE",
       "guard_latched":False,"real_gazebo_world":True,
       "actual_physical_scan":True,
       "native_obstacle_set_pose_ack":True,
       "stop_native_set_pose_ack":True,
       "odom_stopped_dwell_sec":1.016,
       "observed_odom_moved_m":.134,
       "goal_status_at_clear":2,"goal_status_at_slow":2,
       "goal_status_at_stop":2,
       "max_source_interval_sec":.0871,
       "max_cm_interval_sec":.081,
       "max_guard_interval_sec":.075,
       "max_scan_interval_sec":.213,
       "max_odom_interval_sec":.141,
       "max_clock_interval_sec":.104,
       "shared_execution_mode":"ci"}
    if mode=="owner":
        r.update(status="NUMERICAL_CANDIDATE",
                 shared_execution_mode="owner",
                 common_g07_ci_oracle_status="CI_GAZEBO_MOVING_GOAL_CANDIDATE",
                 owner_authority_verified=True,ci_specific=False)
    return r

def events(normal=True):
    rows=[{"kind":"owner_goal_published","t":100.0}]
    for i in range(24):
        t=100.05+ i*.05
        rows.append({"kind":"pre_guard","t":t,
          "rmw_publication_seq":110+i,
          "rmw_source_ns":1795134990000000000+i*50_000_000,
          "rmw_received_ns":1795134990001000000+i*50_000_000})
    if not normal:
        # FV17z53O actual sequence 132->133 moved wall timestamps backward
        # ~6.6815 seconds while monotonic callback time continued forwards.
        rows[23]["rmw_publication_seq"]=132
        rows[23]["rmw_source_ns"]=FIELD_PREV
        rows[23]["rmw_received_ns"]=FIELD_PREV+700_000
        rows[24]["rmw_publication_seq"]=133
        rows[24]["rmw_source_ns"]=FIELD_NEXT
        rows[24]["rmw_received_ns"]=FIELD_NEXT+2_100_000
        rows.extend([
            {"kind":"supervised","t":101.15,"rmw_publication_seq":1403,
             "rmw_source_ns":FIELD_SUP_PREV,"rmw_received_ns":FIELD_SUP_PREV+500_000},
            {"kind":"supervised","t":101.20,"rmw_publication_seq":1404,
             "rmw_source_ns":FIELD_SUP_NEXT,"rmw_received_ns":FIELD_SUP_NEXT+200_000},
        ])
    return rows

class OwnerRmwVerifierParity(unittest.TestCase):
    def test_ci_and_owner_evidence_have_same_timing_gate(self):
        self.assertEqual(assess(report("ci"),events())["status"],
                         "TASK02_PUBLIC_L2_NUMERICAL_CANDIDATE")
        self.assertEqual(assess(report("owner"),events())["status"],
                         "TASK02_PUBLIC_L2_NUMERICAL_CANDIDATE")
    def test_owner_candidate_not_accepted_without_real_owner_provenance(self):
        for key,val in [("owner_authority_verified",False),
                        ("ci_specific",True),
                        ("common_g07_ci_oracle_status","")]:
            r=report("owner");r[key]=val
            self.assertNotEqual(assess(r,events())["status"],
                                "TASK02_PUBLIC_L2_NUMERICAL_CANDIDATE")
    def test_field_wsl2_rmw_step_is_not_claimed_as_callback_ttl_failure(self):
        verdict=assess(report("owner"),events(normal=False))
        self.assertEqual(verdict["status"],
                         "TASK02_RMW_TIMEBASE_DISCONTINUITY_HOLD")
        self.assertEqual(verdict["timebase"]["classification"],
                         "CROSS_STREAM_RMW_CLOCK_DISCONTINUITY_CANDIDATE")
        self.assertTrue(verdict["timebase"]["cm_callback_gap_ms"]<120.0)
        self.assertLess(verdict["timebase"]["first_source_regression_ms"],-6000)
        self.assertFalse(verdict["tracer_off_release_pass"])
    def test_missing_or_corrupt_rmw_is_fail_closed(self):
        rows=events();rows[12].pop("rmw_source_ns")
        self.assertNotEqual(assess(report("owner"),rows)["status"],
                            "TASK02_PUBLIC_L2_NUMERICAL_CANDIDATE")


class OwnerScopedDemoWhenFormalTimebaseUnreliable(unittest.TestCase):
    def candidate(self):
        # Synthetic *numerical review* only, real physical evidence is not
        # faked by this test. The owner reviewer must have proved 20 gates.
        checks={name:True for name in
             ("single_goal_actual_action","exact_goal_cancel","sqlite_14",
             "cm_source_and_observer_120ms","guard_internal_150ms",
             "s02_actual_native_contact_zero","cli_shared_moving_result",
             "no_unexpected_guard_latch","first_timing_violation_none",
             "odom_moved","odom_zero_dwell","cm_callback_120ms",
             "guard_150ms","scan_300ms","odom_300ms","clock_300ms",
             "nav_lifecycle_ack","loc_lifecycle_ack",
             "collision_monitor_child_clean","both_actual_gui_windows",
             "exact_source_sha")}
        checks["cm_source_and_observer_120ms"]=False
        return {"status":"HOLD","scenario_scope":"owner","first_failure":"cm_source_and_observer_120ms",
                "checks":checks,"cm120":{"status":"TASK02_RMW_TIMEBASE_DISCONTINUITY_HOLD"},
                "goal_uuid":"a"*32,"gui_windows_seen":2,"odom_moved_m":.134,
                "stopped_dwell_sec":1.016,"source_sha":"f"*40,
                "certified_estop":False,"owner_wsl2_l3_accepted":False}

    def test_educational_goal_evidence_is_reported_without_formal_timing_pass(self):
        result=assess_owner_demo_scope(self.candidate())
        self.assertEqual(result["status"],
           "MVP_OWNER_PHYSICAL_NUMERICAL_CANDIDATE_FORMAL_TIMEBASE_HOLD")
        self.assertEqual(result["formal_first_hold"],"cm_source_and_observer_120ms")
        self.assertEqual(result["first_failure_preserved"],"cm_source_and_observer_120ms")
        self.assertFalse(result["formal_safety_timing_accepted"])
        self.assertFalse(result["owner_wsl2_l3_accepted"])
        self.assertFalse(result["axia_mvp_demo_accepted"])
        self.assertFalse(result["certified_estop"])

    def test_missing_guard_internal_age_can_never_be_reclassified_as_demo_ready(self):
        x=self.candidate();x["checks"]["guard_internal_150ms"]=False
        self.assertEqual(assess_owner_demo_scope(x)["status"],"HOLD")

    def test_real_cm_ttl_failure_cannot_be_reclassified_as_wall_time_anomaly(self):
        x=self.candidate()
        x["cm120"]["status"]="TASK02_CM120_SOURCE_OR_OBSERVER_FIRST_VIOLATION_HOLD"
        self.assertEqual(assess_owner_demo_scope(x)["status"],"HOLD")

    def test_corrupted_goal_or_wrong_source_never_pass(self):
        for key in ("exact_goal_cancel","exact_source_sha","scan_300ms","collision_monitor_child_clean"):
            x=self.candidate();x["checks"][key]=False
            self.assertEqual(assess_owner_demo_scope(x)["status"],"HOLD")
        x=self.candidate();x["scenario_scope"]="ci"
        self.assertEqual(assess_owner_demo_scope(x)["status"],"HOLD")

if __name__=="__main__":unittest.main()
