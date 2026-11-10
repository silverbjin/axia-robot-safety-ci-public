"""Regression from G07 Owner 93JLtN3u native Gazebo contacts listing."""
from pathlib import Path
import sys
import pytest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'d08/harness'))
from p2_contact_discovery import resolve_g07_contact_topic, ALIAS, SENSOR

def test_real_owner_gazebo_harmonic_sensor_scoped_topic():
    topics='/clock\n/world/default/pose/info\n'+SENSOR+'\n/scan\n'
    assert resolve_g07_contact_topic(topics)==SENSOR

def test_explicit_alias_and_identity_priority():
    assert resolve_g07_contact_topic(ALIAS)==ALIAS
    assert resolve_g07_contact_topic(ALIAS+'\n'+SENSOR)==SENSOR

def test_no_contact_topic_or_forged_nearby_name_is_unknown_not_zero():
    for txt in ('','/clock','/axia_p2_g07/contacts-fake',
                '/world/default/model/other/link/obstacle_link/sensor/axia_contact/contact'):
        assert resolve_g07_contact_topic(txt) is None

def test_duplicate_or_malformed_topic_list_rejected():
    with pytest.raises(ValueError): resolve_g07_contact_topic(SENSOR+'\n'+SENSOR)
    with pytest.raises(ValueError): resolve_g07_contact_topic('a'*60000)
