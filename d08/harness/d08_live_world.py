#!/usr/bin/env python3
"""D08 one-world Gazebo educational view (camera + non-colliding visual actor).

Reuses P2's real physical G07 cylinder and original official Nav2 Waffle model.
The visual-only person is NOT the physical cylinder. Nothing publishes controls.
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

    actor=ET.SubElement(wn,'actor',{'name':ACTOR_NAME})
    skin=_sub(actor,'skin')
    _sub(skin,'filename',str(actor_mesh.resolve()))
    _sub(skin,'scale','0.75')
    anim=_sub(actor,'animation',None,name='walk')
    _sub(anim,'filename',str(actor_mesh.resolve()))
    _sub(anim,'interpolate_x','true')
    script=_sub(actor,'script')
    _sub(script,'loop','true')
    _sub(script,'delay_start','0')
    _sub(script,'auto_start','true')
    trajectory=_sub(script,'trajectory',None,id='0',type='walk')
    # Visual only. This animated person is independently located from the
    # LiDAR physical cylinder, which P2 moves using native Gazebo UserCommands.
    for t,y in [('0','-0.32'),('6','-0.68'),('12','-0.32')]:
        waypoint=_sub(trajectory,'waypoint')
        _sub(waypoint,'time',t)
        _sub(waypoint,'pose',f'-0.38 {y} 1.0 0 0 3.14159')

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
      'gazebo_visual_actor':ACTOR_NAME,
      'actor_pose_initial_world':{'x':-0.38,'y':-0.32,'z':1.0},
      'actor_visual_scale':0.75,
      'robot_world_spawn':{'x':-2.0,'y':-0.5,'yaw':0.0},
      'rgbd_horizontal_fov_rad':1.35,
      'rgbd_sensor_pitch_rad':-0.12,
      'actor_min_forward_from_robot_m':1.62,
      'physical_obstacle_static_gap_not_certified':True,
      'gazebo_physical_fixture':PHYSICAL_NAME,
      'rgb_topic':RGB_TOPIC,
      'depth_topic':DEPTH_TOPIC,
      'optical_frame':OPTICAL_FRAME,
      'actor_physics_collision':False,
      'visual_person_same_as_physical_obstacle':False,
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
        'actor_visual_only':True,'physical_cylinder_distinct':True,
        'ros_gazebo_not_yet_run':True
    }),flush=True)


if __name__=='__main__':
    main()
