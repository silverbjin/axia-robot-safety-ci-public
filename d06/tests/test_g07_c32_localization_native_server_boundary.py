"""C32 RED: original Localization native service ACK and server-stage separation."""
import unittest
from d06.diagnostic.g07_c32_localization_stage import assess_native_shutdown

def log(sec, msg, name="lifecycle_manager_localization"):
    return (f"[lifecycle_manager-7] [INFO] [{sec:.9f}] [{name}]: "
            + msg + "\n")

def native(**kwargs):
    return {"status":"SERVICE_TIMEOUT","request_sent":True,
            "ack_response_received":False,"response_wait_sec":12.997088,
            "request_wall_ns":100_000_000_000,
            "response_wall_ns":113_000_000_000,
            **kwargs}

class NativeServerStage(unittest.TestCase):
    def test_real_server_manager_callback_without_ack_must_not_pass(self):
        launch=(log(99.5,"Shutting down managed nodes...")+
                log(100.2,"Shutting down managed nodes...")+
                log(100.4,"Deactivating amcl")+
                log(113.3,"Running Nav2 LifecycleManager rcl preshutdown"))
        x=assess_native_shutdown(native(),launch)
        self.assertEqual(x["status"],"SERVER_CALLBACK_ENTERED_ACK_MISSING")
        self.assertTrue(x["server_callback_entry_observed"])
        self.assertFalse(x["native_ack"])
        self.assertFalse(x["release_pass"])
        self.assertFalse(x["root_cause_proven"])

    def test_sigint_preshutdown_only_after_timeout_is_not_service_ack(self):
        launch=(log(114,"Running Nav2 LifecycleManager rcl preshutdown")+
                log(114.2,"Destroying lifecycle_manager_localization"))
        x=assess_native_shutdown(native(),launch)
        self.assertEqual(x["status"],"SERVICE_CALLBACK_NOT_OBSERVED_CAUSE_UNPROVEN")
        self.assertFalse(x["server_callback_entry_observed"])
        self.assertFalse(x["native_ack"])
        self.assertFalse(x["owner_accepted"])

    def test_clock_step_or_missing_wall_timestamps_fails_closed(self):
        for item in [
            {**native(),"response_wall_ns":110_000_000_000},
            {"status":"SERVICE_TIMEOUT","request_sent":True,
             "ack_response_received":False,"response_wait_sec":13.0}]:
            with self.subTest(item=item):
                x=assess_native_shutdown(item,log(101,"Shutting down managed nodes..."))
                self.assertEqual(x["status"],"NATIVE_REQUEST_WALL_ALIGNMENT_UNVERIFIED")
                self.assertFalse(x["root_cause_proven"])

    def test_real_native_ack_is_only_positive_evidence(self):
        n=native()
        n.update(status="ACK",ack_response_received=True,response_wait_sec=1.5,
                 response_wall_ns=101_500_000_000)
        x=assess_native_shutdown(n,log(100.2,"Shutting down managed nodes..."))
        self.assertTrue(x["native_ack"])
        self.assertFalse(x["release_pass"]) # separate TTL + clean process gates
        self.assertFalse(x["owner_accepted"])

if __name__=="__main__":
    unittest.main()
