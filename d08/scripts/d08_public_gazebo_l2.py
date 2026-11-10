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
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'d08/harness'))
from d04_waffle_pi_rgb_preflight import _start,_stop_all,sync_ros_discovery_environment
from d08_live_world import build_overlay,RGB_TOPIC,DEPTH_TOPIC
from d08_live_readonly_probe import select_pair

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


def run(out:Path,actor:Path):
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
            parsed=_run(['gz','sdf','-p',str(dest)],env,timeout=25)
            if '<sdf' not in parsed.stdout:
                raise RuntimeError('D08_GZ_SDF_VALIDATION_FAILED')
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
        _start('rgb_bridge',['ros2','run','ros_gz_image','image_bridge',RGB_TOPIC],
               env,out,processes)
        _start('depth_bridge',['ros2','run','ros_gz_image','image_bridge',DEPTH_TOPIC],
               env,out,processes)
        result['actual_rgbd']=observe_real_pair(timeout_s=80)
        topics=_run(['gz','topic','-l'],env,timeout=15)
        (out/'gazebo_topics.txt').write_text(topics.stdout)
        if not result['actual_rgbd']['matched']:
            raise RuntimeError('D08_NO_MATCHED_REAL_REGISTERED_RGBD')
        if not all(t in topics.stdout for t in (RGB_TOPIC,DEPTH_TOPIC)):
            raise RuntimeError('D08_GAZEBO_RGBD_TOPICS_NOT_ADVERTISED')
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
    a=p.parse_args()
    raise SystemExit(run(a.out,a.actor))
