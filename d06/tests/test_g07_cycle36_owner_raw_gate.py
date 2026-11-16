"""No ROS/Goal: Cycle36 final Owner original evidence must stay HOLD until review."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

BASE=Path(__file__).resolve().parents[1]
P=BASE/"live/g07_cycle36_owner_raw_gate.py"
spec=importlib.util.spec_from_file_location("owner_gate",P)
gate=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
SOURCE="2b59c1a74513ac5a5b80c5bd424001a625c07617"

def make_fake_original(root, *,cm_gap=.05):
    """Only test-contract fixture; NEVER use as physical Owner/CI evidence."""
    d=root/"G07"/"live";d.mkdir(parents=True)
    (root/"source.sha").write_text(SOURCE+"\n")
    report={"status":"NUMERICAL_CANDIDATE",
            "common_g07_ci_oracle_status":"CI_GAZEBO_MOVING_GOAL_CANDIDATE",
            "shared_execution_mode":"owner","owner_authority_verified":True,
            "goal_cancel_ack":True,"guard_latched":False,
            "first_guard_latch":None,"first_timing_violation":None,
            "goal_uuid":"a"*32,"odom_stopped_dwell_sec":1.01}
    report.update({k:v*.5 for k,v in gate.LIMITS.items()})
    (d/"ci_moving_goal_result.json").write_text(json.dumps(report))
    events=[{"kind":"owner_goal_published","t":10.0}]
    for i in range(15):
        ns=int((10+i*cm_gap)*1e9)
        events.append({"kind":"pre_guard","t":10+i*cm_gap,
            "rmw_source_ns":ns,"rmw_received_ns":ns+1000000,
            "rmw_publication_seq":200+i})
    (d/"actual_ros_events.jsonl").write_text(
        "".join(json.dumps(x)+"\n" for x in events))
    return d

class OriginalEvidenceGate(unittest.TestCase):
    def test_pass_can_only_return_unaccepted_raw_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);make_fake_original(root)
            r=gate.assess_owner_original(root,SOURCE)
            self.assertEqual(r["status"],"NUMERICAL_CANDIDATE_RAW_REVIEW_REQUIRED")
            self.assertFalse(r["mvp_demo_accepted"])
            self.assertFalse(r["certified_estop"])
            self.assertFalse(r["owner_l3_accepted"])
            self.assertEqual(r["original_cm_packets"],15)
    def test_first_cm_gap_120ms_blocks_even_when_seven_observer_maxima_look_green(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);make_fake_original(root,cm_gap=.133)
            r=gate.assess_owner_original(root,SOURCE)
            self.assertEqual(r["status"],"HOLD")
            self.assertIn("120MS",r["reason"])
    def test_guard_latch_wrong_source_or_missing_original_all_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);d=make_fake_original(root)
            self.assertEqual(gate.assess_owner_original(root,"0"*40)["status"],"HOLD")
            p=d/"ci_moving_goal_result.json"
            j=json.loads(p.read_text());j["guard_latched"]=True
            p.write_text(json.dumps(j))
            self.assertEqual(gate.assess_owner_original(root,SOURCE)["status"],"HOLD")
            p.unlink()
            self.assertEqual(gate.assess_owner_original(root,SOURCE)["status"],"HOLD")
    def test_rmw_sequence_gap_rejected_without_using_nonnative_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);d=make_fake_original(root)
            p=d/"actual_ros_events.jsonl";lines=p.read_text().splitlines()
            row=json.loads(lines[4]);row["rmw_publication_seq"]+=3
            lines[4]=json.dumps(row);p.write_text("\n".join(lines)+"\n")
            r=gate.assess_owner_original(root,SOURCE)
            self.assertEqual(r["status"],"HOLD")
            self.assertIn("SEQUENCE",r["reason"])

if __name__=="__main__":
    unittest.main()
