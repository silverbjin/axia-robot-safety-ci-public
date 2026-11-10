"""RED owner evidence regression: actual 2026-11-10 Gazebo CI Contact excerpt.

Source: Actions #42812302582, positive_contact_native.log; one non-robot
calibration ran successfully, but the former parser falsely reported BLOCKED.
"""
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'d08/harness'))
from d08_contact_positive_contract import count_nonrobot_positive_contacts

# Exact Gazebo protobuf-text shape, shortened to one complete contact record.
REAL_CONTACT='''header {
  stamp {
    sec: 13
    nsec: 539000000
  }
}
contact {
  header {
    stamp {
      sec: 13
      nsec: 539000000
    }
  }
  collision1 {
    id: 48
    name: "axia_p2_g07_obstacle::obstacle_link::obstacle_collision"
  }
  collision2 {
    id: 87
    name: "axia_d08_contact_calibrator::calibrator_link::calibrator_collision"
  }
  position {
    x: -1.2
    y: -0.5
    z: 0.47941600000000006
  }
  normal {
    z: 1
  }
  depth: 0.00058399999999991792
}
'''

def test_actual_native_gazebo_positive_contact_is_detected():
    assert count_nonrobot_positive_contacts(REAL_CONTACT)==1
    assert count_nonrobot_positive_contacts(REAL_CONTACT*3)==3

def test_empty_topic_is_unknown_not_positive():
    assert count_nonrobot_positive_contacts('')==0
    assert count_nonrobot_positive_contacts(
       '/world/default/model/axia_p2_g07_obstacle/link/obstacle_link/sensor/axia_contact/contact')==0

def test_wrong_object_or_malformed_body_is_not_positive():
    bad=REAL_CONTACT.replace('axia_d08_contact_calibrator::','different_robot::')
    assert count_nonrobot_positive_contacts(bad)==0
    # Adjacent contact payload fields, not just any two model names in stdout.
    assert count_nonrobot_positive_contacts(
        'collision1: '+REAL_CONTACT.split('name: ')[1])==0
    assert count_nonrobot_positive_contacts(
        'collision1 { name: "axia_p2_g07_obstacle::obstacle_link::obstacle_collision" }')==0

def test_reversed_collision_order_still_positive():
    assert count_nonrobot_positive_contacts(
        REAL_CONTACT.replace(
         'axia_p2_g07_obstacle::obstacle_link::obstacle_collision','TEMP')
         .replace('axia_d08_contact_calibrator::calibrator_link::calibrator_collision',
                  'axia_p2_g07_obstacle::obstacle_link::obstacle_collision')
         .replace('TEMP','axia_d08_contact_calibrator::calibrator_link::calibrator_collision'))==1

def test_wrong_type_rejected():
    with pytest.raises(TypeError):count_nonrobot_positive_contacts(None)
