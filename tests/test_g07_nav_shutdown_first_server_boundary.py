"""First #163 navigation manage callback evidence in existing launch.log only.

Input synthetic log examples are sanitized; real L2 raw launch.log stays private.
"""
import unittest
from d06.diagnostic.g07_nav_shutdown_first_server_boundary import classify

CYCLE1={"navigation_ack":False,"navigation_service_request_sent":True,
        "navigation_service_status":"SERVICE_TIMEOUT",
        "navigation_response_elapsed_sec":40.001275,
        "navigation_manage_group_probe":{"status":"MANAGE_CALLBACK_GROUP_RESPONSIVE",
                                         "is_active":True,"elapsed_sec":0.090408}}

class NavFirstServerBoundary(unittest.TestCase):
    def test_readonly_active_after_timeout_is_not_ack_or_callback_proof(self):
        log="[lifecycle_manager-18] [INFO] [lifecycle_manager_navigation]: Running Nav2 LifecycleManager rcl preshutdown\n"
        r=classify(CYCLE1,log)
        self.assertEqual(r["status"],"CLIENT_TIMEOUT_SERVER_CALLBACK_NOT_OBSERVED_IN_LOG_HOLD")
        self.assertFalse(r["navigation_ack"])
        self.assertFalse(r["server_entry_proven"])
        self.assertFalse(r["root_cause_proven"])
        self.assertEqual(r["release"],"HOLD")

    def test_entry_without_finish_is_stalled_candidate_not_proof(self):
        log="[lifecycle_manager-18] [INFO] [lifecycle_manager_navigation]: Shutting down managed nodes...\n"
        r=classify(CYCLE1,log)
        self.assertEqual(r["status"],"SERVER_ENTERED_FINISH_NOT_LOGGED_HOLD")
        self.assertTrue(r["server_entry_log_observed"])
        self.assertFalse(r["root_cause_proven"])

    def test_finish_but_client_timeout_is_response_gap_candidate_only(self):
        log=("[lifecycle_manager-18] [INFO] [lifecycle_manager_navigation]: Shutting down managed nodes...\n"
             "[lifecycle_manager-18] [INFO] [lifecycle_manager_navigation]: Managed nodes have been shut down\n")
        r=classify(CYCLE1,log)
        self.assertEqual(r["status"],"SERVER_FINISHED_CLIENT_ACK_MISSING_CANDIDATE_HOLD")
        self.assertFalse(r["response_transport_root_proven"])

    def test_actual_ack_retained_without_claiming_software_estop(self):
        r=classify({"navigation_ack":True,"navigation_service_status":"ACK",
                    "navigation_service_request_sent":True}, "")
        self.assertEqual(r["status"],"NAVIGATION_ACK_REPORTED")
        self.assertFalse(r["certified_estop"])

    def test_missing_or_truncated_evidence_cannot_grant_pass(self):
        r=classify(CYCLE1,"")
        self.assertEqual(r["release"],"HOLD")
        self.assertFalse(r["root_cause_proven"])

if __name__=="__main__":unittest.main()
