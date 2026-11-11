#!/usr/bin/env python3
"""Real OFFICIAL Nav2 Collision Monitor ROS L1 cadence diagnostic.

ISOLATED /axia_ci/* topics, NO Nav2 Goal, NO Gazebo robot command, no
private Guard implementation. Publishes artificial scan + a diagnostic
velocity solely to OFFICIAL CM in a standalone ROS graph. NEVER counts
toward physical G07 acceptance / WSL2 runtime parity.
"""
import argparse
import json
import math
import os
from pathlib import Path
import signal
import statistics
import threading
import subprocess
import tempfile
import time

CFG='''collision_monitor:
  ros__parameters:
    use_sim_time: false
    base_frame_id: "base_scan"
    odom_frame_id: "base_scan"
    cmd_vel_in_topic: "/axia_ci/cm_input"
    cmd_vel_out_topic: "/axia_ci/cm_output"
    transform_tolerance: 0.1
    source_timeout: 2.0
    base_shift_correction: false
    stop_pub_timeout: 1.0
    enable_stamped_cmd_vel: false
    observation_sources: ["ci_scan"]
    ci_scan:
      type: "scan"
      topic: "/axia_ci/scan"
      enabled: true
    polygons: ["ci_stop", "ci_slow"]
    ci_stop:
      type: "polygon"
      points: "[[0.40, 0.32], [0.40, -0.32], [-0.10, -0.32], [-0.10, 0.32]]"
      action_type: "stop"
      min_points: 4
      enabled: true
      visualize: false
    ci_slow:
      type: "polygon"
      points: "[[0.75, 0.40], [0.75, -0.40], [-0.10, -0.40], [-0.10, 0.40]]"
      action_type: "slowdown"
      slowdown_ratio: 0.30
      min_points: 4
      enabled: true
      visualize: false
'''

def _cmd(args,timeout=7):
    return subprocess.run(args,text=True,capture_output=True,timeout=timeout)

def _ready():
    status=_cmd(['ros2','lifecycle','get','/collision_monitor'],timeout=6)
    return status.returncode==0 and 'unconfigured' in status.stdout.lower()

def _pct(values,percent):
    v=sorted(values)
    return round(v[max(0,math.ceil(len(v)*percent)-1)],6)

