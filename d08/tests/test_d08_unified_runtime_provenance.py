"""D08 Task00: fail closed on mixed-world / unpinned runtime evidence (NO_GOAL)."""
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "harness"))
from d08_runtime_provenance import make_runtime_provenance

SHA = "a" * 40
ENV = {"ROS_DOMAIN_ID": "69", "GZ_PARTITION": "axia_d08_ci_123"}

def scene(world="default", extra_world="", physical=True):
    person = """<model name="axia_p2_g07_obstacle"><link name="obstacle_link">
       <collision name="obstacle_collision"><geometry><cylinder>
       <radius>0.07</radius><length>0.48</length>
       </cylinder></geometry></collision>
       <visual name="axia_d08_human_mesh"/>
       <sensor name="axia_contact" type="contact"><contact>
       <collision>obstacle_collision</collision></contact></sensor>
       </link></model>""" if physical else ""
    return f'<sdf version="1.9"><world name="{world}">{person}</world>{extra_world}</sdf>'

def test_one_world_physical_person_has_pinned_source_and_partition(tmp_path):
    f=tmp_path/"scene.sdf";f.write_text(scene())
    p=make_runtime_provenance(f, ENV, SHA)
    assert p["source_sha"]==SHA
    assert p["world"]=="default"
    assert p["human_proxy"]=="axia_p2_g07_obstacle"
    assert p["ros_domain_id"]==69
    assert p["gz_partition"]==ENV["GZ_PARTITION"]
    assert len(p["world_sdf_sha256"])==64
    assert p["no_moving_goal"] is True

def test_two_worlds_or_visual_only_actor_must_never_pass(tmp_path):
    f=tmp_path/"scene.sdf"
    f.write_text(scene(extra_world='<world name="other"/>'))
    with pytest.raises(ValueError, match="D08_WORLD_NOT_UNIQUE"):
        make_runtime_provenance(f,ENV,SHA)
    f.write_text(scene(physical=False))
    with pytest.raises(ValueError, match="D08_PHYSICAL_PERSON"):
        make_runtime_provenance(f,ENV,SHA)

def test_cross_domain_or_unpinned_sha_must_not_be_e2e(tmp_path):
    f=tmp_path/"scene.sdf";f.write_text(scene())
    with pytest.raises(ValueError, match="D08_DOMAIN_PARTITION"):
        make_runtime_provenance(f,{**ENV,"GZ_PARTITION":""},SHA)
    with pytest.raises(ValueError, match="D08_SOURCE_SHA"):
        make_runtime_provenance(f,ENV,"main")

def test_github_checkout_owner_mismatch_regression_is_scoped():
    runner=(Path(__file__).resolve().parents[1] / 'scripts' / 'd08_public_gazebo_l2.py').read_text()
    assert "f'safe.directory={ROOT}'" in runner
    assert 'safe.directory=*' not in runner
    assert 'D08_GITHUB_EVENT_SHA_CHECKOUT_MISMATCH' in runner
    assert 'sha_cp.stderr.strip()' in runner
