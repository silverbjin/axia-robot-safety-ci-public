#!/usr/bin/env python3
"""D08 one-world Gazebo educational view: human-looking *physical* fixture.

Attach the human mesh to the SAME Gazebo model/link as the existing G07
Collision and Contact sensor. Original P2 set_pose moves everything together;
no separate Actor scripted trajectory or new safety/planner/controller code.
This is a collision PROXY, not a human-body geometry certification.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

ET.register_namespace('xacro', 'http://www.ros.org/wiki/xacro')
SENSOR_NAME = 'axia_d08_registered_rgbd'
ACTOR_NAME = 'axia_d08_visual_person'
PHYSICAL_NAME = 'axia_p2_g07_obstacle'
RGB_TOPIC = '/axia/d08/rgbd/image'
DEPTH_TOPIC = '/axia/d08/rgbd/depth_image'
OPTICAL_FRAME = 'axia_d08_rgbd_optical'
HUMAN_VISUAL_NAME='axia_d08_human_mesh'
HUMAN_VISUAL_FALLBACK='axia_d08_human_torso'



def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sub(parent, tag, value=None, **attrs):
    el = ET.SubElement(parent, tag, attrs)
    if value is not None:
        el.text = str(value)
    return el


def make_yolo_params(model: Path) -> str:
    # The private source already contains the tested D04 package.
    # Public simulation-only source tests can import this file without copying
    # the instructor D04 package or its reference implementation.
    sys.path.insert(0, str(ROOT / 'ros2_ws/src/axia_d04_vision_demo'))
    from axia_d04_vision_demo.config import build_yolo_config
    data = build_yolo_config(model)
    old = 'rgb_topic: /camera/image_raw'
    if data.count(old) != 1:
        raise ValueError('D04_YOLO_CONFIG_UNEXPECTED')
    return data.replace(old, 'rgb_topic: ' + RGB_TOPIC)


def attach_human_visual_to_fixture(wn, actor_mesh: Path) -> None:
    """Only change SDF visuals; preserve original P2 Collision/Contact/touch.

    The original `axia_p2_g07_obstacle` model is moved by P2's native
    /world/default/set_pose and renders the human in the same rigid transform.
    An animated <actor> cannot safely guarantee this relationship.
    """
    matches=wn.findall("./model[@name='"+PHYSICAL_NAME+"']")
    if len(matches)!=1:
        raise ValueError('D08_PHYSICAL_OBSTACLE_NOT_UNIQUE')
    model=matches[0]
    links=model.findall("./link[@name='obstacle_link']")
    if len(links)!=1:
        raise ValueError('D08_PHYSICAL_OBSTACLE_LINK_NOT_UNIQUE')
    link=links[0]
    collision=link.find("./collision[@name='obstacle_collision']")
    if collision is None:
        raise ValueError('D08_PHYSICAL_COLLISION_MISSING')
    radius=collision.findtext("./geometry/cylinder/radius")
    length=collision.findtext("./geometry/cylinder/length")
    if radius is None or length is None or abs(float(radius)-.07)>1e-8 or abs(float(length)-.48)>1e-8:
        raise ValueError('D08_COLLISION_GEOMETRY_CHANGED')
    sensors=link.findall("./sensor[@name='axia_contact']")
    if len(sensors)!=1 or sensors[0].findtext("./contact/collision")!='obstacle_collision':
        raise ValueError('D08_CONTACT_SENSOR_NOT_ON_PROXY_COLLISION')
    old=link.findall("./visual[@name='obstacle_visual']")
    if len(old)!=1:
        raise ValueError('D08_EXPECTED_ONE_ORIGINAL_ORANGE_VISUAL')
    link.remove(old[0])

    # The COLLADA human asset was already used by D04's RGB YOLO demo.
    # As an SDF <visual><mesh> it is a static pose, not a skeletal
    # animation; the model itself moves along the P2 G07 test trajectory.
    visual=_sub(link,'visual',None,name=HUMAN_VISUAL_NAME)
    _sub(visual,'pose','0 0 0.76 0 0 3.14159')
    geom=_sub(visual,'geometry')
    mesh=_sub(geom,'mesh')
    _sub(mesh,'uri',str(actor_mesh.resolve()))
    _sub(mesh,'scale','0.75 0.75 0.75')

    # Gazebo Harmonic GPU LiDAR (OGRE2) interrogates rendered geometry.
    # walk.dae has no usable lower-leg rasterized silhouette at scan z~0.2m.
    # Owner EEUOfVQL recorded 50 real /safety/scan fronts 2.02-2.07m
    # after a true set_pose ACK, proving Collision alone was insufficient.
    # This narrow pants-colored shin surface is ONE simple sensor-visible
    # primitive, not a second humanoid and NOT a changed physics collision.
    shin=_sub(link,'visual',None,name='axia_d08_lidar_leg_surface')
    shin_geom=_sub(shin,'geometry')
    shin_cyl=_sub(shin_geom,'cylinder')
    _sub(shin_cyl,'radius','0.07')
    _sub(shin_cyl,'length','0.48')
    shin_mat=_sub(shin,'material')
    _sub(shin_mat,'ambient','0.09 0.13 0.22 1')
    _sub(shin_mat,'diffuse','0.09 0.13 0.22 1')


    # Exactly ONE human renderer. The previous head/torso/leg fallback
    # overlaid the COLLADA mesh and appeared as two stationary humans.
    # No fallback visuals are added; a mesh rendering error must be
    # diagnosed instead of silently drawing a duplicate body.

    if model.find("./link[@name='obstacle_link']/collision[@name='obstacle_collision']") is None:
        raise ValueError('D08_SAFETY_COLLISION_NOT_PRESERVED')
    if wn.find("./actor[@name='"+ACTOR_NAME+"']") is not None:
        raise ValueError('D08_SEPARATE_VISUAL_ACTOR_FORBIDDEN')


def build_overlay(world: Path, robot: Path, actor_mesh: Path, output: Path) -> dict:
    world, robot, actor_mesh, output = map(Path, (world, robot, actor_mesh, output))
    for p in (world, robot, actor_mesh):
        if p.is_symlink() or not p.is_file():
            raise ValueError('D08_REQUIRED_REAL_ASSET_MISSING:' + p.name)
    if actor_mesh.suffix.lower() != '.dae':
        raise ValueError('D08_ACTOR_DAE_REQUIRED')
    if output.exists() or output.is_symlink():
        raise ValueError('D08_OUTPUT_EXISTS')
    w = ET.parse(world)
    r = ET.parse(robot)
    wn = w.getroot().find('.//world')
    if wn is None or wn.get('name') != 'default':
        raise ValueError('D08_OFFICIAL_WORLD_REQUIRED')
    if len(wn.findall(".//model[@name='" + PHYSICAL_NAME + "']")) != 1:
        raise ValueError('D08_PHYSICAL_OBSTACLE_NOT_UNIQUE')
    if len(wn.findall(".//plugin[@name='gz::sim::systems::Contact']")) != 1:
        raise ValueError('D08_PHYSICAL_CONTACT_WORLD_PLUGIN_REQUIRED')
    if wn.find("actor[@name='" + ACTOR_NAME + "']") is not None:
        raise ValueError('D08_DUPLICATE_ACTOR')
    cam = r.getroot().find(".//link[@name='camera_link']")
    if cam is None:
        raise ValueError('D08_OFFICIAL_WAFFLE_CAMERA_LINK_MISSING')
    if r.getroot().find(".//sensor[@name='" + SENSOR_NAME + "']") is not None:
        raise ValueError('D08_DUPLICATE_RGBD')
    before_plugins = len(r.getroot().findall('.//plugin'))
    sensor = ET.SubElement(cam, 'sensor', {
        'name':SENSOR_NAME, 'type':'rgbd_camera'
    })
    _sub(sensor,'pose','0 0 0 0 -0.12 0')
    _sub(sensor,'always_on','1')
    _sub(sensor,'update_rate','5')
    _sub(sensor,'topic','axia/d08/rgbd')
    _sub(sensor,'gz_frame_id',OPTICAL_FRAME)
    camera = _sub(sensor, 'camera')
    _sub(camera, 'horizontal_fov','1.35')
    image = _sub(camera,'image')
    _sub(image,'width','640')
    _sub(image,'height','480')
    _sub(image,'format','R8G8B8')
    clip=_sub(camera,'clip')
    _sub(clip,'near','0.15')
    _sub(clip,'far','8.0')

    attach_human_visual_to_fixture(wn,actor_mesh)

    if len(r.getroot().findall('.//plugin')) != before_plugins:
        raise ValueError('D08_ROBOT_PLUGIN_MODIFIED')
    if len(r.getroot().findall(".//sensor[@name='" + SENSOR_NAME + "']")) != 1:
        raise ValueError('D08_SENSOR_NOT_UNIQUE')
    output.mkdir(parents=True,exist_ok=False)
    robot_out=output/'axia_d08_waffle_rgbd.sdf.xacro'
    world_out=output/'axia_d08_p2_person_world.sdf.xacro'
    r.write(robot_out,encoding='unicode',xml_declaration=True)
    w.write(world_out,encoding='unicode',xml_declaration=True)
    manifest={
      'world':str(world_out.resolve()),
      'robot_sdf':str(robot_out.resolve()),
      'upstream_world_sha256':_sha(world),
      'upstream_robot_sha256':_sha(robot),
      'actor_dae_sha256':_sha(actor_mesh),
      'result_world_sha256':_sha(world_out),
      'result_robot_sha256':_sha(robot_out),
      'gazebo_visual_actor':None,
      'separate_actor_removed':True,
      'human_visual_attached_to_physical_model':True,
      'human_visual_name':HUMAN_VISUAL_NAME,
      'human_visual_count':1,
      'gpu_lidar_leg_surface':True,
      'rendered_visual_count':2,
      'procedural_fallback_visuals':False,
      'human_visible_collision_proxy':'obstacle_collision',
      'human_visual_animated':False,
      'human_model_motion_source':'existing_P2_G07_gz_set_pose',
      'robot_world_spawn':{'x':-2.0,'y':-0.5,'yaw':0.0},
      'rgbd_horizontal_fov_rad':1.35,
      'rgbd_sensor_pitch_rad':-0.12,
      'physical_obstacle_static_gap_not_certified':True,
      'gazebo_physical_fixture':PHYSICAL_NAME,
      'rgb_topic':RGB_TOPIC,
      'depth_topic':DEPTH_TOPIC,
      'optical_frame':OPTICAL_FRAME,
      'actor_physics_collision':False,
      'visual_person_same_as_physical_obstacle':True,
      'robot_drive_model_modified':False,
      'goal_sent':False,'certified_estop':False,
      'collision_ground_truth_verified':False,
      'ros_actual':False,'gazebo_actual':False,
    }
    (output/'manifest.json').write_text(
        json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--world',type=Path,required=True)
    p.add_argument('--robot',type=Path,required=True)
    p.add_argument('--actor',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--model',type=Path,required=True)
    args=p.parse_args()
    manifest=build_overlay(args.world,args.robot,args.actor,args.out)
    (args.out/'d08_yolo.yaml').write_text(
        make_yolo_params(args.model),encoding='utf-8')
    print('D08_ONE_WORLD_OVERLAY_STATIC_PASS '+json.dumps({
        'world':manifest['world'],'robot_sdf':manifest['robot_sdf'],
        'human_visual_on_existing_physical_model':True,
        'separate_actor_removed':True,
        'ros_gazebo_not_yet_run':True
    }),flush=True)


if __name__=='__main__':
    main()
