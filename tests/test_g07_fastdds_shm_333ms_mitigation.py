"""#157 official Fast DDS SHM 333ms hold A/B, never relax safety TTL.

Upstream bug https://github.com/eProsima/Fast-DDS/issues/6535
Merged fix https://github.com/eProsima/Fast-DDS/pull/6559 (master).
Jazzy installed 2.14.x fix availability NOT assumed. Prevent unreviewed
SHM source patch and instead test scoped official UDPv4 builtin transport.
"""
from pathlib import Path
import json
import unittest

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT/".github/workflows/axia-g07-fv17-owner-evidence-parity-native-l2.yml"
FIXTURE=ROOT/"tests/fixtures/g07_44683741133_first_rmw_receipt.json"


class OfficialFastDDSShmMitigation(unittest.TestCase):
    def test_reproduce_first_fastdds_receive_not_source_gap(self):
        x=json.loads(FIXTURE.read_text())
        self.assertEqual(x["rmw"]["publication_seq_gap"],1)
        self.assertLess(x["rmw"]["source_gap_ms"],120)
        self.assertGreater(x["rmw"]["received_gap_ms"],300)
        self.assertEqual(x["status"],"HOLD_FIRST_ACTUAL_RMW_RECEIPT_GAP")
        self.assertFalse(x["rmw"]["rmw_transport_root_proven"])

    def test_scoped_real_l2_disables_shm_for_all_ros_participants(self):
        s=WORKFLOW.read_text()
        self.assertIn("FASTDDS_BUILTIN_TRANSPORTS: UDPv4",s)
        self.assertIn('test "$FASTDDS_BUILTIN_TRANSPORTS" = UDPv4',s)
        self.assertIn("AXIA_G07_FASTDDS_BUILTIN_TRANSPORTS=UDPv4",s)
        # Do NOT enable on global Student/default WSL2 source or unrelated CI.
        self.assertIn("cycle: [1, 2]",s)
        self.assertIn("edd805e84f15a7eae9b14454803fc0912ec0ccf8",s)
        self.assertNotIn("AXIA_G07_OBSERVER_EXECUTOR_AB: 'single'",s)
        self.assertIn("AXIA_G07_INDEPENDENT_CM_RMW_PAIR",s)

    def test_unmodified_official_nav2_and_fail_closed_gate(self):
        s=WORKFLOW.read_text()
        self.assertIn("AXIA_G07_FORMAL_L2=HOLD",s)
        self.assertIn("verify_real_goal_and_guard_evidence || exit 3",s)
        self.assertIn("CERTIFIED_ESTOP=false",s)
        self.assertNotIn("source_timeout: 99",s)
        self.assertNotIn("RMW_IMPLEMENTATION: rmw_cyclonedds_cpp",s)


if __name__=="__main__":
    unittest.main()
