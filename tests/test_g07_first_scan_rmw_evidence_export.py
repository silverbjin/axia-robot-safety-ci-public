"""First actual no-Goal safety boundary regression, immutable numeric evidence.
Sources: native #44861540326, #44863792399. L0 is not native replay.
No root cause, Owner approval or certified E-Stop can be inferred from a fixture.
"""
import unittest
from pathlib import Path
from d06.diagnostic.g07_first_scan_pair_attribution import assess

ROOT=Path(__file__).resolve().parents[1]
STUDENT="d8ec1a50bdd5a9097530b0924709a6ee63ce4eb5"
WORKFLOW=ROOT/".github/workflows/axia-g07-original-multi-first-scan-rmw-native-l2.yml"

def first_run():
    return {
        "status":"HOLD","goal_sent":False,
        "first_failure":"SCAN_PREFLIGHT_CLOCK_ODOM_INTERVAL_BREACH",
        "first_delivery_violation":{"channel":"clock",
           "current_rx_host_monotonic":984.97623911,
           "gap_ms":331.671633,"limit_ms":300.0},
        "first_scan_timing_boundary":{
           "topic":"scan","previous_header_sim":54.102,
           "current_header_sim":54.201,
           "current_rx_host_monotonic":984.980366461,
           "gap_ms":385.643415,"header_sim_gap_ms":99.0},
        "first_scan_rmw_pair":{"status":"SCAN_EXACT_RMW_METADATA_UNAVAILABLE_HOLD",
                              "source_gap_ms":None,"received_gap_ms":None,
                              "publication_seq_gap":None}
    }

def first_bag():
    return {
        "matched_exact_first_header_pair":True,
        "same_header_pair_rosbag_timebase_only":True,
        "independent_bag_scan_gap_ms":83.539915,
        "independent_bag_safety_scan_gap_ms":88.062788,
        "independent_bag_odom_max_gap_ms":369.490976,
        "independent_bag_clock_max_gap_ms":476.612466,
        "expected_first_scan_header_gap_ms":99.0,
        "goal_sent":False,"release":"HOLD"
    }

