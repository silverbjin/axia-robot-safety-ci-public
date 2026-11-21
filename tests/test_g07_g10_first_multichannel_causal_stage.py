"""Numerical regression grounded in actual native first safety delivery failures.

L0 cannot prove DDS/Executor root cause; preserve first pair, time base,
other live callbacks and independent bag. No behavior/TTL mutations.
"""
import unittest
from d06.diagnostic.g07_g10_multichannel_causal_stage import assess

class FirstG10Boundary(unittest.TestCase):
    def test_exact_scan_first_600ms_original_reader_not_global_process_halt(self):
        r=assess(dict(topic='scan',observer_ms=600.502826,header_sim_ms=102.,
                      rmw_source_ms=107.857389,rmw_received_ms=599.696375,
                      rosbag_same_header_ms=107.737729,seq_gap=1,
                      clock_callbacks_inside=9,odom_callbacks_inside=1))
        self.assertEqual(r['first_boundary'],'ORIGINAL_SUBSCRIBER_RECEIVE_OR_TAKE_LATE_HOLD')
        self.assertEqual(r['not_proven'],['RMW_RECEPTION_VS_TAKE','HOST_EXECUTOR_ROOT','GZ_BRIDGE_ROOT'])
        self.assertTrue(r['other_callback_progress_during_gap'])
        self.assertFalse(r['whole_process_halt_proven'])
        self.assertFalse(r['root_cause_proven'])
        self.assertEqual(r['release'],'HOLD')

    def test_original_cm_first_received_gap_but_source_is_normal(self):
        r=assess(dict(topic='cm',observer_ms=388.878454,header_sim_ms=None,
                      rmw_source_ms=50.018636,rmw_received_ms=382.004174,
                      independent_same_seq_received_ms=50.15,seq_gap=1,
                      clock_callbacks_inside=None,odom_callbacks_inside=None))
        self.assertEqual(r['first_boundary'],'ORIGINAL_SUBSCRIBER_RECEIVE_OR_TAKE_LATE_HOLD')
        self.assertEqual(r['release'],'HOLD')
        self.assertFalse(r['rmw_transport_root_proven'])

    def test_source_gap_or_missing_seq_fail_closed(self):
        base=dict(topic='scan',observer_ms=600.5,header_sim_ms=102,
                  rmw_source_ms=108.,rmw_received_ms=600.,rosbag_same_header_ms=107.7,
                  seq_gap=1,clock_callbacks_inside=0,odom_callbacks_inside=0)
        x=assess(dict(base,rmw_source_ms=410.))
        self.assertEqual(x['first_boundary'],'SOURCE_PERIOD_BREACH_CANDIDATE_HOLD')
        y=assess(dict(base,seq_gap=-1))
        self.assertEqual(y['first_boundary'],'EXACT_PAIR_UNVERIFIED_HOLD')
        z=assess(dict(base,rosbag_same_header_ms=None))
        self.assertEqual(z['first_boundary'],'EXACT_PAIR_UNVERIFIED_HOLD')
        w=assess(dict(base,rmw_source_ms=10**15))
        self.assertEqual(w['first_boundary'],'EXACT_PAIR_UNVERIFIED_HOLD')
        for q in (x,y,z,w):
            self.assertFalse(q['root_cause_proven'])
            self.assertEqual(q['release'],'HOLD')

    def test_all_normal_is_not_an_acceptance_certificate(self):
        r=assess(dict(topic='scan',observer_ms=100,header_sim_ms=100,
                      rmw_source_ms=100,rmw_received_ms=99,rosbag_same_header_ms=100,
                      seq_gap=1,clock_callbacks_inside=3,odom_callbacks_inside=1))
        self.assertEqual(r['first_boundary'],'NO_BREACH_IN_THIS_PAIR_NOT_ACCEPTANCE_HOLD')
        self.assertFalse(r['root_cause_proven'])
        self.assertFalse(r['certified_estop'])
        self.assertEqual(r['release'],'HOLD')

if __name__=='__main__': unittest.main()
