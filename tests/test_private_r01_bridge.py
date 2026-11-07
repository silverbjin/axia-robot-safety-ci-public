"""Public synthetic R01 receipt contract; no private instructor imports."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from private_r01_bridge import ReceiptBlocked, verify_receipts

PIN = 'd86ee9860de8924f6a5b2c5828d493fb7ef7f9eb'
NAMES = ('corridor', 'pre_goal_gate', 'graph', 'supervisor_prestart')

def make_case(root, *, rounds=3):
    for i in range(1,rounds+1):
        folder = root / ('run_'+str(i))
        folder.mkdir()
        for order, name in enumerate(NAMES):
            ns=1_000_000_000 + i*1_000_000 + order*1000
            record={'gate_accepted':False,'authorized_goal':False,
                    'status':'SUPERVISOR_PRESTART_READY' if name=='supervisor_prestart' else 'OBSERVED',
                    'provenance':{'run_id':'g00_'+str(12345678+i),'session_id':'g00-session-1234-'+str(i),
                        'source_sha':PIN,'ros_domain_id':str(170+i),
                        'gz_partition':'p1_prelocal_example_3_'+str(i),
                        'captured_monotonic_ns':ns}}
            if name=='corridor':
                record['result']='CORRIDOR_GRID_READY'
            elif name=='pre_goal_gate':
                record.update(status='PRE_GOAL_READY',goal_sent=False,pending_goal_only=True)
            elif name=='graph':
                record['verdict']={'passed':True,'reasons':[]}
            elif name=='supervisor_prestart':
                record['last_state_received_mono']=ns/1e9
            (folder/(name+'.json')).write_text(json.dumps(record))

class TestReadOnlyR01(unittest.TestCase):
    def test_three_complete_sessions_only_readonly_receipts(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);make_case(p)
            r=verify_receipts(p,expected_sha=PIN,rounds=3,now_ns=2_000_000_000)
            self.assertEqual(r['status'],'R01_READONLY_RECEIPTS_VERIFIED')
            self.assertEqual(r['receipt_count'],12)
            self.assertEqual(r['rounds'],3)
            self.assertFalse(r['gate_accepted'])
            self.assertFalse(r['goal_sent'])
    def test_source_graph_and_corridor_without_gate_accepted_field_are_valid(self):
        # Exact instructor sources omit the top-level flag for these read-only
        # producers. Do not invent a required field; reject only true.
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);make_case(p)
            for name in ('corridor','graph'):
                f=p/('run_2/'+name+'.json')
                obj=json.loads(f.read_text())
                del obj['gate_accepted']
                f.write_text(json.dumps(obj))
            out=verify_receipts(p,expected_sha=PIN,rounds=3,now_ns=2_000_000_000)
            self.assertEqual(out['receipt_count'],12)

    def test_modified_source_sha_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);make_case(p)
            f=p/'run_1/graph.json';v=json.loads(f.read_text());v['provenance']['source_sha']='0'*40;f.write_text(json.dumps(v))
            with self.assertRaisesRegex(ReceiptBlocked,'R01_SOURCE_MISMATCH'):
                verify_receipts(p,expected_sha=PIN,rounds=3,now_ns=2_000_000_000)
    def test_cross_run_replay_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);make_case(p)
            f=p/'run_2/corridor.json';v=json.loads(f.read_text());v['provenance']['ros_domain_id']='171';f.write_text(json.dumps(v))
            with self.assertRaisesRegex(ReceiptBlocked,'R01_DOMAIN_MISMATCH'):
                verify_receipts(p,expected_sha=PIN,rounds=3,now_ns=2_000_000_000)
    def test_receive_timestamp_must_equal_actual_dds_callback(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);make_case(p)
            f=p/'run_3/supervisor_prestart.json';v=json.loads(f.read_text());v['last_state_received_mono'] -= 0.25;f.write_text(json.dumps(v))
            with self.assertRaisesRegex(ReceiptBlocked,'R01_SUPERVISOR_RX_TIME_MISMATCH'):
                verify_receipts(p,expected_sha=PIN,rounds=3,now_ns=2_000_000_000)
    def test_missing_or_reordered_evidence_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);make_case(p)
            f=p/'run_1/pre_goal_gate.json';f.unlink()
            with self.assertRaisesRegex(ReceiptBlocked,'R01_RECEIPT_MISSING'):
                verify_receipts(p,expected_sha=PIN,rounds=3,now_ns=2_000_000_000)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);make_case(p)
            f=p/'run_1/graph.json';v=json.loads(f.read_text());v['provenance']['captured_monotonic_ns']=2;f.write_text(json.dumps(v))
            with self.assertRaisesRegex(ReceiptBlocked,'R01_RECEIPT_ORDER_INVALID'):
                verify_receipts(p,expected_sha=PIN,rounds=3,now_ns=2_000_000_000)
    def test_negative_and_future_timestamps_and_missing_session_block(self):
        for field,value,label in [('captured_monotonic_ns',0,'R01_CAPTURE_TIME_INVALID'),
                                  ('captured_monotonic_ns',4_000_000_000,'R01_CAPTURE_TIME_INVALID'),
                                  ('session_id','', 'R01_SESSION_MISMATCH')]:
            with tempfile.TemporaryDirectory() as d:
                p=Path(d);make_case(p)
                f=p/'run_2/graph.json';v=json.loads(f.read_text());v['provenance'][field]=value;f.write_text(json.dumps(v))
                with self.assertRaisesRegex(ReceiptBlocked,label):
                    verify_receipts(p,expected_sha=PIN,rounds=3,now_ns=2_000_000_000)
    def test_approved_cloud_workflow_is_exact_sha_no_goal_private_only(self):
        workflow=(Path(__file__).resolve().parents[1]/'.github/workflows/p1-t08-r01-readonly.yml').read_text()
        self.assertIn('ref: '+PIN, workflow)
        self.assertIn('name: axia-instructor-sealed',workflow)
        self.assertIn('python3 scripts/private_r01_bridge.py',workflow)
        self.assertIn('python3 -m unittest discover -s tests -p test_private_r01_bridge.py',workflow)
        self.assertIn("github.actor == 'silverbjin'",workflow)
        self.assertIn('rm -rf _instructor_private',workflow)
        self.assertNotIn('actions/upload-artifact',workflow)
        self.assertNotIn('ros2 action send_goal',workflow)
        self.assertNotIn('/axia/safety/start',workflow)
        self.assertNotIn('allow_fault_injection:=true',workflow)

    def test_start_ack_or_goal_artifact_never_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);make_case(p)
            (p/'run_2/start_ack.json').write_text('{}')
            with self.assertRaisesRegex(ReceiptBlocked,'R01_FORBIDDEN_MUTATION_EVIDENCE'):
                verify_receipts(p,expected_sha=PIN,rounds=3,now_ns=2_000_000_000)

    def test_isolated_r01_pin_matches_exact_private_checkout(self):
        from private_r01_bridge import PRIVATE_PIN
        self.assertEqual(PRIVATE_PIN, PIN)
