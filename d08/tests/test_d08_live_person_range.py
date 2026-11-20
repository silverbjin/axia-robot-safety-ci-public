"""D08 Task01 actual ROS pipeline source contract, no synthetic ROS success."""
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_live_person_range import stage_contract

def sample(status="VALID",expected="valid"):
    return {
      "status":status,
      "distance_m":0.35 if status=="VALID" else None,
      "valid_count":12,
      "registered_rgbd_from_actual_sensor":True,
      "actual_yolo_person":status=="VALID",
      "actual_rgbd_samples":4,
      "actual_yolo_detection_arrays":4,
      "reason":None if status=="VALID" else "NO_PERSON_CLASS_IN_ACTUAL_YOLO",
      "control_published":False}

def test_actual_valid_and_reasoned_unknown_contract_are_separate():
    assert stage_contract(sample(),"valid")
    assert stage_contract(sample("UNKNOWN"),"unknown")

@pytest.mark.parametrize("edit,expected",[
 (lambda x:x.update(status="UNKNOWN"),"valid"),
 (lambda x:x.update(valid_count=0),"valid"),
 (lambda x:x.update(actual_yolo_person=False),"valid"),
 (lambda x:x.update(registered_rgbd_from_actual_sensor=False),"valid"),
 (lambda x:x.update(actual_yolo_detection_arrays=0),"unknown"),
 (lambda x:x.update(registered_rgbd_from_actual_sensor=False),"unknown"),
 (lambda x:x.update(reason="YOLO_DETECTION_STREAM_MISSING"),"unknown"),
 (lambda x:x.update(control_published=True),"valid"),
])
def test_fail_closed_no_fake_valid_or_unknown(edit,expected):
    v=sample("UNKNOWN" if expected=="unknown" else "VALID")
    edit(v)
    with pytest.raises(ValueError,match="D08_"):
        stage_contract(v,expected)
