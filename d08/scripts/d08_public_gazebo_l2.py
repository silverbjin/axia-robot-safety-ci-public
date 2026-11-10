#!/usr/bin/env python3
"""D08 PUBLIC L2: real official Jazzy Waffle + Gazebo RGBD, NO Nav2 Goal.

World fixture is TEST ONLY. It does not replace private P2 L3 acceptance,
YOLO person detection or the user's live consented motion demonstration.
"""
from __future__ import annotations
from collections import deque
import argparse
import hashlib
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'d08/harness'))
from d04_waffle_pi_rgb_preflight import _start,_stop_all,sync_ros_discovery_environment
from d08_live_world import build_overlay,RGB_TOPIC,DEPTH_TOPIC
from d08_live_readonly_probe import select_pair
from p2_contact_discovery import resolve_g07_contact_topic
from d08_contact_positive_contract import count_nonrobot_positive_contacts

TEST_FIXTURE='''<plugin filename="gz-sim-contact-system"
 name="gz::sim::systems::Contact"/>
<model name="axia_p2_g07_obstacle">
 <static>true</static><pose>-1.2 -0.5 0.24 0 0 0</pose>
 <link name="obstacle_link">
  <collision name="obstacle_collision"><geometry>
   <cylinder><radius>0.07</radius><length>0.48</length></cylinder>
  </geometry></collision>
  <visual name="obstacle_visual"><geometry>
   <cylinder><radius>0.07</radius><length>0.48</length></cylinder>
  </geometry></visual>
  <sensor name="axia_contact" type="contact">
    <always_on>true</always_on><update_rate>30</update_rate>
    <topic>/axia_p2_g07/contacts</topic>
    <contact><collision>obstacle_collision</collision></contact>
  </sensor>
 </link></model>'''


def _run(cmd,env=None,timeout=15,check=True):
    cp=subprocess.run(cmd,env=env,text=True,capture_output=True,
                      timeout=timeout,check=False)
    if check and cp.returncode!=0:
        raise RuntimeError('D08_CMD_FAILED:'+cmd[0]+':'+cp.stderr[-300:])
    return cp


def observe_real_pair(timeout_s=65):
    import rclpy
    from sensor_msgs.msg import Image
    from rclpy.qos import qos_profile_sensor_data
    rclpy.init()
    node=rclpy.create_node('axia_d08_real_gazebo_rgbd_ci_probe')
    rgb=deque(maxlen=40);depth=deque(maxlen=40)
    counts={'rgb':0,'depth':0}
    def handle(msg,kind):
        counts[kind]+=1
        packet={'frame':msg.header.frame_id,
                'stamp_ns':int(msg.header.stamp.sec)*10**9+msg.header.stamp.nanosec,
                'width':msg.width,'height':msg.height,'encoding':msg.encoding,
                'byte_count':len(msg.data)}
        (rgb if kind=='rgb' else depth).append(packet)
    node.create_subscription(Image,RGB_TOPIC,
        lambda m:handle(m,'rgb'),qos_profile_sensor_data)
    node.create_subscription(Image,DEPTH_TOPIC,
        lambda m:handle(m,'depth'),qos_profile_sensor_data)
    try:
        until=time.monotonic()+timeout_s
        while time.monotonic()<until:
            rclpy.spin_once(node,timeout_sec=.4)
            pair=select_pair(rgb,depth)
            if pair is not None and counts['rgb']>=3 and counts['depth']>=3:
                return {'matched':True,'pair':pair,'counts':counts,
                        'real_ros_images':True}
        return {'matched':False,'counts':counts,'real_ros_images':False}
    finally:
        node.destroy_node()
        rclpy.shutdown()


