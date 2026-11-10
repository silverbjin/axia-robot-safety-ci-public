#!/usr/bin/env python3
"""D08 read-only ROS RGBD/YOLO -> PRIVATE instructor D05 range reference.

No /cmd_vel, no ROS publisher, no synthetic ranges. Uses one registered RGBD
camera and real YOLO DetectionArray. Outputs verifiable JSON evidence only.
"""
from __future__ import annotations
import argparse
from collections import Counter,deque
import json
import math
from pathlib import Path
import struct
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
D05_TEACHER=ROOT/'training/block_B/instructor'
RGB_TOPIC='/axia/d08/rgbd/image'
DEPTH_TOPIC='/axia/d08/rgbd/depth_image'
DETECTIONS_TOPIC='/yolo/cam0/detections'

def stamp(msg):
    return int(msg.header.stamp.sec)*1_000_000_000+int(msg.header.stamp.nanosec)

def select_pair(rgb,depth):
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

def diagnose_rgbd_alignment(rgb,depth):
    """Bounded read-only evidence explaining why registered image pairing failed.

    Do not relax same-frame, exact-image geometry, 32FC1 or <=50ms conditions.
    No image pixels are collected here; only ROS Image header metadata.
    """
    r=list(rgb)[-5:]
    d=list(depth)[-5:]
    good_frame=[(a,b) for a in r for b in d
        if a.get('frame') and a.get('frame')==b.get('frame')
        and a.get('stamp_ns',0)>0 and b.get('stamp_ns',0)>0]
    diffs=[abs(a['stamp_ns']-b['stamp_ns'])/1e6
        for a,b in good_frame]
    correct=[(a,b) for a,b in good_frame
        if a.get('width')==b.get('width')==640
        and a.get('height')==b.get('height')==480
        and b.get('encoding')=='32FC1']
    return {
        'rgb_last':r,'depth_last':d,
        'same_frame_candidate_pairs':len(good_frame),
        'correct_geometry_encoding_pairs':len(correct),
        'minimum_same_frame_skew_ms':round(min(diffs),3) if diffs else None,
        'required_max_skew_ms':50.0,
        'pair_requirement_relaxed':False,
    }


def bbox_from_real_detection(d,w:int,h:int):
    cx=float(d.bbox.center.position.x)
    cy=float(d.bbox.center.position.y)
    sx=float(d.bbox.size.x)
    sy=float(d.bbox.size.y)
    score=float(d.score)
    if (str(d.class_name).lower()!='person' or int(d.class_id)!=0
        or not all(math.isfinite(x) for x in (cx,cy,sx,sy,score))
        or not (.15<=score<=1.0) or sx<4 or sy<4):
        return None
    x1=max(0,int(math.floor(cx-sx/2)))
    x2=min(w,int(math.ceil(cx+sx/2)))
    y1=max(0,int(math.floor(cy-sy/2)))
    y2=min(h,int(math.ceil(cy+sy/2)))
    if x2-x1<4 or y2-y1<4:return None
    return {'x1':x1,'y1':y1,'x2':x2,'y2':y2,
        'image_width':w,'image_height':h,'confidence':score}

def decode_real_depth_roi(image,bbox:dict) -> list[list[float]]:
    """Read 16 CENTER-ROI float pixels from actual ROS 32FC1 Image, no fake."""
    width=int(image.width);height=int(image.height)
    step=int(image.step)
    if (image.encoding!='32FC1' or width<=0 or height<=0
        or step<width*4 or len(image.data)<step*height
        or not all(isinstance(bbox.get(k),int) for k in
            ('x1','x2','y1','y2','image_width','image_height'))
        or bbox['image_width']!=width or bbox['image_height']!=height
        or not 0<=bbox['x1']<bbox['x2']<=width
        or not 0<=bbox['y1']<bbox['y2']<=height):
        raise ValueError('D08_INVALID_DEPTH_IMAGE_OR_BBOX')
    fmt=('>' if image.is_bigendian else '<')+'f'
    x1,y1,x2,y2=(bbox[k] for k in ('x1','y1','x2','y2'))
    out=[]
    for ry in range(4):
        row=[]
        for rx in range(4):
            # Inner 60% of the YOLO box: reject background/edge leakage.
            fx=.20+.60*(rx+.5)/4
            fy=.20+.60*(ry+.5)/4
            x=min(x2-1,max(x1,int(x1+(x2-x1)*fx)))
            y=min(y2-1,max(y1,int(y1+(y2-y1)*fy)))
            val=struct.unpack_from(fmt,image.data,y*step+x*4)[0]
            row.append(float(val))
        out.append(row)
    return out

