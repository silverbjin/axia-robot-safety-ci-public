"""Read-only G07 MVP SlowZone motion admission. Not for G05/G06 fault gates.
Actual CM 30% of supervised .13m/s is ~.039m/s, not motor inactivity.
"""
from __future__ import annotations
import math

ACTUAL_SLOW_MOTION_FLOOR_MPS=.015
REQUIRED_MAX_AGE_S=.5

def _finite(value):
    return type(value) in (int,float) and math.isfinite(value)

def admit_g07_mvp_slow_motion(snapshot:dict,observed:dict)->tuple[bool,str]:
    if not isinstance(snapshot,dict) or not isinstance(observed,dict):
        return False,'G07_MVP_NO_LIVE_SNAPSHOT'
    if snapshot.get('final_publishers')!=[
        ('axia_base_command_guard','geometry_msgs/msg/Twist')]:
        return False,'G07_MVP_FINAL_PUBLISHER_NOT_UNIQUE'
    if (not isinstance(snapshot.get('goal_uuid'),str)
            or len(snapshot['goal_uuid'])!=32
            or snapshot.get('action_status')!=2):
        return False,'G07_MVP_OWNED_EXECUTING_GOAL_MISSING'
    guard=snapshot.get('guard')
    if (not isinstance(guard,dict) or guard.get('latched') is not False
            or guard.get('reason')!='FORWARDING_MONITORED_CM'):
        return False,'G07_MVP_GUARD_NOT_FORWARDING'
    now=snapshot.get('mono')
    if not _finite(now) or not snapshot.get('clock_advancing'):
        return False,'G07_MVP_CLOCK_UNAVAILABLE'
    for source in ('scan','odom','guard','supervisor','clock',
                   'final','pre_guard','supervised'):
        at=snapshot.get(source+'_at')
        if not _finite(at) or not 0<=now-at<=REQUIRED_MAX_AGE_S:
            return False,'G07_MVP_STALE_'+source.upper()
    action_at=snapshot.get('action_at')
    if not _finite(action_at) or not 0<=now-action_at<=15:
        return False,'G07_MVP_ACTION_TRANSITION_UNVERIFIED'
    for name in ('odom_speed','final_speed','pre_guard_speed'):
        v=snapshot.get(name)
        if not _finite(v) or v<ACTUAL_SLOW_MOTION_FLOOR_MPS:
            return False,'G07_MVP_NO_POSITIVE_'+name.upper()
    distance=observed.get('scan')
    vin=observed.get('vin')
    pre=observed.get('pre')
    if not _finite(distance) or not .4<distance<.75:
        return False,'G07_MVP_LASER_NOT_IN_SLOWZONE'
    if not isinstance(vin,list) or not vin or not isinstance(pre,list) or not pre:
        return False,'G07_MVP_CM_TWIST_EVIDENCE_MISSING'
    input_cmd,output_cmd=vin[-1],pre[-1]
    if not isinstance(input_cmd,dict) or not isinstance(output_cmd,dict):
        return False,'G07_MVP_CM_TWIST_INVALID'
    for cmd in (input_cmd,output_cmd):
        if (not _finite(cmd.get('t')) or not 0<=now-cmd['t']<=.5
                or not _finite(cmd.get('vx')) or not _finite(cmd.get('wz'))):
            return False,'G07_MVP_CM_TWIST_STALE_OR_NONFINITE'
    if not (input_cmd['vx']>.05 and
            ACTUAL_SLOW_MOTION_FLOOR_MPS<=output_cmd['vx']<=.30*input_cmd['vx']+.01):
        return False,'G07_MVP_CM_SLOWDOWN_NOT_PROVEN'
    if (abs(snapshot['final_speed']-output_cmd['vx'])>.025
            or abs(snapshot['odom_speed']-snapshot['final_speed'])>.025):
        return False,'G07_MVP_COMMAND_ODOM_DISAGREEMENT'
    return True,'G07_MVP_ACTUAL_GUARDED_SLOWZONE_MOTION'