def observe_real_front_scan(timeout_s=30.0):
    """Receive real /scan from official Waffle with sensor-data QoS."""
    import math
    import rclpy
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import LaserScan
    rclpy.init()
    node=rclpy.create_node('axia_d08_no_goal_lidar_ci_probe')
    fronts=[]
    last_stamp=None
    def scan_cb(m):
        nonlocal last_stamp
        stamp=int(m.header.stamp.sec)*10**9+int(m.header.stamp.nanosec)
        if stamp<=0 or stamp==last_stamp:
            return
        last_stamp=stamp
        good=[float(v) for i,v in enumerate(m.ranges)
              if abs(float(m.angle_min)+i*float(m.angle_increment))<=0.18
              and math.isfinite(v) and m.range_min<=v<=m.range_max]
        if good:fronts.append(min(good))
    node.create_subscription(LaserScan,'/scan',scan_cb,qos_profile_sensor_data)
    try:
        end=time.monotonic()+timeout_s
        while time.monotonic()<end:
            rclpy.spin_once(node,timeout_sec=.35)
            if len(fronts)>=6:
                return {'front_m':round(sorted(fronts[-5:])[2],6),
                        'scan_count':len(fronts),
                        'front_samples_m':[round(v,6) for v in fronts[-5:]],
                        'source':'actual_ros_sensor_msgs_LaserScan',
                        'no_synthetic_scan':True}
        raise RuntimeError('D08_REAL_GAZEBO_LIDAR_SCAN_MISSING')
    finally:
        node.destroy_node()
        rclpy.shutdown()


def pregoal_lidar_physical_admission(out:Path,env:dict,processes:list)->dict:
    """Prove Gazebo UserCommands moved actual existing obstacle into SlowZone.

    This is an isolated no-Goal copy of P2 pregoal physical predicate;
    never publish commands, fake ranges, or relax .4/.75m thresholds.
    """
    # /scan must be generated by the *official Waffle* GPU LiDAR.
    _start('scan_bridge',
        ['ros2','run','ros_gz_bridge','parameter_bridge',
         '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan'],
        env,out,processes)
    before=observe_real_front_scan(timeout_s=35)
    target=(-1.28,-.5,.24)
    req=('name: "axia_p2_g07_obstacle", '
         'position: {x: %.6f, y: %.6f, z: %.6f}, orientation: {w: 1}'%target)
    res=_run(['gz','service','-s','/world/default/set_pose',
              '--reqtype','gz.msgs.Pose','--reptype','gz.msgs.Boolean',
              '--timeout','5000','--req',req],env,timeout=13)
    (out/'pregoal_lidar_set_pose_ack.txt').write_text(res.stdout+res.stderr)
    if 'data: true' not in res.stdout:
        raise RuntimeError('D08_PREG0AL_GZ_SET_POSE_NOT_ACKNOWLEDGED')
    after=observe_real_front_scan(timeout_s=35)
    observed_delta=round(before['front_m']-after['front_m'],6)
    verdict={'status':'BLOCKED','before':before,'after':after,
             'expected_pose_world_m':list(target),
             'native_set_pose_ack':True,
             'measured_distance_change_m':observed_delta,
             'no_goal_sent':True,'control_published':False,
             'safety_threshold_modified':False,
             'certified_estop':False,'collision_ground_truth':False}
    (out/'pregoal_lidar_observation.json').write_text(
        json.dumps(verdict,indent=2,ensure_ascii=False)+'\n')
    # A successful service response ALONE never proves sensor observation.
    # The closer fixture should move the actual measured front by ~8cm.
    if not (.4<after['front_m']<.75 and observed_delta>.035):
        raise RuntimeError('D08_PREG0AL_PHYSICAL_LIDAR_SLOWZONE_NOT_OBSERVED:'+
            json.dumps({'before':before['front_m'],'after':after['front_m'],
                        'delta':observed_delta}))
    verdict['status']='PASS_ACTUAL_GAZEBO_SET_POSE_PLUS_LIDAR'
    (out/'pregoal_lidar_observation.json').write_text(
        json.dumps(verdict,indent=2,ensure_ascii=False)+'\n')
    print('D08_REAL_GAZEBO_PREGOAL_LIDAR_SLOWZONE_PASS '+json.dumps(
        {'before':before['front_m'],'after':after['front_m'],
         'delta':observed_delta}),flush=True)
    return verdict