def measure_real_person(depth_msg,bbox:dict,det_stamp_ns:int):
    """Delegate actual D05 validity/median rule to existing PRIVATE answer."""
    if det_stamp_ns<=0 or stamp(depth_msg)<=0:
        return None
    sys.path.insert(0,str(D05_TEACHER))
    from block_b_reference import measure_person_range
    roi=decode_real_depth_roi(depth_msg,bbox)
    valid=sum(math.isfinite(v) and .15<=v<=8.0 for row in roi for v in row)
    if valid<8:return None
    proxy_bbox={'x1':0,'y1':0,'x2':4,'y2':4,
                'image_width':4,'image_height':4}
    distance=measure_person_range(
        roi,proxy_bbox,det_stamp_ns/1e9,stamp(depth_msg)/1e9,max_skew_s=.05)
    if distance is None:return None
    return {'distance_m':float(distance),'valid_count':valid,
            'valid_fraction':round(valid/16,4),
            'frame_stamp_ns':det_stamp_ns,
            'depth_stamp_ns':stamp(depth_msg),
            'bbox_roi_xyxy':[bbox[k] for k in ('x1','y1','x2','y2')],
            'sampling':'4x4_real_float32_center_roi',
            'reference':'private_training_block_b_D05'}

def run(out:Path,timeout_s:float=75):
    import rclpy
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import Image
    from yolo_msgs.msg import DetectionArray
    from rclpy.parameter import Parameter
    if not D05_TEACHER.joinpath('block_b_reference.py').is_file():
        raise RuntimeError('D05_PRIVATE_REFERENCE_SOURCE_MISSING')
    out=Path(out)
    if out.exists() or out.is_symlink():
        raise ValueError('D08_EVIDENCE_MUST_NOT_EXIST')
    out.parent.mkdir(parents=True,exist_ok=True)
    data={'gate':'D08_REAL_GAZEBO_RGBD_YOLO_PRIVATE_D05',
          'status':'BLOCKED','verified_level':'ROS_GAZEBO_SENSOR_ONLY',
          'rgb_count':0,'depth_count':0,'detections_count':0,
          'yolo_person_count':0,'d05_valid_count':0,
          'd05_measurement_source':'actual_depth_pixels_plus_private_D05_reference',
          'robot_moved':False,'control_published':False,'goal_sent':False,
          'collision_free_verified':False,'safety_certified':False,
          'certified_estop':False}
    rgb=deque(maxlen=40);depth=deque(maxlen=40)
    depth_msgs=deque(maxlen=40)
    detections=deque(maxlen=50)
    reasons=Counter()
    detection_classes=Counter()
    rclpy.init()
    node=rclpy.create_node('axia_d08_live_rgbd_probe',
        parameter_overrides=[Parameter('use_sim_time',value=True)])
    try:
        def image_cb(m,kind):
            data[kind+'_count']+=1
            item={'stamp_ns':stamp(m),'frame':m.header.frame_id,
                  'width':m.width,'height':m.height,'encoding':m.encoding}
            if kind=='rgb':rgb.append(item)
            else:
                depth.append(item)
                depth_msgs.append((item,m,time.monotonic()))
        def detect_cb(m):
            data['detections_count']+=1
            for raw_detection in m.detections:
                detection_classes[str(raw_detection.class_name).lower()]+=1
            detected=[]
            for d in m.detections:
                b=bbox_from_real_detection(d,640,480)
                if b is not None:
                    detected.append(b)
            if detected:
                data['yolo_person_count']+=1
                best=max(detected,key=lambda x:x['confidence'])
                data['last_person_confidence']=round(best['confidence'],5)
                detections.append((stamp(m),m.header.frame_id,best,
                                   time.monotonic()))
        subs=[
          node.create_subscription(Image,RGB_TOPIC,
            lambda m:image_cb(m,'rgb'),qos_profile_sensor_data),
          node.create_subscription(Image,DEPTH_TOPIC,
            lambda m:image_cb(m,'depth'),qos_profile_sensor_data),
          node.create_subscription(DetectionArray,DETECTIONS_TOPIC,
            detect_cb,qos_profile_sensor_data)]
        end=time.monotonic()+timeout_s
        last_try=set()
        while time.monotonic()<end:
            rclpy.spin_once(node,timeout_sec=.2)
            if not select_pair(rgb,depth):
                reasons['no_registered_rgb_depth_pair']+=1
                continue
            now=time.monotonic()
            for detected_ns,frame,bbox,seen_at in reversed(detections):
                if now-seen_at>8:continue
                for meta,msg,arrived in reversed(depth_msgs):
                    if now-arrived>8:continue
                    paired=select_pair(rgb,[meta])
                    if paired is None:
                        reasons['no_matching_rgb_for_person_depth']+=1
                        continue
                    if frame and frame!=meta['frame']:
                        reasons['detection_frame_mismatch']+=1
                        continue
                    if abs(meta['stamp_ns']-detected_ns)>50_000_000:
                        reasons['detection_depth_stamp_skew']+=1
                        continue
                    key=(detected_ns,meta['stamp_ns'])
                    if key in last_try:continue
                    last_try.add(key)
                    try:
                        result=measure_real_person(msg,bbox,detected_ns)
                    except (ValueError,TypeError,struct.error):
                        reasons['invalid_actual_depth_or_bbox']+=1
                        continue
                    if result is None:
                        reasons['insufficient_real_person_roi_depth']+=1
                        continue
                    data['d05_valid_count']+=1
                    data.update({'last_distance_m':result['distance_m'],
                        'd05_valid_result':result,
                        'matched_rgbd_pair':paired,
                        'status':'PASS_REAL_GAZEBO_REGISTERED_RGBD_YOLO_PRIVATE_D05',
                        'ros_actual':True,'gazebo_actual':True})
                    print('D08_D05_ACTUAL_DEPTH_VALID distance_m='+
                          str(round(result['distance_m'],3))+
                          ' valid_fraction='+str(result['valid_fraction']),
                          flush=True)
                    break
                if data['d05_valid_count']:break
            if data['d05_valid_count']:break
        if data['status']=='BLOCKED':
            data['reason']='D05_ACTUAL_PERSON_RANGE_NOT_VERIFIED'
            data['ros_actual']=data['rgb_count']>0 or data['depth_count']>0
            data['gazebo_actual']=False
        data['d05_diagnostics']=dict(reasons)
        data['rgbd_alignment_diagnostic']=diagnose_rgbd_alignment(rgb,depth)
        data['observed_yolo_classes']=dict(detection_classes.most_common(12))
        out.write_text(json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
        print('D08_GAZEBO_SENSOR_PROBE_'+
             ('PASS' if data['status'].startswith('PASS') else 'BLOCKED')+
             ' '+json.dumps({k:data.get(k) for k in
               ('rgb_count','depth_count','yolo_person_count','d05_valid_count',
                'last_distance_m','reason','d05_diagnostics',
                'rgbd_alignment_diagnostic','observed_yolo_classes')},allow_nan=False),
              flush=True)
        return 0 if data['status'].startswith('PASS') else 2
    finally:
        node.destroy_node()
        rclpy.shutdown()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--timeout-s',type=float,default=75.0)
    a=p.parse_args()
    raise SystemExit(run(a.out,a.timeout_s))

if __name__=='__main__':
    main()
