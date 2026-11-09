"""D06 RED/GREEN Nav2 Jazzy official monitor source-only YAML contract."""
from pathlib import Path
import yaml
import pytest

YAML=Path(__file__).resolve().parents[1]/"params"/"collision_monitor_d06.yaml"

def params():
    root=yaml.safe_load(YAML.read_text())
    assert list(root)==["collision_monitor"]
    return root["collision_monitor"]["ros__parameters"]

def test_official_nav2_zones_and_point_limit():
    p=params()
    assert p["polygons"]==["StopZone","SlowZone"]
    stop=p["StopZone"];slow=p["SlowZone"]
    assert (stop["type"],stop["action_type"],stop["radius"],stop["min_points"])==("circle","stop",0.4,4)
    assert (slow["type"],slow["action_type"],slow["radius"],slow["slowdown_ratio"],slow["min_points"])==("circle","slowdown",0.75,0.30,4)
    assert p["StopZone"]["radius"]<p["SlowZone"]["radius"]

def test_isolated_cmd_topics_not_robot_actuator():
    p=params()
    assert p["cmd_vel_in_topic"]=="/axia/d06/test/cmd_in"
    assert p["cmd_vel_out_topic"]=="/axia/d06/test/cmd_out"
    assert p["cmd_vel_out_topic"] not in ("/cmd_vel","cmd_vel")
    assert p["enable_stamped_cmd_vel"] is False
    assert p["base_frame_id"]=="base_footprint"

def test_one_scan_source_and_finite_timeout():
    p=params()
    assert p["observation_sources"]==["scan"]
    assert p["scan"]["topic"]=="/axia/d06/test/scan"
    assert p["scan"]["type"]=="scan"
    assert p["scan"]["enabled"] is True
    assert 0<p["source_timeout"]<=1.0
    assert 0<p["scan"]["source_timeout"]<=1.0
    assert p["enabled"] is True
    assert p["use_sim_time"] is False

def test_source_contract_no_motion_or_p1_mutation():
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]
    assert not any("cmd_vel"==v.name for v in root.rglob("*") if v.is_file())
    assert not (root/"ros2_ws").exists()
