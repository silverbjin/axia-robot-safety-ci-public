"""D08 public live same-world mandatory two distances + actual UNKNOWN gate.

Static L0 fixture only. Actual ROS and Gazebo are verified in L2 separately.
"""
import sys
from pathlib import Path
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"harness"))
from d08_live_person_range_session import grade_actual_person_stages

def stages():
    return [{"stage":n,"native_ack":True,
             "roi_status":"UNKNOWN" if n=="unknown" else "VALID",
             "distance_m":None if n=="unknown" else d,
             "registration_confirmed":True,
             "reason":"NO_PERSON_CLASS_IN_ACTUAL_YOLO" if n=="unknown" else None}
             for n,d in [("farther",.58),("stop",.35),("unknown",None)]]

def test_two_distinct_actual_valid_and_reasoned_unknown():
    r=grade_actual_person_stages(stages())
    assert r["valid_distance_delta_m"]==.23
    assert r["robot_goal_sent"] is False

@pytest.mark.parametrize("change,reason",[
  (lambda a:a.pop(0),"STAGES_MISSING"),
  (lambda a:a[0].update(native_ack=False),"ACK_MISSING"),
  (lambda a:a[0].update(roi_status="UNKNOWN"),"TWO_REAL_VALID"),
  (lambda a:a[1].update(distance_m=.54),"NOT_DISTINCT"),
  (lambda a:a[1].update(registration_confirmed=False),"REGISTRATION"),
  (lambda a:a[2].update(reason="YOLO_DETECTION_STREAM_MISSING"),"UNKNOWN_NOT_ACTUAL"),
])
def test_no_fake_two_valid_unknown(change,reason):
    a=stages();change(a)
    with pytest.raises(ValueError,match=reason):
        grade_actual_person_stages(a)
