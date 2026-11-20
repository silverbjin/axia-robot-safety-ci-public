#!/usr/bin/env python3
"""ROS-free contract for read-only D08 original Scan take→callback timeline."""
import asyncio
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"d08/harness"))

class TakeDispatchRegression(unittest.TestCase):
    def _mod(self):
        from d08_rcl_take_dispatch_probe import (TakeTimeline,
            build_scan_take_executor, classify_source_pair)
        return TakeTimeline, build_scan_take_executor, classify_source_pair

    def test_original_subscription_only_records_exact_take_and_callback_stamps(self):
        Timeline, factory, _=self._mod()
        class InvalidHandle(Exception): pass
        class FakeBase:
            def __init__(self, **kwargs): pass
            def _take_subscription(self, sub): return "UPSTREAM_UNMODIFIED"
        class Msg:
            def __init__(self, ns):
                self.header=SimpleNamespace(stamp=SimpleNamespace(
                    sec=ns//1000000000,nanosec=ns%1000000000))
        class Handle:
            def __init__(self): self.calls=0
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def take_message(self,*args):
                self.calls+=1
                return (Msg(43602000000),)
        delivered=[]
        sub=SimpleNamespace(handle=Handle(),msg_type=Msg,raw=False,
            _callback_type="message-only",callback=lambda m:delivered.append(m))
        async def ae(cb,*args): cb(*args)
        E=factory(FakeBase,InvalidHandle,ae,"message-only")
        log=Timeline(32)
        exe=E(log)
        exe.arm_scan(sub)
        self.assertEqual(exe._take_subscription(object()),"UPSTREAM_UNMODIFIED")
        co=exe._take_subscription(sub)
        self.assertEqual(sub.handle.calls,1)
        asyncio.run(co())
        rows=log.snapshot()
        self.assertEqual([r["stage"] for r in rows],["take_complete","callback_dispatch"])
        self.assertEqual([r["source_stamp_ns"] for r in rows],[43602000000]*2)
        self.assertEqual(len(delivered),1)
        self.assertLessEqual(rows[0]["at"],rows[1]["at"])

    def test_first_observer_gap_late_take_distinct_from_late_dispatch(self):
        _,_,diagnose=self._mod()
        pair={"previous_ros_stamp_ns":43500000000,"current_ros_stamp_ns":43602000000,
              "previous_host_monotonic_sec":259.107713,
              "current_host_monotonic_sec":259.642189}
        def rows(take2,dispatch2):
            return [
              {"stage":"take_complete","source_stamp_ns":43500000000,"at":259.105},
              {"stage":"callback_dispatch","source_stamp_ns":43500000000,"at":259.107},
              {"stage":"take_complete","source_stamp_ns":43602000000,"at":take2},
              {"stage":"callback_dispatch","source_stamp_ns":43602000000,"at":dispatch2},
            ]
        late=diagnose(pair,rows(259.638,259.640),0.223221)
        self.assertTrue(late["exact_source_pair_proven"])
        self.assertEqual(late["candidate"],"ORIGINAL_RCL_TAKE_LATE_CANDIDATE")
        self.assertGreater(late["take_gap_sec"],.5)
        early=diagnose(pair,rows(259.328,259.641),0.223221)
        self.assertEqual(early["candidate"],"ORIGINAL_POST_TAKE_DISPATCH_DELAY_CANDIDATE")
        self.assertLess(early["take_gap_sec"],.5)
        self.assertGreater(early["current_take_to_dispatch_sec"],.3)

    def test_missing_or_duplicate_stamps_fail_closed_not_a_cause(self):
        _,_,diagnose=self._mod()
        pair={"previous_ros_stamp_ns":1,"current_ros_stamp_ns":2,
              "previous_host_monotonic_sec":1.0,
              "current_host_monotonic_sec":1.534476}
        self.assertEqual(diagnose(pair,[],.223)["candidate"],"TAKE_DISPATCH_EVIDENCE_INCOMPLETE")
        rows=[{"stage":t,"source_stamp_ns":s,"at":v}
            for s,v in ((1,1.0),(2,1.3)) for t in ("take_complete","callback_dispatch")]
        rows.append(rows[0].copy())
        self.assertEqual(diagnose(pair,rows,.223)["candidate"],"TAKE_DISPATCH_EVIDENCE_INCOMPLETE")

    def test_read_only_opt_in_in_original_observer_not_safety_layers(self):
        src=(ROOT/"d08/harness/d08_same_world_replan.py").read_text()
        self.assertIn('AXIA_D08_TAKE_DISPATCH_PROBE',src)
        self.assertIn("original_rcl_take_vs_callback",src)
        self.assertIn("exe.arm_scan(subs[0])",src)
        self.assertIn("first_scan_timing_boundary",src)
        self.assertNotIn("500ms limit disabled",src)

    def test_single_wsl2_handover_pins_l2_and_compacts_latest_failure(self):
        wrapper=(ROOT/"d08/scripts/d08_owner_take_dispatch_wsl2_one_shot.sh")
        self.assertTrue(wrapper.exists(),"WSL2 GitHub one-shot missing")
        src=wrapper.read_text()
        self.assertIn("0998978174f9b40ad83bc2fe7907d5dab62115bc",src)
        self.assertIn("1a17ddaab0eac123188e29cf031c819187c4f82d",src)
        self.assertIn("142c4dcc820a04accdf869b4cc903f62c7977b2c",src)
        self.assertIn("export AXIA_D08_TAKE_DISPATCH_PROBE=1",src)
        self.assertIn('D08_OWNER_UPLOAD_ONLY_THIS_ZIP=',src)
        self.assertIn('--max-mib 8',src)
        self.assertIn('bash "$BASH_SRC" --doctor',src)
        self.assertIn('bash "$BASH_SRC" --run',src)
        self.assertNotIn("AXIA_MVP_DEMO_ACCEPTED=PASS",src)

if __name__=="__main__":
    unittest.main()
