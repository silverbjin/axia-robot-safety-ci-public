#!/usr/bin/env python3
"""D08: check actual Gazebo RGBD+YOLO+D05 ROS messages; no actuator output."""
from __future__ import annotations
import argparse
from collections import deque
import json
import math
from pathlib import Path
import time


def stamp(msg):
    return int(msg.header.stamp.sec)*1_000_000_000+int(msg.header.stamp.nanosec)


def select_pair(rgb,depth):
    # Same registered Gazebo sensor, not merely two similarly named topics.
    for a in reversed(list(rgb)):
        for b in reversed(list(depth)):
            if (a['frame']==b['frame'] and a['frame']
                and a['stamp_ns']>0 and b['stamp_ns']>0
                and abs(a['stamp_ns']-b['stamp_ns'])<=50_000_000
                and a['width']==b['width']==640
                and a['height']==b['height']==480
                and b['encoding']=='32FC1'):
                return {'rgb':a,'depth':b,'stamp_skew_ms':
                        round(abs(a['stamp_ns']-b['stamp_ns'])/1e6,3)}
    return None


def run(out:Path,timeout_s:float=60.0):
    import rclpy
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import Image
    from yolo_msgs.msg import DetectionArray
    from std_msgs.msg import String
    from rclpy.parameter import Parameter
    out=Path(out)
    if out.exists() or out.is_symlink():
        raise ValueError('D08_EVIDENCE_MUST_NOT_EXIST')
    out.parent.mkdir(parents=True,exist_ok=True)
    data={'gate':'D08_REAL_GAZEBO_RGBD_YOLO_D05',
          'status':'BLOCKED','verified_level':'ROS_GAZEBO_SENSOR_ONLY',
          'rgb_count':0,'depth_count':0,'detections_count':0,
          'yolo_person_count':0,'d05_valid_count':0,
          'robot_moved':False,'control_published':False,
          'goal_sent':False,'collision_free_verified':False,
          'safety_certified':False,'certified_estop':False}
    rgb=deque(maxlen=25);depth=deque(maxlen=25)
    rclpy.init()
    node=rclpy.create_node('axia_d08_live_rgbd_probe',
        parameter_overrides=[Parameter('use_sim_time',value=True)])
    try:
        def image_cb(m,kind):
            data[kind+'_count']+=1
            item={'stamp_ns':stamp(m),'frame':m.header.frame_id,
                  'width':m.width,'height':m.height,'encoding':m.encoding}
            if kind=='rgb':rgb.append(item)
            else:depth.append(item)
        def detect_cb(m):
            data['detections_count']+=1
            for d in m.detections:
                if str(d.class_name).lower()=='person' and int(d.class_id)==0:
                    score=float(d.score)
                    if math.isfinite(score) and score>=0.15:
                        data['yolo_person_count']+=1
                        data['last_person_confidence']=round(score,5)
                        break
        def status_cb(m):
            try:
                v=json.loads(m.data)
                d=v.get('distance_m')
                if (v.get('status')=='VALID'
                        and v.get('safety_certified') is False
                        and type(d) in (int,float) and math.isfinite(d)
                        and 0.15<d<8.0):
                    data['d05_valid_count']+=1
                    data['last_distance_m']=float(d)
            except (ValueError,TypeError):
                pass
        subs=[
            node.create_subscription(Image,'/axia/d08/rgbd/image',
                lambda m:image_cb(m,'rgb'),qos_profile_sensor_data),
            node.create_subscription(Image,'/axia/d08/rgbd/depth_image',
                lambda m:image_cb(m,'depth'),qos_profile_sensor_data),
            node.create_subscription(DetectionArray,'/yolo/cam0/detections',
                detect_cb,qos_profile_sensor_data),
            node.create_subscription(String,'/axia/d05/person_range_status',
                status_cb,10)]
        end=time.monotonic()+timeout_s
        while time.monotonic()<end:
            rclpy.spin_once(node,timeout_sec=.25)
            pair=select_pair(rgb,depth)
            if pair is not None and data['yolo_person_count']>0 and data['d05_valid_count']>0:
                data['matched_rgbd_pair']=pair
                data['status']='PASS_REAL_GAZEBO_REGISTERED_RGBD_YOLO_D05'
                data['ros_actual']=True
                data['gazebo_actual']=True
                break
        if data['status']=='BLOCKED':
            data['reason']='NO_MATCHED_RGBD_YOLO_PERSON_AND_D05_VALID'
            data['ros_actual']=data['rgb_count']>0 or data['depth_count']>0
            data['gazebo_actual']=False
        out.write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
        print('D08_GAZEBO_SENSOR_PROBE_'+('PASS' if data['status'].startswith('PASS') else 'BLOCKED')
              +' '+json.dumps({k:data.get(k) for k in (
                 'rgb_count','depth_count','yolo_person_count','d05_valid_count',
                 'last_distance_m','reason')},allow_nan=False),flush=True)
        return 0 if data['status'].startswith('PASS') else 2
    finally:
        node.destroy_node()
        rclpy.shutdown()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--timeout-s',type=float,default=60.0)
    a=p.parse_args()
    raise SystemExit(run(a.out,a.timeout_s))


if __name__=='__main__':
    main()
