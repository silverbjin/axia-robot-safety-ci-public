#!/usr/bin/env python3
"""Real Jazzy native Nav2 LifecycleManager STARTUP readiness L1, NO Goal.

Use transient private teacher preflight file from a *public sealed* Actions
checkout. No teacher source/logs ever printed/uploaded.
- Missing lifecycle get_state reproduces the Jazzy manager's blocking
  client-initialization condition while /manage_nodes endpoint exists.
- Real official CM valid service: preflight READY, command=0 exactly ONCE,
  manager success reply AND CM state ACTIVE; then command=4 cleanup.
NO Gazebo/Goal/cmd_vel or certified E-Stop claims.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

MANAGER='/opt/ros/jazzy/lib/nav2_lifecycle_manager/lifecycle_manager'
CM='/opt/ros/jazzy/lib/nav2_collision_monitor/collision_monitor'

def start(args,env,path):
    with open(path,'w') as log:
        return subprocess.Popen(args,stdout=log,stderr=subprocess.STDOUT,
                                start_new_session=True,env=env)
def stop(proc,*,allow_missing=False):
    if proc is None:return None
    if proc.poll() is None:
        try:os.killpg(proc.pid,signal.SIGINT)
        except ProcessLookupError:pass
        try:proc.wait(timeout=6)
        except subprocess.TimeoutExpired:
            try:os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            proc.wait(timeout=4)
            if not allow_missing:
                raise RuntimeError('NATIVE_ROS_PROCESS_SHUTDOWN_FORCED')
    if not allow_missing and proc.returncode!=0:
        raise RuntimeError('NATIVE_ROS_PROCESS_NONZERO:'+str(proc.returncode))
    return proc.returncode

def invoke_preflight(preflight,folder,env,deadline=12):
    p=folder/'prerequisites.json'
    cmd=[sys.executable,str(preflight),'--output',str(p),
         '--deadline-s',str(deadline)]
    out=subprocess.run(cmd,env=env,capture_output=True,text=True,
                       timeout=deadline+14)
    if not p.is_file():
        raise RuntimeError('NAV_MANAGER_PREFLIGHT_NO_EVIDENCE')
    report=json.loads(p.read_text())
    return out.returncode,report

def call_manager(command,domain,timeout=40):
    import rclpy
    from nav2_msgs.srv import ManageLifecycleNodes
    from lifecycle_msgs.srv import GetState
    rclpy.init()
    node=rclpy.create_node('axia_ci_nav_manager_startup_client')
    try:
        cli=node.create_client(ManageLifecycleNodes,
                               '/lifecycle_manager_navigation/manage_nodes')
        if not cli.wait_for_service(timeout_sec=8):
            raise RuntimeError('NAV_MANAGER_MANAGE_NODES_SERVICE_MISSING')
        req=ManageLifecycleNodes.Request();req.command=command
        sent=time.monotonic()
        future=cli.call_async(req)
        rclpy.spin_until_future_complete(node,future,timeout_sec=timeout)
        if not future.done() or future.exception() is not None:
            raise RuntimeError('NAV_MANAGER_MANAGE_NODES_NO_REPLY')
        if not future.result().success:
            raise RuntimeError('NAV_MANAGER_MANAGE_NODES_REJECTED')
        state_cli=node.create_client(GetState,'/collision_monitor/get_state')
        if not state_cli.wait_for_service(timeout_sec=8):
            raise RuntimeError('NATIVE_CM_GET_STATE_NOT_AVAILABLE')
        state_future=state_cli.call_async(GetState.Request())
        rclpy.spin_until_future_complete(node,state_future,timeout_sec=8)
        if not state_future.done() or state_future.exception() is not None:
            raise RuntimeError('NATIVE_CM_GET_STATE_UNRESPONSIVE')
        state=state_future.result().current_state
        required=3 if command==0 else 4
        if int(state.id)!=required:
            raise RuntimeError('NATIVE_CM_STATE_MISMATCH:'+str(state.id))
        return dict(command=command,ack=True,
                    elapsed_sec=round(time.monotonic()-sent,6),
                    cm_state_id=int(state.id),cm_state_label=state.label)
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

def run(preflight:Path,out:Path):
    from d08_real_nav2_cm_l1 import CFG
    out.mkdir(parents=True,exist_ok=True)
    for file in (MANAGER,CM,preflight):
        if not Path(file).is_file():raise RuntimeError('REAL_NATIVE_FILE_MISSING')
    verdict={'status':'BLOCKED','actual_nav2_manager_binary':True,
             'actual_cm_binary':True,'actual_ros':True,
             'gazebo_run':False,'goal_sent':False,'cmd_vel_robot_published':False,
             'certified_estop':False,'teacher_source_published':False}
    try:
        # RED condition: real official Nav2 manager blocks waiting for
        # an intentionally nonexistent managed get_state service.
        env=os.environ.copy()
        env['ROS_DOMAIN_ID']='65'
        env['ROS_AUTOMATIC_DISCOVERY_RANGE']='LOCALHOST'
        missing_yaml=out/'missing_manager.yaml'
        missing_yaml.write_text('''lifecycle_manager_navigation:
  ros__parameters:
    autostart: false
    node_names: [axia_ci_missing_navigation_node]
    bond_timeout: 4.0
''')
        manager=None
        try:
            manager=start([MANAGER,'--ros-args','-r',
                           '__node:=lifecycle_manager_navigation',
                           '--params-file',str(missing_yaml)],env,
                          out/'manager_missing.log')
            rc,negative=invoke_preflight(preflight,out/'negative',env,deadline=9)
            if (rc!=2 or negative.get('reason')!='NAV_LIFECYCLE_SERVICE_MISSING'
                    or '/axia_ci_missing_navigation_node/get_state'
                    not in negative.get('missing',[])):
                raise RuntimeError('REAL_MISSING_ENDPOINT_RED_NOT_REPRODUCED:'+
                                   negative.get('reason','NO_REASON'))
            verdict['missing_endpoint_reproduced']=True
            verdict['negative_probe']=negative['reason']
            print('AXIA_FISQMVZZ_REAL_NAV_MANAGER_MISSING_LIFECYCLE_ENDPOINT_RED_CONFIRMED',flush=True)
        finally:
            stop(manager,allow_missing=True)
        # GREEN condition: actual CM native binary responds to get_state,
        # official Nav2 manager accepts a single STARTUP, CM ACTIVE.
        env=os.environ.copy()
        env['ROS_DOMAIN_ID']='66'
        env['ROS_AUTOMATIC_DISCOVERY_RANGE']='LOCALHOST'
        good_yaml=out/'valid_manager.yaml'
        good_yaml.write_text('''lifecycle_manager_navigation:
  ros__parameters:
    autostart: false
    node_names: [collision_monitor]
    bond_timeout: 4.0
''')
        cm_yaml=out/'collision_monitor.yaml'
        cm_yaml.write_text(CFG)
        manager=cm=None
        try:
            cm=start([CM,'--ros-args','--params-file',str(cm_yaml)],env,
                     out/'collision_monitor.log')
            manager=start([MANAGER,'--ros-args','-r',
                           '__node:=lifecycle_manager_navigation',
                           '--params-file',str(good_yaml)],env,
                          out/'manager_real.log')
            rc,positive=invoke_preflight(preflight,out/'positive',env,deadline=22)
            if rc!=0 or positive.get('status')!='READY' or not (
                positive.get('managed_nodes')==['collision_monitor']):
                raise RuntimeError('REAL_NAV_MANAGER_VALID_SERVICE_NOT_READY:'+
                                   positive.get('reason','NO_REASON'))
            verdict['valid_lifecycle_get_state_preflight']=True
            print('AXIA_FISQMVZZ_REAL_NAV_MANAGER_LIFECYCLE_PREREQUISITES_GREEN',flush=True)
            started=call_manager(0,66,timeout=40)
            stopped=call_manager(4,66,timeout=30)
            verdict['nav_startup']=started
            verdict['nav_shutdown']=stopped
            print('AXIA_FISQMVZZ_REAL_NAV_MANAGER_STARTUP_ACK_CM_ACTIVE_PASS',flush=True)
        finally:
            native_cm_exit=stop(cm)
            nav_manager_exit=stop(manager)
        verdict.update(status='PASS_REAL_NAV_MANAGER_L1_NO_GOAL',
                       native_cm_exit=native_cm_exit,
                       manager_exit=nav_manager_exit)
        print('AXIA_FISQMVZZ_REAL_NAV_MANAGER_L1_GREEN_NO_GOAL',flush=True)
    except Exception as exc:
        verdict['failure_class']=type(exc).__name__
        verdict['status']='BLOCKED_REAL_NAV_MANAGER_L1'
        print('AXIA_FISQMVZZ_REAL_NAV_MANAGER_L1_BLOCKED class='+
              type(exc).__name__,flush=True)
    (out/'verdict.json').write_text(json.dumps(verdict,indent=2,
                                              sort_keys=True)+'\n')
    return 0 if verdict['status']=='PASS_REAL_NAV_MANAGER_L1_NO_GOAL' else 2

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--preflight',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    raise SystemExit(run(args.preflight,args.out))