def run(out, *, set_pose_while_publishing=None, stop_front_m=None):
    import rclpy
    from geometry_msgs.msg import Twist
    from sensor_msgs.msg import LaserScan
    from rclpy.qos import qos_profile_sensor_data

    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    yamlpath=out/'ci_collision_monitor.yaml'
    yamlpath.write_text(CFG)
    log=(out/'cm_ros_log.txt').open('w')
    proc=subprocess.Popen([
        'ros2','run','nav2_collision_monitor','collision_monitor',
        '--ros-args','--params-file',str(yamlpath.resolve())],
        stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    status={'status':'BLOCKED','no_goal':True,'cmd_vel_robot_published':False,
            'synthetic_scan':True,'real_nav2_cm_executable':True,
            'private_guard_executed':False,'wslg_gpu_verified':False,
            'certified_estop':False}
    node=None
    try:
        until=time.monotonic()+15
        while time.monotonic()<until and proc.poll() is None:
            if _ready():break
            time.sleep(.25)
        else:raise RuntimeError('NATIVE_CM_LIFECYCLE_UNCONFIGURED_MISSING')
        for step in ['configure','activate']:
            resp=_cmd(['ros2','lifecycle','set','/collision_monitor',step],timeout=15)
            if resp.returncode!=0 or 'success' not in resp.stdout.lower():
                raise RuntimeError('NATIVE_CM_LIFECYCLE_'+step.upper()+'_FAILED:'+resp.stdout[-150:])
        rclpy.init()
        node=rclpy.create_node('axia_ci_nav2_cm_l1_cadence')
        pub=node.create_publisher(Twist,'/axia_ci/cm_input',10)
        scan_pub=node.create_publisher(LaserScan,'/axia_ci/scan',qos_profile_sensor_data)
        receipts=[];speeds=[]
        def accept(msg):
            receipts.append(time.monotonic())
            speeds.append(msg.linear.x)
        subscription=node.create_subscription(Twist,'/axia_ci/cm_output',accept,10)
        # Owner 1XZYehm8: previous L2 accepted 57/82 CM outputs while
        # evaluating only 47 interior gaps. Verify DDS discovery AND real
        # CM warm-up before the 20Hz steady-state sample window. Startup
        # silence must not be misclassified as steady-state delivery loss.
        ready_deadline=time.monotonic()+8.0
        while time.monotonic()<ready_deadline:
            if (pub.get_subscription_count()>0
                    and scan_pub.get_subscription_count()>0
                    and node.count_publishers('/axia_ci/cm_output')>0):
                break
            rclpy.spin_once(node,timeout_sec=.05)
        else:
            raise RuntimeError('NATIVE_CM_L1_DDS_DISCOVERY_UNREADY')
        def publish_pair(front=.55):
            stamp=node.get_clock().now().to_msg()
            scan=LaserScan();scan.header.stamp=stamp
            scan.header.frame_id='base_scan'
            scan.angle_min=-.52;scan.angle_max=.52
            scan.angle_increment=1.04/60
            scan.range_min=.12;scan.range_max=5.0
            scan.ranges=[front]*61
            scan_pub.publish(scan)
            twist=Twist();twist.linear.x=.08
            pub.publish(twist)
        def publish_period(front=.55):
            start=time.monotonic()
            publish_pair(front)
            while time.monotonic()-start<.05:
                rclpy.spin_once(node,timeout_sec=.008)
            return start
        for _ in range(20):
            publish_period()
        warmup_output_count=len(receipts)
        if warmup_output_count<10:
            raise RuntimeError('NATIVE_CM_L1_WARMUP_OUTPUT_MISSING:'+str(warmup_output_count))
        receipts.clear();speeds.clear()
        service_timing={}
        worker=None
        def call_pose():
            service_timing['start']=time.monotonic()
            try:
                service_timing['ack']=bool(set_pose_while_publishing())
            except Exception as exc:
                service_timing['error']=type(exc).__name__
                service_timing['ack']=False
            finally:
                service_timing['end']=time.monotonic()
        sent=[]
        for i in range(82):
            # Exercise the REAL concurrent native Gazebo UserCommands while
            # OFFICIAL Nav2 CM delivers 20Hz commands. The older CI moved
            # the obstacle before starting CM and missed the Owner TTL gap.
            if i==22 and set_pose_while_publishing is not None:
                worker=threading.Thread(target=call_pose,daemon=True)
                worker.start()
            sent.append(publish_period())
        for _ in range(12):
            rclpy.spin_once(node,timeout_sec=.02)
        if worker is not None:
            worker.join(timeout=15)
            if worker.is_alive() or service_timing.get('ack') is not True:
                raise RuntimeError('NATIVE_GAZEBO_CONCURRENT_SETPOSE_ACK_BLOCKED')
        if len(receipts)<74:
            raise RuntimeError('NATIVE_CM_L1_STEADY_STATE_DELIVERY_INSUFFICIENT:'+
                               str(len(receipts))+'/82')
        # Exclude startup/discovery and shutdown portions; require actual
        # continuous output while messages are being delivered.
        used=receipts[5:-5]
        gaps=[b-a for a,b in zip(used,used[1:])]
        steady_count=len(receipts)
        steady_speeds=list(speeds)
        concurrent_service_gaps=[]
        if worker is not None:
            t0=service_timing['start']
            t1=service_timing['end']
            concurrent_service_gaps=[b-a for a,b in zip(receipts,receipts[1:])
                                     if a<=t1 and b>=t0]
            if not concurrent_service_gaps:
                raise RuntimeError('NATIVE_CM_DURING_SETPOSE_OUTPUT_UNOBSERVED')
        status.update(
            status='REAL_NAV2_CM_L1_CADENCE_PASS',
            output_count=steady_count,
            input_count=len(sent),
            gazebo_set_pose_during_cm=worker is not None,
            gazebo_concurrent_service_ack=service_timing.get('ack') if worker is not None else None,
            gazebo_concurrent_service_duration_sec=round(
                service_timing['end']-service_timing['start'],6) if worker is not None else None,
            cm_max_gap_during_gazebo_service_sec=round(
                max(concurrent_service_gaps),6) if concurrent_service_gaps else None,
            warmup_output_count=warmup_output_count,
            steady_delivery_ratio=round(len(receipts)/len(sent),4),
            scan_qos_discovery_verified=True,
            callback_wall_max_sec=round(max(gaps),6),
            callback_wall_p95_sec=_pct(gaps,.95),
            callback_wall_p99_sec=_pct(gaps,.99),
            output_speed_nonzero_count=sum(abs(x)>.001 for x in steady_speeds),
            source='native_nav2_collision_monitor_ros_jazzy',
        )
        if (status['callback_wall_max_sec']>=.15
                or status['output_speed_nonzero_count']<20
                or (worker is not None and
                    status['cm_max_gap_during_gazebo_service_sec']>=.15)):
            status['status']='BLOCKED_CM_REAL_CADENCE_OR_OUTPUT'
            raise RuntimeError('NATIVE_CM_L1_150MS_GAP_OR_NO_SLOWDOWN')
        if stop_front_m is not None:
            # The range comes from ACTUAL GPU LiDAR in real Gazebo, but
            # this isolated CM scan input is a REPLAYED message. Never
            # label it a true ROS bridge / moving Nav2 Goal integration.
            if type(stop_front_m) not in (int,float) or not .14<=stop_front_m<.4:
                raise RuntimeError('NATIVE_CM_NO_REAL_STOP_FRONT_TO_REPLAY')
            prior=len(receipts)
            for _ in range(20):
                publish_period(stop_front_m)
            for _ in range(5):
                rclpy.spin_once(node,timeout_sec=.02)
            stopped=speeds[prior:]
            status['measured_static_stop_front_replayed_m']=round(stop_front_m,6)
            status['stop_output_samples']=len(stopped)
            status['stop_zero_output_samples']=sum(abs(x)<.001 for x in stopped)
            status['stop_scan_is_synthetic_replay_of_real_gazebo_front']=True
            if len(stopped)<15 or any(abs(x)>.001 for x in stopped[4:]):
                status['status']='BLOCKED_CM_STOP_ZONE_REPLAY'
                raise RuntimeError('NATIVE_CM_REAL_GAZEBO_RANGE_REPLAY_NO_ZERO')
        print('D08_REAL_NAV2_CM_L1_TIMING_PASS '+json.dumps(status,sort_keys=True),flush=True)
    except Exception as e:
        status['blocker']=type(e).__name__+':'+str(e)[:250]
        print('D08_REAL_NAV2_CM_L1_TIMING_BLOCKED '+status['blocker'],flush=True)
    finally:
        if node is not None:
            node.destroy_node();rclpy.shutdown()
        # Owner wZBKMnXa: *numerical G07 was successful*, but real official
        # CM died -11 when simultaneous launch SIGINT raced its Scan and
        # TF cleanup. Test real lifecycle finalization BEFORE process signal
        # under already-running real Gazebo (still NO robot Goal).
        status['cm_lifecycle_finalized_before_signal']=False
        status['cm_exit_code']=None
        if proc.poll() is None and status['status']=='REAL_NAV2_CM_L1_CADENCE_PASS':
            try:
                for transition in ('deactivate','cleanup','shutdown'):
                    r=_cmd(['ros2','lifecycle','set','/collision_monitor',transition],timeout=12)
                    if r.returncode!=0 or 'success' not in r.stdout.lower():
                        raise RuntimeError('CM_LIFECYCLE_'+transition.upper()+'_NO_ACK')
                state=_cmd(['ros2','lifecycle','get','/collision_monitor'],timeout=8)
                if state.returncode!=0 or 'finalized' not in state.stdout.lower():
                    raise RuntimeError('CM_LIFECYCLE_FINALIZED_UNVERIFIED')
                status['cm_lifecycle_finalized_before_signal']=True
                print('D08_REAL_NATIVE_CM_LIFECYCLE_FINALIZED_BEFORE_SIGTERM',flush=True)
            except Exception as e:
                status['status']='BLOCKED_CM_ORDERED_LIFECYCLE'
                status['teardown_blocker']=str(e)[:230]
                print('D08_NATIVE_CM_ORDERED_TEARDOWN_BLOCKED '+status['teardown_blocker'],flush=True)
        if proc.poll() is None:
            os.killpg(proc.pid,signal.SIGTERM)
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=3)
                status['status']='BLOCKED_CM_FORCED_TEARDOWN'
        else:
            proc.wait(timeout=1)
        status['cm_exit_code']=proc.returncode
        status['cm_sigsegv_observed']=proc.returncode==-11
        if proc.returncode!=0 or not status['cm_lifecycle_finalized_before_signal']:
            status['status']='BLOCKED_CM_TEARDOWN_EXIT_OR_LIFECYCLE'
            print('D08_REAL_NAV2_CM_TEARDOWN_BLOCKED exit_code='+str(proc.returncode),flush=True)
        else:
            print('D08_REAL_NAV2_CM_TEARDOWN_EXIT_ZERO_PASS',flush=True)
        log.close()
        (out/'verdict.json').write_text(json.dumps(status,indent=2,sort_keys=True)+'\n')
    return 0 if status['status']=='REAL_NAV2_CM_L1_CADENCE_PASS' else 2

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    raise SystemExit(run(args.out))