class NativeFirstBoundaryAttribution(unittest.TestCase):
    def test_original_real_clock_first_scan_not_native_generation_proof(self):
        r=assess(first_run(),first_bag())
        self.assertEqual(r["first_violation_topic"],"clock")
        self.assertAlmostEqual(r["first_violation_ms"],331.671633)
        self.assertAlmostEqual(r["first_scan_observer_gap_ms"],385.643415)
        self.assertEqual(r["independent_exact_scan_bag_gap_ms"],83.539915)
        self.assertEqual(r["scan_header_sim_gap_ms"],99.0)
        self.assertEqual(r["rmw_interval_class"],"RMW_INTERVAL_UNAVAILABLE_HOLD")
        self.assertFalse(r["same_first_clock_rosbag_pair_proven"])
        self.assertFalse(r["same_first_odom_rosbag_pair_proven"])
        self.assertFalse(r["exact_publication_cross_process_proven"])
        self.assertFalse(r["root_cause_proven"])
        self.assertEqual(r["release"],"HOLD")
        self.assertFalse(r["pregoal_goal_sent"])
        self.assertNotIn("actual_goal_sent",r) # report cannot infer post-pregoal actual Goal

    def test_latest_real_424ms_scan_with_synthetic_valid_rmw_intervals_is_candidate_only(self):
        d=first_run()
        d["first_delivery_violation"]={"channel":"clock",
          "current_rx_host_monotonic":146.507190425,
          "gap_ms":337.093495,"limit_ms":300.0}
        d["first_scan_timing_boundary"].update(
          previous_header_sim=45.402,current_header_sim=45.501,
          current_rx_host_monotonic=146.507508325,gap_ms=424.373456)
        # Synthetic RMW numeric values illustrate what a real exact pair
        # would distinguish; they are NOT observations from #44863792399.
        d["first_scan_rmw_pair"]={
           "status":"SCAN_OBSERVER_TAKE_OR_EXECUTOR_DELAY_CANDIDATE_HOLD",
           "source_gap_ms":99.0,"received_gap_ms":100.0,
           "observer_gap_ms":424.373456,"header_sim_gap_ms":99.0,
           "publication_seq_gap":1}
        b=first_bag()
        b.update(independent_bag_scan_gap_ms=101.297422,
          independent_bag_odom_max_gap_ms=343.795109,
          independent_bag_clock_max_gap_ms=335.607688)
        r=assess(d,b)
        self.assertEqual(r["rmw_interval_class"],
                         "AFTER_RMW_TIMESTAMP_BEFORE_CALLBACK_CANDIDATE_HOLD")
        self.assertFalse(r["exact_publication_cross_process_proven"])
        self.assertFalse(r["executor_root_proven"])
        self.assertEqual(r["release"],"HOLD")

    def test_seq_missing_header_ambiguous_or_bad_clock_fails_closed(self):
        d=first_run()
        for mode in ("seq_missing","header_not_exact","source_epoch_mix"):
            with self.subTest(mode=mode):
                b=first_bag()
                x=dict(d)
                x["first_scan_rmw_pair"]={"status":"SCAN_OBSERVER_TAKE_OR_EXECUTOR_DELAY_CANDIDATE_HOLD",
                    "source_gap_ms":99.,"received_gap_ms":100.,
                    "observer_gap_ms":385.643415,
                    "header_sim_gap_ms":99., "publication_seq_gap":1}
                if mode=="seq_missing":
                    x["first_scan_rmw_pair"]["publication_seq_gap"]=-1
                elif mode=="header_not_exact":
                    b["matched_exact_first_header_pair"]=False
                else:
                    x["first_scan_rmw_pair"]["source_gap_ms"]=1_800_000_000_000.0
                r=assess(x,b)
                self.assertEqual(r["release"],"HOLD")
                self.assertFalse(r["root_cause_proven"])
                self.assertFalse(r["exact_publication_cross_process_proven"])
                if mode=="seq_missing":
                    self.assertEqual(r["rmw_interval_class"],"RMW_INTERVAL_UNAVAILABLE_HOLD")
                if mode=="header_not_exact":
                    self.assertIsNone(r["independent_exact_scan_bag_gap_ms"])

    def test_native_diag_workflow_must_retain_strict_safety_and_capture_rmw_pair(self):
        s=WORKFLOW.read_text()
        self.assertIn(STUDENT,s)
        self.assertIn("AXIA_G07_EVENTS_EXECUTOR_AB: '0'",s)
        self.assertIn('"first_scan_rmw_pair"',s)
        self.assertIn('"scan_rmw_metadata_capability"',s)
        self.assertIn("test_g07_scan_rmw_first_pair.py",s)
        self.assertIn("AXIA_G07_SCAN_PREFLIGHT_STRICT: '1'",s)
        self.assertIn("AXIA_G07_TASK03_FORMAL_CI: '1'",s)
        self.assertIn("compare_same_cm_pair",s)
        self.assertIn('"first_executor_silence_snapshot"',s)
        self.assertIn("FIRST_EXECUTOR_SILENCE_STACK",s)
        self.assertNotIn("scan_wall_limit_ms: 500",s)
        self.assertNotIn("certified_estop: true",s)


    def test_native_artifact_must_include_first_scan_rmw_bag_attribution_and_checksum(self):
        # Regression for actual run #44864568561 artifact #14690808653.
        # Its workflow CREATED the bounded attribution JSON + SHA256,
        # but upload-artifact omitted both. A future first-gap failure
        # would therefore lose its most useful diagnosis.
        workflow=WORKFLOW.read_text()
        self.assertIn('first_scan_rmw_bag_attribution.json',workflow)
        artifact=workflow.split('uses: actions/upload-artifact@',1)[-1]
        self.assertNotEqual(artifact,workflow, 'native upload step missing')
        self.assertIn('public_evidence/first_scan_rmw_bag_attribution.json',artifact)
        self.assertIn('public_evidence/first_scan_rmw_bag_attribution.sha256',artifact)
        self.assertNotIn('native/rosbag2/',artifact)
        self.assertIn("AXIA_G07_EVENTS_EXECUTOR_AB: '0'",workflow)


    def test_native_must_pin_proven_jazzy_two_arg_messageinfo_student(self):
        # #44864568561 / #44865087050 had 1-arg rclpy callback due to
        # optional 'info=None' at old Student SHA, so all 238 RMW fields
        # were absent. Student #89 fixed to required 'cb(msg, info)'.
        # Native Jazzy separate-process L1 #44865731221 verified
        # source/received/sequence 35/35/35. CI must pin THAT snapshot.
        workflow=WORKFLOW.read_text()
        self.assertIn("ref: "+STUDENT,workflow)
        self.assertNotIn("1edd816039381719b4b3a4b0725dd18320ea6ae9",workflow)


    def test_first_supervisor_observed_transition_relative_to_original_gap(self):
        # No inference from final Navigation error or a later NORMAL state.
        from d06.diagnostic.g07_first_actual_delivery_gap import first_observed_safety_transition
        events=[
            {"kind":"supervisor","t":10.00,"data":{"state":"NORMAL"}},
            {"kind":"guard","t":10.02,"data":{"latched":False}},
            {"kind":"supervisor","t":10.20,"data":{"state":"NORMAL"}},
            {"kind":"supervisor","t":10.32,"data":{"state":"HEALTH_BAD_DIAGNOSTIC"}},
            {"kind":"guard","t":10.33,"data":{"latched":True}},
        ]
        gap={"channel":"guard","previous_rx_monotonic":10.05,
             "current_rx_monotonic":10.31,"gap_ms":260.,"limit_ms":150}
        v=first_observed_safety_transition(events,gap)
        self.assertEqual(v["first_observed_state"],"NORMAL")
        self.assertEqual(v["first_observed_transition"]["from_state"],"NORMAL")
        self.assertEqual(v["first_observed_transition"]["to_state"],"HEALTH_BAD_DIAGNOSTIC")
        self.assertEqual(v["relative_to_first_gap"],"AFTER_FIRST_CALLBACK_BREACH")
        self.assertAlmostEqual(v["first_observed_guard_latch_at"],10.33)
        self.assertFalse(v["root_cause_proven"])
        self.assertEqual(v["release"],"HOLD")

    def test_first_supervisor_state_cannot_infer_transition_from_missing_data(self):
        from d06.diagnostic.g07_first_actual_delivery_gap import first_observed_safety_transition
        d=first_observed_safety_transition(
            [{"kind":"supervisor","t":10.1,"data":{"state":"NORMAL"}}],None)
        self.assertIsNone(d["first_observed_transition"])
        self.assertEqual(d["status"],"FIRST_SAFETY_TRANSITION_NOT_OBSERVED_HOLD")
        self.assertFalse(d["root_cause_proven"])
        self.assertNotIn("accepted",str(d))


    def test_original_multi_two_independent_cold_native_cycles_required(self):
        # Earlier #44870025677 was ONLY one scoped PASS without the first
        # intermittent breach. Never call it accepted independent 2/2.
        s=WORKFLOW.read_text()
        self.assertIn("cycle: [1, 2]",s)
        self.assertIn("name: AXIA G07 Original Multi First Scan RMW Exact Pair",s)
        self.assertIn("ref: "+STUDENT,s)
        self.assertIn('AXIA_G07_EVENTS_EXECUTOR_AB: \'0\'',s)
        self.assertIn('AXIA_G07_SCAN_PREFLIGHT_STRICT: \'1\'',s)
        self.assertIn('AXIA_G07_TASK03_FORMAL_CI: \'1\'',s)
        self.assertIn("first_delivery_actual_pairs.json",s)
        self.assertIn("observer_io_first_boundary.json",s)
        self.assertIn("first_scan_rmw_bag_attribution.json",s)
        self.assertIn("public_evidence/first_nav_server_boundary.json",s)
        self.assertNotIn("scan_wall_limit_ms: 500",s)
        self.assertNotIn("CERTIFIED_ESTOP=true",s)


    def test_strict_native_bounded_multi2_waitset_is_only_opt_in_under_ci(self):
        s=WORKFLOW.read_text()
        self.assertIn("AXIA_G07_CI_EXECUTOR_WAIT_BOUNDED_AB: '0'",s)
        self.assertIn("FIRST_EXECUTOR_SILENCE_STACK",s)
        self.assertIn("AXIA_G07_OWNER_STARTUP_PARITY: '1'",s)
        self.assertIn("AXIA_G07_CI_OWNER_OBSERVER_PARITY: '1'",s)
        self.assertIn("AXIA_G07_OBSERVER_IO_PROBE: '1'",s)
        self.assertIn("AXIA_G07_EVENTS_EXECUTOR_AB: '0'",s)
        self.assertIn("cycle: [1, 2]",s)
        self.assertIn("ref: "+STUDENT,s)
        self.assertIn("AXIA_G07_SCAN_PREFLIGHT_STRICT: '1'",s)
        self.assertNotIn("CERTIFIED_ESTOP=true",s)


    def test_owner_lock_disallows_unvalidated_cyclone_release_in_native_2cycle(self):
        # D08 #208 is no-Goal scoped and G07 Owner lock explicitly requires
        # rmw_fastrtps_cpp. NEVER promote experimental Cyclone to Owner.
        s=WORKFLOW.read_text()
        self.assertNotIn("RMW_IMPLEMENTATION: rmw_cyclonedds_cpp",s)
        self.assertNotIn("ros-jazzy-rmw-cyclonedds-cpp",s)
        self.assertIn("FASTDDS_BUILTIN_TRANSPORTS: UDPv4",s)
        self.assertIn("AXIA_G07_CI_EXECUTOR_WAIT_BOUNDED_AB: '0'",s)
        self.assertNotIn("AXIA_G07_CI_EXECUTOR_WAIT_BOUNDED_AB: '1'",s)
        self.assertIn("cycle: [1, 2]",s)
        self.assertIn("ref: "+STUDENT,s)
        self.assertIn("AXIA_G07_TASK03_FORMAL_CI: '1'",s)
        self.assertIn("AXIA_G07_SCAN_PREFLIGHT_STRICT: '1'",s)
        self.assertIn("AXIA_G07_EVENTS_EXECUTOR_AB: '0'",s)
        self.assertNotIn("CERTIFIED_ESTOP=true",s)


    def test_pre_goal_check_effective_fastdds_not_parity_hardcoded_label(self):
        # Owner parity script echoes rmw_effective_class as a literal;
        # actual installed library MUST be checked using rclpy before Goal.
        s=WORKFLOW.read_text()
        self.assertIn("rclpy.get_rmw_implementation_identifier()",s)
        self.assertIn("AXIA_G07_NATIVE_RMW_EFFECTIVE_VERIFIED",s)
        self.assertIn("rmw_fastrtps_cpp",s)
        self.assertNotIn("RMW_IMPLEMENTATION: rmw_cyclonedds_cpp",s)

if __name__=="__main__":
    unittest.main()