def positive_contact_once(out:Path,env:dict,contact_topic:str)->dict:
    """One isolated NON-ROBOT calibration contact. Never send a Nav2 Goal.

    The physical sphere falls onto the existing human's G07 cylinder.
    Positive sensor response proves this topic can carry contact, not that
    a later moving-robot experiment has zero collisions.
    """
    out=Path(out)
    probe_name='axia_d08_contact_calibrator'
    sphere=out/'positive_contact_calibrator.sdf'
    sphere.write_text('''<?xml version="1.0"?>
<sdf version="1.9"><model name="axia_d08_contact_calibrator">
  <static>false</static><link name="calibrator_link">
  <inertial><mass>0.2</mass><inertia>
    <ixx>0.001</ixx><iyy>0.001</iyy><izz>0.001</izz>
    <ixy>0</ixy><ixz>0</ixz><iyz>0</iyz>
  </inertia></inertial>
  <collision name="calibrator_collision"><geometry>
    <sphere><radius>0.11</radius></sphere>
  </geometry></collision>
  <visual name="calibrator_visual"><geometry><sphere><radius>0.11</radius></sphere></geometry>
    <material><diffuse>0.5 0.5 0.5 1</diffuse></material>
  </visual>
  </link>
</model></sdf>''',encoding='utf-8')
    log=out/'positive_contact_native.log'
    watcher=None
    try:
        with log.open('w',encoding='utf-8') as file:
            watcher=subprocess.Popen(['gz','topic','-e','-t',contact_topic],
                env=env,stdout=file,stderr=subprocess.STDOUT,
                start_new_session=True)
            time.sleep(1.2)
            # Exactly ONE probe entity create. It drops under gravity onto
            # the existing Contact-monitored cylinder, while Waffle is still.
            cmd=['gz','service','-s','/world/default/create',
                '--reqtype','gz.msgs.EntityFactory','--reptype','gz.msgs.Boolean',
                '--timeout','7000','--req',
                'sdf_filename: "'+str(sphere)+'", name: "'+probe_name+
                '", pose: { position: { x: -1.2, y: -0.5, z: 0.6 }, '
                'orientation: { w: 1.0 } }']
            ack=_run(cmd,env,timeout=17)
            (out/'contact_calibration_spawn_ack.txt').write_text(ack.stdout+ack.stderr)
            if 'data: true' not in ack.stdout:
                raise RuntimeError('CONTACT_CALIBRATOR_CREATE_NOT_ACKNOWLEDGED')
            time.sleep(9.0)
    finally:
        if watcher is not None and watcher.poll() is None:
            try:os.killpg(watcher.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:watcher.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:os.killpg(watcher.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                watcher.wait(timeout=3)
    raw=log.read_text(encoding='utf-8',errors='replace')[:200000]
    # Gazebo gz.msgs.Contacts text uses 'collision1 { name: ... }', NOT
    # 'collision1: ...'. The actual Owner-profile CI fixture recorded
    # 2,978 adjacent collision pairs in its full native log, despite the
    # legacy literal-colon parser incorrectly reporting BLOCKED.
    sampled=count_nonrobot_positive_contacts(raw)
    positive=sampled>0
    verdict={'status':('POSITIVE_CONTACT_VERIFIED' if positive
                       else 'CONTACT_POSITIVE_NOT_OBSERVED'),
             'contact_topic':contact_topic,
             'calibrator_name':probe_name,
             'positive_contact_detected':positive,
             'sampled_actual_collision_pairs':sampled,
             'calibration_events_are_robot_contacts':False,
             'robot_goal_sent':False,
             'certified_estop':False,
             'robot_collision_free_verified':False,
             'raw_contact_log':str(log)}
    (out/'positive_contact_verdict.json').write_text(
        json.dumps(verdict,indent=2,ensure_ascii=False)+'\n')
    print('D08_G07_NONROBOT_CONTACT_CALIBRATION_'+
          ('PASS' if positive else 'BLOCKED'),flush=True)
    if not positive:raise RuntimeError('POSITIVE_CONTACT_NONROBOT_SENSOR_UNVERIFIED')
    return verdict


def run(out:Path,actor:Path,positive_contact:bool=False,lidar_pre_goal:bool=False):
    out=Path(out).resolve()
    if out.exists():raise ValueError('D08_EVIDENCE_EXISTS')
    out.mkdir(parents=True)
    result={'gate':'D08_ONE_WORLD_GAZEBO_RGBD_NO_GOAL',
      'status':'BLOCKED','goal_sent':False,'cmd_vel_published':False,
      'yolo_executed':False,'d05_executed':False,'p2_goal_executed':False,
      'collision_ground_truth':False,'certified_estop':False}
    processes=[]
    env=os.environ.copy()
    env['ROS_DOMAIN_ID']='69'
    env['ROS_AUTOMATIC_DISCOVERY_RANGE']='LOCALHOST'
    env['GZ_PARTITION']='axia_d08_ci_'+str(os.getpid())
    env['LIBGL_ALWAYS_SOFTWARE']='1'
    env['GALLIUM_DRIVER']='llvmpipe'
    env.pop('EGL_PLATFORM',None)
    sync_ros_discovery_environment(env)
    try:
        from ament_index_python.packages import get_package_share_directory
        nav2=Path(get_package_share_directory('nav2_minimal_tb3_sim'))
        tb3=Path(get_package_share_directory('turtlebot3_gazebo'))
        robot=nav2/'urdf/gz_waffle.sdf.xacro'
        world=nav2/'worlds/tb3_sandbox.sdf.xacro'
        if not (robot.is_file() and world.is_file() and actor.is_file()):
            raise FileNotFoundError('D08_OFFICIAL_ROBOT_WORLD_OR_ACTOR_MISSING')
        source=world.read_text()
        if source.count('</world>')!=1 or 'gz::sim::systems::UserCommands' not in source:
            raise ValueError('D08_UNEXPECTED_NAV2_UPSTREAM_WORLD')
        testworld=out/'original_plus_physical_fixture.sdf.xacro'
        testworld.write_text(source.replace('</world>',TEST_FIXTURE+'</world>'))
        m=build_overlay(testworld,robot,actor,out/'overlay')
        result['overlay_manifest']=m
        # Must resolve model://turtlebot3_world DURING `gz sdf -p`, not
        # only later when the simulator is started.
        env['GZ_SIM_RESOURCE_PATH']=str(tb3/'models')+':'+env.get('GZ_SIM_RESOURCE_PATH','')
        gz_world=out/'actual_world.sdf'
        gz_robot=out/'actual_waffle.sdf'
        for src,dest in ((m['world'],gz_world),(m['robot_sdf'],gz_robot)):
            with dest.open('w') as fp:
                cp=subprocess.run(['xacro',str(src)],stdout=fp,stderr=subprocess.PIPE,
                     env=env,text=True,timeout=15)
            if cp.returncode!=0:
                raise RuntimeError('D08_XACRO_FAILED:'+cp.stderr[-400:])
            # The standalone 'gz sdf -p' tool lacks gz-sim's model://
            # resource find callback, so it reports a false missing-model
            # error for the stock turtlebot3_world include. Parse XML here,
            # then require the actual Gazebo server to resolve models.
            parsed=ET.parse(dest)
            if parsed.getroot().tag!='sdf':
                raise RuntimeError('D08_XACRO_OUTPUT_IS_NOT_SDF')
        sim=_start('gazebo_server',
          ['xvfb-run','-a','-s','-screen 0 1280x720x24',
           'gz','sim','-r','-s','-v3',str(gz_world)],
          env,out,processes)
        # Native UserCommands create ACK must be true, not just the service URI.
        service='/world/default/create'
        until=time.monotonic()+35
        while time.monotonic()<until:
            if sim.poll() is not None:raise RuntimeError('GAZEBO_PROCESS_EXITED')
            probe=_run(['gz','service','-is',service],env,timeout=8,check=False)
            if 'gz.msgs.EntityFactory' in (probe.stdout+probe.stderr):
                break
            time.sleep(1)
        else:raise RuntimeError('GAZEBO_USER_COMMANDS_NOT_READY')
        request=('sdf_filename: "'+str(gz_robot)+
          '", name: "axia_d08_ci_waffle", pose: { position: { x: -2.0, y: -0.5, z: 0.02 }, orientation: { w: 1.0 } }')
        create=_run(['gz','service','-s',service,'--reqtype','gz.msgs.EntityFactory',
                  '--reptype','gz.msgs.Boolean','--timeout','6000','--req',request],
                  env,timeout=15)
        (out/'native_create_ack.txt').write_text(create.stdout+create.stderr)
        if 'data: true' not in create.stdout:
            raise RuntimeError('D08_WAFFLE_SPAWN_NOT_ACKNOWLEDGED')
        # Mirror the Owner's one-process image bridge on real Gazebo L2.
        _start('rgbd_bridge',['ros2','run','ros_gz_image','image_bridge',
              RGB_TOPIC,DEPTH_TOPIC],env,out,processes)
        result['actual_rgbd']=observe_real_pair(timeout_s=80)
        topics=_run(['gz','topic','-l'],env,timeout=15)
        contact_topic=resolve_g07_contact_topic(topics.stdout)
        if contact_topic is None:
            # Gazebo creates sensor topic asynchronously after model load.
            for _ in range(15):
                time.sleep(.4)
                topics=_run(['gz','topic','-l'],env,timeout=15)
                contact_topic=resolve_g07_contact_topic(topics.stdout)
                if contact_topic is not None:break
        (out/'gazebo_topics.txt').write_text(topics.stdout)
        result['resolved_native_contact_topic']=contact_topic
        result['contact_topic_proven']=contact_topic is not None
        # Existence != zero collisions or continuous ground truth.
        result['collision_ground_truth']=False
        if contact_topic is None:
            raise RuntimeError('G07_NATIVE_CONTACT_SENSOR_TOPIC_NOT_PUBLISHED')
        if not result['actual_rgbd']['matched']:
            raise RuntimeError('D08_NO_MATCHED_REAL_REGISTERED_RGBD')
        if not all(t in topics.stdout for t in (RGB_TOPIC,DEPTH_TOPIC)):
            raise RuntimeError('D08_GAZEBO_RGBD_TOPICS_NOT_ADVERTISED')
        # The calibration happens ONCE, only on the actual no-Goal L2 CI
        # path after real RGBD and the native Contact topic were verified.
        if lidar_pre_goal:
            result['pregoal_lidar']=pregoal_lidar_physical_admission(
                out,env,processes)
        if positive_contact:
            result['positive_contact_calibration']=positive_contact_once(
                out,env,contact_topic)
        result['status']='D08_REAL_GAZEBO_WAFFLE_RGBD_NO_GOAL_PASS'
        result['ros_actual']=True
        result['gazebo_actual']=True
        print('D08_REAL_GAZEBO_WAFFLE_RGBD_NO_GOAL_PASS',flush=True)
    except Exception as exc:
        result['blocker']=type(exc).__name__+':'+str(exc)[:500]
        print('D08_REAL_GAZEBO_L2_BLOCKED '+result['blocker'],flush=True)
    finally:
        _stop_all(processes,result)
        if result['status']!='D08_REAL_GAZEBO_WAFFLE_RGBD_NO_GOAL_PASS':
            result['gazebo_actual']=False
        (out/'verdict.json').write_text(json.dumps(
            result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
        hashes=[]
        for p in sorted(out.iterdir()):
            if p.is_file() and p.name!='SHA256SUMS':
                hashes.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name)
        (out/'SHA256SUMS').write_text('\n'.join(hashes)+'\n')
    return 0 if result['status']=='D08_REAL_GAZEBO_WAFFLE_RGBD_NO_GOAL_PASS' else 2


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--actor',type=Path,required=True)
    p.add_argument('--lidar-pre-goal',action='store_true',
        help='Real /scan before and after G07 set_pose, no Nav2 Goal')
    p.add_argument('--positive-contact-once',action='store_true',
        help='Single non-robot Gazebo Contact positive calibration, no Nav2 Goal')
    a=p.parse_args()
    raise SystemExit(run(a.out,a.actor,positive_contact=a.positive_contact_once,
                             lidar_pre_goal=a.lidar_pre_goal))
