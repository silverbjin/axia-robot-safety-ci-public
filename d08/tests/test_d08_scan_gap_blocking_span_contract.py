"""RED: first process-local Scan gap vs READ-ONLY operation timing scopes.

Source facts: CI #44360979382 initial Path Observer 166.756151 ->
167.153354 with CM native verification complete at 166.821754.
Overlap is correlation, NOT proof the operation caused the GIL stall.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_scan_gap_trace import scan_gap_operation_overlaps

PAIR={"previous_host_monotonic_sec":166.756151,
      "current_host_monotonic_sec":167.153354}
SPANS=[
  {"name":"graph_subscriptions","start_sec":166.700,"end_sec":166.790},
  {"name":"cm_native_service_probe","start_sec":166.790,"end_sec":166.822},
  {"name":"gazebo_native_set_pose","start_sec":166.825,"end_sec":167.100},
  {"name":"later_path","start_sec":167.201,"end_sec":167.500},
]

def test_overlap_sorted_but_not_falsely_called_root_cause():
    v=scan_gap_operation_overlaps(PAIR,SPANS)
    assert v["status"]=="OBSERVED_OVERLAP_NOT_CAUSE"
    assert v["root_cause_confirmed"] is False
    assert v["overlaps"][0]["name"]=="gazebo_native_set_pose"
    assert abs(v["overlaps"][0]["overlap_sec"]-.275)<1e-6
    assert {x["name"] for x in v["overlaps"]}=={
        "graph_subscriptions","cm_native_service_probe","gazebo_native_set_pose"}
    assert all(x["overlap_sec"]>0 for x in v["overlaps"])

def test_no_time_or_untrusted_span_cannot_forge_an_overlap():
    v=scan_gap_operation_overlaps(None,SPANS)
    assert v["status"]=="INSUFFICIENT_TIMING_EVIDENCE"
    assert v["overlaps"]==[]
    v=scan_gap_operation_overlaps(PAIR,[{
      "name":"invalid","start_sec":167.4,"end_sec":166.8}])
    assert v["overlaps"]==[]

def test_span_instrumentation_is_limited_to_no_goal_observer():
    source=(Path(__file__).resolve().parents[1]/
            "harness/d08_same_world_replan.py").read_text()
    for op in ("graph_publishers","graph_subscriptions",
               "cm_get_state_service_wait","cm_get_parameters_service_wait",
               "cm_native_service_probe","gazebo_native_set_pose"):
        assert op in source
    assert "scan_gap_operation_overlaps(" in source
