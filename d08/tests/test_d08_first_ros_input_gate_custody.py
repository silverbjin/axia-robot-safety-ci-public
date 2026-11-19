"""RED: missing first ROS startup topic must be identified, not generic HOLD.

Actual Gazebo #44441214032 cycle_0007: native Gazebo Scan 259,
independent ROS Scan 248, native Clock 623 while Observer's initial
Scan/Costmap/Odom readiness gate failed at 25s. Which input is missing
cannot be determined from the old verdict. No timeout/TTL changes.
"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_same_world_replan import diagnose_initial_ros_gate

def item(at,stamp=2.0):
    return {"at":at,"stamp":stamp}

def test_costmap_missing_captured_by_name_not_all_sensors_failed():
    v=diagnose_initial_ros_gate(
        ([item(10.),item(10.1)],[],[item(10.2)]),
        {"scan":[{"at":10.}],"odom":[{"at":10.1}],
         "clock":[{"at":10.2}],"tf":[]},
        {"scan":3,"costmap":0,"odom":2},
        now=10.3)
    assert v["missing_inputs"]==["costmap"]
    assert v["accepted_counts"]=={"scan":2,"costmap":0,"odom":1}
    assert v["raw_callback_counts"]["scan"]==3
    assert v["independent_ros_counts"]["scan"]==1
    assert v["last_host_age_sec"]["costmap"] is None

def test_scan_missing_captured_even_when_native_transport_exists():
    v=diagnose_initial_ros_gate(
        ([],[item(10.1)],[item(10.2)]),{},
        {"scan":0,"costmap":1,"odom":1},now=10.3)
    assert v["missing_inputs"]==["scan"]
    assert v["ready"] is False

def test_diagnostics_are_read_only_and_do_not_relax_initial_gate():
    src=(Path(__file__).resolve().parents[1]/
       "harness/d08_same_world_replan.py").read_text()
    assert 'result["initial_gate_diagnostics"]=' in src
    assert '"SCAN_COSTMAP_ODOM_MISSING",25' in src
    assert "raw_callback_counts" in src
    assert "diagnose_initial_ros_gate(" in src
